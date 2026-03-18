#pragma once
#include <dma_uart.hpp>
#include <cstring>
#include <string>
#include <vector>

using namespace std; // TODO dont do this
// macro global defined so they can be initialized
#define LED_PIN 25
#define BLINK_DELAY 100
void blink(int count);

constexpr uint8_t COMS_START_BYTE = 0xf8;
enum comsCodex : uint8_t {
  // basic state codes
  WAITING,
  WAKE,
  CONFIRM,
  MESSAGE,
  ERROR,
  // settings codes
  NEW_PUMP,
  A_MOTOR,
  B_MOTOR,
  Z_MOTOR,
  MACHINE_PIN_DEFINITIONS,
  // action codes
  MOVE,
  DISPENSE,
  ASPIRATE,
  TOGGLE_PUMPS,
  TOGGLE_MOTORS,
  ZERO_MOTORS,
  // for outgoing mostly
  A_POSITION,
  B_POSITION,
  Z_POSITION,
};
class ComsInstance : public DmaUart {
public:
  // data sending functions
  void send_data(const uint8_t code, const uint8_t *data, const uint8_t length);
  void send_data(const uint8_t code, const int data);
  void
  send_vector(const uint8_t code,
              const vector<int> data); // write and send entire vector at once
  void send_string(string toWrite);
  uint64_t read_time_limit_us;
  uint get_packet(); // main blocking rx read function, gets state/checksum
  // enums in a structure interpret this vector for
  // use by that structure (eg for motor indexing)
  vector<int> argumentVector;
  // determines how the comsInstance handles incoming argvec
  uint8_t coms_rx_code;
  void reflect_argvec();
  ComsInstance(uart_inst_t *uart, uint baudrate);
};
