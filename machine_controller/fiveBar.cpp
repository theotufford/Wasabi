#pragma once
#include <cstddef>
#include <cstdint>
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

Motor::Motor(const std::vector<int> &argumentVector)
    : step_pin(argumentVector[step_pin_arg]),
      dir_pin(argumentVector[dir_pin_arg]), w_max(argumentVector[w_max_arg]),
      stp_per_rev(argumentVector[stp_per_rev_arg]) {
  gpio_init(dir_pin);
  gpio_init(step_pin);
  gpio_set_dir(step_pin, GPIO_OUT);
  gpio_set_dir(dir_pin, GPIO_OUT);
  gpio_put(dir_pin, 1);
  while (true) {
    step();
    sleep_ms(30);
  }
}

void Motor::step() {
  // step logic
  gpio_put(step_pin, 1);
  sleep_ms(5);
  gpio_put(step_pin, 0);
  current_step_position++;
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

  coms_rx_state = rx_header[0];
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
  bool parse_ints = coms_rx_state > ERROR;

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

void ComsInstance::reflect_argvec() {
  // Toy function to test int packing
  send_data(MESSAGE, static_cast<uint8_t>(argumentVector.size()));
  send_vector(ERROR, argumentVector);
}

ComsInstance::ComsInstance(uart_inst_t *uart, uint baudrate)
    : DmaUart(uart, baudrate), read_time_limit_us(100 * 1000) {}

void machine::unlock_movement() {}
void machine::unlock_pumps() {}
void machine::estop() {}
