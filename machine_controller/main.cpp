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
#include <pico/multicore.h>
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
  multicore_launch_core1(core1_main);
  bool settings_initialized = false;
  Motor **motors;
  Motor *A_motor;
  Motor *B_motor;
  Motor *Z_motor;
  Motor **pumps;
  int motor_enable_pin;
  int pump_enable_pin;
  int pump_count;
  ComsInstance coms = ComsInstance(uart0, 115200);

  coms.add_response(Response_Callback(
      "settings_parse", code_conditional_func(WAKE),
      [&](LoopContext ctx) mutable -> void {
        vector<int> settings_vector = ctx.most_recent_packet->get_int_argvec();
        int motor_count = settings_vector.size() / MOTOR_CONFIG_SIZE;
        motors = (Motor **)malloc(sizeof(Motor *) * motor_count);
        for (int i = 0; i < motor_count; i++) {
          auto frame_start = settings_vector.begin() + i * MOTOR_CONFIG_SIZE;
          auto frame_end = frame_start + MOTOR_CONFIG_SIZE;
          vector<int> argvec(frame_start, frame_end);
          Motor *newmotor = new Motor(argvec);
          motors[i] = newmotor;
        }
        A_motor = motors[0];
        B_motor = motors[1];
        Z_motor = motors[2];
        pumps = motors + 3;
        settings_initialized = true;
      }));

  coms.add_response(Response_Callback(
      "move_handler", code_conditional_func(MOVE),
      [&motors](LoopContext ctx) mutable -> void {
        await_async_move(parse_move_packet(ctx.most_recent_packet, motors));
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
        await_async_move({zmove});
        MoveEntity amove(NO_DECEL, ab_vmax, ab_accel, 999999, A_motor);
        MoveEntity bmove(NO_DECEL, ab_vmax, ab_accel, -999999, B_motor);
        await_async_move({amove, bmove});

        vector<int> initial_positions = {-A_motor->position_state,
                                         -B_motor->position_state,
                                         -Z_motor->position_state};
        A_motor->position_state = 0;
        B_motor->position_state = 0;
        Z_motor->position_state = 0;
        ctx.coms_ctx->queue_send(packet_from_vec<int>(HOME, initial_positions));
      }));

  while (true) {
    coms.main_loop();
  }
}
