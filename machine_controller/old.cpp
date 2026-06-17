#include <fiveBar.cpp>
#include <fiveBar.hpp>
#include <hardware/gpio.h>
#include <hardware/timer.h>
#include <pico/platform/common.h>
#include <pico/time.h>
#include <vector>

Motor *motor_target;
void step_callback(uint alarm_num) {
  motor_target->step();
  hardware_alarm_set_callback(alarm_num,
                              (hardware_alarm_callback_t)step_callback);

  auto time = get_absolute_time();
  hardware_alarm_set_target(
      alarm_num, delayed_by_us(get_absolute_time(), BLINK_DELAY * 1000 * 2));
}

int main() {
  gpio_init(LED_PIN);
  gpio_set_dir(LED_PIN, GPIO_OUT);
  int step_pin = 3;
  int dir_pin = 4;
  gpio_init(dir_pin);
  gpio_init(step_pin);
  gpio_set_dir(step_pin, GPIO_OUT);
  gpio_set_dir(dir_pin, GPIO_OUT);
  gpio_put(dir_pin, 1);
  vector<int> argvec = {step_pin, dir_pin, 200, 10, 10};
  Motor test(argvec);
  motor_target = &test;

  int async_alarm_num = hardware_alarm_claim_unused(true);

  hardware_alarm_set_callback(async_alarm_num,
                              (hardware_alarm_callback_t)step_callback);
  hardware_alarm_set_target(
      async_alarm_num,
      delayed_by_us(get_absolute_time(), BLINK_DELAY * 1000 * 2));

  while (true) {
    tight_loop_contents();
  }
  return 0;
}
