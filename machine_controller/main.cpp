#include <hardware/gpio.h>
#include <pico/time.h>

#define LED_PIN 25
#define BLINK_DELAY 100
void blink(int count) {
  // debug blink convenience function
  for (int blinked; blinked < count; blinked++) {
    gpio_put(LED_PIN, 1);
    sleep_ms(BLINK_DELAY);
    gpio_put(LED_PIN, 0);
    sleep_ms(BLINK_DELAY);
  }
}
int main() {
  gpio_init(LED_PIN);
  gpio_set_dir(LED_PIN, GPIO_OUT);
  int step_pin = 4;
  int dir_pin = 5;
  gpio_init(dir_pin);
  gpio_init(step_pin);
  gpio_set_dir(step_pin, GPIO_OUT);
  gpio_set_dir(dir_pin, GPIO_OUT);

  blink(1);
  gpio_put(dir_pin, 1);

  while (true) {
    blink(1);
    gpio_put(step_pin, 1);
    blink(1);
    gpio_put(step_pin, 0);
  }
  return 0;
}
