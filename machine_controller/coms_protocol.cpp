#include "coms_defs.h"
#include <algorithm>
#include <coms_protocol.hpp>
#include <concepts>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <dma_uart.hpp>
#include <filesystem>
#include <hardware/gpio.h>
#include <iostream>
#include <memory>
#include <motors.hpp>
#include <pico/time.h>
#include <type_traits>
#include <utility>
#include <variant>
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

// // I know there is a hardware way to do this but I think generally
// // packets are small enough that speed shouldnt matter that much
// static uint32_t calc_crc32r(uint8_t *bytp, uint32_t length) {
//   uint32_t crc = CRC32_INIT;
//   while (length--) {
//     uint32_t byte32 = (uint32_t)*bytp++;
//     for (uint8_t bit = 8; bit; bit--, byte32 >>= 1) {
//       crc = (crc >> 1) ^ (((crc ^ byte32) & 1ul) ? REVERSED_STD_POLY : 0ul);
//     }
//   }
//   return crc ^ ((uint32_t)-1l);
// }
//
// bool verify_checksum() {
//   uint32_t message_length = packet[LENGTH_INDEX];
//   uint32_t calculated_crc = calc_crc32r(packet, message_length +
//   HEADER_SIZE); uint32_t given_crc; memcpy(&given_crc, &packet[HEADER_SIZE +
//   message_length], 4);
//
//   if (CRC_DISABLED) {
//     return true;
//   }
//
//   if (calculated_crc == given_crc) {
//     return true;
//   }
//   return false;
// }
//

Response_Callback::Response_Callback(string name,
                                     function<bool(LoopContext)> condition,
                                     function<void(LoopContext)> callback)
    : condition(condition), callback(callback), name(name) {}

function<bool(LoopContext)> code_conditional_func(uint8_t code) {
  return [code](LoopContext ctx) -> bool {
    return ctx.most_recent_packet->coms_code == code;
  };
};

LoopContext::LoopContext(ComsInstance *coms_instance_ctx,
                         Packet &received_packet)
    : coms_ctx(coms_instance_ctx), most_recent_packet(&received_packet) {}

Packet::Packet(uint8_t code, uint8_t datatype_id, uint16_t datalen,
               uint8_t *data, uint32_t checksum = CRC32_INIT)
    : coms_code(code), datatype_id(datatype_id), datalen(datalen),
      data(unique_ptr<uint8_t[]>(data)), checksum(checksum) {}

// TODO
uint32_t Packet::calculate_checksum() { return CRC32_INIT; }

void Packet::populate_header_bytearray(uint8_t *target) {
  target[0] = COMS_START_BYTE;
  target[1] = coms_code;
  target[2] = datatype_id;
  memcpy(target + 3, &datalen, 2);
}

void Packet::populate_output_data_bytearray(
    uint8_t *target //  must be uint8_t array of size HEADER_SIZE + datalen +
                    //  CHECKSUM_SIZE_BYTES
) {
  uint8_t *body_ptr = target + HEADER_SIZE;
  uint8_t *checksum_ptr = body_ptr + datalen;
  populate_header_bytearray(target);
  checksum = calculate_checksum();
  memcpy(body_ptr, data.get(), datalen);
  memcpy(checksum_ptr, &checksum, CHECKSUM_SIZE_BYTES);
}

vector<float> Packet::get_float_argvec() {
  vector<float> output;
  for (int i = 0; i < datalen; i += sizeof(float)) {
    uint8_t *num_ind = data.get() + i;
    float tmp;
    memcpy(&tmp, num_ind, sizeof(float));
    output.push_back(tmp);
  }
  return output;
}

vector<int> Packet::get_int_argvec() {
  vector<int> output;
  for (int i = 0; i < datalen; i += sizeof(int)) {
    uint8_t *num_ind = data.get() + i;
    int tmp;
    memcpy(&tmp, num_ind, sizeof(int));
    output.push_back(tmp);
  }
  return output;
}
void ComsInstance::transmit_next() {
  Packet &packet = *tx_queue[tx_read_index];
  tx_read_index = (tx_read_index + 1) % TX_HISTORY_LEN;
  uint32_t calculated_checksum = 0; // TODO currently stubbed
  int total_length = packet.datalen + CHECKSUM_SIZE_BYTES + HEADER_SIZE;
  uint8_t output_Data[total_length];
  packet.populate_output_data_bytearray(output_Data);
  write_and_flush(output_Data, total_length);
  partner_state = BUSY;
}

