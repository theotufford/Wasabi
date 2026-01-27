#include <cstdint>
#include <cstdlib>
#include <dma_uart.hpp>
#include <fiveBar.cpp>
#include <fiveBar.hpp>
#include <format>
#include <hardware/gpio.h>
#include <hardware/uart.h>
#include <iostream>
#include <memory>
#include <pico/time.h>
#include <pico/types.h>
#include <sstream>
#include <string>
#include <sys/_intsup.h>
#include <sys/unistd.h>
#include <vector>

int main() {
  gpio_init(LED_PIN);
  gpio_set_dir(LED_PIN, GPIO_OUT);
  blink(1);

  ComsInstance coms = ComsInstance(uart0, 115200);

  // handshake:
  // send wake
  // wait for CONFIRM
  // send CONFIRM
  // wait for final ack
  // continue
  coms.send_data(WAKE);
  uint handshake_index = 0;
  while (handshake_index < 2) { // break after second confirm
    uint messageFound =
        coms.get_packet(); // set coms state to waiting and listen
    sleep_ms(20);
    if (coms.coms_rx_state == CONFIRM) {
      coms.send_data(CONFIRM, &coms.coms_rx_state, 1);
      handshake_index++;
    }
  }
  // handshake confirmation blink
  blink(3);
  while (true) {
    uint messageFound = coms.get_packet();
    if (messageFound != 0) {
      continue;
    }
    if (!(coms.coms_rx_state >= NEW_PUMP)) {
      coms.send_string("got code outside of config range");
      coms.send_data(MESSAGE, &coms.coms_rx_state, 1);
      continue;
    }
    if (coms.argumentVector.size() == 0) {
      coms.send_string("empty args");
      continue;
    }
    coms.reflect_argvec();
  }
}
