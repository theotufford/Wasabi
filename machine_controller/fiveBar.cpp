#pragma once
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <dma_uart.hpp>
#include <fiveBar.hpp>
#include <format>
#include <hardware/gpio.h>
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

void Motor::buzz() {

  double buzz_amplitude_deg = 1.8;

  int amp_steps = buzz_amplitude_deg / (360 / stp_per_rev);

  if (amp_steps < 0) {
    amp_steps = 1;
  }
  step_delta = 1;
  for (int cycle_count = 0; cycle_count < 100; cycle_count++) {
    for (int stpcnt = 0; stpcnt < amp_steps; stpcnt++) {
      step();
      sleep_ms(1);
    }
    step_delta *= -1;
    update_dir();
  }
}

Motor::Motor(const std::vector<int> &argumentVector)
    : step_pin(argumentVector[step_pin_arg]),
      dir_pin(argumentVector[dir_pin_arg]), w_max(argumentVector[w_max_arg]),
      stp_per_rev(argumentVector[stp_per_rev_arg]), current_position(0), direction(1) {
  gpio_init(dir_pin);
  gpio_init(step_pin);
  gpio_set_dir(step_pin, GPIO_OUT);
  gpio_set_dir(dir_pin, GPIO_OUT);

  buzz();
}

void Motor::update_dir() {
  if (step_delta == 0) {
    return;
  }
  direction = step_delta / abs(step_delta);
  bool bin_dir = direction > 0;
  gpio_put(dir_pin, bin_dir);
}

void Motor::step() {
  // step logic
  gpio_put(step_pin, 1);
  sleep_us(1);
  gpio_put(step_pin, 0);
  current_position += direction;
  // set calculate flag high
}

void ComsInstance::send_data(const uint8_t code, const uint8_t *data = nullptr,
                             const uint8_t data_length = 0) {
  uint8_t tx_header[] = {COMS_START_BYTE, code, data_length};
  write(tx_header, 3);
  if (data_length > 0) {
    write(data, data_length);
  }
  flush();
}
void ComsInstance::send_data(const uint8_t code, const int data) {
  uint8_t tx_header[] = {COMS_START_BYTE, code, 4};
  write(tx_header, 3);
  uint8_t int_buff[4];
  memcpy(int_buff, &data, 4);
  write(int_buff, 4);
  flush();
}
void ComsInstance::send_vector(const uint8_t code,
                               const std::vector<int> data) {
  uint8_t vec_data_len = static_cast<uint8_t>(data.size() * 4);
  uint8_t tx_header[] = {COMS_START_BYTE, code, vec_data_len};
  write(tx_header, 3);
  for (int num : data) {
    uint8_t int_buff[4];
    memcpy(int_buff, &num, 4);
    write(int_buff, 4);
  }
  flush();
}

void ComsInstance::send_string(std::string toWrite) {
  return; // DISABLED FUNCTION FOR DEBUG
  uint8_t stringlen = static_cast<uint8_t>(toWrite.length());
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
  bool got_start = false;
  while (true) {
    uint16_t available = get_available_rx();
    if (!got_start && available > 0) {
      read_byte(&rx_header[0]);
      if (rx_header[0] == COMS_START_BYTE) {
        got_start = true;
      }
      continue;
    }
    if (available >= 3) {
      read(rx_header, 3);
      break;
    }
  }

  coms_rx_code = rx_header[0];
  uint8_t &len = rx_header[1];
  uint8_t &message_index = rx_header[2];

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

  // all but the status codes have ints as their body
  bool parse_ints = coms_rx_code > ERROR;

  if (parse_ints) {
    if (len % 4 != 0) {
      send_string("bytecount indivisible error");
      return 3;
    }

    int body_index = 0;
    int tmp_index = 0;
    uint8_t int_buffer[4];

    while (true) {
      if (tmp_index == 0 && body_index != 0) {
        int tmp_int;
        memcpy(&tmp_int, int_buffer, 4);
        argumentVector.push_back(tmp_int);
      }
      int_buffer[tmp_index] = body[body_index];
      if (body_index == len) {
        break;
      }
      body_index++;
      tmp_index = body_index % 4;
    }
  }
  return 0;
}

int Machine::move(std::vector<int> positional_argvec) {
  Motor &amot = *a_motor;
  Motor &bmot = *b_motor;
  Motor &zmot = *z_motor;

  amot.step_delta = positional_argvec[0] - amot.current_position;
  amot.update_dir();

  bmot.step_delta = positional_argvec[1] - bmot.current_position;
  bmot.update_dir();

  zmot.step_delta = positional_argvec[2] - zmot.current_position;
  zmot.update_dir();

  //naive move function 
  // int local_step_count = 0;
  // int abs_delta = abs(amot.step_delta);
  //
  // blink(3);
  //
  // while (local_step_count < abs_delta) {
  //   amot.step();
  //   sleep_ms(1);
  //   local_step_count++;
  // }
  return 0;
}
int Machine::dispense(std::vector<int> pump_indexes, std::vector<int> volumes) {
  return 0;
}
int Machine::aspirate(std::vector<int> pump_indexes, std::vector<int> volumes) {
  return 0;
}

void ComsInstance::reflect_argvec() {
  // Toy function to test int packing
  send_data(MESSAGE, static_cast<uint8_t>(argumentVector.size()));
  send_vector(ERROR, argumentVector);
}

ComsInstance::ComsInstance(uart_inst_t *uart, uint baudrate)
    : DmaUart(uart, baudrate), read_time_limit_us(100 * 1000) {}

void Machine::unlock_movement() {}
void Machine::unlock_pumps() {}
void Machine::estop() {}
