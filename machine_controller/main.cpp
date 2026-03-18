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
#include <sys/_intsup.h>
#include <sys/unistd.h>
#include <utility>
#include <vector>

using namespace std;

int main() {
  gpio_init(LED_PIN);
  gpio_set_dir(LED_PIN, GPIO_OUT);
  blink(1);

  ComsInstance coms = ComsInstance(uart0, 115200);
  // Motor settings configuration loop

  vector<unique_ptr<Motor>> axis_motors;
  vector<unique_ptr<Motor>> pumps;

  while (true) {
    uint messageFound = coms.get_packet(); // blocking header read
    if (messageFound != 0) {
      // if read error try again
      continue;
    }
    if (coms.coms_rx_code == CONFIRM) { // listen for break signal
      break;
    }
    if (coms.argumentVector.size() == 0) { // ensure there is data to parse
      continue;
    }
    // ensure the com is a settings packet
    if (coms.coms_rx_code < NEW_PUMP ||
        coms.coms_rx_code > MACHINE_PIN_DEFINITIONS) {
      continue;
    }

    bool non_async = coms.coms_rx_code == NEW_PUMP;
    auto new_motor = make_unique<Motor>(coms.argumentVector, non_async);

    if (non_async) {
      pumps.push_back(std::move(new_motor));
    } else {
      axis_motors.push_back(std::move(new_motor));
    }
    coms.send_data(CONFIRM);
  }

  // settings initialized blink
  blink(5);

  // main motion control loop
  while (true) {
    uint messageFound = coms.get_packet(); // blocking header read
    if (messageFound != 0) {
      continue;
    }
    if (coms.argumentVector.size() == 0) { // ensure there is data to parse
      continue;
    }

    // state machine operated by coms rx code
    switch (coms.coms_rx_code) {

    case MOVE: {
      // prepare moves
      for (int axis_ind = 0; axis_ind < 3; axis_ind++) {
        Motor &axis = *axis_motors[axis_ind];
        axis.target_distance =
            coms.argumentVector[axis_ind] - axis.current_position;
        axis.live_abs_pos = 0;

        if (axis.target_distance == 0) {
          continue;
        }
        // calculate stops
        axis.accel_stop =
            (long)(axis.ang_v_max * axis.ang_v_max * axis.stp_per_rev) /
            (4 * axis.ang_accel * M_PI);

        // if motor wont reach vmax on move
        if (axis.accel_stop > abs(axis.target_distance) / 2) {
          axis.accel_stop = abs(axis.target_distance) / 2;
          // ignore const vel section of mvmnt profile
          axis.constv_stop = 0;
        } else {
          axis.constv_stop = abs(axis.target_distance) - axis.accel_stop;
        }
        axis.update_dir();
      }

      // initiate moves
      for (int axis_ind = 0; axis_ind < 3; axis_ind++) {
        Motor &axis = *axis_motors[axis_ind];
        if (axis.target_distance == 0) {
          continue;
        }
        hardware_alarm_force_irq(axis.alarm_num);
      }
      // wait around and dont ask for another message until the full move is
      // complete
      for (int axis_ind = 0; axis_ind < 3; axis_ind++) {
        Motor &axis = *axis_motors[axis_ind];
        while (axis.live_abs_pos != abs(axis.target_distance)) {
          tight_loop_contents();
        }
      }
      break;
    }
      // naive move function
      //  int local_step_count = 0;
      //  int abs_delta = abs(amot.step_delta);
      //
      //  blink(3);
      //
      //  while (local_step_count < abs_delta) {
      //    amot.step();
      //    sleep_ms(1);
      //    local_step_count++;
      //  }
    case ASPIRATE: {
      break;
    }
    case DISPENSE: {
      break;
    }
    }
    coms.send_data(CONFIRM);
  }
}
