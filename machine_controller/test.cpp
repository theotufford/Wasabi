#include <hardware/gpio.h>
#include <pico/time.h>
#include <sys/unistd.h>
int main() {
  int stp1 = 28;
  int stp2 = 20;
  gpio_init(2);
  gpio_init(stp1);
  gpio_init(stp2);
  gpio_set_dir(2, GPIO_OUT);
  gpio_set_dir(stp1, GPIO_OUT);
  gpio_set_dir(stp2, GPIO_OUT);
  gpio_put(2, 1);
  while (true) {
    gpio_put(stp1, 1);
    gpio_put(stp2, 1);
    sleep_us(10);
    gpio_put(stp1, 0);
    gpio_put(stp2, 0);
    sleep_ms(60);
  }
}
