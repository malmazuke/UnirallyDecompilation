// A research probe of an isolated dependency, not a native gameplay runner.
#include "track_sampling.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <vector>

static std::vector<std::uint8_t> read_file(const char* path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error("missing extracted content");
    const std::vector<char> chars{std::istreambuf_iterator<char>(stream), {}};
    return {chars.begin(), chars.end()};
}

int main(int argc, char** argv) {
    if (argc != 4) return 3;
    try {
        const auto track = read_file(argv[1]);
        const auto poses = read_file(argv[2]);
        const auto templates = read_file(argv[3]);
        const unirally::SamplingContent content{track, poses, templates};
        unsigned pose{}, reflected{}, x{}, y{}, width{};
        while (std::cin >> pose >> reflected >> x >> y >> width) {
            if (pose > 65535 || reflected > 1 || x > 65535 || y > 65535 || width > 65535) return 3;
            const auto points = unirally::collision_points(content, static_cast<std::uint16_t>(pose), reflected != 0);
            const auto samples = unirally::sample_track(content, points, static_cast<std::uint16_t>(x), static_cast<std::uint16_t>(y), static_cast<std::uint16_t>(width));
            for (const auto value : samples) std::cout << value << ' ';
            std::cout << '\n';
        }
        if (!std::cin.eof()) return 3;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 2;
    }
}
