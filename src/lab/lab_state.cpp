// Synthetic determinism probe. NOT recovered game code.
#include "lab_state.hpp"

#include <cstring>

namespace lab {
namespace {

std::uint32_t lcg(std::uint32_t& rng) noexcept {
    // Numerical Recipes constants; unsigned wrap is defined behaviour.
    rng = rng * 1664525u + 1013904223u;
    return rng;
}

std::int16_t saturate16(std::int32_t value) noexcept {
    if (value > 32767) return 32767;
    if (value < -32768) return -32768;
    return static_cast<std::int16_t>(value);
}

std::int32_t wrap_add32(std::int32_t a, std::int32_t b) noexcept {
    // Two's complement wrap via unsigned arithmetic, then a value-preserving
    // conversion (well defined since C++20).
    return static_cast<std::int32_t>(static_cast<std::uint32_t>(a) + static_cast<std::uint32_t>(b));
}

void put_u16(std::uint8_t* p, std::uint16_t v) noexcept {
    p[0] = static_cast<std::uint8_t>(v & 0xFFu);
    p[1] = static_cast<std::uint8_t>((v >> 8) & 0xFFu);
}

void put_u32(std::uint8_t* p, std::uint32_t v) noexcept {
    put_u16(p, static_cast<std::uint16_t>(v & 0xFFFFu));
    put_u16(p + 2, static_cast<std::uint16_t>((v >> 16) & 0xFFFFu));
}

std::uint16_t get_u16(const std::uint8_t* p) noexcept {
    return static_cast<std::uint16_t>(p[0] | (static_cast<std::uint16_t>(p[1]) << 8));
}

std::uint32_t get_u32(const std::uint8_t* p) noexcept {
    return static_cast<std::uint32_t>(get_u16(p)) | (static_cast<std::uint32_t>(get_u16(p + 2)) << 16);
}

}  // namespace

void step(State& s, Input input) noexcept {
    const std::uint8_t pressed = static_cast<std::uint8_t>(input.buttons & static_cast<std::uint8_t>(~s.previous_buttons));
    std::int32_t velocity = s.velocity_fp;

    if (input.buttons & 0x01u) velocity += 12;
    if (input.buttons & 0x02u) velocity -= 20;
    if (s.airborne == 0u) {
        // Ground friction: arithmetic shift on a non-negative magnitude only.
        const std::int32_t magnitude = velocity < 0 ? -velocity : velocity;
        const std::int32_t friction = magnitude >> 6;
        velocity = velocity < 0 ? velocity + friction : velocity - friction;
        if (pressed & 0x04u) s.airborne = 24;
    } else {
        s.airborne = static_cast<std::uint8_t>(s.airborne - 1u);
        // Wind jitter from the RNG, bounded to [-3, 3].
        const std::uint32_t r = lcg(s.rng);
        velocity += static_cast<std::int32_t>(r % 7u) - 3;
    }

    s.velocity_fp = saturate16(velocity);
    s.position_fp = wrap_add32(s.position_fp, static_cast<std::int32_t>(s.velocity_fp) * 256);
    s.previous_buttons = input.buttons;
    s.tick += 1u;
}

Serialized serialize(const State& s) noexcept {
    Serialized out{};
    std::uint8_t* p = out.data();
    put_u32(p, kStateSchemaVersion);
    put_u32(p + 4, s.tick);
    put_u32(p + 8, static_cast<std::uint32_t>(s.position_fp));
    put_u16(p + 12, static_cast<std::uint16_t>(s.velocity_fp));
    put_u32(p + 14, s.rng);
    p[18] = s.airborne;
    p[19] = s.previous_buttons;
    return out;
}

bool deserialize(const Serialized& bytes, State& out) noexcept {
    const std::uint8_t* p = bytes.data();
    if (get_u32(p) != kStateSchemaVersion) return false;
    State s;
    s.tick = get_u32(p + 4);
    s.position_fp = static_cast<std::int32_t>(get_u32(p + 8));
    s.velocity_fp = static_cast<std::int16_t>(get_u16(p + 12));
    s.rng = get_u32(p + 14);
    s.airborne = p[18];
    s.previous_buttons = p[19];
    out = s;
    return true;
}

std::uint64_t hash(const State& s) noexcept {
    const Serialized bytes = serialize(s);
    std::uint64_t h = 14695981039346656037ull;
    for (const std::uint8_t b : bytes) {
        h ^= b;
        h *= 1099511628211ull;
    }
    return h;
}

}  // namespace lab
