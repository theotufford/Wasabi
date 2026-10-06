#include <algorithm>
#include <array>
#include <cmath>
#include <csignal>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <dma_uart.hpp>
#include <exception>
#include <hardware/gpio.h>
#include <hardware/irq.h>
#include <hardware/timer.h>
#include <motors.hpp>
#include <pico/time.h>
#include <sys/unistd.h>
#include <tuple>
#include <utility>
#include <vector>

using namespace std;

Motor::Motor(const vector<int> &argumentVector)
    : step_pin(argumentVector[step_pin_arg]),
      dir_pin_inverted(argumentVector[invert_dir_arg]),
      dir_pin(argumentVector[dir_pin_arg]),
      stp_per_rev(argumentVector[stp_per_rev_arg]) {
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
  live_steps_moved = 1;
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
  live_steps_moved++;
}

MoveEntity::MoveEntity(int profile_id, float angv_max, float ang_accel,
                       int step_distance, Motor *motor)
    : profile_id(profile_id), angv_max(angv_max), ang_accel(ang_accel),
      step_distance(step_distance), motor(motor), calculation_step_index(0) {
  angular_distance = motor->TORADS * step_distance;
  float v_reached = angv_max;
  bool short_hop =
      (angular_distance / 2) < ((float)(angv_max * angv_max) / ang_accel);
  accel_stop = (v_reached * v_reached) / (2. * ang_accel);
  const_stop = (angular_distance - (v_reached * v_reached) / (2 * ang_accel));

  if (profile_id == TRAPEZOIDAL) {
    total_move_time = (angular_distance / v_reached + v_reached / ang_accel);
  }
  if (profile_id == NO_ACCEL) {
    accel_stop = 0;
    total_move_time =
        angular_distance / v_reached + v_reached / (2 * ang_accel);
  }
  if (profile_id == NO_DECEL) {
    const_stop = angular_distance + 1;
  }
  if (profile_id == LINEAR) {
    accel_stop = 0;
    const_stop = angular_distance + 1;
  }

  return;
}

uint64_t MoveEntity::find_step_timing() {

  if (calculation_step_index == step_distance) {
    return 0;
  }

  double theta = motor->TORADS * (calculation_step_index + 1);
  double stepTiming;

  if (theta < accel_stop) {
    stepTiming = sqrt((2 * theta) / ang_accel);
  } else if (theta < const_stop) {
    stepTiming = (theta / angv_max) + (angv_max / (2. * ang_accel));
  } else {
    stepTiming =
        total_move_time - sqrt((2 * (step_distance - theta)) / ang_accel);
  }

  uint64_t next_step_time =
      motor->move_init_time + (uint64_t)(stepTiming * 1e6f);
  return next_step_time;
}

#define alarm_count 4
int available_alarm_index = 0;
static array<StepAlarmQueue *, alarm_count> step_queues;
vector<StepAlarmQueue *> to_be_sorted;

StepAlarmQueue::StepAlarmQueue() {
  alarm_number = hardware_alarm_claim_unused(true);
  step_queues[alarm_number] = this;
}

StepAlarmQueue::~StepAlarmQueue() { hardware_alarm_unclaim(alarm_number); }

void StepAlarmQueue::alarm_callback() {
  MoveEntity *move = circ_queue[read_index];
  move->motor->step();
}

static void alarm_isr(int alarm_num) {}

void enqeue_next_step(MoveEntity *move) {
  uint64_t next_timing = move->find_step_timing();
  if (next_timing == 0) {
    return;
  }
  StepAlarmQueue &queue = *step_queues[available_alarm_index];
  do {
    StepAlarmQueue &queue = *step_queues[available_alarm_index];
    available_alarm_index = (available_alarm_index + 1) % alarm_count;
  } while (queue.queue_count == ALARM_QUEUE_LENGTH);

  if (next_timing < queue.next_timing) {
    queue.read_index =
        (queue.read_index + ALARM_QUEUE_LENGTH - 1) % ALARM_QUEUE_LENGTH;
    queue.next_timing = next_timing;
    queue.circ_queue[queue.read_index] = move;
    hardware_alarm_set_target(queue.alarm_number, next_timing);
  } else {
    queue.circ_queue[queue.write_index] = move;
    for (int i = queue.write_index;
         i != (queue.read_index + 1) % ALARM_QUEUE_LENGTH;
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
    queue.write_index = (queue.write_index + 1) % ALARM_QUEUE_LENGTH;
  }
}

void initiate_move(vector<MoveEntity> moves) {
  for (auto &move : moves) {
    enqeue_next_step(&move);
  }
}
