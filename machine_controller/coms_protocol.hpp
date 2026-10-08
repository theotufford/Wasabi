#pragma once
#include <coms_defs.h>
#include <cstdint>
#include <cstring>
#include <dma_uart.hpp>
#include <functional>
#include <map>
#include <memory>
#include <string>
#include <variant>
#include <vector>

using namespace std; // TODO dont do this

// macro global defined so they can be initialized
#define LED_PIN 25
#define BLINK_DELAY 100

void blink(int count);

// coms codes
enum : uint8_t { STATE, RE_REQUEST, MESSAGE, MOVE, HOME, WAKE };

// coms states
enum : uint8_t { BUSY, LISTENING, IDLE };

// coms data type ids
enum : uint8_t { INT_ID, FLOAT_ID, STRUCT_ID, NONETYPE_ID };

//  Constructs and writes out packet, also calculates checksum
//  packet structure is strictly ordered by byte:
//  0: start byte
//  1: coms code
//  2: data type
//  3-4: data length
//  5 to n + 5: data
//  n+6 to n+10: checksum

class Packet {
public:
  uint8_t coms_code;
  uint8_t datatype_id;
  uint16_t datalen;
  uint8_t *data;
  uint32_t checksum;
  void populate_header_bytearray(uint8_t *target);
  void populate_output_data_bytearray(uint8_t *target);
  uint32_t calculate_checksum();
  vector<float> get_float_argvec();
  vector<int> get_int_argvec();
  Packet(uint8_t code, uint8_t datatype_id, uint16_t datalen, uint8_t *data,
         uint32_t checksum);
  ~Packet();
};

class ComsInstance;

class LoopContext {
public:
  vector<string> executed_functions;
  Packet *most_recent_packet;
  ComsInstance *coms_ctx;
  LoopContext(ComsInstance *coms_instance_ctx, Packet &received_packet);
};

class Response_Callback {
public:
  string name;
  function<bool(LoopContext)> condition;
  function<void(LoopContext)> callback;
  Response_Callback(string name, function<bool(LoopContext)> condition,
                    function<void(LoopContext)> callback);
};

class ComsInstance : public DmaUart {
private:
  map<string, Response_Callback> response_tree;

public:
  uint8_t partner_state;
  uint8_t self_state;
  int tx_write_index;
  int tx_read_index;
  Packet *tx_queue[TX_HISTORY_LEN] = {nullptr};
  void queue_send(Packet *to_send);
  void transmit_next();
  void handle_rereq();
  variant<Packet *, int>
  listen_for_packet(); // main rx read function, gets state/checksum
  void add_response(Response_Callback callback);
  void main_loop();
  ComsInstance(uart_inst_t *uart, uint baudrate);
};

// motor frame settings codex
enum { STP_PIN, DIR_PIN, LIM_PIN, INVERSION, STP_PER_REV, MOTOR_CONFIG_SIZE };
