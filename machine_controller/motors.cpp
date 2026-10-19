#include "coms_protocol.hpp"
#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <dma_uart.hpp>
#include <hardware/gpio.h>
#include <hardware/irq.h>
#include <hardware/regs/intctrl.h>
#include <hardware/structs/timer.h>
#include <hardware/sync/spin_lock.h>
#include <hardware/timer.h>
#include <motors.hpp>
#include <pico/platform/common.h>
#include <pico/time.h>
#include <pico/types.h>
#include <sys/unistd.h>
#include <utility>
#include <vector>

using namespace std;

// hw alarm set target but tolerant of lateness
Motor::Motor(const vector<int> &argumentVector)
    : step_pin(argumentVector[STP_PIN]), dir_pin(argumentVector[DIR_PIN]),
      lim_pin(argumentVector[LIM_PIN]),
      lim_pin_stp_position(argumentVector[LIM_STP_POS]),
      dir_pin_inverted(argumentVector[INVERSION]),
      stp_per_rev(argumentVector[STP_PER_REV]), position_state(0),
      direction(1) {
  if (lim_pin != -1) {
    gpio_init(lim_pin);
    gpio_set_dir(lim_pin, GPIO_IN);
    gpio_pull_up(lim_pin);
  }
  gpio_init(dir_pin);
  gpio_init(step_pin);
  gpio_set_dir(step_pin, GPIO_OUT);
  gpio_set_dir(dir_pin, GPIO_OUT);
  gpio_put(dir_pin, dir_pin_inverted);
}

void Motor::buzz(int cycles) {
  float buzz_amplitude_deg = 3.6;

  int amp_steps = (int)(buzz_amplitude_deg / (360.f / (float)stp_per_rev));
  if (amp_steps < 0) {
    amp_steps = 1;
  }
  for (int cycle_count = 0; cycle_count < cycles; cycle_count++) {
    for (int stpcnt = 0; stpcnt < amp_steps; stpcnt++) {
      step();
      sleep_ms(5);
    }
    set_dir(-direction);
  }
}

void Motor::set_dir(int dir) {
  direction = dir;
  bool bin_dir = direction > 0;
  if (dir_pin_inverted) {
    bin_dir = !bin_dir;
  }
  gpio_put(dir_pin, bin_dir);
}

void Motor::step() {
  gpio_put(step_pin, 1);
  busy_wait_us_32(1);
  gpio_put(step_pin, 0);
  position_state += direction;
}

MoveEntity::MoveEntity(uint8_t profile_id, float angv_max, float ang_accel,
                       int step_distance, Motor *motor)
    : profile_id(profile_id), angv_max(angv_max), ang_accel(ang_accel),
      step_distance(step_distance), motor(motor), calculation_step_index(0),
      hit_limit(false), is_complete(false), homing(false) {

  angular_distance = motor->TORADS * step_distance;
  abs_ang_dist = abs(angular_distance);
  abs_stp_dist = abs(step_distance);

  float v_reached = angv_max;
  bool short_hop = abs_ang_dist < ((angv_max * angv_max) / ang_accel);
  accel_stop = (v_reached * v_reached) / (2. * ang_accel);
  const_stop = (abs_ang_dist - (v_reached * v_reached) / (2 * ang_accel));

  if (profile_id == TRAPEZOIDAL) {
    if (short_hop) {
      accel_stop = const_stop = abs_ang_dist / 2;
      total_move_time = 2 * sqrt(abs_ang_dist / ang_accel);
    } else {
      total_move_time = (abs_ang_dist / v_reached + v_reached / ang_accel);
    }
  }
  if (profile_id == NO_ACCEL) {
    accel_stop = 0;
    total_move_time = abs_ang_dist / v_reached + v_reached / (2 * ang_accel);
  }
  if (profile_id == NO_DECEL) {
    const_stop = abs_ang_dist + 1;
    total_move_time = abs_ang_dist / v_reached + v_reached / (2 * ang_accel);
  }
  if (profile_id == LINEAR) {
    accel_stop = 0;
    const_stop = abs_ang_dist + 1;
    total_move_time = abs_ang_dist / v_reached;
  }
  return;
}

uint32_t MoveEntity::find_step_timing() {
  if (calculation_step_index == abs_stp_dist || hit_limit) {
    is_complete = true;
    return 0;
  }
  if (calculation_step_index == 0) {
    move_init_time = time_us_32();
  }
  calculation_step_index += 1;
  double theta = motor->TORADS * (calculation_step_index);
  double stepTiming;

  if (profile_id == TRAPEZOIDAL) {
    if (theta < accel_stop) {
      stepTiming = sqrt((2 * theta) / ang_accel);
    } else if (theta < const_stop) {
      stepTiming = (theta / angv_max) + (angv_max / (2. * ang_accel));
    } else {
      stepTiming =
          total_move_time - sqrt((2 * (abs_ang_dist - theta)) / ang_accel);
    }
  } else if (profile_id == NO_DECEL) {
    if (theta < accel_stop) {
      stepTiming = sqrt((2 * theta) / ang_accel);
    } else {
      stepTiming = (theta / angv_max) + (angv_max / (2. * ang_accel));
    }
  } else if (profile_id == LINEAR) {
    stepTiming = (theta / angv_max);
  } else if (profile_id == NO_ACCEL) {
    if (theta < const_stop) {
      stepTiming = (theta / angv_max);
    } else {
      stepTiming =
          total_move_time - sqrt((2 * (abs_ang_dist - theta)) / ang_accel);
    }
  }
  uint64_t next_step_time = (uint64_t)(stepTiming * 1e6f);
  return next_step_time;
}

