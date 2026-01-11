#pragma once
#include <cstdint>
#include <cstring>
#include <ctime>
#include <dma_uart.hpp>
#include <fiveBar.hpp>
#include <iostream>
#include <memory>
#include <pico/time.h>
#include <pico/types.h>
#include <string>
#include <sys/unistd.h>
#include <vector>
// this is stupid and is only here for convenience blink should go in a proper
// folder / section
#define LED_PIN 25
#define BLINK_DELAY 100

Motor::Motor(const std::vector<float> &argumentVector)
    : _step_pin((int)argumentVector[step_pin_arg]),
      _dir_pin((int)argumentVector[dir_pin_arg]),
      _stp_per_rev((int)argumentVector[stp_per_rev_arg]) {
  // claim pins and stuff
}

void Motor::step() {
  // step logic
  current_step_position++;
  // set calculate flag high
}

void AxisMotor::queue_movement(float target) {}

Pump::Pump(const std::vector<float> &argumentVector)
    : Motor(argumentVector), flowrate_max(argumentVector[flowrate_max_arg]),
      _eSteps_ul(argumentVector[eSteps_ul_arg]) {}

void Pump::queue_dispense(float volume) {
  // add to step delta, put motor into daemon vector
}
void Pump::queue_aspiration(float volume) {
  // flip direction, add to step delta, put motor into daemon vector
}

void ComsInstance::send_data(const uint8_t code, const uint8_t *data) {
  write(&COMS_START_BYTE, 1);
  write(&code, 1);
  write(data, (sizeof(*data) / sizeof(data[0])));
  write(&COMS_END_BYTE, 1);
  sleep_ms(10);
  flush();
}

void ComsInstance::send_data(uint8_t code) {
  write(&COMS_START_BYTE, 1);
  write(&code, 1);
  write(&COMS_END_BYTE, 1);
  flush();
}
void ComsInstance::send_string(std::string toWrite) {
  const uint8_t *data_ptr = reinterpret_cast<const uint8_t *>(toWrite.c_str());
  send_data(MESSAGE, data_ptr);
}
void blink(int count) {
  for (int blinked; blinked < count; blinked++) {
    gpio_put(LED_PIN, 1);
    sleep_ms(BLINK_DELAY);
    gpio_put(LED_PIN, 0);
    sleep_ms(BLINK_DELAY);
  }
}
uint ComsInstance::await_data() {
  coms_rx_state = WAITING;
  uint8_t tmpbyte;
  uint8_t rxbuff[4];
  int index = 0;

  while (true) {
    bool bytes_available = read_byte(&tmpbyte);
    bool is_startbyte = memcmp(&tmpbyte, &COMS_START_BYTE, 1) == 0;
		if (!bytes_available) {
			continue;
		}
    if (!is_startbyte) {
			send_data(ERROR, &tmpbyte);
      return 1;
    }
		break;
  }
  while (true) {
    bool bytes_available = read_byte(&tmpbyte);
    if (!bytes_available) {
      absolute_time_t timerStart = get_absolute_time();
      while (true) {
        absolute_time_t elapsed_time =
            absolute_time_diff_us(timerStart, get_absolute_time());
        if (elapsed_time > interbit_time_limit) {
          return 1;
        }
        bytes_available = read_byte(&tmpbyte);
        if (bytes_available) {
          break;
        }
      }
    }
    bool is_endbyte = COMS_END_BYTE == tmpbyte;
    if (is_endbyte) {
      return 0;
    }
    rxbuff[index] = tmpbyte;
    index = (index + 1) % 4;
  }
}

void ComsInstance::loopback() {
  for (float notnum : argumentVector) {
    float num = 38.28374;
    uint8_t converted_float[sizeof(float)];
    memcpy(converted_float, &num, sizeof(float));
    while (true) {
      send_data(MESSAGE, converted_float);
      sleep_ms(100);
    }
  }
}

AxisMotor::AxisMotor(std::vector<float> argumentVector)
    : Motor(argumentVector), v_max(argumentVector[v_max_arg]),
      accel_max(argumentVector[accel_max_arg]),
      _lin_eSteps(argumentVector[accel_max_arg]),
      _rad_esteps(2 * M_PI / argumentVector[stp_per_rev_arg]) {}

ComsInstance::ComsInstance(uart_inst_t *uart, uint baudrate)
    : DmaUart(uart, baudrate), interbit_time_limit(100) {}

int FiveBar::kinematic_solver(float x_target, float y_target) {}
void FiveBar::unlock_movement() {}
void FiveBar::unlock_pumps() {}
void FiveBar::estop() {}
int FiveBar::homing_routine() {}
