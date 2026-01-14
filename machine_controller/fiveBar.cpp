#pragma once
#include <cstddef>
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

void ComsInstance::send_data(const uint8_t code, const uint8_t *data = nullptr,
                             const uint8_t data_length = 0) {
  flush();
  uint8_t header[] = {COMS_START_BYTE, code, data_length};
  write(header, 3);
  if (data_length > 0) {
    write(data, data_length);
  }
  flush();
}

void ComsInstance::send_string(std::string toWrite) {
  size_t stringlen = toWrite.length();
  const uint8_t *text_data = reinterpret_cast<const uint8_t *>(toWrite.c_str());
  send_data(MESSAGE, text_data, stringlen);
}
void blink(int count) {
  for (int blinked; blinked < count; blinked++) {
    gpio_put(LED_PIN, 1);
    sleep_ms(BLINK_DELAY);
    gpio_put(LED_PIN, 0);
    sleep_ms(BLINK_DELAY);
  }
}

bool ComsInstance::timeout_read(uint8_t *rx_byte) {
  bool bytes_available = read_byte(rx_byte);
  if (!bytes_available) {
    absolute_time_t timerStart = get_absolute_time();
    while (true) {
      absolute_time_t elapsed_time =
          absolute_time_diff_us(timerStart, get_absolute_time());
      if (elapsed_time > interbit_time_limit_us) {
        return false;
      }
      bytes_available = read_byte(rx_byte);
      if (bytes_available) {
        return true;
      }
    }
  }
}

uint ComsInstance::get_packet() {
  /*
   * function to get waiting packet from dma output buffer
   * structure of packet:
   *		[START BYTE][coms code][body length][body 0][...][body n]
   */
  uint8_t header[3];
  absolute_time_t timerStart = get_absolute_time(); // start waiting timer
  while (true) {
    uint16_t available = get_available();
    if (available >= 3) {
      // wait until full header is available and then read
      read(header, 3);
      break;
    }
    absolute_time_t elapsed_time =
        absolute_time_diff_us(timerStart, get_absolute_time());
    // ensure elapsed
    if (elapsed_time > interbit_time_limit_us) {
      send_string("timout error (header)");
      return 1;
    }
  }
  if (header[0] != COMS_START_BYTE) {
    return 2;
  }
  uint8_t &len = header[2];
  coms_rx_state = header[1];
  uint8_t body[len];
  timerStart = get_absolute_time();
  while (true) {
    uint16_t available = get_available();
    if (available >= len) {
      read(body, len);
      break;
    }
    absolute_time_t elapsed_time =
        absolute_time_diff_us(timerStart, get_absolute_time());
    if (elapsed_time > interbit_time_limit_us) {
      send_string("timout error (body)");
      return 1;
    }
  }
  return 0;
}

void ComsInstance::loopback() {
  for (float notnum : argumentVector) {
    float num = 38.28374;
    uint8_t converted_float[sizeof(float)];
    memcpy(converted_float, &num, sizeof(float));
    while (true) {
      send_data(MESSAGE, converted_float, 4);
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
    : DmaUart(uart, baudrate), interbit_time_limit_us(500 * 1000) {}

int FiveBar::kinematic_solver(float x_target, float y_target) {}
void FiveBar::unlock_movement() {}
void FiveBar::unlock_pumps() {}
void FiveBar::estop() {}
int FiveBar::homing_routine() {}
