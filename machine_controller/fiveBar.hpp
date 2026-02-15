#pragma once
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <dma_uart.hpp>
#include <hardware/gpio.h>
#include <hardware/uart.h>
#include <iostream>
#include <memory>
#include <pico/types.h>
#include <string>
#include <sys/_intsup.h>
#include <tuple>
#include <vector>

constexpr uint8_t COMS_START_BYTE = 0xf8;

class ComsInstance;

class Motor {
public:
  const int step_pin;
  const int dir_pin;
  const int stp_per_rev;
  const int w_max;
  bool homed;
  enum { step_pin_arg, dir_pin_arg, stp_per_rev_arg, w_max_arg };
  bool enabled;
  int current_step_position;
  int abs_step_delta;
  int direction;
  void step();
  void toggle_dir();
  void buzz();
  Motor(const std::vector<int> &argumentVector);
};

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
  MACHINE_DIMENSIONS,
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
  X_POSITION,
  Y_POSITION,
  Z_POSITION,
};


class machine {
public:
  std::unique_ptr<Motor> a_motor;
  std::unique_ptr<Motor> b_motor;
  std::unique_ptr<Motor> z_motor;

  std::vector<std::unique_ptr<Motor>> pumps;

  void positional_move(int A_POSITION, int B_POSITION, int Z_POSITION);
  void dispense_reagents(std::vector<std::tuple<int, int>> pmpInd_stpcnt_tuples);

  std::vector<int> measuring_move();

  void unlock_movement();
  void unlock_pumps();
  void estop();
  int homing_routine();
};

class ComsInstance : public DmaUart {
public:
  // data sending functions
  void send_data(const uint8_t code, const uint8_t *data, const uint8_t length);
  void send_data(const uint8_t code, const int data);
  void send_vector(
      const uint8_t code,
      const std::vector<int> data); // write and send entire vector at once
  void send_string(std::string toWrite);
  uint64_t read_time_limit_us;
  uint get_packet(); // main blocking rx read function, gets state/checksum
  // enums in a structure interpret this vector for
  // use by that structure (eg for motor indexing)
  std::vector<int> argumentVector;
  uint8_t
      coms_rx_state; // determines how the comsInstance handles incoming data
  void reflect_argvec();
  ComsInstance(uart_inst_t *uart, uint baudrate);
};
