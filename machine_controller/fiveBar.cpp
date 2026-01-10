#pragma once
#include <cstdint>
#include <cstring>
#include <dma_uart.hpp>
#include <fiveBar.hpp>
#include <iostream>
#include <memory>
#include <pico/time.h>
#include <pico/types.h>
#include <string>
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
  write(&code, 1);
  write(&COMS_START_BYTE, 1);
  write(data, (sizeof(*data) / sizeof(data[0])));
  write(&COMS_END_BYTE, 1);
  flush();
}

void ComsInstance::send_data(uint8_t code) {
  write(&code, 1);
  write(&COMS_START_BYTE, 1);
  write(&COMS_END_BYTE, 1);
  flush();
}
void ComsInstance::send_string(std::string toWrite) {
  send_data(MESSAGE, (reinterpret_cast<const uint8_t *>(toWrite.c_str(),
                                                        toWrite.size())));
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

  argumentVector.clear();
	coms_rx_state = WAITING;

  uint buff_index = 0;
  uint rx_stack_ind = 0;
  uint8_t float_buffer[4];

  float tmp_float;
  bool bytes_available = false;
  bool is_startbyte;
  bool is_endbyte;

  uint64_t elapsed_time = 0;
  absolute_time_t start_time = get_absolute_time();

  while (true) {
    elapsed_time =
        (absolute_time_diff_us(start_time, get_absolute_time())) / 1000;

    if (elapsed_time > interbit_time_limit) {
      return 1;
    }

    uint8_t tmpbyte = 0;

    bytes_available = read_byte(&tmpbyte);
    if (!bytes_available) {
      if (is_endbyte) { // references last byte evaluation
        return 0;
      }
      continue;
    }
    rx_data_stack[rx_stack_ind] = tmpbyte;
    rx_stack_ind = (rx_stack_ind + 1) % 256;
    start_time = get_absolute_time();

    is_startbyte = memcmp(&tmpbyte, &COMS_START_BYTE, 1);
    is_endbyte = memcmp(&tmpbyte, &COMS_END_BYTE, 1);

    if (buff_index == 1 && !is_startbyte) {
			send_data(ERROR);
      return 1;
    }
      if (rx_stack_ind ==0) {
        coms_rx_state = tmpbyte;
      continue;
      }
    float_buffer[buff_index] = tmpbyte;
    // if (buff_index == 3) {
    //   memcpy(&tmp_float, float_buffer, sizeof(float));
    //   // python should send checksum that is of the entire float
    //   // checksum verify (checksum input)
    //   // look into hw integrated crc32
    //   argumentVector.push_back(tmp_float);
    // }

    buff_index = (buff_index + 1) % 4;
    // send_data(ERROR);
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
    : DmaUart(uart, baudrate) {}

int FiveBar::kinematic_solver(float x_target, float y_target) {}
void FiveBar::unlock_movement() {}
void FiveBar::unlock_pumps() {}
void FiveBar::estop() {}
int FiveBar::homing_routine() {}
