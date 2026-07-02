#pragma once
#include <coms_defs.h>
#include <cstdint>
#include <cstring>
#include <dma_uart.hpp>
#include <string>
#include <vector>

using namespace std; // TODO dont do this

// macro global defined so they can be initialized
#define LED_PIN 25
#define BLINK_DELAY 100

void blink(int count);

enum : uint8_t {
  EMPTY,
  WAKE,
  CONFIRM,
  MESSAGE,
  ERROR,
  RE_REQUEST,
  NEW_PUMP,
  A_MOTOR,
  B_MOTOR,
  Z_MOTOR,
  MACHINE_PIN_DEFINITIONS,
  MOVE,
  PUMP_ACTION,
  ENABLE_PUMPS,
  DISABLE_PUMPS,
  ENABLE_MOTORS,
  DISABLE_MOTORS,
  HOME,
  INITIAL_POSITION,
  BUZZ
};

class ComsInstance : public DmaUart {
public:
  // data sending functions
  void handle_rereq();
  void send_packet(const uint8_t code, const uint8_t *data,
                   const uint8_t length);
  void send_code(const uint8_t code);
  void send_int(const uint8_t code, const int data);
  void
  send_vector(const uint8_t code,
              const vector<int> data); // write and send entire vector at once
  void send_string(string toWrite);
  uint64_t read_time_limit_us;
  uint get_packet(); // main blocking rx read function, gets state/checksum
  // enums in a structure interpret this vector for
  // use by that structure (eg for motor indexing)
  vector<int> argumentVector;
  uint8_t coms_rx_code;
  uint8_t most_recent_tx[MAX_PACKET_SIZE];
  uint16_t most_recent_tx_size;
  void reflect_argvec();
  ComsInstance(uart_inst_t *uart, uint baudrate);
};
