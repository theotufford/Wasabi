#include "pico/multicore.h"
#include <cmath>
#include <coms_protocol.cpp>
#include <coms_protocol.hpp>
#include <cstddef>
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
  blink(5);
  init_step_queues();
  multicore_launch_core1(core1_main);
  bool settings_initialized = false;
  Motor *motors[24] = {nullptr}; // more motors than are possible physically -
                                 // lazy solution to stack allocating this
  Motor **pumps = motors + 3;
  Motor *A_motor;
  Motor *B_motor;
  Motor *Z_motor;
  int motor_enable_pin;
  int pump_enable_pin;
  int pump_count;

  ComsInstance coms = ComsInstance(uart0, 115200);
  coms.add_response(Response_Callback(
      "settings_parse", code_conditional_func(WAKE),
      [&](LoopContext ctx) mutable -> void {
        vector<int> settings_vector = ctx.most_recent_packet->get_int_argvec();
        int motor_count = settings_vector.size() / MOTOR_CONFIG_SIZE;

        for (int i = 0; i < motor_count; i++) {
          auto frame_start = settings_vector.begin() + i * MOTOR_CONFIG_SIZE;
          auto frame_end = frame_start + MOTOR_CONFIG_SIZE;
          vector<int> argvec(frame_start, frame_end);
          Motor *newmotor = new Motor(argvec);
          motors[i] = newmotor;
        }
        settings_initialized = true;
        A_motor = motors[0];
        B_motor = motors[1];
        Z_motor = motors[2];

        for (int i = 0; i < 2; i++) {
          vector<MoveEntity> gen_move;
          vector<MoveEntity> rev_gen_move;
          for (Motor *mot : motors) {
            if (mot == nullptr) {
              continue;
            }
            gen_move.push_back(MoveEntity(TRAPEZOIDAL, 10, 4, 200, mot));
            rev_gen_move.push_back(MoveEntity(TRAPEZOIDAL, 10, 4, -200, mot));
          }
          await_async_move(gen_move);
          await_async_move(rev_gen_move);
        }
      }));

  coms.add_response(
      Response_Callback("move_handler", code_conditional_func(MOVE),
                        [&motors](LoopContext ctx) mutable -> void {
                          vector<MoveEntity> given_move =
                              parse_move_packet(ctx.most_recent_packet, motors);
                          await_async_move(given_move);
                        }));
  coms.add_response(
      Response_Callback("buzz_handler", code_conditional_func(BUZZ),
                        [&motors](LoopContext ctx) mutable -> void {
                          int id = ctx.most_recent_packet->get_int_argvec()[0];
                          Motor &to_buzz = *motors[id + 3];
                          to_buzz.buzz(10);
                        }));

  coms.add_response(Response_Callback(
      "home", code_conditional_func(HOME),
      [&](LoopContext ctx) mutable -> void {
        vector<float> speeds = ctx.most_recent_packet->get_float_argvec();
        float z_vmax = speeds[0];
        float z_accel = speeds[1];
        float ab_vmax = speeds[2];
        float ab_accel = speeds[3];

        A_motor->position_state = 0;
        B_motor->position_state = 0;
        Z_motor->position_state = 0;

        MoveEntity zmove(NO_DECEL, z_vmax, z_accel, 999999, Z_motor);
        zmove.homing = true;
        vector<MoveEntity> z_home_move = {zmove};
        await_async_move(z_home_move);

        MoveEntity amove(NO_DECEL, ab_vmax, ab_accel, 999999, A_motor);
        MoveEntity bmove(NO_DECEL, ab_vmax, ab_accel, -999999, B_motor);

        amove.homing = true;
        bmove.homing = true;
        vector<MoveEntity> ab_home_move = {amove, bmove};
        await_async_move(ab_home_move);

        A_motor->set_dir(A_motor->direction * -1);
        B_motor->set_dir(B_motor->direction * -1);

        while (!gpio_get(A_motor->lim_pin)) {
          A_motor->step();
          sleep_ms(10);
        }

        while (!gpio_get(B_motor->lim_pin)) {
          B_motor->step();
          sleep_ms(10);
        }

        A_motor->set_dir(A_motor->direction * -1);
        B_motor->set_dir(B_motor->direction * -1);

        while (gpio_get(A_motor->lim_pin)) {
          A_motor->step();
          sleep_ms(10);
        }

        while (gpio_get(B_motor->lim_pin)) {
          B_motor->step();
          sleep_ms(10);
        }

        vector<int> initial_positions = {
            A_motor->lim_pin_stp_position - A_motor->position_state,
            B_motor->lim_pin_stp_position - B_motor->position_state,
            Z_motor->lim_pin_stp_position - Z_motor->position_state};

        ctx.coms_ctx->queue_send(packet_from_vec<int>(HOME, initial_positions));

        MoveEntity areset(TRAPEZOIDAL, ab_vmax, ab_accel,
                          -A_motor->position_state, A_motor);
        MoveEntity breset(TRAPEZOIDAL, ab_vmax, ab_accel,
                          -B_motor->position_state, B_motor);
        MoveEntity zreset(TRAPEZOIDAL, z_vmax, z_accel,
                          -Z_motor->position_state, Z_motor);

        vector<MoveEntity> reset_move = {areset, breset, zreset};

        A_motor->position_state = A_motor->lim_pin_stp_position;
        B_motor->position_state = B_motor->lim_pin_stp_position;
        Z_motor->position_state = Z_motor->lim_pin_stp_position;

        await_async_move(reset_move);
      }));

  while (true) {
    coms.main_loop();
  }
}
