#include "coms_protocol.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <dma_uart.hpp>
#include <hardware/gpio.h>
#include <hardware/irq.h>
#include <hardware/regs/intctrl.h>
#include <hardware/structs/timer.h>
#include <hardware/timer.h>
#include <motors.hpp>
#include <pico/platform/common.h>
#include <pico/time.h>
#include <sys/unistd.h>
#include <utility>
#include <vector>

using namespace std;

Motor::Motor(const vector<int> &argumentVector)
    : step_pin(argumentVector[STP_PIN]), dir_pin(argumentVector[DIR_PIN]),
      lim_pin(argumentVector[LIM_PIN]),
      dir_pin_inverted(argumentVector[INVERSION]),
      stp_per_rev(argumentVector[STP_PER_REV]), position_state(0),
      direction(1) {
  if (lim_pin != -1) {
    gpio_init(lim_pin);
    gpio_set_dir(lim_pin, GPIO_IN);
  }
  gpio_init(dir_pin);
  gpio_init(step_pin);
  gpio_set_dir(step_pin, GPIO_OUT);
  gpio_set_dir(dir_pin, GPIO_OUT);
  gpio_put(dir_pin, dir_pin_inverted);
}

void Motor::buzz() {

  float buzz_amplitude_deg = 3.6;

  int amp_steps = (int)(buzz_amplitude_deg / (360.f / (float)stp_per_rev));
  if (amp_steps < 0) {
    amp_steps = 1;
  }
  for (int cycle_count = 0; cycle_count < 50; cycle_count++) {
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
  sleep_us(1);
  gpio_put(step_pin, 0);
  position_state += direction;
}

MoveEntity::MoveEntity(int profile_id, float angv_max, float ang_accel,
                       int step_distance, Motor *motor)
    : profile_id(profile_id), angv_max(angv_max), ang_accel(ang_accel),
      step_distance(step_distance), motor(motor), calculation_step_index(0),
      hit_limit(false), is_complete(false) {
  angular_distance = motor->TORADS * step_distance;
  abs_ang_dist = abs(angular_distance);
  abs_stp_dist = abs(step_distance);

  float v_reached = angv_max;
  bool short_hop = abs_ang_dist < ((float)(angv_max * angv_max) / ang_accel);
  accel_stop = (v_reached * v_reached) / (2. * ang_accel);
  const_stop = (abs_ang_dist - (v_reached * v_reached) / (2 * ang_accel));

  if (profile_id == TRAPEZOIDAL) {
    total_move_time = (abs_ang_dist / v_reached + v_reached / ang_accel);
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

uint64_t MoveEntity::find_step_timing() {
  if (calculation_step_index == abs_stp_dist || hit_limit) {
    is_complete = true;
    return 0;
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
          total_move_time - sqrt((2 * (angular_distance - theta)) / ang_accel);
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
          total_move_time - sqrt((2 * (angular_distance - theta)) / ang_accel);
    }
  }
  next_timing = move_init_time + (uint64_t)(stepTiming * 1e6f);
  return next_timing;
}

// behold... the sorted step queue torus
#define alarm_count 4
static array<StepAlarmQueue *, alarm_count> step_queues;
static int alarm_write_index = 0;
static volatile int currently_in_isr = -1;

void alarm_isr(uint alarm_num) {
  currently_in_isr = alarm_num;
  hw_clear_bits(&timer_hw->intr, 1u << alarm_num);
  StepAlarmQueue &queue = *step_queues[alarm_num];
  int lim_pin = queue.circ_queue[queue.read_index]->motor->lim_pin;
  if (lim_pin > 0) {
    if (gpio_get(lim_pin)) {
      queue.circ_queue[queue.read_index]->hit_limit = true;
    }
  }
  queue.alarm_callback();
  if ((uint32_t)(queue.time_target - timer_hw->timelr) <= 0) {
    alarm_isr(alarm_num);
  }
  hardware_alarm_set_target(alarm_num, queue.time_target);
  currently_in_isr = -1;
}

static void (*alarm_isrs[])() = {
    []() -> void { alarm_isr(0); },
    []() -> void { alarm_isr(1); },
    []() -> void { alarm_isr(2); },
    []() -> void { alarm_isr(3); },
};

// only need to set the handler via the api on core 1 because core 0 and 1
// share alarm interrupts so regardless of who sets the actual time, they both
// catch it. however, the irq_set_exclusive_handler function implicitly
// handles the callback from the assigning core
void core1_main() {
  for (int timer_ind = 0; timer_ind < alarm_count; timer_ind++) {
    hardware_alarm_claim(timer_ind);
    step_queues[timer_ind] = new StepAlarmQueue();
    irq_set_enabled(timer_ind, false);
    irq_set_exclusive_handler(timer_ind, alarm_isrs[timer_ind]);
    irq_set_enabled(timer_ind, true);
    timer_hw->inte |= 1u << timer_ind;
  }
  while (true) {
    tight_loop_contents();
  }
}

void StepAlarmQueue::alarm_callback() {
  MoveEntity &entity = *circ_queue[read_index];
  entity.motor->step();
  queue_count -= 1;
  read_index = (read_index + 1) % ALARM_QUEUE_LENGTH;
  if (queue_count == 0) {
    return;
  };
  time_target = circ_queue[read_index]->next_timing;
}

void enqeue_next_step(MoveEntity *move) {
  uint64_t next_timing = move->find_step_timing();
  if (next_timing == 0) {
    return;
  }
  // idle until open queue found
  StepAlarmQueue &queue = *step_queues[alarm_write_index];
  do {
    StepAlarmQueue &queue = *step_queues[alarm_write_index];
    alarm_write_index = (alarm_write_index + 1) % alarm_count;
  } while (queue.queue_count == ALARM_QUEUE_LENGTH);

  if (queue.queue_count == 0) {
    queue.time_target = next_timing;
    queue.circ_queue[queue.read_index] = move;
    hardware_alarm_set_target(queue.alarm_number, next_timing);
    queue.write_index = (queue.write_index + 1) % ALARM_QUEUE_LENGTH;
  } else if (next_timing < queue.time_target) {
    while (currently_in_isr == alarm_write_index) {
      tight_loop_contents();
    }
    queue.read_index =
        (queue.read_index + ALARM_QUEUE_LENGTH - 1) % ALARM_QUEUE_LENGTH;
    queue.time_target = next_timing;
    queue.circ_queue[queue.read_index] = move;
    hardware_alarm_set_target(queue.alarm_number, next_timing);
  } else {
    queue.circ_queue[queue.write_index] = move;
    queue.write_index = (queue.write_index + 1) % ALARM_QUEUE_LENGTH;
    int prev = queue.write_index;
    for (int i = prev; i != queue.write_index;
         i = (i + ALARM_QUEUE_LENGTH - 1) % ALARM_QUEUE_LENGTH) {
      int j = (i + ALARM_QUEUE_LENGTH - 1) % ALARM_QUEUE_LENGTH;
      MoveEntity *just_added = queue.circ_queue[i];
      MoveEntity *candidate = queue.circ_queue[j];
      if (candidate->next_timing > just_added->next_timing) {
        swap(candidate, just_added);
      } else {
        break;
      }
    }
  }
  queue.queue_count += 1;
}

void await_async_move(vector<MoveEntity> moves) {
  for (auto &move : moves) {
    Motor &mot = *move.motor;
    int direction = abs(move.step_distance) / move.step_distance;
    mot.set_dir(direction);
  }
  bool all_complete = false;
  for (auto &move : moves) {
    move.move_init_time = get_absolute_time();
  }
  while (!all_complete) {
    all_complete = true;
    for (auto &move : moves) {
      if (!move.is_complete) {
        enqeue_next_step(&move);
      } else {
        all_complete = move.is_complete && all_complete;
      }
    }
  }
}
