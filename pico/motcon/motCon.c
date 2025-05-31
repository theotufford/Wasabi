#include <stdio.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "pico/binary_info.h"

const uint LED_PIN = 25;
const uint STP_PIN = 4;
const uint DIR_PIN = 5;
const uint constant_delay = 100;

int main() {

  bi_decl(bi_program_description("This is a test binary."));
  bi_decl(bi_1pin_with_name(LED_PIN, "On-board LED"));
  stdio_init_all();

  gpio_init(LED_PIN);
  gpio_init(STP_PIN);
  gpio_init(DIR_PIN);

  gpio_set_dir(LED_PIN, GPIO_OUT);
  gpio_set_dir(STP_PIN, GPIO_OUT);
  gpio_set_dir(DIR_PIN, GPIO_OUT);
  //settings initialization 
  {
  int the_void;
  scanf("%d", &the_void);
  }

  //put initialization code here


  // control loop
  while (1) { // input loop
    int steps;
    int stepCount = 0;
    puts("\n");
    printf("input step count:\n");
    scanf("%d", &steps);
    printf("%d targeted\n", steps);

    if (steps > 0 ){ // invert by direction given by sign of $steps
      gpio_put(DIR_PIN, 1);
    } else {
      gpio_put(DIR_PIN, 0);
    }

    int delay = 1200;
    steps = abs(steps);
    while ( stepCount <= steps ){ // step loop
      gpio_put(LED_PIN, 1);
      gpio_put(STP_PIN, 1);
      sleep_us(1);
      gpio_put(STP_PIN, 0);
      gpio_put(LED_PIN, 0);
      sleep_us(delay);
      printf("\rstep %d", stepCount);
      stepCount++;
      if (delay > 350){
        delay-=10;
      }
    }
 }
}
