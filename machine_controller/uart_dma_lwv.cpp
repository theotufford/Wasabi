#include <cstdint>
#include <dma_uart.hpp>
#include <hardware/gpio.h>
#include <hardware/uart.h>
#include <hardware/watchdog.h>
#include <iostream>
#include <pico/time.h>
#include <pico/types.h>
#include <sys/_intsup.h>
#include <sys/unistd.h>
#include <time.h>

#define LED_PIN 25
#define BLINK_DELAY 300

void blink(int count) {
  for (int blinked; blinked < count; ++blinked) {
    gpio_put(LED_PIN, 1);
    sleep_ms(BLINK_DELAY);
    gpio_put(LED_PIN, 0);
    sleep_ms(BLINK_DELAY);
  }
}
int main() {
  gpio_init(LED_PIN);
  gpio_set_dir(LED_PIN, GPIO_OUT);
  blink(1);
  return 0;
}
