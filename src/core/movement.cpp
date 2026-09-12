#include "movement.hpp"

#include <stdexcept>

namespace unirally {
namespace {
void put8(std::vector<std::uint8_t>& out, std::uint8_t value) { out.push_back(value); }
void put16(std::vector<std::uint8_t>& out, std::uint16_t value) {
    put8(out, static_cast<std::uint8_t>(value)); put8(out, static_cast<std::uint8_t>(value >> 8));
}
void put32(std::vector<std::uint8_t>& out, std::uint32_t value) {
    put16(out, static_cast<std::uint16_t>(value)); put16(out, static_cast<std::uint16_t>(value >> 16));
}
void put_bool(std::vector<std::uint8_t>& out, bool value) { put8(out, value ? 1 : 0); }

class Reader {
public:
    explicit Reader(std::span<const std::uint8_t> bytes) : bytes_(bytes) {}
    std::uint8_t u8() { require(1); return bytes_[offset_++]; }
    std::uint16_t u16() { const auto lo=u8(); return static_cast<std::uint16_t>(lo | (static_cast<unsigned>(u8())<<8)); }
    std::uint32_t u32() { const auto lo=u16(); return static_cast<std::uint32_t>(lo | (static_cast<std::uint32_t>(u16())<<16)); }
    bool flag() { const auto value=u8(); if(value>1) throw std::invalid_argument("movement state flag is not binary"); return value!=0; }
    void require_end() const { if(offset_!=bytes_.size()) throw std::invalid_argument("movement state has trailing bytes"); }
private:
    void require(std::size_t count) const { if(bytes_.size()-offset_<count) throw std::invalid_argument("movement state is truncated"); }
    std::span<const std::uint8_t> bytes_; std::size_t offset_{};
};

void write_rider(std::vector<std::uint8_t>& out, const RiderMovementState& r) {
    for(auto v:{r.motion.x,r.motion.y,r.motion.velocity_x,r.motion.velocity_y,r.motion.previous_x_displacement,r.motion.response_a,r.motion.response_b,r.motion.orientation_impulse}) put16(out,v);
    for(auto v:{r.contact.unsupported_count,r.contact.previous_unsupported_count,r.contact.unsupported_duration,r.contact.previous_uncorrected_x,r.contact.previous_uncorrected_y,r.contact.surface_angle,r.contact.auxiliary_flag,r.contact.selected_word}) put16(out,v);
    put_bool(out,r.contact.angle_unspecified); put8(out,r.contact.selected_high); put_bool(out,r.contact.recontact);
    for(auto v:{r.speed.boost,r.speed.vertical_boost,r.speed.progress_adjustment,r.progress.marker_word,r.progress.previous_tag,r.progress.transition_count}) put16(out,v);
    put_bool(out,r.progress.transition_rejected);
    for(auto v:{r.jump.pending,r.jump.impulse_phase,r.jump.baseline,r.jump.previous_input,r.pose.orientation,r.pose.reflected_orientation,r.pose.animation_phase,r.pose.animation_increment,r.pose.previous_x,r.pose.previous_y,r.pose.displacement_remainder,r.pose.target_orientation,r.pose.pose_index}) put16(out,v);
    for(auto v:r.pose.displacement_history) put16(out,v);
    put16(out,r.pose.rolling_level); put16(out,r.pose.alternate_animation_phase);
    put_bool(out,r.pose.rolling); put_bool(out,r.pose.reflected);
    for(auto v:{r.quarter_turn.previous_quadrant,r.quarter_turn.forward_turns,r.quarter_turn.reverse_turns,r.quarter_turn.forward_quarters,r.quarter_turn.reverse_quarters}) put16(out,v);
    put_bool(out,r.quarter_turn.initialized); put_bool(out,r.quarter_turn.reflected_at_start);
    for(auto v:{r.residue_x,r.residue_y,r.throttle,r.previous_brake,r.launch_override,r.small_motion_counter}) put16(out,v);
}
void read_rider(Reader& in, RiderMovementState& r) {
    for(auto* v:{&r.motion.x,&r.motion.y,&r.motion.velocity_x,&r.motion.velocity_y,&r.motion.previous_x_displacement,&r.motion.response_a,&r.motion.response_b,&r.motion.orientation_impulse}) *v=in.u16();
    for(auto* v:{&r.contact.unsupported_count,&r.contact.previous_unsupported_count,&r.contact.unsupported_duration,&r.contact.previous_uncorrected_x,&r.contact.previous_uncorrected_y,&r.contact.surface_angle,&r.contact.auxiliary_flag,&r.contact.selected_word}) *v=in.u16();
    r.contact.angle_unspecified=in.flag(); r.contact.selected_high=in.u8(); r.contact.recontact=in.flag();
    for(auto* v:{&r.speed.boost,&r.speed.vertical_boost,&r.speed.progress_adjustment,&r.progress.marker_word,&r.progress.previous_tag,&r.progress.transition_count}) *v=in.u16();
    r.progress.transition_rejected=in.flag();
    for(auto* v:{&r.jump.pending,&r.jump.impulse_phase,&r.jump.baseline,&r.jump.previous_input,&r.pose.orientation,&r.pose.reflected_orientation,&r.pose.animation_phase,&r.pose.animation_increment,&r.pose.previous_x,&r.pose.previous_y,&r.pose.displacement_remainder,&r.pose.target_orientation,&r.pose.pose_index}) *v=in.u16();
    for(auto& v:r.pose.displacement_history) v=in.u16();
    r.pose.rolling_level=in.u16(); r.pose.alternate_animation_phase=in.u16();
    r.pose.rolling=in.flag(); r.pose.reflected=in.flag();
    for(auto* v:{&r.quarter_turn.previous_quadrant,&r.quarter_turn.forward_turns,&r.quarter_turn.reverse_turns,&r.quarter_turn.forward_quarters,&r.quarter_turn.reverse_quarters}) *v=in.u16();
    r.quarter_turn.initialized=in.flag(); r.quarter_turn.reflected_at_start=in.flag();
    for(auto* v:{&r.residue_x,&r.residue_y,&r.throttle,&r.previous_brake,&r.launch_override,&r.small_motion_counter}) *v=in.u16();
}

bool negative(std::uint16_t value) { return (value & 0x8000U) != 0; }

std::uint16_t add_word(std::uint16_t left, std::uint16_t right) {
    return static_cast<std::uint16_t>(static_cast<std::uint32_t>(left) + right);
}

void update_horizontal(RiderMovementState& rider, bool brake, bool opponent,
                       const MovementState& whole, const MovementContent& content) {
    // $81:8592 common reset clears the one-update launch override before the
    // throttle routine. The value written by a launch remains in the serialized
    // end-of-frame state and is cleared at the next call.
    rider.launch_override = 0;
    if (rider.contact.unsupported_count >= 2) {
        rider.throttle = 0;
    } else {
        if (brake && rider.motion.velocity_x != 0) {
            throw std::invalid_argument("moving brake is outside the recovered movement domain");
        }
        // Player inputs and the recovered opponent AI both request Right in the
        // primary domain. Leftward throttle remains explicitly unsupported.
        rider.motion.velocity_x = add_word(rider.motion.velocity_x, 24);
        const auto signed_boost = static_cast<std::int16_t>(rider.speed.boost);
        const auto limit = static_cast<std::uint16_t>(448U +
            (signed_boost > 0 ? static_cast<unsigned>(signed_boost) : 0U));
        const auto candidate = add_word(rider.throttle, 16);
        if (negative(static_cast<std::uint16_t>(candidate - limit))) rider.throttle = candidate;
        if (brake) {
            rider.motion.velocity_x = 0;
        } else if (rider.previous_brake != 0 && rider.throttle != 0) {
            rider.motion.velocity_x = add_word(rider.motion.velocity_x, rider.throttle);
            rider.throttle = 0;
            rider.launch_override = 256;
        }
    }
    rider.previous_brake = brake ? 1 : 0;

    SpeedLimitContext context{};
    context.opponent = opponent;
    context.pose_byte = 0; // Primary screen-coordinate values 43..104 keep this branch inactive.
    context.start_override = rider.launch_override != 0;
    context.ai_enabled = true;
    context.player_progress = whole.riders[0].progress.transition_count;
    context.opponent_progress = whole.riders[1].progress.transition_count;
    context.adjustment_limit = 96;
    context.player_base_cap = 448;
    context.update_counter = whole.update_counter;
    context.friction_mode = 2;
    limit_rider_speed(rider.motion.velocity_x, rider.motion.velocity_y,
                      rider.speed, context, content.speed_decay);

    const auto total = static_cast<std::int32_t>(static_cast<std::int16_t>(rider.motion.velocity_x)) +
                       static_cast<std::int16_t>(rider.residue_x);
    const auto magnitude = total < 0 ? -total : total;
    auto whole_units = magnitude / 32;
    auto remainder = magnitude % 32;
    if (total < 0) { whole_units = -whole_units; remainder = -remainder; }
    rider.motion.x = static_cast<std::uint16_t>(rider.motion.x + whole_units);
    rider.residue_x = static_cast<std::uint16_t>(remainder);
    rider.motion.previous_x_displacement = static_cast<std::uint16_t>(whole_units);
}
}

std::vector<std::uint8_t> serialize_movement_state(const MovementState& s) {
    if(s.contact_phase>1 || s.progress_phase>1) throw std::invalid_argument("movement phase is not binary");
    std::vector<std::uint8_t> out(movement_state_magic.begin(),movement_state_magic.end());
    put32(out,s.frame);
    for(auto v:{s.player_input.low_image,s.player_input.high_image,s.player_input.vertical,s.player_input.horizontal}) put8(out,v);
    for(const auto& rider:s.riders) write_rider(out,rider);
    for(auto v:{s.timer.minutes,s.timer.tens_seconds,s.timer.seconds,s.timer.tenths,s.timer.subframe}) put16(out,v);
    for(auto v:{s.opponent_ai.impulse_countdown,s.opponent_ai.trick_selector,s.opponent_ai.suppression_counter}) put16(out,v);
    for(auto v:s.rewards.entries) put8(out,v);
    put8(out,s.rewards.read_cursor); put8(out,s.rewards.write_cursor); put16(out,s.rewards.cooldown); put16(out,s.rewards.feature_total); put8(out,s.rewards.event_one_weight);
    put16(out,s.countdown); put8(out,s.contact_phase); put8(out,s.progress_phase); put8(out,s.animation_counter); put8(out,s.update_counter);
    return out;
}

MovementState deserialize_movement_state(std::span<const std::uint8_t> bytes) {
    if(bytes.size()<movement_state_magic.size()) throw std::invalid_argument("movement state is truncated");
    for(std::size_t i=0;i<movement_state_magic.size();++i) if(bytes[i]!=movement_state_magic[i]) throw std::invalid_argument("movement state magic is unsupported");
    Reader in(bytes.subspan(movement_state_magic.size())); MovementState s{}; s.frame=in.u32();
    s.player_input.low_image=in.u8(); s.player_input.high_image=in.u8(); s.player_input.vertical=in.u8(); s.player_input.horizontal=in.u8();
    for(auto& rider:s.riders) read_rider(in,rider);
    for(auto* v:{&s.timer.minutes,&s.timer.tens_seconds,&s.timer.seconds,&s.timer.tenths,&s.timer.subframe}) *v=in.u16();
    s.opponent_ai.impulse_countdown=in.u16(); s.opponent_ai.trick_selector=in.u16(); s.opponent_ai.suppression_counter=in.u16();
    for(auto& v:s.rewards.entries) v=in.u8();
    s.rewards.read_cursor=in.u8(); s.rewards.write_cursor=in.u8(); s.rewards.cooldown=in.u16(); s.rewards.feature_total=in.u16(); s.rewards.event_one_weight=in.u8();
    s.countdown=in.u16(); s.contact_phase=in.u8(); s.progress_phase=in.u8(); s.animation_counter=in.u8(); s.update_counter=in.u8();
    if(s.contact_phase>1 || s.progress_phase>1 || s.animation_counter>31 ||
       s.player_input.vertical>2 || s.player_input.horizontal>2 ||
       s.rewards.read_cursor>31 || s.rewards.write_cursor>31) throw std::invalid_argument("movement state contains an out-of-domain counter");
    (void)serialize_timer(s.timer); // Reuse the reviewed digit-domain validation.
    in.require_end(); return s;
}


void update_movement(MovementState& state, const ControllerButtons& player_buttons,
                     const MovementContent& content) {
    state.player_input = sample_controller(player_buttons);
    if (state.player_input.horizontal == 0) {
        throw std::invalid_argument("leftward movement is outside the recovered primary domain");
    }
    state.update_counter = static_cast<std::uint8_t>(state.update_counter + 1U);
    state.animation_counter = static_cast<std::uint8_t>((state.animation_counter + 1U) & 31U);
    state.contact_phase = static_cast<std::uint8_t>(1U - state.contact_phase);
    state.progress_phase = static_cast<std::uint8_t>(1U - state.progress_phase);

    // The countdown handler publishes a forced brake while entering with 70 or
    // more, then decrements. End-1533 contains 69, so frame 1534 releases the
    // stored brake and takes the ordinary launch transition.
    const bool forced_brake = state.countdown >= 70;
    const bool timer_enabled = state.countdown < 69;
    if (state.countdown != 0) --state.countdown;
    const bool player_brake = forced_brake || player_buttons.b;
    if (state.player_input.horizontal != 2 && !player_brake) {
        throw std::invalid_argument("neutral player throttle is not implemented yet");
    }
    update_horizontal(state.riders[0], player_brake, false, state, content);
    update_horizontal(state.riders[1], forced_brake, true, state, content);
    (void)advance_timer_digits(state.timer, timer_enabled);
    ++state.frame;
}
} // namespace unirally
