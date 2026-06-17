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

using namespace std;

class Motor {
public:
  inline static vector<Motor *> async_bay;
  inline static vector<Motor *> pump_table;
  static void move_isr(uint alarm);

  int alarm_num;

  const int step_pin;
  const int dir_pin;
  const int stp_per_rev;
  const int vMax;
  const int ang_accel;

  bool homed;
  enum {
    step_pin_arg,
    dir_pin_arg,
    stp_per_rev_arg,
    ang_v_max_arg,
    ang_accel_arg
  };

  bool enabled;
  int current_position;
  // distance to be traveled this move
  int move_delta;
  double ang_targ_dist;
  int direction;
  volatile int live_abs_pos;
  int accel_stop;
  int constv_stop;
  uint64_t accel_factor;
  uint64_t move_init_time;
  double total_move_time;
  double TORADS = (2 * M_PI / stp_per_rev);
  double TOSTEPS = (stp_per_rev / (2 * M_PI));

  void move_precalc();
  int move_callback();

  // the hardware alarm system really does
  // not like using non static functions
  // so the only reason this exists is to be a static
  // function that calls the correct function.
  void step();
  void update_dir();
  void buzz();

  Motor(const vector<int> &argumentVector, bool non_async);
};
