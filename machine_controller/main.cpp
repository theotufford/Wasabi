#include <cstdint>
#include <dma_uart.hpp>
#include <fiveBar.cpp>
#include <fiveBar.hpp>
#include <hardware/gpio.h>
#include <hardware/uart.h>
#include <hardware/watchdog.h>
#include <iostream>
#include <pico/time.h>
#include <pico/types.h>
#include <sys/_intsup.h>
#include <sys/unistd.h>
#include <time.h>

int main() {
  gpio_init(LED_PIN);
  gpio_set_dir(LED_PIN, GPIO_OUT);
  blink(1);

  ComsInstance coms = ComsInstance(uart0, 115200);

  absolute_time_t start_time = get_absolute_time();
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
  blink(3); // handshake confirmation blink
	coms.loopback();

  // setup machine
  FiveBar new_machine;
  while (true) {
    uint messageFound = coms.get_packet();

    if (messageFound != 1) {
      continue;
    }

    if (coms.coms_rx_state == CONFIRM) {
      break;
    }

    if (!(coms.coms_rx_state >= NEW_PUMP &&
          coms.coms_rx_state <= MACHINE_DIMENSIONS)) {
      continue;
    }

    switch (coms.coms_rx_state) {
    case NEW_PUMP: {
      new_machine.pumps.push_back(std::make_unique<Pump>(coms.argumentVector));
      break;
    }
    case A_MOTOR: {
      new_machine.a_motor = std::make_unique<AxisMotor>(coms.argumentVector);
      break;
    }
    case B_MOTOR: {
      new_machine.b_motor = std::make_unique<AxisMotor>(coms.argumentVector);
      break;
    }
    case Z_MOTOR: {
      new_machine.z_motor = std::make_unique<AxisMotor>(coms.argumentVector);
      break;
    }
    case MACHINE_PIN_DEFINITIONS: {
      // blank for now
      break;
    }
    case MACHINE_DIMENSIONS: {
      // blank for now
      break;
    }
    }
    coms.send_data(coms.coms_rx_state);
  }
}
