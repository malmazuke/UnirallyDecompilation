// Synthetic determinism probe runner. NOT recovered game code.
//
// Usage: lab_runner [--steps N] [--seed S] [--sleep-ms M]
// Prints a single JSON line with the final state hash so the tooling can
// compare runs across processes and hosts. --sleep-ms exists only so the
// tooling's timeout path can be exercised.
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>

#include "lab_state.hpp"

namespace {

bool parse_u32(const char* text, std::uint32_t& out) {
    char* end = nullptr;
    const unsigned long long value = std::strtoull(text, &end, 10);
    if (end == text || *end != '\0' || value > 0xFFFFFFFFull) return false;
    out = static_cast<std::uint32_t>(value);
    return true;
}

}  // namespace

int main(int argc, char** argv) {
    std::uint32_t steps = 1000;
    std::uint32_t seed = 0x12345678u;
    std::uint32_t sleep_ms = 0;
    for (int i = 1; i < argc; ++i) {
        const bool has_value = i + 1 < argc;
        if (std::strcmp(argv[i], "--steps") == 0 && has_value) {
            if (!parse_u32(argv[++i], steps)) return 3;
        } else if (std::strcmp(argv[i], "--seed") == 0 && has_value) {
            if (!parse_u32(argv[++i], seed)) return 3;
        } else if (std::strcmp(argv[i], "--sleep-ms") == 0 && has_value) {
            if (!parse_u32(argv[++i], sleep_ms)) return 3;
        } else {
            std::fprintf(stderr, "usage: lab_runner [--steps N] [--seed S] [--sleep-ms M]\n");
            return 3;
        }
    }
    if (sleep_ms > 0) std::this_thread::sleep_for(std::chrono::milliseconds(sleep_ms));

    lab::State state;
    state.rng = seed;
    for (std::uint32_t t = 0; t < steps; ++t) {
        // A fixed, input-independent script: accelerate, jump every 64 ticks, brake in the last quarter.
        lab::Input input;
        input.buttons = 0x01u;
        if ((t & 63u) == 0u) input.buttons |= 0x04u;
        if (steps >= 4 && t >= steps - steps / 4) input.buttons = 0x02u;
        lab::step(state, input);
    }
    std::printf("{\"schema\":%u,\"steps\":%u,\"seed\":%u,\"tick\":%u,\"hash\":\"%016llx\"}\n",
                static_cast<unsigned>(lab::kStateSchemaVersion), static_cast<unsigned>(steps),
                static_cast<unsigned>(seed), static_cast<unsigned>(state.tick),
                static_cast<unsigned long long>(lab::hash(state)));
    return 0;
}
