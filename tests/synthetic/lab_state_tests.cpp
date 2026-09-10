// Synthetic checks for the determinism probe. NOT recovered game code.
#include <cstdint>
#include <cstdio>
#include <cstring>

#include "lab_state.hpp"

namespace {

int failures = 0;

#define EXPECT(cond)                                                            \
    do {                                                                        \
        if (!(cond)) {                                                          \
            std::fprintf(stderr, "%s:%d: expectation failed: %s\n", __FILE__,   \
                         __LINE__, #cond);                                      \
            ++failures;                                                         \
        }                                                                       \
    } while (0)

int roundtrip() {
    lab::State s;
    s.tick = 0xDEADBEEFu;
    s.position_fp = -123456;
    s.velocity_fp = -32768;
    s.rng = 0xCAFEBABEu;
    s.airborne = 7;
    s.previous_buttons = 5;
    const lab::Serialized bytes = lab::serialize(s);
    lab::State back;
    EXPECT(lab::deserialize(bytes, back));
    EXPECT(std::memcmp(&back, &s, sizeof s) == 0 || lab::hash(back) == lab::hash(s));
    EXPECT(back.position_fp == s.position_fp);
    EXPECT(back.velocity_fp == s.velocity_fp);
    EXPECT(back.tick == s.tick);
    // First four bytes are the schema version, little-endian.
    EXPECT(bytes[0] == 1 && bytes[1] == 0 && bytes[2] == 0 && bytes[3] == 0);
    lab::Serialized wrong = bytes;
    wrong[0] = 2;
    EXPECT(!lab::deserialize(wrong, back));
    return failures;
}

int bounds() {
    lab::State s;
    lab::Input accel;
    accel.buttons = 0x01u;
    for (int i = 0; i < 100000; ++i) lab::step(s, accel);
    EXPECT(s.velocity_fp == 32767 || s.velocity_fp > 0);
    EXPECT(s.velocity_fp <= 32767);
    lab::Input brake;
    brake.buttons = 0x02u;
    for (int i = 0; i < 100000; ++i) lab::step(s, brake);
    EXPECT(s.velocity_fp >= -32768);
    EXPECT(s.tick == 200000u);
    // Wrap-around of the 32-bit position must not trap or change tick accounting.
    lab::State w;
    w.position_fp = 0x7FFFFFFF;
    w.velocity_fp = 32767;
    lab::step(w, accel);
    EXPECT(w.position_fp < 0);
    return failures;
}

int known_hash() {
    // Reference value recorded on the first macOS arm64 build (see tasks/M0-02.md).
    // A different value on another host indicates a portability defect in
    // the probe or the toolchain, which is exactly what this check exists for.
    lab::State s;
    for (std::uint32_t t = 0; t < 1000; ++t) {
        lab::Input input;
        input.buttons = 0x01u;
        if ((t & 63u) == 0u) input.buttons |= 0x04u;
        if (t >= 750u) input.buttons = 0x02u;
        lab::step(s, input);
    }
    const std::uint64_t h = lab::hash(s);
    std::printf("known_hash observed %016llx\n", static_cast<unsigned long long>(h));
    EXPECT(h == LAB_KNOWN_HASH);
    return failures;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::fprintf(stderr, "usage: lab_state_tests <roundtrip|bounds|known_hash>\n");
        return 3;
    }
    if (std::strcmp(argv[1], "roundtrip") == 0) return roundtrip() == 0 ? 0 : 1;
    if (std::strcmp(argv[1], "bounds") == 0) return bounds() == 0 ? 0 : 1;
    if (std::strcmp(argv[1], "known_hash") == 0) return known_hash() == 0 ? 0 : 1;
    std::fprintf(stderr, "unknown test %s\n", argv[1]);
    return 3;
}
