#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <ctime>
#include <dma_uart.hpp>
#include <fiveBar.hpp>
#include <format>
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
void blink(int count) {
  // debug blink convenience function
  for (int blinked; blinked < count; blinked++) {
    gpio_put(LED_PIN, 1);
    sleep_ms(BLINK_DELAY);
    gpio_put(LED_PIN, 0);
    sleep_ms(BLINK_DELAY);
  }
}

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
  uint8_t tx_header[] = {COMS_START_BYTE, code, data_length};
  write(tx_header, 3);
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

/*
 * function to get waiting packet from dma output buffer
 * structure of packet:
 *		[START BYTE][coms code][body length][body 0][...][body n]
 */
// TODO implement request retransmission on timeout or formatting failure
// (later checksum fail will also trigger this)
uint ComsInstance::get_packet() {
	argumentVector.clear();
  uint8_t rx_header[3];
  absolute_time_t timerStart = get_absolute_time(); // start waiting timer
  while (true) {
    uint16_t available = get_available_rx();
    if (available >= 3) {
      read(rx_header, 3);
      break;
    }
    absolute_time_t elapsed_time =
        absolute_time_diff_us(timerStart, get_absolute_time());
    // check timeout
    if (elapsed_time > read_time_limit_us) {
			send_string("timeout header");
			uint8_t orphan_bytes[2];
			uint16_t bytes_read = read(orphan_bytes, available);
			send_data(ERROR, orphan_bytes, 2);
      return 1;
    }
  }
  // formatting check
  if (rx_header[0] != COMS_START_BYTE) {
		send_string("format err start byte");
    return 2;
  }
  uint8_t &len = rx_header[2];
  coms_rx_state = rx_header[1];
  uint8_t body[len];
  // reset timer to read body
  timerStart = get_absolute_time();
  while (true) {
    if (get_available_rx() >= len) {
      read(body, len);
      break;
    }
    absolute_time_t elapsed_time =
        absolute_time_diff_us(timerStart, get_absolute_time());
    if (elapsed_time > read_time_limit_us) {
			send_string("timeout body");
      return 1;
    }
  }
  // all but the status codes have floats as their body
  bool parse_floats = coms_rx_state > ERROR;
  if (parse_floats) {
    if (len % 4 != 0) {
			send_string("indivisible error");
      return 3;
    }
    int body_index = 0;
    int tmp_index = 0;
    uint8_t float_buffer[4];
    // loop through full body
    while (true) {
      if (tmp_index == 0 && body_index != 0) {
        float tmp_float;
        memcpy(&tmp_float, float_buffer, 4);
        argumentVector.push_back(tmp_float);
				if (body_index == len) {
					break;
				}
      }
      float_buffer[tmp_index] = body[body_index];
      body_index++;
      tmp_index = body_index % 4;
    }
  }
  return 0;
}

void ComsInstance::loopback() {
  // toy function to test float packing
  while (true) {
		send_data(WAITING);
    sleep_ms(100);
    uint packet_rxd = get_packet();
    if (!(packet_rxd == 0)) {
      continue;
    }
    if (argumentVector.size() == 0) {
			send_string("empty args");
      continue;
    }
		for (float num : argumentVector) {
    uint8_t converted_float[sizeof(float)];
    memcpy(converted_float, &num, sizeof(float));
    send_data(MOVE, converted_float, 4);
		}
  }
}

AxisMotor::AxisMotor(std::vector<float> argumentVector)
    : Motor(argumentVector), v_max(argumentVector[v_max_arg]),
      accel_max(argumentVector[accel_max_arg]),
      _lin_eSteps(argumentVector[accel_max_arg]),
      _rad_esteps(2 * M_PI / argumentVector[stp_per_rev_arg]) {}

ComsInstance::ComsInstance(uart_inst_t *uart, uint baudrate)
    : DmaUart(uart, baudrate), read_time_limit_us(100 * 1000) {}

int FiveBar::kinematic_solver(float x_target, float y_target) {}
void FiveBar::unlock_movement() {}
void FiveBar::unlock_pumps() {}
void FiveBar::estop() {}
int FiveBar::homing_routine() {}
