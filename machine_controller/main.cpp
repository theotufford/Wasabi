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
  vector<unique_ptr<Motor>> axis_motors;
  vector<unique_ptr<Motor>> pumps;
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

    coms.send_vector(A_MOTOR, coms.argumentVector);

    bool non_async = coms.coms_rx_code == NEW_PUMP;
    auto new_motor = make_unique<Motor>(coms.argumentVector, non_async);

    if (non_async) {
      pumps.push_back(std::move(new_motor));
    } else {
      axis_motors.push_back(std::move(new_motor));
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
    }
    case ENABLE_MOTORS: {
      gpio_put(pins[MOT_ENA], 1);
    }
    case DISABLE_MOTORS: {
      gpio_put(pins[MOT_ENA], 0);
    }
    case ENABLE_PUMPS: {
      gpio_put(pins[PUMP_ENA], 1);
    }
    case DISABLE_PUMPS: {
      gpio_put(pins[PUMP_ENA], 0);
    }
    case MOVE: {
      // prepare moves
      for (int axis_ind = 0; axis_ind < 3; axis_ind++) {
        Motor &axis = *axis_motors[axis_ind];
        axis.live_abs_pos = 0;
        axis.move_delta = coms.argumentVector[axis_ind] - axis.current_position;
        if (axis.move_delta == 0) {
          continue;
        }
        axis.move_precalc();
        axis.update_dir();
      }

      // initiate moves
      for (int axis_ind = 0; axis_ind < 3; axis_ind++) {
        Motor &axis = *axis_motors[axis_ind];
        if (axis.move_delta == 0) {
          continue;
        }
        axis.move_init_time = get_absolute_time();
        hardware_alarm_force_irq(axis.alarm_num);
      }
      // wait around and dont ask for another message until the full move is
      // complete
      for (int axis_ind = 0; axis_ind < 3; axis_ind++) {
        Motor &axis = *axis_motors[axis_ind];
        while (axis.live_abs_pos != abs(axis.move_delta)) {
          tight_loop_contents();
        }
      }
      break;
    }
    case PUMP_ACTION: {
      int pump_id = coms.argumentVector[0];
      int step_count = coms.argumentVector[1];
      Motor &pump = *pumps[pump_id];
      pump.live_abs_pos = 0;
      pump.move_delta = step_count;
      pump.move_precalc();
      pump.update_dir();
      pump.move_init_time = get_absolute_time();
      hardware_alarm_force_irq(pump.alarm_num);
      while (pump.live_abs_pos != abs(pump.move_delta)) {
        tight_loop_contents();
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
        sleep_ms(1);
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
    }
    }
    coms.send_code(CONFIRM);
  }
}
