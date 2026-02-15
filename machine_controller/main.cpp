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
#include <utility>
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

  machine fiveBar;
  // settings configuration loop
  while (true) {
    uint messageFound = coms.get_packet(); // blocking header read
    if (messageFound != 0) {
      continue;
    }

    if (coms.coms_rx_state == CONFIRM) { // listen for break signal
      break;
    }

    if (coms.argumentVector.size() == 0) { // ensure there is data to parse
      continue;
    }

    // ensure the com is a settings packet
    if (coms.coms_rx_state < NEW_PUMP ||
        coms.coms_rx_state > MACHINE_PIN_DEFINITIONS) {
      continue;
    }

    if (coms.coms_rx_state == MACHINE_PIN_DEFINITIONS) {
      continue;
    }

    // i dont completely understand why this works
    // and why using normal pointers fails
    std::unique_ptr<Motor> new_motor =
        std::make_unique<Motor>(coms.argumentVector);


    switch (coms.coms_rx_state) {
    case NEW_PUMP:
      fiveBar.pumps.push_back(std::move(new_motor));
      break;
    case A_MOTOR:
      fiveBar.a_motor = std::move(new_motor);
      break;
    case B_MOTOR:
      fiveBar.b_motor = std::move(new_motor);
      break;
    case Z_MOTOR:
      fiveBar.z_motor = std::move(new_motor);
      break;
    case MACHINE_PIN_DEFINITIONS:
      break;
    }
    coms.send_data(CONFIRM);
  }

}
