// Synthetic determinism probe. NOT recovered game code.
//
// A tiny fixed-width simulation whose only purpose is to check that the
// toolchain, arithmetic conventions and serialization behave identically on
// every supported host. Every operation is defined on unsigned integers or
// on explicitly bounded signed values, so the result is specified by the
// language rather than by the compiler.
#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace lab {

inline constexpr std::uint32_t kStateSchemaVersion = 1;

struct Input {
    std::uint8_t buttons = 0;  // bit0 accelerate, bit1 brake, bit2 jump
};

struct State {
    std::uint32_t tick = 0;
    std::int32_t position_fp = 0;  // 16.16 fixed point, wrapping in two's complement
    std::int16_t velocity_fp = 0;  // 8.8 fixed point, saturated
    std::uint32_t rng = 0x12345678u;
    std::uint8_t airborne = 0;
    std::uint8_t previous_buttons = 0;
};

inline constexpr std::size_t kSerializedSize = 4 + 4 + 4 + 2 + 4 + 1 + 1;
using Serialized = std::array<std::uint8_t, kSerializedSize>;

// Advances the state by one update. Deterministic and total.
void step(State& state, Input input) noexcept;

// Canonical little-endian encoding with an explicit schema version prefix.
Serialized serialize(const State& state) noexcept;
bool deserialize(const Serialized& bytes, State& out) noexcept;

// FNV-1a over the canonical encoding. Independent of host byte order.
std::uint64_t hash(const State& state) noexcept;

}  // namespace lab
