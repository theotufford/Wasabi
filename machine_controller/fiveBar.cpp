#pragma once
#include "fiveBar.hpp"
#include "dma_uart.hpp"
#include <cmath>
#include <cstdint>
#include <cstring>
#include <hardware/gpio.h>
#include <hardware/uart.h>
#include <iostream>
#include <memory>
#include <pico/time.h>
#include <pico/types.h>
#include <ratio>
#include <set>
#include <span>
#include <vector>

Motor::Motor(const MotorConfig &motor_config)
    : _step_pin(motor_config.step_pin), _dir_pin(motor_config.dir_pin),
      _stp_per_rev(motor_config.stp_per_rev), _daemon(motor_config.daemon) {
  // initialize all of the pins
}

void Motor::step() {
  // step logic
  current_step_position++;
  // set calculate flag high
}

void AxisMotor::queue_movement(float target) {}

Pump::Pump(const MotorConfig &motor_config, float eSteps_ul, float flowrate)
    : Motor(motor_config), _eSteps_ul(eSteps_ul), flowrate_max(flowrate) {
  // also dont know
}

void Pump::queue_dispense(float volume) {
  // add to step delta, put motor into daemon vector
}
void Pump::queue_aspiration(float volume) {
  // flip direction, add to step delta, put motor into daemon vector
}

MotorDaemon::MotorDaemon() {}

int MotorDaemon::handle_liquid() {}

int MotorDaemon::handle_move() {}
void ComsInstance::writeString(std::string toWrite) {
  toWrite += "\n";
  write_and_flush(reinterpret_cast<const uint8_t *>(toWrite.c_str()),
                  toWrite.size());
}
uint ComsInstance::awaitMessage() {
  uint loadstatus = 3;
  absolute_time_t startTime = get_absolute_time();
  uint64_t elapsedTime = 0;
  uint8_t rx_data[64];
  bool bytesAvailable = false;
  uint16_t buffIndex = 0;

  while (true) {
    elapsedTime =
        (absolute_time_diff_us(startTime, get_absolute_time())) / 1000;
    if (elapsedTime > timeLimit) {
      loadstatus = 2;
      break;
    }
    bytesAvailable = read_byte(&rx_data[buffIndex]);
    if (!bytesAvailable) {
      continue;
    }
    switch (rx_data[buffIndex]) {
    case '\n': {
      loadstatus = 0;
      break;
    }
    case ':': {
      comsCode = rx_data[buffIndex - 1];
      buffIndex = 0;
    }
    case ';': {
      argumentVector.push_back(rx_data);
      buffIndex = 0;
      memset(rx_data, 0, sizeof(rx_data));
    }
    }
    startTime = get_absolute_time();
    buffIndex++;
    if (buffIndex == 64) {
      loadstatus = 1;
      break;
    }
    if (loadstatus > 0) {
      return 1;
    }
  }
  return loadstatus;
}

AxisMotor::AxisMotor(std::vector<float> argumentVector)
    : Motor(argumentVector), v_max(argumentVector[axis_ArgVecCodex::v_max_arg]),
      accel_max(argumentVector[axis_ArgVecCodex::accel_max_arg]),
      _lin_eSteps(argumentVector[axis_ArgVecCodex::accel_max_arg]),
      _rad_esteps(2 * M_PI / argumentVector[Motor::motor_ArgVecKey::stp_per_rev_arg]){}
}

ComsInstance::ComsInstance(uart_inst_t *uart, uint baudrate)
    : DmaUart(uart, baudrate) {
  sendMessage(WAKE, 0);
  while (true) {
    uint messageFound = awaitMessage();
    if (comsCode == WAKE && messageFound == 0) {
      break;
    }
  }
  sendMessage(CONFIRM, 0);
  while (true) {
    uint messageFound = awaitMessage();
    if (messageFound != 0) {
      continue;
    }
    if (comsCode == CONFIRM) {
      break;
    }
    if (!(comsCode >= NEW_PUMP && comsCode <= MACHINE_DIMENSIONS)) {
      continue;
    }
    switch (comsCode) {
    case NEW_PUMP: {
    }
    case A_MOTOR: {
      settings.a_motor = new_axis_motor(argumentVector);
      sendMessage(CONFIRM, 0);
    }
    case B_MOTOR: {
      settings.b_motor = new_axis_motor(argumentVector);
      sendMessage(CONFIRM, 0);
    }
    case Z_MOTOR: {
      settings.z_motor = new_axis_motor(argumentVector);
      sendMessage(CONFIRM, 0);
    }
    case MACHINE_PIN_DEFINITIONS: {
    }
    case MACHINE_DIMENSIONS: {
    }
    }
  }
}

FiveBar::FiveBar(uart_inst_t *uart, uint baudrate) {}

int FiveBar::kinematic_solver(float x_target, float y_target) {}
void FiveBar::unlock_movement() {}
void FiveBar::unlock_pumps() {}
void FiveBar::estop() {}
int FiveBar::homing_routine() {}
