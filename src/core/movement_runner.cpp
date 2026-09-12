#include "movement.hpp"

#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
std::vector<std::uint8_t> read_bytes(const std::filesystem::path& path) {
    std::ifstream input(path,std::ios::binary);
    if (!input) throw std::runtime_error("cannot open native movement input: " + path.string());
    return {std::istreambuf_iterator<char>(input),std::istreambuf_iterator<char>()};
}

unirally::ControllerButtons buttons(std::uint16_t mask) {
    unirally::ControllerButtons value{};
    value.b=mask&(1U<<0); value.y=mask&(1U<<1); value.select=mask&(1U<<2);
    value.start=mask&(1U<<3); value.up=mask&(1U<<4); value.down=mask&(1U<<5);
    value.left=mask&(1U<<6); value.right=mask&(1U<<7); value.a=mask&(1U<<8);
    value.x=mask&(1U<<9); value.left_shoulder=mask&(1U<<10);
    value.right_shoulder=mask&(1U<<11);
    return value;
}

void emit(const unirally::MovementState& state) {
    const auto& player=state.riders[0];
    std::cout << state.frame << ' ' << unsigned(state.player_input.low_image) << ' '
              << unsigned(state.player_input.high_image) << ' '
              << unsigned(state.player_input.vertical) << ' '
              << unsigned(state.player_input.horizontal) << ' ' << player.motion.x << ' '
              << static_cast<std::int16_t>(player.motion.previous_x_displacement) << ' '
              << static_cast<std::int16_t>(player.throttle) << ' '
              << static_cast<std::int16_t>(player.motion.velocity_x) << ' '
              << state.timer.minutes << ' ' << state.timer.tens_seconds << ' '
              << state.timer.seconds << ' ' << state.timer.tenths << ' '
              << state.timer.subframe << ' ';
    for (const auto byte : unirally::serialize_movement_state(state)) {
        std::cout << std::hex << std::setw(2) << std::setfill('0') << unsigned(byte);
    }
    std::cout << std::dec << '\n';
}
}

int main(int argc,char** argv) try {
    std::filesystem::path seed,content,inputs;
    for (int index=1;index<argc;index+=2) {
        if (index+1>=argc) throw std::invalid_argument("movement runner requires option values");
        const std::string option=argv[index];
        if (option=="--seed") seed=argv[index+1];
        else if (option=="--content-dir") content=argv[index+1];
        else if (option=="--inputs") inputs=argv[index+1];
        else throw std::invalid_argument("unknown movement runner option: " + option);
    }
    if (seed.empty() || content.empty() || inputs.empty()) {
        throw std::invalid_argument("movement runner requires --seed, --content-dir and --inputs");
    }
    auto state=unirally::deserialize_movement_state(read_bytes(seed));
    const auto masks=read_bytes(content/"speed-masks.bin");
    const auto decrements=read_bytes(content/"speed-decrements.bin");
    const auto track=read_bytes(content/"track-data.bin");
    const auto poses=read_bytes(content/"collision-poses.bin");
    const auto templates=read_bytes(content/"collision-templates.bin");
    const auto transitions=read_bytes(content/"progress-transitions.bin");
    const auto columns=read_bytes(content/"tile-tables.bin");
    const auto flags=read_bytes(content/"tile-flags.bin");
    const auto slopes=read_bytes(content/"pose-slopes.bin");
    const auto displacement=read_bytes(content/"displacement-table.bin");
    const auto reward=read_bytes(content/"rotation-reward.bin");
    const auto reward_class=read_bytes(content/"rotation-class.bin");
    const unirally::MovementContent movement_content{{track,poses,templates},{columns,flags},
                                                       transitions,slopes,displacement,reward,reward_class,
                                                       {masks,decrements}};
    std::ifstream stream(inputs);
    if (!stream) throw std::runtime_error("cannot open controller input stream");
    std::cout << "unirally-movement-v1\n";
    emit(state);
    std::uint32_t frame{};
    unsigned player_mask{},opponent_mask{};
    while (stream >> frame >> player_mask >> opponent_mask) {
        if (frame != state.frame+1 || player_mask>0xffffU || opponent_mask>0xffffU) {
            throw std::invalid_argument("controller input frames or masks are invalid");
        }
        if (opponent_mask != 0) throw std::invalid_argument("controller port 1 is outside the recovered domain");
        unirally::update_movement(state,buttons(static_cast<std::uint16_t>(player_mask)),movement_content);
        emit(state);
    }
    if (!stream.eof()) throw std::invalid_argument("malformed controller input stream");
    return 0;
} catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
}
