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
#include <vector>

constexpr uint8_t COMS_START_BYTE = 0xf8;
constexpr uint8_t COMS_END_BYTE = 0xf6;

class MotorDaemon;
class ComsInstance;

class Motor {
public:
  const int _step_pin;
  const int _dir_pin;
  const int _stp_per_rev;
  enum { step_pin_arg, dir_pin_arg, stp_per_rev_arg };
  MotorDaemon *_daemon;
  bool enabled;
  int current_step_position;
  int abs_step_delta; // child class action function modifies this and then
                      // pushes itself to the appropriate motor daemon vector
  int direction;
  void step();
  Motor(const std::vector<float> &argumentVector);
};

class AxisMotor : public Motor {
private:
  const float _lin_eSteps, _rad_esteps;
  enum { v_max_arg = 3, accel_max_arg, lin_eSteps_arg };

public:
  const float v_max;
  const float accel_max;
  void dump_settings(ComsInstance &coms);
  bool homed;
  void queue_movement(float target);
  AxisMotor(std::vector<float> argumentVector);
};

class Pump : public Motor {
private:
  const float _eSteps_ul;
  float est_remainingVolume;
  enum { flowrate_max_arg = 3, eSteps_ul_arg };

public:
  std::string reagent;
  const float flowrate_max;
  float aspirant_volume;
  void buzz();
  void queue_dispense(float volume);
  void queue_aspiration(float volume);
  Pump(const std::vector<float> &argumentVector);
};

class MotorDaemon { // main loop checks for motors in
                    // vectors then handles movement
public:
  std::vector<AxisMotor *> move_queue;
  std::vector<Pump *> handler_queue;

  int handle_Movement(); // runs on second core
                         // handles initial accel/const/decel point calc
                         // sets irq hw timer recursively on completion
                         // according to initial calcs

  int handle_liquids(); // similiar to movement but all motors are in sync
  MotorDaemon();        // claim timers for async
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

class FiveBar {
public:
  std::unique_ptr<AxisMotor> a_motor;
  std::unique_ptr<AxisMotor> b_motor;
  std::unique_ptr<AxisMotor> z_motor;
  std::vector<std::unique_ptr<Pump>> pumps;

  int kinematic_solver(
      float x_target,
      float y_target); // solves 5 bar kinematic equation and calls move
                       // functions from motors accordingly
  float current_x, current_y, current_z;
  void unlock_movement();
  void unlock_pumps();
  void estop(); // sets estop pin high via software
  int homing_routine();
};

class ComsInstance : public DmaUart {
public:
  // data sending functions
  void send_data(const uint8_t code, const uint8_t *data, const uint8_t length);
  void send_data(const uint8_t code, const float data);
  void send_string(std::string toWrite); // convenience, auto attaches MESSAGE
                                         // code and casts string to bytearray
	
  uint64_t read_time_limit_us; // time limit for waiting on rx buffer to fill to
                               // predicted size (eg 3 for header)
	
  uint get_packet(); // main blocking rx read function, gets state/checksum and
	
  std::vector<float> argumentVector; // most rx data are floats, private enums determine how
																		 // each reader treats the floats in this vector 
																	   // (eg for poisitioning {x,y,z})
	
  uint8_t rx_data_stack[256]; // big ol temp rx stack for checksums
  uint8_t coms_rx_state; // determines how the comsInstance handles incoming data
  void reflect_argvec();
  ComsInstance(uart_inst_t *uart, uint baudrate);
};
