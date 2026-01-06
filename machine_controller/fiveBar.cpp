#pragma once
#include "fiveBar.hpp"
#include "dma_uart.hpp"
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <hardware/gpio.h>
#include <hardware/uart.h>
#include <iostream>
#include <memory>
#include <pico/time.h>
#include <pico/types.h>
#include <vector>

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
  write(&code, 1);
  write(&COMS_PUNCTUATION_BYTE, 1);
  write(data, (sizeof(*data) / sizeof(data[0])));
  write(&COMS_PUNCTUATION_BYTE, 1);
  flush();
}
void ComsInstance::send_data(uint8_t code) {
  write(&code, 1);
  flush();
}
void ComsInstance::send_string(std::string toWrite) {
  send_data(MESSAGE, (reinterpret_cast<const uint8_t *>(toWrite.c_str(),
                                                          toWrite.size())));
}
uint ComsInstance::await_data() {
  coms_rx_state = WAITING;
  argumentVector.clear();
  absolute_time_t startTime = get_absolute_time();
  uint64_t elapsedTime = 0;
  uint8_t rx_data[4];
  float tmpFloat;
  bool bytesAvailable = false;
  uint buffIndex = 0;
  while (true) {
    if (coms_rx_state == CONFIRM) {
      break;
    }
    elapsedTime =
        (absolute_time_diff_us(startTime, get_absolute_time())) / 1000;
    if (elapsedTime > timeLimit) {
			send_string("timeout");
			return 1;
    }
    bytesAvailable = read_byte(&rx_data[buffIndex]);
    if (!bytesAvailable) {
      continue;
    }
    startTime = get_absolute_time();
    bool ispunctuationByte = rx_data[buffIndex] == COMS_PUNCTUATION_BYTE;
    if (coms_rx_state == WAITING && ispunctuationByte) {
      coms_rx_state = rx_data[buffIndex - 1];
      buffIndex = 0;
      memset(rx_data, 0, sizeof(rx_data));
      send_data(CONFIRM);
      continue;
    }
    if (buffIndex == 0 && ispunctuationByte) {
      return 0;
    }
    if (buffIndex == 3) {
      memcpy(&tmpFloat, rx_data, sizeof(float));
      argumentVector.push_back(tmpFloat);
    }
    buffIndex = (buffIndex + 1) % 4;
  }
}

AxisMotor::AxisMotor(std::vector<float> argumentVector)
    : Motor(argumentVector), v_max(argumentVector[v_max_arg]),
      accel_max(argumentVector[accel_max_arg]),
      _lin_eSteps(argumentVector[accel_max_arg]),
      _rad_esteps(2 * M_PI / argumentVector[stp_per_rev_arg]) {}

ComsInstance::ComsInstance(uart_inst_t *uart, uint baudrate)
    : DmaUart(uart, baudrate) {
  // wakeup
  send_data(WAKE);
  while (true) {
    uint messageFound = await_data();
		if (messageFound == 1) {
			continue;
		}
    if (coms_rx_state == WAKE) {
      break;
    }
  }
  send_data(CONFIRM);
}
FiveBar ComsInstance::setup_machine() {
  FiveBar new_machine;
  while (true) {
    uint messageFound = await_data();
    if (messageFound != 1) {
      continue;
    }
    if (coms_rx_state == CONFIRM) {
      break;
    }
    if (!(coms_rx_state >= NEW_PUMP && coms_rx_state <= MACHINE_DIMENSIONS)) {
			send_string("calling settings setup but coms code outside range");
      continue;
    }
    switch (coms_rx_state) {
    case NEW_PUMP: {
      new_machine.pumps.push_back(std::make_unique<Pump>(argumentVector));
    }
    case A_MOTOR: {
      new_machine.a_motor = std::make_unique<AxisMotor>(argumentVector);
    }
    case B_MOTOR: {
      new_machine.b_motor = std::make_unique<AxisMotor>(argumentVector);
    }
    case Z_MOTOR: {
      new_machine.z_motor = std::make_unique<AxisMotor>(argumentVector);
    }
    case MACHINE_PIN_DEFINITIONS: {
      // blank for now
    }
    case MACHINE_DIMENSIONS: {
      // blank for now
    }
    }
		send_data(coms_rx_state);
  }
  return new_machine;
}

int FiveBar::kinematic_solver(float x_target, float y_target) {}
void FiveBar::unlock_movement() {}
void FiveBar::unlock_pumps() {}
void FiveBar::estop() {}
int FiveBar::homing_routine() {}
