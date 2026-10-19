#pragma once
#include <array>
#include <atomic>
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

// hardware defined max of 4
#define ALARM_COUNT  4

// arbitrary but must be power of 2 for the AQ_MASK to work
static constexpr int ALARM_QUEUE_LENGTH = 4;
static constexpr int AQ_MASK = ALARM_QUEUE_LENGTH - 1;

using namespace std;

class Motor {
public:
  const int step_pin;
  const int dir_pin;
  const int dir_pin_inverted;
  const int stp_per_rev;
  const int lim_pin;
  const int lim_pin_stp_position;

  volatile int position_state;
  int direction;

  double TORADS = (2 * M_PI / stp_per_rev);
  double TOSTEPS = (stp_per_rev / (2 * M_PI));

  void move_precalc();

  int move_callback();

  void step();
  void set_dir(int dir);

  void buzz(int cycles);

  Motor(const vector<int> &argumentVector);
};


class MoveEntity {
public:
  uint8_t profile_id;
  float angv_max;
  float ang_accel;
  double angular_distance;
  int step_distance;
  double abs_ang_dist;
  int abs_stp_dist;
  double accel_stop;
  double const_stop;
  double total_move_time;
  int calculation_step_index;
  bool is_complete;
  bool homing;
  volatile uint32_t move_init_time;
  volatile bool hit_limit;

  uint32_t next_timing;

  Motor *motor;

  MoveEntity(uint8_t profile_id, float angv_max, float ang_accel_max,
             int step_distance, Motor *mtr);
  uint32_t find_step_timing();
};

struct Step_Event {
  uint32_t time;
  MoveEntity * move;
};
class StepAlarmQueue {
public:
  int alarm_number;
  volatile int write_index = 0;
  volatile int read_index = 0;
  volatile uint32_t time_target = 0;
  atomic<int> queue_count = 0;

  array<Step_Event, ALARM_QUEUE_LENGTH> circ_queue;
  void enqeue_next_step(MoveEntity *entity);
  void alarm_callback();
};
