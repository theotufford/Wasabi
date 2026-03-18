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
      ang_v_max(argumentVector[ang_v_max_arg]),
      ang_accel(argumentVector[ang_accel_arg]), live_abs_pos(0),
      target_distance(0), current_position(0), direction(1) {

  gpio_init(dir_pin);
  gpio_init(step_pin);
  gpio_set_dir(step_pin, GPIO_OUT);
  gpio_set_dir(dir_pin, GPIO_OUT);

  buzz();
  // calculate acceleration constant factor
  accel_factor =
      (uint64_t)(pow(10, 6) *
                 (2.f * M_PI /
                  (sqrt(2 * ang_accel * stp_per_rev * stp_per_rev))));
  min_step_delay =
      (uint64_t)(pow(10, 6) * (2.f * M_PI / (ang_v_max * stp_per_rev)));
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
  target_distance = 1;
  for (int cycle_count = 0; cycle_count < 100; cycle_count++) {
    for (int stpcnt = 0; stpcnt < amp_steps; stpcnt++) {
      step();
      sleep_ms(1);
    }
    target_distance *= -1;
    update_dir();
  }
}

void Motor::update_dir() {
  if (target_distance == 0) {
    return;
  }
  direction = target_distance / abs(target_distance);
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

// needed for accel timing calculation
float fast_inv_sqrt(float stp) {
  uint32_t i;
  std::memcpy(&i, &stp, sizeof(float)); // Copy float bits to int
  i = 0x5f3759df - (i >> 1);            // quake bit magic
  float y;
  std::memcpy(&y, &i, sizeof(float)); // Copy int bits back to float
  y = y * (1.5f - (stp * 0.5f * y * y));
  return y;
}

int Motor::move_callback() {
  // this would be too convoluted to explain in comments
  // return to the step delay calc portion of the docs
  uint64_t delay;
  step();

  if (live_abs_pos == abs(target_distance)) {
    return 1;
  }

  if (live_abs_pos <= accel_stop) { // accel calc
    delay = (uint64_t)(fast_inv_sqrt((float)live_abs_pos)) * accel_factor;
  } else if (live_abs_pos <= constv_stop) {
    delay = min_step_delay;
  } else { // deccel calc
    delay = min_step_delay;
    // delay = (uint64_t)(fast_inv_sqrt(
    //             (float)(abs(target_distance) - live_abs_pos))) *
    //         accel_factor;
  }
  hardware_alarm_set_target(alarm_num,
                            delayed_by_us(get_absolute_time(), delay));
  return 0;
}
