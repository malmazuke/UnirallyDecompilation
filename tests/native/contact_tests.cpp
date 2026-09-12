#include "flat_contact.hpp"

#include <array>
#include <iostream>
#include <stdexcept>
#include <string_view>

namespace {
void check(bool condition, const char* reason) {
    if (!condition) throw std::runtime_error(reason);
}
template<class Function> void rejects(Function function) {
    bool rejected = false;
    try { function(); } catch (const std::exception&) { rejected = true; }
    check(rejected, "unsupported branch accepted");
}

void sampling() {
    std::array<std::uint8_t, 64> columns{};
    std::array<std::uint8_t, 2> flags{};
    const unirally::FlatContactContent content{columns, flags};
    unirally::CollisionPoints points{};
    unirally::TrackSamples samples{};
    samples[0] = 0x0800; // marker-only must never produce collision support
    auto summary = unirally::summarize_flat_contact(content, points, samples, 0, 0);
    check(!summary.supported && summary.penetration == 0 && summary.selected_word == 0,
          "marker-only sample became solid");
    samples[8] = 2;
    samples[9] = 0x0802;
    summary = unirally::summarize_flat_contact(content, points, samples, 0, 0);
    check(summary.supported && summary.penetration == 1, "initial signed-byte maximum comparison failed");
    check(summary.selected_word == 2 && summary.selected_high == 8, "tie changed first descriptor or lost last metadata");
    points[9].y = 15;
    summary = unirally::summarize_flat_contact(content, points, samples, 0, 0);
    check(summary.penetration == 16, "eight-bit height subtraction lost wrap");
    columns[32] = 0xA0;
    summary = unirally::summarize_flat_contact(content, points, samples, 0, 0);
    check(!summary.supported && summary.selected_word == 2, "empty geometry lost eligible descriptor");
}

void response() {
    unirally::RiderContactState state{};
    state.unsupported_count = 8;
    state.unsupported_duration = 65535;
    unirally::ContactMotion motion{100, 1, 321, 0xFF00, 14, 5, 2, 7};
    unirally::ContactContext context{0, true, 0, 0};
    unirally::FlatContactSummary empty{};
    unirally::resolve_flat_contact(state, motion, empty, context);
    check(state.unsupported_count == 9 && state.previous_unsupported_count == 8 && state.unsupported_duration == 0,
          "unsupported counter boundary or duration wrap failed");
    unirally::resolve_flat_contact(state, motion, empty, context);
    check(state.unsupported_count == 9 && state.previous_unsupported_count == 9, "counter did not saturate");
    check(motion.velocity_y == 0xFF00 && motion.response_b == 2 && motion.response_a == 5,
          "unsupported response changed motion state");
    state.unsupported_count = 0;
    motion.velocity_y = 200;
    const unirally::FlatContactSummary flat{true, 2, 0, 2, 0, 0};
    unirally::resolve_flat_contact(state, motion, flat, context);
    check(state.previous_uncorrected_y == 1 && motion.y == 65535, "saved corrected rather than uncorrected position");
    check(motion.velocity_x == 321 && motion.velocity_y == 0 && motion.response_a == 0 && motion.response_b == 0,
          "continuous response failed");
    motion.response_a = 5; motion.response_b = 2; context.phase = 1;
    unirally::resolve_flat_contact(state, motion, flat, context);
    check(motion.response_a == 5 && motion.response_b == 2 && motion.orientation_impulse == 7,
          "phase-one contact did not preserve orientation channels");
    // A different position/displacement tuple proves dispatch is arithmetic,
    // not a special case for the original frame/coordinates/impulse.
    state.unsupported_count = 9; state.unsupported_duration = 37;
    state.previous_uncorrected_x = 86; state.previous_uncorrected_y = 32;
    motion = {100, 40, 600, 200, 18, 0, 2, 0};
    unirally::resolve_flat_contact(state, motion, flat, context);
    check(state.recontact && state.unsupported_count == 0 && state.unsupported_duration == 0,
          "recontact counters failed");
    check(motion.velocity_x == 600 && motion.velocity_y == 200 && motion.orientation_impulse == 5 && motion.response_b == 2,
          "recontact sentinel/impulse response failed");
}

void boundaries() {
    std::array<std::uint8_t, 64> columns{};
    std::array<std::uint8_t, 2> flags{};
    const unirally::FlatContactContent content{columns, flags};
    unirally::CollisionPoints points{};
    unirally::TrackSamples samples{};
    samples[0] = 2;
    rejects([&] { unirally::summarize_flat_contact(content, points, samples, 0, 0); });
    samples[0] = 0; samples[1] = 2;
    rejects([&] { unirally::summarize_flat_contact(content, points, samples, 0, 0); });
    samples[1] = 0; samples[9] = 0x8002;
    rejects([&] { unirally::summarize_flat_contact(content, points, samples, 0, 0); });
    samples[9] = 2; flags[1] = 1;
    rejects([&] { unirally::summarize_flat_contact(content, points, samples, 0, 0); });
    flags[1] = 0; columns[33] = 1;
    rejects([&] { unirally::summarize_flat_contact(content, points, samples, 0, 0); });
    columns[33] = 0; columns[32] = 127;
    rejects([&] { unirally::summarize_flat_contact(content, points, samples, 0, 0); });
    const unirally::FlatContactContent short_content{{}, flags};
    rejects([&] { unirally::summarize_flat_contact(short_content, points, samples, 0, 0); });

    const unirally::FlatContactSummary flat{true, 2, 0, 2, 0, 0};
    for (unsigned variant = 0; variant < 11; ++variant) {
        unirally::RiderContactState state{};
        state.unsupported_count = 9; state.unsupported_duration = 37;
        state.previous_uncorrected_x = 86; state.previous_uncorrected_y = 32;
        unirally::ContactMotion motion{100, 40, 600, 200, 14, 0, 2, 0};
        unirally::ContactContext context{0, true, 0, 0};
        if (variant == 0) context.cartridge_options = 8;
        if (variant == 1) context.opponent = false;
        if (variant == 2) context.phase = 2;
        if (variant == 3) context.mode = 1;
        if (variant == 4) state.previous_uncorrected_x = 101;
        if (variant == 5) state.previous_uncorrected_x = 99; // non-sentinel coarse angle
        if (variant == 6) state.unsupported_duration = 120;
        if (variant == 7) motion.velocity_y = 0xFFFF;
        if (variant == 8) motion.previous_x_displacement = 32;
        if (variant == 9) state.auxiliary_flag = 1;
        auto summary = flat;
        if (variant == 10) summary.selected_word = 3;
        rejects([&] { unirally::resolve_flat_contact(state, motion, summary, context); });
        check(state.unsupported_count == 9 && state.unsupported_duration == (variant == 6 ? 120 : 37) &&
                  !state.recontact && state.previous_uncorrected_y == 32 && motion.y == 40 && motion.orientation_impulse == 0,
              "rejected update partially mutated state");
    }
    // Zero displacement does not hang the repeated-subtraction endpoint.
    unirally::RiderContactState state{};
    state.unsupported_count = 9; state.unsupported_duration = 9;
    unirally::ContactMotion motion{}; motion.previous_x_displacement = 3;
    unirally::resolve_flat_contact(state, motion, flat, {0, true, 0, 0});
    check(state.recontact && motion.orientation_impulse == 1, "zero-difference endpoint failed");
}
} // namespace

int main(int argc, char** argv) {
    if (argc != 2) return 3;
    try {
        const std::string_view name{argv[1]};
        if (name == "sampling") sampling();
        else if (name == "response") response();
        else if (name == "boundaries") boundaries();
        else return 3;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
