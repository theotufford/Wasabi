#include <cmath>
#include <coms_protocol.cpp>
#include <coms_protocol.hpp>
#include <cstdlib>
#include <dma_uart.hpp>
#include <hardware/gpio.h>
#include <hardware/timer.h>
#include <hardware/uart.h>
#include <motors.cpp>
#include <motors.hpp>
#include <pico/platform/common.h>
#include <pico/time.h>
#include <pico/types.h>
#include <ratio>
#include <sys/_intsup.h>
#include <sys/unistd.h>
#include <utility>
#include <vector>

using namespace std;

int main() {
  gpio_init(LED_PIN);
  gpio_set_dir(LED_PIN, GPIO_OUT);

  blink(3);

  ComsInstance coms = ComsInstance(uart0, 115200);
  vector<Motor *> axis_motors;
  vector<Motor *> pumps;
  vector<int> pins;

  enum pin_indexes {
    MOT_ENA,
    PUMP_ENA,
    A_lim,
    B_lim,
    Z_lim,
  };

  // configuration loop that exits once everything is configured
  while (true) {
    uint messageFound = coms.get_packet(); // blocking read
    if (messageFound != 0) {
      // if read fail try again
      continue;
    }
    // listen for break signal
    if (coms.coms_rx_code == CONFIRM) {
      break;
    }

    if (coms.coms_rx_code > MACHINE_PIN_DEFINITIONS ||
        coms.coms_rx_code < NEW_PUMP) {
      continue;
    }

    if (coms.coms_rx_code == MACHINE_PIN_DEFINITIONS) {
      pins = coms.argumentVector;
      continue;
    }

    coms.send_vector(coms.coms_rx_code, coms.argumentVector);

    auto new_motor = new Motor(coms.argumentVector);
    if (coms.coms_rx_code == NEW_PUMP) {
      new_motor->is_pump = true;
      pumps.push_back(new_motor);
    } else {
      new_motor->is_pump = false;
      axis_motors.push_back(new_motor);
    }
    coms.send_code(CONFIRM);
  }

  // setup the machine pins
  for (int pin_id : pins) {
    gpio_init(pin_id);
  }

  gpio_set_dir(pins[A_lim], GPIO_IN);
  gpio_set_dir(pins[B_lim], GPIO_IN);
  gpio_set_dir(pins[Z_lim], GPIO_IN);
  gpio_set_dir(pins[MOT_ENA], GPIO_OUT);
  gpio_set_dir(pins[PUMP_ENA], GPIO_OUT);

  gpio_put(pins[MOT_ENA], 1);
  gpio_put(pins[PUMP_ENA], 1);

  gpio_pull_up(pins[A_lim]);
  gpio_pull_up(pins[B_lim]);
  gpio_pull_up(pins[Z_lim]);

  blink(3); // settings initialized blink

  coms.send_code(CONFIRM);

  // main control loop
  while (true) {
    uint messageFound = coms.get_packet(); // blocking header read
    if (messageFound != 0) {
      continue;
    }
    // state machine operated by coms rx code
    switch (coms.coms_rx_code) {
    case RE_REQUEST: {
      break;
    }
    case BUZZ: {
      int pump_id = coms.argumentVector[0] - 1;
      Motor &pump = *pumps[pump_id];
      pump.buzz();
      break;
    }
    case ENABLE_MOTORS: {
      gpio_put(pins[MOT_ENA], 1);
      break;
    }
    case DISABLE_MOTORS: {
      gpio_put(pins[MOT_ENA], 0);
      break;
    }
    case ENABLE_PUMPS: {
      gpio_put(pins[PUMP_ENA], 1);
      break;
    }
    case DISABLE_PUMPS: {
      gpio_put(pins[PUMP_ENA], 0);
      break;
    }
    case MOVE: {
      // prepare moves
      bool moved[3] = {false, false, false};

      for (int axis_ind = 0; axis_ind < 3; axis_ind++) {
        Motor &axis = *axis_motors[axis_ind];
        axis.live_abs_pos = 0;
        axis.move_delta = coms.argumentVector[axis_ind] - axis.current_position;
        if (axis.move_delta == 0) {
          continue;
        }
        axis.move_precalc();
        axis.update_dir();
        moved[axis_ind] = true;
      }

      for (int axis_ind = 0; axis_ind < 3; axis_ind++) {
        if (!moved[axis_ind])
          continue;
        Motor &axis = *axis_motors[axis_ind];
        axis.move_init_time = get_absolute_time();
        hardware_alarm_force_irq(axis.alarm_num);
      }

      for (int axis_ind = 0; axis_ind < 3; axis_ind++) {
        if (!moved[axis_ind])
          continue;
        Motor &axis = *axis_motors[axis_ind];
        while (axis.live_abs_pos != abs(axis.move_delta)) {
          tight_loop_contents();
        }
      }
      break;
    }
    case PUMP_ACTION: {
      int pump_id = coms.argumentVector[0] - 1;
      Motor &pump = *pumps[pump_id];
      pump.vMax = coms.argumentVector[1];
      pump.ang_accel = coms.argumentVector[2];
      int step_count = coms.argumentVector[3];
      if (step_count == 0) {
        break;
      }

      bool is_aspiration = step_count < 0;

      int accel_distance_steps =
          floor((pump.vMax * pump.vMax) / (2. * pump.ang_accel) * pump.TOSTEPS);

      if (is_aspiration) {
        pump.singular_linear_move(step_count);
      } else {
        pump.singular_accel_move(-accel_distance_steps);
        step_count += accel_distance_steps;
        pump.singular_accel_move(step_count);
      }
      break;
    }
    case HOME: {

      for (int axis_ind = 0; axis_ind < 3; axis_ind++) {
        Motor &axis = *axis_motors[axis_ind];
        axis.live_abs_pos = 0;
      }

      Motor &amot = *axis_motors[0];
      Motor &bmot = *axis_motors[1];
      Motor &zmot = *axis_motors[2];

      amot.live_abs_pos = 0;
      bmot.live_abs_pos = 0;
      zmot.live_abs_pos = 0;
      amot.set_dir(1);
      bmot.set_dir(-1);
      zmot.set_dir(-1);

      vector<int> initial_position = {0, 0, 0};

      // b and z motor are moving in reverse to home
      // because their limit switches are at 0
      // home z first to avoid physical collisions
      while (true) {
        bool z_triggered = !gpio_get(pins[Z_lim]);
        if (z_triggered) {
          initial_position[2] = zmot.live_abs_pos;
          zmot.current_position = 0;
          break;
        }
        zmot.step();
        sleep_us(500);
      }

      while (true) {
        bool a_triggered = !gpio_get(pins[A_lim]);
        bool b_triggered = !gpio_get(pins[B_lim]);

        if (a_triggered) {
          int homing_switch_step_pos = ceil(amot.stp_per_rev * 250. / 360.);
          initial_position[0] = homing_switch_step_pos - amot.live_abs_pos;
          amot.current_position = homing_switch_step_pos;
          // TODO
        } else {
          amot.step();
        }
        if (b_triggered) {
          initial_position[1] = bmot.live_abs_pos;
          bmot.current_position = 0;
        } else {
          bmot.step();
        }

        if (a_triggered && b_triggered) {
          break;
        }

        sleep_ms(3);
      }
      coms.send_vector(INITIAL_POSITION, initial_position);
      break;
    }
    }
    coms.send_code(CONFIRM);
  }
}
