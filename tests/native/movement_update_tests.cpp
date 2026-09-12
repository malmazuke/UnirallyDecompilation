#include "movement.hpp"

#include <array>
#include <stdexcept>

static void require(bool value, const char* expectation) {
    if (!value) throw std::runtime_error(expectation);
}

int main() {
    unirally::MovementState state{};
    state.frame = 1533;
    state.countdown = 69;
    state.contact_phase = 1;
    state.progress_phase = 1;
    state.animation_counter = 13;
    state.update_counter = 205;
    state.rewards.write_cursor=1;
    state.rewards.cooldown=2;
    state.rewards.event_one_weight=4;
    for (auto& rider : state.riders) {
        rider.motion.x = 1088;
        rider.motion.y = 64;
        rider.pose.previous_x = 1088;
        rider.pose.previous_y = 64;
        rider.throttle = 432;
        rider.previous_brake = 1;
    }
    state.riders[0].residue_x = 0xffff;
    const std::array<std::uint8_t,9> masks{0xff,0x7f,0x3f,0x1f,0x0f,0x07,0x03,0x01,0x00};
    const std::array<std::uint8_t,18> decrements{
        4,0,4,0,4,0,4,0,4,0,4,0,4,0,4,0,4,0};
    std::array<std::uint8_t,33815> track{};
    std::array<std::uint8_t,32768> poses{};
    std::array<std::uint8_t,17249> templates{};
    std::array<std::uint8_t,80> transitions{};
    std::array<std::uint8_t,640> columns{};
    std::array<std::uint8_t,20> flags{};
    std::array<std::uint8_t,128> slopes{};
    std::array<std::uint8_t,512> displacement{};
    std::array<std::uint8_t,2> reward{};
    std::array<std::uint8_t,1> reward_class{};
    // Authored empty geometry: coarse cells point at zero-filled sample blocks.
    displacement[28]=196;
    unirally::ControllerButtons buttons{};
    buttons.right = true;
    unirally::update_movement(state,buttons,
        {{track,poses,templates},{columns,flags},transitions,slopes,displacement,reward,reward_class,
         {masks,decrements}});
    require(state.frame == 1534 && state.countdown == 68, "frame/countdown");
    require(state.contact_phase == 0 && state.progress_phase == 0, "phases");
    require(state.update_counter == 206 && state.animation_counter == 14, "counters");
    require(state.player_input.low_image == 0 && state.player_input.high_image == 1, "input images");
    require(state.player_input.vertical == 1 && state.player_input.horizontal == 2, "input axes");
    require(state.riders[0].motion.x == 1102 && state.riders[0].motion.previous_x_displacement == 14, "player position/displacement");
    require(state.riders[0].motion.velocity_x == 456 && state.riders[0].residue_x == 7, "player velocity/residue");
    require(state.riders[0].throttle == 0 && state.riders[0].launch_override == 256, "player launch");
    require(state.riders[1].motion.x == 1102 && state.riders[1].residue_x == 8, "opponent position/residue");
    require(state.riders[1].motion.velocity_x == 456 && state.riders[1].launch_override == 256, "opponent launch");
    require(state.timer.subframe == 0, "timer");
}
