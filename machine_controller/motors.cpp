#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <dma_uart.hpp>
#include <hardware/gpio.h>
#include <hardware/timer.h>
#include <motors.hpp>
#include <pico/time.h>
#include <vector>

using namespace std;

void Motor::move_isr(uint alarm_num) {
  Motor *mot = Motor::async_bay[alarm_num];
  int init_move = mot->move_callback();
}

Motor::Motor(const vector<int> &argumentVector, bool non_async = false)
    : step_pin(argumentVector[step_pin_arg]),
      dir_pin(argumentVector[dir_pin_arg]),
      stp_per_rev(argumentVector[stp_per_rev_arg]),
      vMax(argumentVector[ang_v_max_arg]),
      ang_accel(argumentVector[ang_accel_arg]), live_abs_pos(0),
      move_delta(0), current_position(0), direction(1) {

  gpio_init(dir_pin);
  gpio_init(step_pin);
  gpio_set_dir(step_pin, GPIO_OUT);
  gpio_set_dir(dir_pin, GPIO_OUT);

  buzz();
  // calculate acceleration constant factor
  if (!non_async) {
    Motor::async_bay.push_back(this);
    alarm_num = hardware_alarm_claim_unused(true);
    hardware_alarm_set_callback(alarm_num, (hardware_alarm_callback_t)move_isr);
  }
}

void Motor::buzz() {

  float buzz_amplitude_deg = 1.8;

  int amp_steps = (int)(buzz_amplitude_deg / (360.f / (float)stp_per_rev));

  if (amp_steps < 0) {
    amp_steps = 1;
  }
  move_delta = 1;
  for (int cycle_count = 0; cycle_count < 100; cycle_count++) {
    for (int stpcnt = 0; stpcnt < amp_steps; stpcnt++) {
      step();
      sleep_ms(1);
    }
    move_delta *= -1;
    update_dir();
  }
}

void Motor::update_dir() {
  direction = move_delta / abs(move_delta);
  bool bin_dir = direction > 0;
  gpio_put(dir_pin, bin_dir);
}
void Motor::step() {
  // step logic
  gpio_put(step_pin, 1);
  sleep_us(1);
  gpio_put(step_pin, 0);
  current_position += direction;
  live_abs_pos++;
  // set calculate flag high
}

void Motor::move_precalc() {
  ang_targ_dist = TORADS * abs(move_delta); // gets the total distance of
                                            // the move in rads
  float v_reached = vMax;

  // if the max v isnt reached by halfway
  // we use the highest v reached as the
  // vmax in our calculations

  bool short_hop = (ang_targ_dist / 2) < ((float)(vMax * vMax) / ang_accel);
  if (short_hop) {
    v_reached = sqrt(ang_targ_dist * ang_accel);
  }

  accel_stop = (v_reached * v_reached) / (2 * ang_accel);
  constv_stop = (ang_targ_dist - (v_reached * v_reached) / (2 * ang_accel));

  total_move_time = (ang_targ_dist / v_reached + v_reached / ang_accel);

  return;
}

int Motor::move_callback() {

  step();

  if (live_abs_pos == move_delta) {
    return 0;
  }

  double theta = TORADS * (live_abs_pos + 1);
  double stepTiming;
  if (theta < accel_stop) {
    stepTiming = sqrt((2 * theta) / ang_accel);
  } else if (theta < constv_stop) {
    stepTiming = (theta / vMax) + (vMax / (2. * ang_accel));
  } else {
    stepTiming =
        total_move_time - sqrt((2 * (ang_targ_dist - theta)) / ang_accel);
  }
  uint64_t next_step_time = (uint64_t)(stepTiming * 1e6f);
  hardware_alarm_set_target(alarm_num,
                            delayed_by_us(move_init_time, next_step_time));
  return 0;
}