void set_stp_alarm(int alarm_num, uint32_t rel_time, MoveEntity * move){
    uint32_t time = delayed_by_us(rel_time, move->move_init_time);
    if (hardware_alarm_set_target(alarm_num, time)) {
      auto missed_by = ((int32_t)timer_hw->timelr - (int32_t)time);
      move->move_init_time += missed_by;
      hardware_alarm_force_irq(alarm_num);
    }
}

// behold... the sorted step queue torus
static array<StepAlarmQueue *, ALARM_COUNT> step_queues;
static int alarm_write_index = 0;

void init_step_queues() { // call on core 0, BEFORE multicore_launch_core1
  for (int i = 0; i < ALARM_COUNT; i++) {
    step_queues[i] = new StepAlarmQueue();
    step_queues[i]->alarm_number = i;
  }
}

static int num = spin_lock_claim_unused(true);
static spin_lock_t *queue_lock = spin_lock_init(num);

void alarm_isr(uint alarm_num) {
  StepAlarmQueue &q = *step_queues[alarm_num];
  q.alarm_callback();
  if (q.time_target != 0) {
    set_stp_alarm(alarm_num, q.time_target, q.circ_queue[q.read_index].move);
  }
}

// only need to set the handler via the api on core 1 because core 0 and 1
// share alarm interrupts so regardless of who sets the actual time, they both
// catch it. however, the irq_set_exclusive_handler function implicitly
// handles the callback from the assigning core
void core1_main() {
  for (int i = 0; i < ALARM_COUNT; i++) {
    hardware_alarm_claim(i);
    hardware_alarm_set_callback(i, (hardware_alarm_callback_t)alarm_isr);
  }
  while (true)
    tight_loop_contents();
}

void StepAlarmQueue::alarm_callback() {
  MoveEntity &move = *circ_queue[read_index].move;
  Motor &mot = *move.motor;
  if (move.homing && mot.lim_pin != -1 && !gpio_get(mot.lim_pin))
    move.hit_limit = true;
  if (!move.hit_limit)
    mot.step();
  queue_count--;
  read_index = (read_index + 1) & AQ_MASK;
  if (queue_count > 0)
    time_target = circ_queue[read_index].time;
  else
    time_target = 0;
}


void enqueue_next_step(MoveEntity *move) {
  uint32_t next_timing = move->find_step_timing();
  if (move->is_complete) {
    return;
  }
  Step_Event stp_to_queue = {next_timing, move};
  // idle until open queue found
  StepAlarmQueue *queue_ptr = step_queues[alarm_write_index];
  while (queue_ptr->queue_count == ALARM_QUEUE_LENGTH) {
    alarm_write_index = (alarm_write_index + 1) & (ALARM_COUNT - 1);
    queue_ptr = step_queues[alarm_write_index];
  }

  StepAlarmQueue &queue = *queue_ptr;

  if (queue.queue_count == 0) { // first step in queue
    queue.time_target = next_timing;
    queue.circ_queue[queue.read_index] = stp_to_queue;
    queue.write_index = (queue.write_index + 1) & AQ_MASK;
    // set initial alarm
    set_stp_alarm(queue.alarm_number, next_timing, move);

  } else if (next_timing < queue.time_target) {
    queue.read_index = (queue.read_index - 1 + ALARM_QUEUE_LENGTH) & AQ_MASK;
    queue.time_target = next_timing;
    queue.circ_queue[queue.read_index] = stp_to_queue;
    // wrote timing before current target and thus need to push target ahead
    set_stp_alarm(queue.alarm_number, next_timing, move);
  } else {
    int i = queue.write_index;
    queue.circ_queue[i] = stp_to_queue;
    queue.write_index = (i + 1) & AQ_MASK;
    while (i != queue.read_index) {
      int j = (i - 1) & AQ_MASK;
      if (queue.circ_queue[j].time > queue.circ_queue[i].time) {
        swap(queue.circ_queue[j], queue.circ_queue[i]);
        i = j;
      } else
        break;
    }
  }
  queue.queue_count++;
  alarm_write_index = (alarm_write_index + 1) & (ALARM_COUNT - 1);
}

void await_async_move(vector<MoveEntity> &moves) {
  for (auto &move : moves) {
    Motor &mot = *move.motor;
    int direction = abs(move.step_distance) / move.step_distance;
    mot.set_dir(direction);
  }
  bool all_complete = false;
  while (!all_complete) {
    all_complete = true;
    for (auto &move : moves) {
      if (!move.is_complete) {
        enqueue_next_step(&move);
      }
      all_complete = move.is_complete && all_complete;
    }
  }
  int total_waiting = 0;
  do {
    total_waiting = 0;
    for (auto &queue : step_queues) {
      total_waiting += queue->queue_count;
    }
  } while (total_waiting != 0);
}
