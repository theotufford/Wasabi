#pragma once
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <dma_uart.hpp>
#include <hardware/gpio.h>
#include <hardware/timer.h>
#include <hardware/uart.h>
#include <iostream>
#include <memory>
#include <pico/types.h>
#include <string>
#include <sys/_intsup.h>
#include <tuple>
#include <vector>

#define ALARM_QUEUE_LENGTH 4

using namespace std;

class Motor {
public:
  const int step_pin;
  const int dir_pin;
  const int dir_pin_inverted;
  const int stp_per_rev;
  bool homed;
  enum {
    step_pin_arg,
    dir_pin_arg,
    invert_dir_arg,
    stp_per_rev_arg,
    ang_v_max_arg,
    ang_accel_arg
  };
  int static_position_state;
  volatile int live_steps_moved;
  int direction;

  int accel_stop;
  int constv_stop;
  uint64_t move_init_time;
  double TORADS = (2 * M_PI / stp_per_rev);
  double TOSTEPS = (stp_per_rev / (2 * M_PI));

  void move_precalc();

  int move_callback();

  void step();
  void set_dir(int dir);

  void buzz();

  Motor(const vector<int> &argumentVector);
};

enum { TRAPEZOIDAL, NO_DECEL, NO_ACCEL, LINEAR };

class MoveEntity {
public:
  int profile_id;
  float angv_max;
  float ang_accel;
  double angular_distance;
  int step_distance;
  double accel_stop;
  double const_stop;
  double total_move_time;
  uint64_t next_timing;
  int calculation_step_index;

  Motor *motor;

  MoveEntity(int profile_id, float angv_max, float ang_accel_max,
             int step_distance, Motor *mtr);
  uint64_t find_step_timing();
};

class StepAlarmQueue {
public:
  int alarm_number;
  int write_index = 0;
  int read_index = 0;
  int queue_count = 0;
  uint64_t next_timing = 0;

  array<MoveEntity *, ALARM_QUEUE_LENGTH> circ_queue;
  void enqeue_next_step(MoveEntity * entity);
  void alarm_callback();

  // claim alarm
  StepAlarmQueue();

  // prevent double claiming of alarm
  StepAlarmQueue(const StepAlarmQueue&) = delete;
  StepAlarmQueue& operator=(const StepAlarmQueue&) = delete;

  // unclaim alarm
  ~StepAlarmQueue();

};