variant<Packet *, int> ComsInstance::listen_for_packet() {
  auto head_packet = tx_queue[tx_write_index];
  uint8_t header_data[HEADER_SIZE];
  absolute_time_t timerStart = get_absolute_time(); // start waiting timer
  while (true) {
    uint16_t available = get_available_rx();
    uint8_t &tmp = header_data[0];
    if (available > 0 && tmp != COMS_START_BYTE) {
      read(&tmp, 1);
    }
    if (available >= HEADER_SIZE && tmp == COMS_START_BYTE) {
      read(header_data + 1, HEADER_SIZE - 1);
    }
    absolute_time_t elapsed_time =
        absolute_time_diff_us(timerStart, get_absolute_time());
    if (elapsed_time > READ_TIMEOUT_US) {
      return 0;
    }
  }

  uint8_t coms_rx_code = header_data[CODE_INDEX];
  uint8_t datatype_id = header_data[TYPE_INDEX];
  uint16_t len;
  memcpy(header_data + LENGTH_INDEX, &len, 2);
  uint8_t *packet_data = (uint8_t *)malloc(len);
  uint32_t checksum;

  // reset timer to read body
  timerStart = get_absolute_time();
  while (true) {
    if (get_available_rx() >= len + CHECKSUM_SIZE_BYTES) {

      read(packet_data, len);

      uint8_t tmp[CHECKSUM_SIZE_BYTES];
      read(tmp, CHECKSUM_SIZE_BYTES);
      memcpy(tmp, &checksum, CHECKSUM_SIZE_BYTES);
      break;
    }
    absolute_time_t elapsed_time =
        absolute_time_diff_us(timerStart, get_absolute_time());
    if (elapsed_time > READ_TIMEOUT_US) {
      return -1;
    }
  }

  auto got_packet =
      new Packet(coms_rx_code, datatype_id, len, packet_data, checksum);

  // if (!verify_checksum(packet)) {
  //   queue_send(state_packet(RE_REQUEST));
  //   return -2;
  // }

  return got_packet;
}
template <typename T> Packet *packet_from_vec(uint8_t code, vector<T> vec) {
  size_t vec_data_size = vec.size() * sizeof(vec[0]);
  uint8_t *vec_data_ptr = (uint8_t *)malloc(vec_data_size);
  memcpy(vec_data_ptr, vec.data(), vec_data_size);

  if constexpr (is_same_v<T, int>) {
    return new Packet(code, INT_ID, vec_data_size, vec_data_ptr);
  } else if constexpr (is_same_v<T, float>) {
    return new Packet(code, FLOAT_ID, vec_data_size, vec_data_ptr);
  }
}

// remove padding
#pragma pack(push, 1)
struct MoveData {
  uint8_t mot_id;
  uint8_t profile_id;
  uint8_t movetype;
  int step_target;
  float vmax;
  float accel;
};
#pragma pack(pop)

enum { ABSOLUTE, RELATIVE };

vector<MoveEntity> parse_move_packet(Packet *movepacket, Motor **motors_byid) {
  Packet &packet = *movepacket;
  // move packet structure:
  // for n motors we have:
  vector<MoveEntity> output;
  for (int i = 0; i < packet.datalen; i += sizeof(MoveData)) {
    uint8_t *raw_data = packet.data.get() + i;
    MoveData tmp_mdata;
    memcpy(&tmp_mdata, raw_data, sizeof(MoveData));
    Motor *motor = motors_byid[tmp_mdata.mot_id];
    int step_distance = tmp_mdata.step_target;

    if (tmp_mdata.movetype == ABSOLUTE) {
      step_distance = step_distance - motor->position_state;
    }

    output.push_back(MoveEntity(tmp_mdata.profile_id, tmp_mdata.vmax,
                                tmp_mdata.accel, step_distance, motor));
  }
  return output;
}

Packet *state_packet(uint8_t state) {
  return new Packet(STATE, INT_ID, 1, &state);
}

ComsInstance::ComsInstance(uart_inst_t *uart, uint baudrate)
    : DmaUart(uart, baudrate), partner_state(BUSY), tx_write_index(0),
      tx_read_index(0) {
  add_response(Response_Callback(
      "partner_state_updater", code_conditional_func(STATE),
      [](LoopContext ctx) -> void {
        ctx.coms_ctx->partner_state = ctx.most_recent_packet->data[0];
      }));
}
void ComsInstance::queue_send(Packet *packet_to_send) {
  if (tx_queue[tx_write_index] != nullptr) {
    delete tx_queue[tx_write_index];
  }
  tx_queue[tx_write_index] = packet_to_send;
  tx_write_index = (tx_write_index + 1) % TX_HISTORY_LEN;
}

void ComsInstance::main_loop() {
  // dump the transmission queue
  if (partner_state == LISTENING) {
    if (tx_write_index == tx_read_index) {
      // partner is listening and we have nothing to say, thus idling
      queue_send(state_packet(IDLE));
    } else {
      queue_send(state_packet(LISTENING));
    }
    while (tx_read_index != tx_write_index) {
      transmit_next();
    }
    partner_state = BUSY;
  }
  // once tx is dumped, if pi3b is working, listen
  variant<Packet *, int> listen_response = listen_for_packet();
  if (holds_alternative<Packet *>(listen_response)) {
    Packet &got_packet = *get<Packet *>(listen_response);
    auto current_ctx = LoopContext(this, got_packet);
    for (const auto &[name, response_obj] : response_tree) {
      if (response_obj.condition(current_ctx)) {
        response_obj.callback(current_ctx);
        current_ctx.executed_functions.push_back(response_obj.name);
      }
    }
  }
}
