#pragma once
#include "dma_uart.hpp"
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <hardware/gpio.h>
#include <hardware/uart.h>
#include <iostream>
#include <pico/types.h>
#include <string>
#include <vector>

class MotorDaemon;

class Motor {
private:
  const int _step_pin;
  const int _dir_pin;
  const int _stp_per_rev;

public:
  enum motor_ArgVecKey { step_pin_arg, dir_pin_arg, stp_per_rev_arg };
  MotorDaemon *_daemon;
  bool enabled;
  int current_step_position;
  int abs_step_delta;
  int direction;
  void step();
  Motor(const std::vector<float> &argumentVector)
      : _step_pin((int)argumentVector[motor_ArgVecKey::step_pin_arg]),
        _dir_pin((int)argumentVector[motor_ArgVecKey::dir_pin_arg]),
        _stp_per_rev((int)argumentVector[motor_ArgVecKey::stp_per_rev_arg]) {}
};

class AxisMotor : public Motor {
private:
  const float _lin_eSteps, _rad_esteps;
  enum axis_ArgVecCodex { v_max_arg = 2, accel_max_arg, lin_eSteps_arg };

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

public:
  const float flowrate_max;
  float aspirant_volume;
  void buzz();
  void queue_dispense(float volume);
  void queue_aspiration(float volume);
  Pump();
};

class MotorDaemon {
public:
  std::vector<AxisMotor *> move_queue;
  std::vector<Pump *> handler_queue;
  int handle_move();
  int handle_liquid();
  MotorDaemon();
};

struct machineSettings {
  std::unique_ptr<AxisMotor> a_motor;
  std::unique_ptr<AxisMotor> b_motor;
  std::unique_ptr<AxisMotor> z_motor;
  std::vector<std::unique_ptr<Pump>> pumps;
  float dimensions;
};
enum comsCodex : uint8_t {
  WAKE,
  CONFIRM,
  NEW_PUMP,
  A_MOTOR,
  B_MOTOR,
  Z_MOTOR,
  MACHINE_PIN_DEFINITIONS,
  MACHINE_DIMENSIONS,
  MOVE,
  DISPENSE,
  ASPIRATE
};

// argumentVector intrepreter enums
enum class pump_ArgVecCodex {};

class ComsInstance : public DmaUart {
public:
  void writeString(std::string toWrite);
  void sendMessage(uint code, uint8_t *data);
  uint64_t timeLimit;
  uint awaitMessage();
  std::vector<float> argumentVector;
  uint8_t comsCode = 0;
  machineSettings settings;
  ComsInstance(uart_inst_t *uart, uint baudrate);
};

class FiveBar {
private:
  const AxisMotor *_a_motor, *_b_motor, *_z_motor;
  ComsInstance _coms;
  const std::vector<Pump *> _pumps;

public:
  int kinematic_solver(float x_target, float y_target);
  float current_x, current_y, current_z;
  void unlock_movement();
  void unlock_pumps();
  void estop();
  int homing_routine();
  int get_settings;
  FiveBar(uart_inst_t *uart, uint baudrate);
};
