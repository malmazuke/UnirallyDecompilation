#include "speed_limits.hpp"
#include <array>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <vector>

std::vector<std::uint8_t> load(const char* path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error("missing speed content");
    return {std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
}
int main(int argc, char** argv) {
    try {
        if (argc != 3) throw std::runtime_error("expected mask and decrement content paths");
        const auto masks = load(argv[1]);
        const auto decrements = load(argv[2]);
        std::array<unsigned, 19> values{};
        while (std::cin >> values[0]) {
            for (std::size_t index = 1; index < values.size(); ++index) {
                if (!(std::cin >> values[index])) throw std::runtime_error("incomplete speed input");
            }
            for (const auto value : values) if (value > 65535) throw std::runtime_error("input exceeds word");
            if (values[5] > 1 || values[8] > 255 || values[16] > 255 || values[18] > 255) {
                throw std::runtime_error("invalid rider or byte context");
            }
            const auto word = [&values](std::size_t index) { return static_cast<std::uint16_t>(values[index]); };
            auto velocity_x = word(0);
            auto velocity_y = word(1);
            unirally::SpeedModifiers state{word(2), word(3), word(4)};
            unirally::SpeedLimitContext context{
                values[5] != 0, values[6] != 0, values[7] != 0, static_cast<std::uint8_t>(values[8]),
                values[9] != 0, values[10] != 0, word(11), word(12), word(13), word(14), word(15),
                static_cast<std::uint8_t>(values[16]), word(17), static_cast<std::uint8_t>(values[18])};
            unirally::limit_rider_speed(velocity_x, velocity_y, state, context, {masks, decrements});
            std::cout << velocity_x << ' ' << velocity_y << ' ' << state.boost << ' '
                      << state.vertical_boost << ' ' << state.progress_adjustment << '\n';
        }
        if (!std::cin.eof()) throw std::runtime_error("invalid speed input");
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
