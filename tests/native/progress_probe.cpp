// Isolated progress recurrence on native gathered words, not native movement.
#include "track_progress.hpp"
#include <charconv>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string_view>
#include <vector>

static std::uint16_t argument(const char* text) {
    const std::string_view value{text}; unsigned result{};
    const auto parsed = std::from_chars(value.data(), value.data() + value.size(), result);
    if (parsed.ec != std::errc{} || parsed.ptr != value.data() + value.size() || result > 65535) throw std::invalid_argument("invalid u16 seed");
    return static_cast<std::uint16_t>(result);
}
int main(int argc, char** argv) {
    if (argc != 9) return 3;
    try {
        std::ifstream file(argv[1], std::ios::binary);
        if (!file) return 2;
        const std::vector<char> raw{std::istreambuf_iterator<char>(file), {}};
        const std::vector<std::uint8_t> tables{raw.begin(), raw.end()};
        unirally::ProgressUpdateState state{{{
            {argument(argv[2]),argument(argv[3]),argument(argv[4]),false},
            {argument(argv[5]),argument(argv[6]),argument(argv[7]),false}}},
            static_cast<std::uint8_t>(argument(argv[8]))};
        if (argument(argv[8]) > 1) return 3;
        unsigned value{};
        while (std::cin >> value) {
            std::array<unirally::TrackSamples, 2> samples{};
            if (value > 65535) return 3;
            samples[0][0] = static_cast<std::uint16_t>(value);
            for (unsigned i = 1; i < 20; ++i) {
                if (!(std::cin >> value) || value > 65535) return 3;
                samples[i / 10][i % 10] = static_cast<std::uint16_t>(value);
            }
            unirally::update_track_progress(state, samples, tables);
            // Exercise the explicit representation at every continuation.
            state = unirally::deserialize_progress(unirally::serialize_progress(state));
            for (const auto& rider : state.riders) {
                std::cout << rider.marker_word << ' ' << rider.previous_tag << ' '
                          << rider.transition_count << ' ' << rider.transition_rejected << '\n';
            }
        }
        if (!std::cin.eof()) return 3;
    } catch (const std::invalid_argument& error) {
        std::cerr << error.what() << '\n'; return 3;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n'; return 2;
    }
}
