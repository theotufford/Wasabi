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
  const int lim_pin;

  volatile int position_state;
  int direction;

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
  bool is_complete;
  volatile bool hit_limit;

  Motor *motor;

  MoveEntity(int profile_id, float angv_max, float ang_accel_max,
             int step_distance, Motor *mtr);
  uint64_t find_step_timing();
};

class StepAlarmQueue {
public:
  int alarm_number;
  volatile int write_index = 0;
  volatile int read_index = 0;
  int queue_count = 0;
  uint64_t next_timing = 0;

  array<MoveEntity *, ALARM_QUEUE_LENGTH> circ_queue;
  void enqeue_next_step(MoveEntity *entity);
  void alarm_callback();
};
