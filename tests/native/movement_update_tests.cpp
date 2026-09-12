#include "movement.hpp"

#include <array>
#include <stdexcept>

static void require(bool value) {
    if (!value) throw std::runtime_error("movement update expectation failed");
}

int main() {
    unirally::MovementState state{};
    state.frame = 1533;
    state.countdown = 69;
    state.contact_phase = 1;
    state.progress_phase = 1;
    state.animation_counter = 13;
    state.update_counter = 205;
    for (auto& rider : state.riders) {
        rider.motion.x = 1088;
        rider.throttle = 432;
        rider.previous_brake = 1;
    }
    state.riders[0].residue_x = 0xffff;
    const std::array<std::uint8_t,9> masks{0xff,0x7f,0x3f,0x1f,0x0f,0x07,0x03,0x01,0x00};
    const std::array<std::uint8_t,18> decrements{
        4,0,4,0,4,0,4,0,4,0,4,0,4,0,4,0,4,0};
    unirally::ControllerButtons buttons{};
    buttons.right = true;
    unirally::update_movement(state, buttons, {{masks,decrements}});
    require(state.frame == 1534 && state.countdown == 68);
    require(state.contact_phase == 0 && state.progress_phase == 0);
    require(state.update_counter == 206 && state.animation_counter == 14);
    require(state.player_input.low_image == 0 && state.player_input.high_image == 1);
    require(state.player_input.vertical == 1 && state.player_input.horizontal == 2);
    require(state.riders[0].motion.x == 1102 && state.riders[0].motion.previous_x_displacement == 14);
    require(state.riders[0].motion.velocity_x == 456 && state.riders[0].residue_x == 7);
    require(state.riders[0].throttle == 0 && state.riders[0].launch_override == 256);
    require(state.riders[1].motion.x == 1102 && state.riders[1].residue_x == 8);
    require(state.riders[1].motion.velocity_x == 456 && state.riders[1].launch_override == 256);
    require(state.timer.subframe == 0);
}
