#include "coms_defs.h"
#include <coms_protocol.hpp>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <dma_uart.hpp>
#include <hardware/gpio.h>
#include <pico/time.h>
#include <vector>

using namespace std; // TODO dont do this

void blink(int count) {
  // debug blink convenience function
  for (int blinked = 0; blinked < count; blinked++) {
    gpio_put(LED_PIN, 1);
    sleep_ms(BLINK_DELAY);
    gpio_put(LED_PIN, 0);
    sleep_ms(BLINK_DELAY);
  }
}

// I know there is a hardware way to do this but I think generally
// packets are small enough that speed shouldnt matter that much
static uint32_t calc_crc32r(uint8_t *bytp, uint32_t length) {
  uint32_t crc = CRC32_INIT;
  while (length--) {
    uint32_t byte32 = (uint32_t)*bytp++;
    for (uint8_t bit = 8; bit; bit--, byte32 >>= 1) {
      crc = (crc >> 1) ^ (((crc ^ byte32) & 1ul) ? REVERSED_STD_POLY : 0ul);
    }
  }
  return crc ^ ((uint32_t)-1l);
}

bool verify_checksum(uint8_t *packet) {
  uint32_t message_length = packet[LENGTH_INDEX];
  uint32_t calculated_crc = calc_crc32r(packet, message_length + HEADER_SIZE);
  uint32_t given_crc;
  memcpy(&given_crc, &packet[HEADER_SIZE + message_length], 4);

  if (CRC_DISABLED) {
    return true;
  }

  if (calculated_crc == given_crc) {
    return true;
  }
  return false;
}

//  Constructs and writes out packet, also calculates checksum
//  packet structure is strictly ordered by byte:
//  0: start byte
//  1: coms code
//  2: data length
//  3 to n + 3: data
//  n+4 to n+8: checksum
void ComsInstance::send_packet(const uint8_t code, const uint8_t *body,
                               const uint8_t body_size) {

  uint16_t total_size = HEADER_SIZE + body_size + CHECKSUM_SIZE_BYTES;
  uint32_t message_size = HEADER_SIZE + body_size;

  uint8_t packet[total_size];
  uint8_t *body_ptr = packet + HEADER_SIZE;
  uint8_t *checksum_ptr = packet + HEADER_SIZE + body_size;

  packet[0] = COMS_START_BYTE;
  packet[1] = code;
  packet[2] = body_size;

  memcpy(body_ptr, body, body_size);

  uint32_t calculated_checksum = calc_crc32r(packet, message_size);

  memcpy(checksum_ptr, &calculated_checksum, CHECKSUM_SIZE_BYTES);

  write_and_flush(packet, total_size);

  memcpy(most_recent_tx, packet, total_size);
  most_recent_tx_size = total_size;
}

void ComsInstance::send_code(const uint8_t code) {
  send_packet(code, nullptr, 0);
}

void ComsInstance::handle_rereq() {
  write_and_flush(most_recent_tx, most_recent_tx_size);
};

void ComsInstance::send_vector(const uint8_t code, const vector<int> int_vec) {
  int data_len = int_vec.size() * sizeof(int);
  uint8_t data[data_len];
  memcpy(data, int_vec.data(), data_len);

  send_packet(code, data, data_len);
}

void ComsInstance::send_string(string toWrite) {
  return; // DISABLED FUNCTION FOR DEBUG
  uint8_t stringlen = static_cast<uint8_t>(toWrite.length());
  const uint8_t *text_data = reinterpret_cast<const uint8_t *>(toWrite.c_str());
  send_packet(MESSAGE, text_data, stringlen);
}

uint ComsInstance::get_packet() {
  argumentVector.clear();
  coms_rx_code = EMPTY;

  uint8_t rx_header[HEADER_SIZE];
  absolute_time_t timerStart = get_absolute_time(); // start waiting timer

  while (true) {
    uint16_t available = get_available_rx();
    if (available >= HEADER_SIZE) {
      read(rx_header, HEADER_SIZE);
      break;
    }
  }

  coms_rx_code = rx_header[CODE_INDEX];
  uint8_t &len = rx_header[LENGTH_INDEX];
  uint8_t packet[HEADER_SIZE + len + CHECKSUM_SIZE_BYTES];
  memcpy(packet, rx_header, HEADER_SIZE);

  // reset timer to read body
  timerStart = get_absolute_time();
  while (true) {
    if (get_available_rx() >= len + CHECKSUM_SIZE_BYTES) {
      uint8_t tmp[CHECKSUM_SIZE_BYTES];
      read(packet + HEADER_SIZE, len + CHECKSUM_SIZE_BYTES);
      break;
    }

    absolute_time_t elapsed_time =
        absolute_time_diff_us(timerStart, get_absolute_time());
    if (elapsed_time > read_time_limit_us) {
      send_string("timeout body");
      return 1;
    }
  }

  if (!verify_checksum(packet)) {
    send_code(RE_REQUEST);
    uint result = get_packet();
  }

  int body_index = 0;
  int tmp = 0;
  uint8_t byte_buffer[4];

  uint8_t *data_ptr = packet + HEADER_SIZE;
  for (int body_index = 0; body_index < len; body_index += 4) {
    memcpy(&tmp, data_ptr + body_index, 4);
    argumentVector.push_back(tmp);
  }

  return 0;
}

ComsInstance::ComsInstance(uart_inst_t *uart, uint baudrate)
    : DmaUart(uart, baudrate), read_time_limit_us(100 * 1000) {
  // handshake:
  // send wake
  // wait for CONFIRM
  // send CONFIRM
  // wait for final ack
  // continue
  send_code(WAKE);
  uint handshake_index = 0;
  while (handshake_index < 2) { // break after second confirm
    uint messageFound = get_packet();
    sleep_ms(20);
    if (coms_rx_code == CONFIRM) {
      send_code(CONFIRM);
      handshake_index++;
    }
  }
  // handshake confirmation blink
  blink(1);
}
