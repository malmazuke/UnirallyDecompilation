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
    put16(out,r.pose.rolling_level); put16(out,r.pose.alternate_animation_phase); put_bool(out,r.pose.rolling);
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
    r.pose.rolling_level=in.u16(); r.pose.alternate_animation_phase=in.u16(); r.pose.rolling=in.flag();
    for(auto* v:{&r.quarter_turn.previous_quadrant,&r.quarter_turn.forward_turns,&r.quarter_turn.reverse_turns,&r.quarter_turn.forward_quarters,&r.quarter_turn.reverse_quarters}) *v=in.u16();
    r.quarter_turn.initialized=in.flag(); r.quarter_turn.reflected_at_start=in.flag();
    for(auto* v:{&r.residue_x,&r.residue_y,&r.throttle,&r.previous_brake,&r.launch_override,&r.small_motion_counter}) *v=in.u16();
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
    if(s.contact_phase>1 || s.progress_phase>1 || s.rewards.read_cursor>31 || s.rewards.write_cursor>31) throw std::invalid_argument("movement state contains an out-of-domain counter");
    in.require_end(); return s;
}
} // namespace unirally
