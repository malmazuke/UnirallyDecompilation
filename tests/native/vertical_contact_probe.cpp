// Captured-argument component probe; not an autonomous native replay.
#include "vertical_contact.hpp"

#include <array>
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

static std::vector<std::uint8_t> read_file(const char* path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error("missing contact probe content");
    const std::vector<char> bytes{std::istreambuf_iterator<char>(stream), {}};
    return {bytes.begin(), bytes.end()};
}

int main(int argc, char** argv) {
    if (argc != 7) return 3;
    try {
        const auto track = read_file(argv[1]);
        const auto poses = read_file(argv[2]);
        const auto templates = read_file(argv[3]);
        const auto columns = read_file(argv[4]);
        const auto flags = read_file(argv[5]);
        const auto coefficients = read_file(argv[6]);
        if (coefficients.size()!=18) return 3;
        const unirally::SamplingContent sampling{track, poses, templates};
        const unirally::FlatContactContent content{columns, flags};
        std::string line;
        std::size_t row = 0;
        while (std::getline(std::cin, line)) {
            ++row;
            std::istringstream input(line);
            std::array<std::uint16_t, 22> values{};
            for (auto& value : values) {
                unsigned raw{};
                if (!(input >> raw) || raw > 65535) return 3;
                value = static_cast<std::uint16_t>(raw);
            }
            std::string extra;
            if (input >> extra) return 3;
            if (values[1] > 1 || values[16] > 1 || values[18] > 1 || values[19] > 1) return 3;
            const auto points = unirally::collision_points(sampling, values[0], values[1] != 0);
            const auto samples = unirally::sample_track(sampling, points, values[3], values[4], values[2]);
            const auto summary = unirally::summarize_vertical_contact(content, points, samples, values[3], values[4]);
            unirally::ContactMotion motion{values[3], values[4], values[5], values[6],
                                          values[7], values[8], values[9], values[10]};
            unirally::RiderContactState state{};
            state.unsupported_count = values[11];
            state.unsupported_duration = values[12];
            state.previous_uncorrected_x = values[13];
            state.previous_uncorrected_y = values[14];
            state.surface_angle = values[15];
            state.angle_unspecified = values[16] != 0;
            state.auxiliary_flag = values[17];
            const unirally::ContactContext context{static_cast<std::uint8_t>(values[18]),
                                                   values[19] != 0, values[20], values[21]};
            try {
                unirally::resolve_vertical_contact(state, motion, summary, context,
                    std::span(coefficients).first(9),std::span(coefficients).subspan(9));
            } catch (const std::exception& error) {
                std::cerr << "row " << row << ": " << error.what() << '\n';
                return 2;
            }
            std::cout << motion.x << ' ' << motion.y << ' ' << motion.velocity_x << ' '
                      << motion.velocity_y << ' ' << motion.response_a << ' ' << motion.response_b << ' '
                      << motion.orientation_impulse << ' ' << state.unsupported_count << ' '
                      << state.previous_unsupported_count << ' ' << state.unsupported_duration << ' '
                      << state.previous_uncorrected_x << ' ' << state.previous_uncorrected_y << ' '
                      << state.surface_angle << ' ' << state.angle_unspecified << ' ' << state.auxiliary_flag << ' '
                      << state.selected_word << ' ' << static_cast<unsigned>(state.selected_high) << ' '
                      << state.recontact << ' ' << summary.supported << ' '
                      << static_cast<unsigned>(summary.penetration) << ' '
                      << static_cast<std::uint16_t>(summary.angle) << ' ' << summary.selected_word << ' '
                      << static_cast<unsigned>(summary.selected_high) << ' '
                      << static_cast<unsigned>(summary.tile_flags) << '\n';
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 2;
    }
}
