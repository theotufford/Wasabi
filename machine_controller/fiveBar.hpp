#pragma once
#include <dma_uart.hpp>
#include <cmath>
#include <cstddef>
#include <cstdint>
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

class Motor {
private:
  const int _step_pin;
  const int _dir_pin;
  const int _stp_per_rev;

public:
  enum { step_pin_arg, dir_pin_arg, stp_per_rev_arg };
  MotorDaemon *_daemon;
  bool enabled;
  int current_step_position;
  int abs_step_delta;
  int direction;
  void step();
  Motor(const std::vector<float> &argumentVector);
};

class AxisMotor : public Motor {
private:
  const float _lin_eSteps, _rad_esteps;
  enum { v_max_arg = 2, accel_max_arg, lin_eSteps_arg };

public:
  const float v_max;
  const float accel_max;
  bool homed;
  void queue_movement(float target);
  AxisMotor(std::vector<float> argumentVector);
};

class Pump : public Motor {
private:
  const float _eSteps_ul;
  float est_remainingVolume;
  enum { flowrate_max_arg = 2, eSteps_ul_arg };

public:
	std::string reagent;
  const float flowrate_max;
  float aspirant_volume;
  void buzz();
  void queue_dispense(float volume);
  void queue_aspiration(float volume);
  Pump(const std::vector<float> &argumentVector);
};

class MotorDaemon {
public:
  std::vector<AxisMotor *> move_queue;
  std::vector<Pump *> handler_queue;
  int handle_Movement();
};

struct machineSettings {
  std::unique_ptr<AxisMotor> a_motor;
  std::unique_ptr<AxisMotor> b_motor;
  std::unique_ptr<AxisMotor> z_motor;
  std::vector<std::unique_ptr<Pump>> pumps;
  float dimensions;
};
enum comsCodex : uint8_t {
	WAITING,
  WAKE,
  CONFIRM,
	MESSAGE,
	ERROR,
  NEW_PUMP,
  A_MOTOR,
  B_MOTOR,
  Z_MOTOR,
  MACHINE_PIN_DEFINITIONS,
  MACHINE_DIMENSIONS,
  MOVE,
  DISPENSE,
  ASPIRATE,
	TOGGLE_PUMPS,
	TOGGLE_MOTORS,
	ZERO_MOTORS,
	A_POSITION,
	B_POSITION,
	X_POSITION,
	Y_POSITION,
	Z_POSITION,
};

// two way codex, pico reflects status with the same code used to set it 

class FiveBar {
public:
  std::unique_ptr<AxisMotor> a_motor;
  std::unique_ptr<AxisMotor> b_motor;
  std::unique_ptr<AxisMotor> z_motor;
  std::vector<std::unique_ptr<Pump>> pumps;

  int kinematic_solver(float x_target, float y_target);
  float current_x, current_y, current_z;
  void unlock_movement();
  void unlock_pumps();
  void estop();
  uint8_t machine_state = WAITING; //MOVE state should trigger motor daemon
  int homing_routine();
};

class ComsInstance : public DmaUart {
public:
  void send_string(std::string toWrite);
  void send_data(const uint8_t code, const uint8_t *data);
  void send_data(const uint8_t code);
  uint64_t interbit_time_limit;
  uint await_data();// needs to be called in main loop
  std::vector<float> argumentVector;
  uint8_t rx_data_stack[256];
  uint8_t coms_rx_state; // determines how the comsInstance handles incoming data
  FiveBar setup_machine();
	void loopback();
  ComsInstance(uart_inst_t *uart, uint baudrate);
};
