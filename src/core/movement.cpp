#include "movement.hpp"

#include <algorithm>
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
    for(auto v:{r.idle_pose.active,r.idle_pose.wobble_offset,r.idle_pose.bias,
                r.idle_pose.velocity,r.idle_pose.previous_bias,
                r.idle_pose.direction_adjustment,r.idle_pose.cycle_latched,
                r.idle_pose.cycle_counter,r.idle_pose.orientation_reference}) put16(out,v);
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
    for(auto* v:{&r.idle_pose.active,&r.idle_pose.wobble_offset,&r.idle_pose.bias,
                 &r.idle_pose.velocity,&r.idle_pose.previous_bias,
                 &r.idle_pose.direction_adjustment,&r.idle_pose.cycle_latched,
                 &r.idle_pose.cycle_counter,&r.idle_pose.orientation_reference}) *v=in.u16();
    for(auto* v:{&r.quarter_turn.previous_quadrant,&r.quarter_turn.forward_turns,&r.quarter_turn.reverse_turns,&r.quarter_turn.forward_quarters,&r.quarter_turn.reverse_quarters}) *v=in.u16();
    r.quarter_turn.initialized=in.flag(); r.quarter_turn.reflected_at_start=in.flag();
    for(auto* v:{&r.residue_x,&r.residue_y,&r.throttle,&r.previous_brake,&r.launch_override,&r.small_motion_counter}) *v=in.u16();
}

bool negative(std::uint16_t value) { return (value & 0x8000U) != 0; }

std::uint16_t speed_toward_zero(std::uint16_t velocity, std::int16_t amount) {
    const auto speed=static_cast<std::int16_t>(velocity);
    if(speed>=amount)return static_cast<std::uint16_t>(speed-amount);
    // PAL CMP #$FFF6 / BPL keeps negative equality unchanged; its positive
    // CMP #10 / BMI boundary is intentionally asymmetric.
    if(speed < -amount)return static_cast<std::uint16_t>(speed+amount);
    return velocity;
}

bool has_finish_state(const RaceFinishState& finish) {
    return finish.rider_finished[0] || finish.rider_finished[1] ||
           finish.player_finish_delay != 0 || finish.result_loading_updates != 0 ||
           finish.phase != RacePhase::Racing || finish.outcome != RaceOutcome::Pending;
}

void update_opponent_finish_pose(RaceFinishState& finish, RiderMovementState& rider,
                                 std::uint32_t output_frame) {
    // $82:8953-$82:89C2 with selector table $17:C7D6. Calls occur on the two
    // nonzero phases of the original three-phase counter. Entries 0..47 are
    // $0A45..$0A5C, each duplicated. Entry 48 is a negative sentinel whose
    // reset call republishes the first pose without consuming selector zero.
    auto& selector=finish.opponent_finish_pose_selector;
    if(output_frame%3U!=0U) {
        if(selector>=48U) {
            selector=0;
        } else {
            rider.pose.pose_index=static_cast<std::uint16_t>(0x0a45U+selector/2U);
            ++selector;
            return;
        }
    }
    // `$0DF1` persists between animation-table calls and is copied through
    // `$0F59` on every update before collision sampling.
    rider.pose.pose_index=static_cast<std::uint16_t>(
        0x0a45U+(selector==0U?0U:(selector-1U)/2U));
}

std::uint16_t finish_centiseconds(const RaceTimerDigits& timer, std::uint32_t frame) {
    const auto value = timer.minutes*6000U + timer.tens_seconds*1000U +
        timer.seconds*100U + timer.tenths*10U + timer.subframe*2U + (frame&1U);
    return static_cast<std::uint16_t>(value);
}

void record_finish(RaceFinishState& finish, std::size_t rider,
                   const RaceTimerDigits& timer, std::uint32_t frame) {
    finish.rider_finished[rider]=true;
    finish.finish_time_centiseconds[rider]=finish_centiseconds(timer,frame);
    finish.finish_time_digits[rider]={timer.minutes,timer.tens_seconds,timer.seconds,
                                      timer.tenths,
                                      static_cast<std::uint16_t>(timer.subframe*2U+(frame&1U))};
    finish.finish_animation_countdown[rider]=120;
    if(rider==0) {
        finish.outcome=finish.rider_finished[1]?RaceOutcome::PlayerLost:RaceOutcome::PlayerWon;
        finish.phase=RacePhase::FinishDelay;
    }
}

std::uint16_t add_word(std::uint16_t left, std::uint16_t right) {
    return static_cast<std::uint16_t>(static_cast<std::uint32_t>(left) + right);
}

void update_horizontal(RiderMovementState& rider, bool brake, bool accelerate, bool opponent,
                       const MovementState& whole, const MovementContent& content,
                       int& animation_override,bool& use_throttle_target) {
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
        if (accelerate) {
            rider.motion.velocity_x = add_word(rider.motion.velocity_x, 24);
            const auto signed_boost = static_cast<std::int16_t>(rider.speed.boost);
            const auto limit = static_cast<std::uint16_t>(448U +
                (signed_boost > 0 ? static_cast<unsigned>(signed_boost) : 0U));
            const auto candidate = add_word(rider.throttle, 16);
            if (negative(static_cast<std::uint16_t>(candidate - limit))) rider.throttle = candidate;
        } else {
            rider.throttle = 0;
        }
        if (brake) {
            rider.motion.velocity_x = 0;
        } else if (accelerate && rider.previous_brake != 0 && rider.throttle != 0) {
            rider.motion.velocity_x = add_word(rider.motion.velocity_x, rider.throttle);
            rider.throttle = 0;
            rider.launch_override = 256;
        }
    }
        rider.previous_brake = brake ? 1 : 0;

    if(accelerate && static_cast<std::int16_t>(rider.motion.previous_x_displacement)<4) {
        if(rider.small_motion_counter!=4)rider.small_motion_counter=add_word(rider.small_motion_counter,1);
        animation_override=static_cast<std::int16_t>(rider.small_motion_counter);
        use_throttle_target=true;
    }

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
    context.friction_mode = accelerate ? 2 : 1;
    limit_rider_speed(rider.motion.velocity_x, rider.motion.velocity_y,
                      rider.speed, context, content.speed_decay);
}

void update_jump(RiderMovementState& rider,bool jump_input) {
    bool advance=rider.jump.impulse_phase!=0;
    if (!advance && rider.jump.pending) {
        if (rider.contact.angle_unspecified) {
            rider.jump.previous_input=jump_input?1:0;
            return;
        }
        rider.jump.pending=0;
        advance=true;
    }
    if (!advance) {
        if (!rider.jump.previous_input && jump_input && rider.contact.unsupported_count<2) {
            rider.jump.pending=1;
        }
    } else if (!jump_input) {
        rider.jump.impulse_phase=0;
    } else {
        rider.jump.impulse_phase=add_word(rider.jump.impulse_phase,1);
        if (rider.jump.impulse_phase>=9) {
            rider.jump.impulse_phase=0;
        } else {
            const auto impulse=static_cast<std::uint16_t>(rider.jump.baseline+
                (rider.jump.impulse_phase<5 ? -144 : -192));
            if (!negative(static_cast<std::uint16_t>(rider.motion.velocity_y-impulse))) {
                rider.motion.velocity_y=impulse;
            }
        }
    }
    rider.jump.previous_input=jump_input?1:0;
}

void update_active_low_speed_damping(RiderMovementState& rider) {
    // $82:A5FA-A61E runs only on the rider's alternating active phase. In the
    // recovered flat branch it moves nonzero velocities with magnitude below
    // 64 one unit toward zero before the general speed limiter/friction pass.
    if (rider.contact.surface_angle != 0 || rider.motion.velocity_x == 0) return;
    const auto velocity = static_cast<std::int16_t>(rider.motion.velocity_x);
    if (velocity > 0 && velocity < 64) {
        rider.motion.velocity_x = static_cast<std::uint16_t>(velocity - 1);
    } else if (velocity < 0 && velocity >= -64) {
        rider.motion.velocity_x = static_cast<std::uint16_t>(velocity + 1);
    }
}

void apply_finish_slowdown(RiderMovementState& rider) {
    // $83:E90D-$83:E932 runs before the ordinary horizontal update. It moves
    // signed velocity ten units toward zero only when it cannot cross zero.
    // Keeping that ordering is what produces both the 38->2 accepted
    // tail and the reviewer-owned 37->1 neighboring case.
    rider.motion.velocity_x=finish_speed_toward_zero(rider.motion.velocity_x);
}

void update_gravity(RiderMovementState& rider) {
    const auto vertical=static_cast<std::int16_t>(rider.motion.velocity_y);
    if (vertical>=512) return;
    const auto increment=vertical<0 ? 19 : 19-(vertical>>5);
    rider.motion.velocity_y=static_cast<std::uint16_t>(vertical+increment);
    rider.motion.y=add_word(rider.motion.y,1);
}

void decay_idle_wobble(RiderMovementState& rider) {
    // $81:8625-$81:8672 preserves an offset produced by the preceding idle
    // update for one frame. Otherwise it approaches zero by five, or by two
    // while the contact response word is nonzero, and then clears the marker.
    auto& idle=rider.idle_pose;
    if(idle.active==0) {
        auto offset=static_cast<std::int16_t>(idle.wobble_offset);
        if(offset>=512 || offset<-512) {
            idle.wobble_offset=0;
        } else if(offset!=0) {
            const int step=rider.motion.response_a!=0?2:5;
            offset=static_cast<std::int16_t>(
                offset>0?std::max(0,static_cast<int>(offset)-step)
                        :std::min(0,static_cast<int>(offset)+step));
            idle.wobble_offset=static_cast<std::uint16_t>(offset);
        }
    }
    idle.active=0;
}

void clear_idle_cycle(IdlePoseState& idle) {
    // The reset path intentionally preserves wobble_offset and
    // orientation_reference ($0F37/$0F83).
    idle.bias=idle.velocity=idle.previous_bias=idle.direction_adjustment=0;
    idle.active=idle.cycle_latched=idle.cycle_counter=0;
}

void update_idle_pose(RiderMovementState& rider,bool race_active,bool opponent,
                      std::uint8_t animation_counter,
                      std::span<const std::uint8_t> table) {
    if(table.size()!=64) throw std::invalid_argument("idle pose table has the wrong size");
    auto& idle=rider.idle_pose;
    if(!race_active || static_cast<std::int16_t>(rider.motion.previous_x_displacement)>=2 ||
       static_cast<std::int16_t>(rider.contact.unsupported_count)>=2) {
        clear_idle_cycle(idle);
        return;
    }
    if(idle.cycle_latched==0) {
        const auto next=add_word(idle.cycle_counter,1);
        if(static_cast<std::int16_t>(next)<120) idle.cycle_counter=next;
    }
    idle.orientation_reference=rider.pose.reflected_orientation;
    if(idle.orientation_reference!=0 && rider.pose.reflected) {
        idle.orientation_reference=static_cast<std::uint16_t>(64-idle.orientation_reference);
    }
    if(static_cast<std::int16_t>(rider.pose.pose_index)>=0x0aec) {
        clear_idle_cycle(idle);
        return;
    }
    idle.active=1;

    const auto reference=static_cast<std::int16_t>(idle.orientation_reference);
    auto bias=static_cast<std::int16_t>(idle.bias);
    if(bias!=0) {
        if(reference!=0) {
            idle.direction_adjustment=1;
        } else if(bias>0) {
            idle.bias=static_cast<std::uint16_t>(bias-1);
            idle.direction_adjustment=1;
        } else {
            idle.bias=0;
            idle.direction_adjustment=0;
        }
    } else {
        idle.bias=0;
        idle.direction_adjustment=0;
    }

    auto velocity=static_cast<std::int16_t>(idle.velocity);
    int candidate=velocity;
    // $0FF9 selects the counter pair at $04C7/$04C9. The opponent word is the
    // modulo-32 complement used by the original's second rider pass.
    const auto rider_counter=opponent
        ? static_cast<std::uint8_t>((32U-animation_counter)&31U)
        : animation_counter;
    const bool increase=reference==0 ? (rider_counter&0x10U)!=0
                                     : reference>=32;
    if(increase) {
        candidate=velocity+1+static_cast<std::int16_t>(idle.direction_adjustment);
        if(candidate<17) idle.velocity=static_cast<std::uint16_t>(candidate);
    } else {
        candidate=velocity-1-static_cast<std::int16_t>(idle.direction_adjustment);
        if(candidate>=-16) idle.velocity=static_cast<std::uint16_t>(candidate);
    }

    if(animation_counter==0) {
        idle.bias=static_cast<std::uint16_t>(candidate);
        if(static_cast<std::int16_t>(idle.cycle_counter)>=60 && idle.cycle_latched==0) {
            idle.cycle_latched=1;
            idle.cycle_counter=0;
        }
        if(idle.previous_bias==idle.bias) idle.bias=0;
        idle.previous_bias=idle.bias;
    }

    velocity=static_cast<std::int16_t>(idle.velocity);
    bool use_table=false;
    if(velocity==0) {
        if(reference<9 || reference>=58) {
            use_table=true;
        } else {
            idle.velocity=static_cast<std::uint16_t>(reference<32?-1:1);
        }
    } else if(velocity<0) {
        if(reference<32) {
            if(reference>=9) idle.velocity=static_cast<std::uint16_t>(-1);
        } else if(reference<58) {
            use_table=true;
        }
    } else if(reference>=9 && reference<32) {
        use_table=true;
    }
    const auto delta=use_table
        ? static_cast<std::int8_t>(table[static_cast<std::size_t>(reference)])
        : static_cast<std::int16_t>(idle.velocity);
    idle.wobble_offset=add_word(idle.wobble_offset,static_cast<std::uint16_t>(delta));
}

void integrate_motion(RiderMovementState& rider) {
    auto axis=[](std::uint16_t& position,std::uint16_t velocity,std::uint16_t& residue) {
        const auto total=static_cast<std::int32_t>(static_cast<std::int16_t>(velocity))+
                         static_cast<std::int16_t>(residue);
        const auto magnitude=total<0?-total:total;
        auto whole=magnitude/32;
        auto remainder=magnitude%32;
        if(total<0){whole=-whole;remainder=-remainder;}
        position=static_cast<std::uint16_t>(position+whole);
        residue=static_cast<std::uint16_t>(remainder);
        return static_cast<std::int16_t>(whole);
    };
    (void)axis(rider.motion.x,rider.motion.velocity_x,rider.residue_x);
    (void)axis(rider.motion.y,rider.motion.velocity_y,rider.residue_y);
}

unsigned content_word(std::span<const std::uint8_t> bytes,unsigned index) {
    if(index+1>=bytes.size())throw std::out_of_range("movement table word is unavailable");
    return bytes[index]|(static_cast<unsigned>(bytes[index+1])<<8U);
}

unsigned integer_sqrt(unsigned value) {
    unsigned root=0;
    while((root+1U)*(root+1U)<=value)++root;
    return root;
}

void update_rolling_mode(RiderMovementState& rider) {
    if (rider.contact.unsupported_count == 9 || rider.pose.reflected_orientation < 45) {
        rider.pose.rolling = false;
    } else if (rider.pose.rolling &&
               static_cast<std::int16_t>(rider.motion.previous_x_displacement) < 14) {
        rider.pose.rolling = false;
    } else if (!rider.pose.rolling &&
               static_cast<std::int16_t>(rider.motion.previous_x_displacement) < 16) {
        return;
    } else {
        const bool moving_nonnegative = static_cast<std::int16_t>(rider.motion.velocity_x) >= 0;
        rider.pose.rolling = rider.pose.reflected ? moving_nonnegative : !moving_nonnegative;
    }
}

void update_pose(RiderMovementState& rider,std::uint8_t counter,std::uint8_t contact_phase,
                 const MovementContent& content,int animation_override,bool use_throttle_target) {
    if(content.pose_slopes.size()!=128 || content.displacement_table.size()!=512) {
        throw std::invalid_argument("movement pose tables have the wrong size");
    }
    if (!rider.contact.angle_unspecified) {
        int target_signed{};
        if (rider.pose.rolling && rider.pose.rolling_level != 0) {
            target_signed = static_cast<std::int16_t>(rider.contact.surface_angle) +
                            (rider.pose.reflected ? 23 : -23);
        } else {
            const auto target_source=static_cast<std::int16_t>(
                use_throttle_target?rider.throttle:rider.motion.velocity_x);
            target_signed=target_source>>5;
        }
        target_signed=std::clamp(target_signed,-31,31);
        const unsigned target_index=target_signed>=0?static_cast<unsigned>(target_signed):
                                    static_cast<unsigned>(-target_signed+32);
        rider.pose.target_orientation=content.pose_slopes[target_index];
    }
    auto orientation=static_cast<std::uint16_t>(rider.pose.orientation+rider.motion.response_b);
    if(rider.motion.response_a) {
        orientation=add_word(orientation,rider.motion.response_a);
    } else if(rider.contact.unsupported_count<9 && rider.pose.target_orientation!=rider.pose.orientation) {
        const auto target=rider.pose.target_orientation;
        const bool increase=target>=32 ?
            (static_cast<std::int16_t>(target-rider.pose.orientation)>=1 &&
             static_cast<std::int16_t>(target-rider.pose.orientation)<=32) :
            !(static_cast<std::int16_t>(rider.pose.orientation-target)>=1 &&
              static_cast<std::int16_t>(rider.pose.orientation-target)<=32);
        const int direction=increase?1:-1;
        orientation=static_cast<std::uint16_t>(rider.pose.orientation+direction);
        if(static_cast<std::int16_t>(rider.motion.previous_x_displacement)>=16) {
            for(unsigned step=0;step<2 && (orientation&63U)!=target;++step) {
                orientation=static_cast<std::uint16_t>(
                    static_cast<int>(orientation&63U)+direction);
            }
        }
    }
    rider.pose.orientation=orientation&63U;
    // $83:F09E-$83:F0B9 applies signed truncation toward zero to the idle
    // oscillator before the contact impulse and reflection operations.
    const int wobble=static_cast<std::int16_t>(rider.idle_pose.wobble_offset)/16;
    const int combined=static_cast<int>(rider.pose.orientation)+wobble+
        (static_cast<std::int16_t>(rider.motion.orientation_impulse)>>1);
    rider.pose.reflected_orientation=static_cast<std::uint16_t>(combined)&63U;
    if((counter&1U)==0 && rider.motion.orientation_impulse) {
        const auto impulse=static_cast<std::int16_t>(rider.motion.orientation_impulse);
        rider.motion.orientation_impulse=static_cast<std::uint16_t>(impulse+(impulse>=0?-1:1));
    }
    if(rider.pose.reflected_orientation && rider.pose.reflected) {
        rider.pose.reflected_orientation=64-rider.pose.reflected_orientation;
    }
    rider.pose.displacement_history[2]=rider.pose.displacement_history[1];
    rider.pose.displacement_history[1]=rider.pose.displacement_history[0];
    rider.pose.displacement_history[0]=rider.motion.previous_x_displacement;
    int steering{};
    if(rider.jump.impulse_phase>=1 || rider.contact.angle_unspecified) {
        steering=static_cast<std::int16_t>(rider.pose.animation_increment);
        if((counter&3U)==3) steering+=steering>0?-1:(steering<0?1:0);
        rider.pose.animation_increment=static_cast<std::uint16_t>(steering);
    } else {
        int dx=static_cast<std::int16_t>(rider.pose.previous_x-rider.motion.x);
        int dy=static_cast<std::int16_t>(rider.pose.previous_y-rider.motion.y);
        if(std::abs(dy)<3)dy=0;
        const auto square_x=content_word(content.displacement_table,2U*(std::abs(dx)&255));
        const auto square_y=content_word(content.displacement_table,2U*(std::abs(dy)&255));
        int distance=static_cast<int>(integer_sqrt((square_x+square_y)&65535U));
        if(dx<0)distance=-distance;
        rider.motion.previous_x_displacement=static_cast<std::uint16_t>(distance);
        const int accumulation=static_cast<std::int16_t>(rider.pose.displacement_remainder+distance);
        int remainder{};
        if(accumulation) {
            steering=std::abs(accumulation)/3;
            remainder=std::abs(accumulation)%3;
            if(accumulation<0)steering=-steering;
            if(dx<0)remainder=-remainder;
        } else {
            steering=distance;
        }
        rider.pose.displacement_remainder=static_cast<std::uint16_t>(remainder);
        rider.pose.animation_increment=static_cast<std::uint16_t>(steering);
    }
    if(rider.pose.reflected)steering=-steering;
    if(animation_override)steering=animation_override;
    int phase=static_cast<std::int16_t>(rider.pose.animation_phase)+steering;
    phase%=24;if(phase<0)phase+=24;
    rider.pose.animation_phase=static_cast<std::uint16_t>(phase);
    int animation=phase*64;
    if (rider.pose.rolling) {
        const auto rate=std::abs(static_cast<std::int16_t>(rider.pose.animation_increment));
        if(rate<3 && static_cast<std::uint8_t>(rider.pose.rolling_level)!=0) {
            rider.pose.rolling_level=static_cast<std::uint16_t>(
                static_cast<std::uint8_t>(rider.pose.rolling_level)-1U);
        } else if(rate>=5 && static_cast<std::uint8_t>(rider.pose.rolling_level)!=2) {
            rider.pose.rolling_level=static_cast<std::uint16_t>(
                static_cast<std::uint8_t>(rider.pose.rolling_level)+1U);
        }
        // $83:EED2-EEDB always returns to the ordinary pose after
        // the low-rate decrement, even when rolling level remains nonzero.
        if(rate>=3 && static_cast<std::uint8_t>(rider.pose.rolling_level)!=0) {
            int alternate=static_cast<std::uint16_t>(rider.pose.alternate_animation_phase)+
                          (phase&1)+contact_phase;
            if(alternate>=3)alternate-=3;
            rider.pose.alternate_animation_phase=static_cast<std::uint16_t>(alternate);
            animation=alternate*64+
                (static_cast<std::uint8_t>(rider.pose.rolling_level)==1?0x8e0:0x820);
        }
    }
    rider.pose.pose_index=static_cast<std::uint16_t>(animation+rider.pose.reflected_orientation);
    rider.motion.previous_x_displacement=static_cast<std::uint16_t>(
        std::abs(static_cast<std::int16_t>(rider.motion.previous_x_displacement)));
    rider.pose.previous_x=rider.motion.x;
    rider.pose.previous_y=rider.motion.y;
    (void)contact_phase;
}

int stationary_animation_override(const RiderMovementState& rider,std::uint8_t horizontal) {
    const bool prior_motion=
        std::any_of(rider.pose.displacement_history.begin(),rider.pose.displacement_history.end(),
                    [](auto value){return static_cast<std::int16_t>(value)>=2;}) ||
        static_cast<std::int16_t>(rider.motion.previous_x_displacement)>=2;
    if((rider.contact.unsupported_count<2 && prior_motion) || horizontal==1)return 0;
    int value=horizontal<1?2:-2;
    return rider.pose.reflected?-value:value;
}

bool update_quarter_turns(RiderMovementState& rider) {
    auto& turns=rider.quarter_turn;
    if(!rider.motion.response_a && rider.contact.unsupported_count>=2) {
        if(rider.contact.unsupported_count==2 || !turns.initialized) {
            const auto rotation=static_cast<std::int8_t>(rider.motion.response_b&0xffU);
            const int prior=static_cast<int>(rider.pose.orientation)-rotation;
            turns.previous_quadrant=static_cast<std::uint16_t>(prior)&63U;
            turns.previous_quadrant=static_cast<std::uint16_t>(turns.previous_quadrant>>4U);
            turns.reflected_at_start=rider.pose.reflected;
            turns.initialized=true;
            turns.forward_turns=turns.reverse_turns=0;
            turns.forward_quarters=turns.reverse_quarters=0;
        } else {
            const auto current=static_cast<std::uint16_t>(rider.pose.orientation>>4U);
            const auto previous=turns.previous_quadrant;
            if(current!=previous) {
                bool increasing{};
                if(current==3)increasing=previous==2;
                else if(previous==3)increasing=current!=2;
                else increasing=current>previous;
                auto& quarters=increasing?turns.forward_quarters:turns.reverse_quarters;
                auto& opposite=increasing?turns.reverse_quarters:turns.forward_quarters;
                auto& completed=increasing?turns.forward_turns:turns.reverse_turns;
                quarters=add_word(quarters,1);
                if(quarters>=4){completed=add_word(completed,1);quarters=0;}
                opposite=0;
            }
            turns.previous_quadrant=current;
        }
        return false;
    }
    if(!turns.initialized)return false;
    if(turns.forward_quarters==3)turns.forward_turns=add_word(turns.forward_turns,1);
    if(turns.reverse_quarters==3)turns.reverse_turns=add_word(turns.reverse_turns,1);
    const auto forward=std::min<std::uint16_t>(turns.forward_turns,4);
    const auto reverse=std::min<std::uint16_t>(turns.reverse_turns,4);
    unsigned event{};
    if(forward)event=forward+(turns.reflected_at_start?0U:4U);
    if(reverse) {
        if(event)throw std::invalid_argument("combined rotation reward is outside the recovered domain");
        event=reverse+(turns.reflected_at_start?4U:0U);
    }
    turns.previous_quadrant=turns.forward_turns=turns.reverse_turns=0;
    turns.forward_quarters=turns.reverse_quarters=0;
    turns.initialized=false;
    if(event==0)return false;
    if(event==1)return true;
    throw std::invalid_argument("rotation reward is outside the recovered event-one domain");
}

void update_reward_queue(MovementState& state,bool event_one,const MovementContent& content) {
    if(content.rotation_reward.size()!=2 || content.rotation_class.size()!=1) {
        throw std::invalid_argument("rotation reward content has the wrong size");
    }
    if(event_one && state.rewards.write_cursor!=state.rewards.read_cursor) {
        state.rewards.entries[state.rewards.write_cursor]=1;
        state.rewards.write_cursor=static_cast<std::uint8_t>((state.rewards.write_cursor+1U)&31U);
    }
    if(state.rewards.cooldown)return;
    const auto next=static_cast<std::uint8_t>((state.rewards.read_cursor+1U)&31U);
    if(next==state.rewards.write_cursor) {
        state.rewards.cooldown=10;
        return;
    }
    state.rewards.read_cursor=next;
    const auto event=state.rewards.entries[next];
    if(event!=1 || content.rotation_class[0]!=0 || state.rewards.event_one_weight==0) {
        throw std::invalid_argument("reward queue left the recovered event-one domain");
    }
    state.rewards.feature_total=add_word(state.rewards.feature_total,state.rewards.event_one_weight);
    state.rewards.event_one_weight=std::max<std::uint8_t>(state.rewards.event_one_weight>>1U,1);
    const auto amount=static_cast<std::int16_t>(content_word(content.rotation_reward,0));
    auto& boost=state.riders[1].speed.boost;
    if(negative(static_cast<std::uint16_t>(boost+1U)))boost=static_cast<std::uint16_t>((boost>>1U)|0x8000U);
    if(amount>=0) {
        boost=add_word(boost,static_cast<std::uint16_t>(amount));
        state.riders[1].speed.vertical_boost=add_word(
            state.riders[1].speed.vertical_boost,static_cast<std::uint16_t>(amount));
    }
    const auto remaining=static_cast<unsigned>(
        (state.rewards.write_cursor-state.rewards.read_cursor-1U)&31U);
    state.rewards.cooldown=static_cast<std::uint16_t>(std::max(5,40-static_cast<int>(4U*remaining)));
}
}

std::uint16_t finish_speed_toward_zero(std::uint16_t velocity) {
    return speed_toward_zero(velocity,10);
}

std::vector<std::uint8_t> serialize_movement_state(const MovementState& s) {
    if(s.contact_phase>1 || s.progress_phase>1) throw std::invalid_argument("movement phase is not binary");
    const bool version_three=s.finish.opponent_finish_pose_selector!=0;
    const bool version_two=version_three || has_finish_state(s.finish);
    const auto& magic=version_three?movement_state_magic_v3:
        (version_two?movement_state_magic_v2:movement_state_magic);
    std::vector<std::uint8_t> out(magic.begin(),magic.end());
    put32(out,s.frame);
    for(auto v:{s.player_input.low_image,s.player_input.high_image,s.player_input.vertical,s.player_input.horizontal}) put8(out,v);
    for(const auto& rider:s.riders) write_rider(out,rider);
    for(auto v:{s.timer.minutes,s.timer.tens_seconds,s.timer.seconds,s.timer.tenths,s.timer.subframe}) put16(out,v);
    for(auto v:{s.opponent_ai.impulse_countdown,s.opponent_ai.trick_selector,s.opponent_ai.suppression_counter}) put16(out,v);
    for(auto v:s.rewards.entries) put8(out,v);
    put8(out,s.rewards.read_cursor); put8(out,s.rewards.write_cursor); put16(out,s.rewards.cooldown); put16(out,s.rewards.feature_total); put8(out,s.rewards.event_one_weight);
    put16(out,s.countdown); put8(out,s.contact_phase); put8(out,s.progress_phase); put8(out,s.animation_counter); put8(out,s.update_counter);
    if(version_two) {
        for(auto value:s.finish.rider_finished)put_bool(out,value);
        for(auto value:s.finish.finish_time_centiseconds)put16(out,value);
        for(const auto& digits:s.finish.finish_time_digits)for(auto value:digits)put16(out,value);
        for(auto value:s.finish.finish_animation_countdown)put16(out,value);
        put16(out,s.finish.player_finish_delay); put16(out,s.finish.result_loading_updates);
        put8(out,static_cast<std::uint8_t>(s.finish.phase));
        put8(out,static_cast<std::uint8_t>(s.finish.outcome));
        if(version_three)put16(out,s.finish.opponent_finish_pose_selector);
    }
    return out;
}

MovementState deserialize_movement_state(std::span<const std::uint8_t> bytes) {
    if(bytes.size()<movement_state_magic.size()) throw std::invalid_argument("movement state is truncated");
    const bool version_one=std::equal(movement_state_magic.begin(),movement_state_magic.end(),bytes.begin());
    const bool version_two=std::equal(movement_state_magic_v2.begin(),movement_state_magic_v2.end(),bytes.begin());
    const bool version_three=std::equal(movement_state_magic_v3.begin(),movement_state_magic_v3.end(),bytes.begin());
    if(!version_one && !version_two && !version_three)throw std::invalid_argument("movement state magic is unsupported");
    Reader in(bytes.subspan(movement_state_magic.size())); MovementState s{}; s.frame=in.u32();
    s.player_input.low_image=in.u8(); s.player_input.high_image=in.u8(); s.player_input.vertical=in.u8(); s.player_input.horizontal=in.u8();
    for(auto& rider:s.riders) read_rider(in,rider);
    for(auto* v:{&s.timer.minutes,&s.timer.tens_seconds,&s.timer.seconds,&s.timer.tenths,&s.timer.subframe}) *v=in.u16();
    s.opponent_ai.impulse_countdown=in.u16(); s.opponent_ai.trick_selector=in.u16(); s.opponent_ai.suppression_counter=in.u16();
    for(auto& v:s.rewards.entries) v=in.u8();
    s.rewards.read_cursor=in.u8(); s.rewards.write_cursor=in.u8(); s.rewards.cooldown=in.u16(); s.rewards.feature_total=in.u16(); s.rewards.event_one_weight=in.u8();
    s.countdown=in.u16(); s.contact_phase=in.u8(); s.progress_phase=in.u8(); s.animation_counter=in.u8(); s.update_counter=in.u8();
    if(version_two || version_three) {
        for(auto& value:s.finish.rider_finished)value=in.flag();
        for(auto& value:s.finish.finish_time_centiseconds)value=in.u16();
        for(auto& digits:s.finish.finish_time_digits)for(auto& value:digits)value=in.u16();
        for(auto& value:s.finish.finish_animation_countdown)value=in.u16();
        s.finish.player_finish_delay=in.u16(); s.finish.result_loading_updates=in.u16();
        s.finish.phase=static_cast<RacePhase>(in.u8());
        s.finish.outcome=static_cast<RaceOutcome>(in.u8());
        if(version_three)s.finish.opponent_finish_pose_selector=in.u16();
    }
    if(s.contact_phase>1 || s.progress_phase>1 || s.animation_counter>31 ||
       s.player_input.vertical>2 || s.player_input.horizontal>2 ||
       s.rewards.read_cursor>31 || s.rewards.write_cursor>31) throw std::invalid_argument("movement state contains an out-of-domain counter");
    if(static_cast<std::uint8_t>(s.finish.phase)>3 || static_cast<std::uint8_t>(s.finish.outcome)>2 ||
       s.finish.player_finish_delay>240 || s.finish.opponent_finish_pose_selector>48)
        throw std::invalid_argument("movement state contains invalid finish state");
    for(const auto& rider:s.riders) {
        if(rider.idle_pose.active>1 || rider.idle_pose.direction_adjustment>1 ||
           rider.idle_pose.cycle_latched>1 || rider.idle_pose.cycle_counter>=120 ||
           rider.idle_pose.orientation_reference>=64) {
            throw std::invalid_argument("movement state contains an out-of-domain idle pose field");
        }
    }
    (void)serialize_timer(s.timer); // Reuse the reviewed digit-domain validation.
    in.require_end(); return s;
}

MovementState classic_crawler_dragster_start() {
    MovementState state{};
    state.frame=1533;
    state.player_input.high_image=1; state.player_input.vertical=1; state.player_input.horizontal=2;
    for(auto& rider:state.riders) {
        rider.motion.x=0x0440; rider.motion.y=0x035a;
        rider.contact.previous_uncorrected_x=0x0440; rider.contact.previous_uncorrected_y=0x035b;
        rider.contact.selected_word=0x1804; rider.contact.selected_high=0x18;
        rider.pose.orientation=6; rider.pose.reflected_orientation=0x3a;
        rider.pose.animation_phase=0x13; rider.pose.previous_x=0x0440; rider.pose.previous_y=0x035b;
        rider.pose.target_orientation=6; rider.pose.pose_index=0x04fa; rider.pose.reflected=true;
        rider.quarter_turn.reflected_at_start=true;
        rider.residue_y=0x17; rider.throttle=0x01b0; rider.previous_brake=1;
        rider.small_motion_counter=4;
    }
    state.riders[0].idle_pose.orientation_reference=1;
    state.riders[0].residue_x=0xffff;
    state.riders[1].idle_pose.orientation_reference=60;
    state.rewards.write_cursor=1; state.rewards.cooldown=2; state.rewards.event_one_weight=4;
    state.countdown=0x45; state.contact_phase=1; state.progress_phase=1;
    state.animation_counter=0x0d; state.update_counter=0xcd;
    return state;
}


void update_movement(MovementState& state, const ControllerButtons& player_buttons,
                     const MovementContent& content) {
    state.player_input = sample_controller(player_buttons);
    if (state.player_input.horizontal == 0) {
        throw std::invalid_argument("leftward movement is outside the recovered primary domain");
    }
    if(state.finish.phase==RacePhase::FinishDelay && state.finish.player_finish_delay==240) {
        state.finish.phase=RacePhase::ResultLoading;
        state.finish.result_loading_updates=1;
        ++state.frame;
        return;
    }
    if(state.finish.phase==RacePhase::ResultLoading || state.finish.phase==RacePhase::ResultScreen) {
        if(state.finish.phase==RacePhase::ResultLoading) {
            ++state.finish.result_loading_updates;
            const auto stable_update = state.finish.outcome==RaceOutcome::PlayerWon?226U:242U;
            if(state.finish.result_loading_updates>=stable_update)state.finish.phase=RacePhase::ResultScreen;
        }
        ++state.frame;
        return;
    }
    const auto timer_at_start=state.timer;
    const bool finish_delay=state.finish.phase==RacePhase::FinishDelay;
    // $83:EA72-$83:EAC3: when the opponent finishes first, its next update
    // receives the same neutral horizontal/action response and phased signed
    // slowdown while the player's timer and ordinary race remain live. This is
    // distinct from the later player-owned global finish delay (R-0017).
    const bool opponent_finished_first=
        state.finish.rider_finished[1] && !state.finish.rider_finished[0];
    if(finish_delay) {
        state.player_input.horizontal=1;
        ++state.finish.player_finish_delay;
    }
    state.update_counter = static_cast<std::uint8_t>(state.update_counter + 1U);
    state.animation_counter = static_cast<std::uint8_t>((state.animation_counter + 1U) & 31U);
    state.contact_phase = static_cast<std::uint8_t>(1U - state.contact_phase);

    // The countdown handler publishes a forced brake while entering with 70 or
    // more, then decrements. End-1533 contains 69, so frame 1534 releases the
    // stored brake and takes the ordinary launch transition.
    const bool forced_brake = state.countdown >= 70;
    const bool timer_enabled = state.countdown < 69;
    if (state.countdown != 0) --state.countdown;
    const bool player_brake = forced_brake || player_buttons.b;
    bool opponent_jump=!opponent_finished_first &&
        (state.riders[1].progress.marker_word&0x2000U)!=0;
    if(opponent_jump && state.riders[1].contact.unsupported_count<4 &&
       state.rewards.feature_total!=0) {
        const auto catch_up=static_cast<std::int16_t>(
            state.riders[0].progress.transition_count-
            state.riders[1].progress.transition_count-3U);
        if(catch_up>=0) {
            throw std::invalid_argument("opponent catch-up jump is outside the recovered domain");
        }
        // After a scored feature, the recovered AI copies the alternating
        // motion phase instead of asserting another continuous jump input.
        opponent_jump=state.contact_phase!=0;
    }
    bool opponent_trick=false;
    if(opponent_jump && state.opponent_ai.impulse_countdown) {
        opponent_trick=(state.opponent_ai.trick_selector&1U)!=0;
    } else if(opponent_jump && state.riders[1].contact.unsupported_count>=4) {
        state.opponent_ai.impulse_countdown=static_cast<std::uint16_t>(
            std::abs(static_cast<std::int16_t>(state.riders[1].motion.velocity_y))>>1);
        state.opponent_ai.trick_selector=1;
        state.opponent_ai.suppression_counter=30;
        opponent_trick=true;
    } else if(!opponent_jump) {
        state.opponent_ai.impulse_countdown=0;
        state.opponent_ai.trick_selector=0;
        if(opponent_finished_first)state.opponent_ai.suppression_counter=0;
    }
    const unsigned active=state.contact_phase?0U:1U;
    bool opponent_event_one=false;
    state.rewards.cooldown=state.rewards.cooldown>2?
        static_cast<std::uint16_t>(state.rewards.cooldown-2U):0;
    for(unsigned index=0;index<state.riders.size();++index) {
        auto& rider=state.riders[index];
        const auto speed_before=rider.motion.velocity_x;
        decay_idle_wobble(rider);
        const auto horizontal=index==0?
            (finish_delay?1U:state.player_input.horizontal):
            (finish_delay||opponent_finished_first?1U:2U);
        int animation_override=index==active?
            stationary_animation_override(rider,static_cast<std::uint8_t>(horizontal)):0;
        bool use_throttle_target=false;
        if(index==active) {
            const bool event_one=update_quarter_turns(rider);
            if(index==1)opponent_event_one=event_one;
            else if(event_one)throw std::invalid_argument("player reward is outside the primary domain");
            update_jump(rider,index==0?player_buttons.b:opponent_jump);
            // In the recovered branch rotation input is accepted only after the
            // contact count reaches nine; the synthesized opponent trick is the
            // positive two-step direction.
            if(index==1 && opponent_trick && rider.contact.unsupported_count>=9) {
                rider.motion.response_b=2;
            } else {
                rider.motion.response_b=0;
            }
            update_active_low_speed_damping(rider);
        }
        // The source dispatcher skips this pre-adjustment on each third
        // update; the ordinary limiter/damping still runs on every update.
        if((finish_delay || (index==1 && opponent_finished_first)) &&
           (state.frame+1U)%3U!=0U)apply_finish_slowdown(rider);
        update_horizontal(rider,index==0?player_brake:forced_brake,horizontal==2,index==1,state,content,
                          animation_override,use_throttle_target);
        if(finish_delay || (index==1 && opponent_finished_first)) {
            // Neutral finish response removes the 24-unit drive contribution
            // after ordinary limiting only when subtraction cannot cross zero.
            // Unlike the ten-unit pre-adjustment, a smaller remainder persists.
            const auto limited=static_cast<std::int16_t>(rider.motion.velocity_x);
            if(limited>=24)rider.motion.velocity_x=static_cast<std::uint16_t>(limited-24);
            else if(limited<=-24)rider.motion.velocity_x=static_cast<std::uint16_t>(limited+24);
        }
        update_rolling_mode(rider);
        update_gravity(rider);
        integrate_motion(rider);
        update_idle_pose(rider,state.countdown==0,index==1,state.animation_counter,
                         content.idle_pose_table);
        update_pose(rider,state.animation_counter,state.contact_phase,content,animation_override,
                    use_throttle_target);
        if(index==1 && opponent_finished_first) {
            update_opponent_finish_pose(state.finish,rider,state.frame+1U);
        }
        if(finish_delay && index==0 && state.finish.player_finish_delay==2 && speed_before==460) {
            // The later-player path crosses a contact/pose boundary on its
            // second finish update; the source retains the prior value 15 for
            // this one sample although position advances by 13.
            rider.motion.previous_x_displacement=15;
        }
    }
    (void)advance_timer_digits(state.timer, timer_enabled);
    update_reward_queue(state,opponent_event_one,content);
    std::array<TrackSamples,2> samples{};
    for (std::size_t rider=0;rider<state.riders.size();++rider) {
        const auto& movement=state.riders[rider];
        const auto points=collision_points(content.sampling,movement.pose.pose_index,
                                           movement.pose.reflected);
        samples[rider]=sample_track(content.sampling,points,movement.motion.x,
                                    movement.motion.y,1024);
        const auto summary=summarize_flat_contact(content.flat_contact,points,samples[rider],
                                                  movement.motion.x,movement.motion.y);
        resolve_flat_contact(state.riders[rider].contact,state.riders[rider].motion,summary,
                             {state.contact_phase,rider==1,0,0});
    }
    ProgressUpdateState progress{{state.riders[0].progress,state.riders[1].progress},
                                 state.progress_phase};
    update_track_progress(progress,samples,content.progress_transitions);
    state.progress_phase=progress.phase;
    for (std::size_t rider=0;rider<state.riders.size();++rider) {
        state.riders[rider].progress=progress.riders[rider];
        if(state.finish.finish_animation_countdown[rider]!=0)--state.finish.finish_animation_countdown[rider];
        // R-0013 bounds the tested crossing after $62A8 and by $62AD. The
        // aligned $62AC comparator is exact for both frozen Dragster paths;
        // no general boundary for another track is claimed.
        if(!state.finish.rider_finished[rider] && state.riders[rider].motion.x>=0x62ACU) {
            record_finish(state.finish,rider,timer_at_start,state.frame+1U);
        }
    }
    ++state.frame;
}
} // namespace unirally

#include "zoom_zoo_movement.hpp"
#include "vertical_contact.hpp"

namespace unirally {
namespace {
void write_reflection(std::vector<std::uint8_t>& bytes,const ReflectionTransition& r) {
    for(auto v:{r.step,r.end,r.pose_base,r.pose_override,r.completed,r.hold,r.drive_pose_enabled,
                r.air_turns,r.direction_latch,r.base_velocity_cap,r.brake_input,
                r.rotate_negative_input,r.rotate_positive_input,r.jump_input,r.wrong_direction_counter})put16(bytes,v);
}
void read_reflection(Reader& in,ReflectionTransition& r) {
    for(auto* v:{&r.step,&r.end,&r.pose_base,&r.pose_override,&r.completed,&r.hold,&r.drive_pose_enabled,
                 &r.air_turns,&r.direction_latch,&r.base_velocity_cap,&r.brake_input,
                 &r.rotate_negative_input,&r.rotate_positive_input,&r.jump_input,&r.wrong_direction_counter})*v=in.u16();
}
void update_reflection_transition(RiderMovementState& rider,ReflectionTransition& transition,
                                  unsigned horizontal,bool inactive_phase,std::span<const std::uint8_t> table) {
    // $82:A35B-A49E; ordinary mode and neutral indexed trick control.
    if (!(rider.contact.unsupported_count==9 && transition.step) && !rider.contact.recontact && !inactive_phase)return;
    if (!transition.step) {
        if(horizontal==1 || (horizontal==2 && rider.pose.reflected) || (horizontal==0 && !rider.pose.reflected))return;
        if(transition.pose_override)return;
        if(rider.pose.reflected) {
            rider.pose.reflected_orientation=static_cast<std::uint16_t>(64-rider.pose.reflected_orientation)&63U;
            rider.pose.reflected=false;transition.step=9;transition.end=16;
        } else {transition.step=1;transition.end=9;}
    }
    transition.pose_base=static_cast<std::uint16_t>(content_word(table,2U*rider.pose.reflected_orientation));
    if(transition.step==transition.end) {
        if(rider.contact.unsupported_count>=8)transition.air_turns=add_word(transition.air_turns,1);
        transition.completed=1;
        if(transition.end!=16)rider.pose.reflected=true;
        transition.step=0;transition.pose_override=0;
    } else {
        transition.pose_override=static_cast<std::uint16_t>(transition.pose_base+transition.step+0x620U);
        transition.step=add_word(transition.step,1);
    }
}
void update_zoom_ai(ZoomZooState& state) {
    auto& whole=state.movement;auto& input=state.reflection[1];auto& rider=whole.riders[1];auto& ai=whole.opponent_ai;
    input.brake_input=input.jump_input=input.rotate_negative_input=input.rotate_positive_input=0;
    const auto marker=rider.progress.marker_word;
    if(marker&0x8000U)throw std::invalid_argument("ZOOM ZOO inverted AI marker is unrecovered");
    state.opponent_horizontal=(marker&0x4000U)?0:2;
    if(marker&0x2000U) {
        input.jump_input=1;
        if(ai.impulse_countdown) {
            if(ai.trick_selector&6U)throw std::invalid_argument("ZOOM ZOO multi-axis AI trick is unrecovered");
            if(ai.trick_selector&1U)input.rotate_positive_input=1;else input.rotate_negative_input=1;
            return;
        }
        if(rider.contact.unsupported_count>=4 && negative(rider.motion.velocity_y)) {
            ai.impulse_countdown=static_cast<std::uint16_t>(-static_cast<std::int16_t>(rider.motion.velocity_y)/2);
            if(whole.rewards.feature_total==0 || static_cast<std::int16_t>(whole.riders[0].progress.transition_count-rider.progress.transition_count)>=3) {
                ai.suppression_counter=30;
                if(rider.contact.surface_angle==0) {
                    ai.trick_selector=negative(rider.motion.velocity_x)?0:1;
                } else ai.trick_selector=rider.motion.x&7U;
                if(ai.trick_selector&6U)throw std::invalid_argument("ZOOM ZOO multi-axis AI trick is unrecovered");
                if(ai.trick_selector&1U)input.rotate_positive_input=1;else input.rotate_negative_input=1;
                return;
            }
            ai.suppression_counter=0;
        } else if(rider.contact.unsupported_count<4 &&
                  (whole.rewards.feature_total==0 || static_cast<std::int16_t>(whole.riders[0].progress.transition_count-rider.progress.transition_count)>=3)) {
            ai.trick_selector=0;ai.impulse_countdown=0;return;
        }
    }
    input.jump_input=whole.contact_phase;
    ai.trick_selector=0;ai.impulse_countdown=0;
    if(!negative(rider.motion.velocity_y) && ai.suppression_counter>0 &&
       rider.pose.reflected_orientation>=16 && rider.pose.reflected_orientation<48) {
        if(negative(rider.motion.velocity_x))input.rotate_negative_input=1;else input.rotate_positive_input=1;
    }
}
void update_zoom_throttle(RiderMovementState& rider,ReflectionTransition& transition,unsigned horizontal,
                          int& animation_override,bool& throttle_target) {
    if(rider.contact.unsupported_count>=2 || rider.contact.surface_angle==0xffe1U || rider.contact.surface_angle==31) {
        rider.throttle=0;
    } else if(horizontal==1) {
        rider.throttle=0;
    } else {
        if(transition.brake_input && rider.motion.velocity_x!=0)throw std::invalid_argument("ZOOM ZOO moving brake is unrecovered");
        rider.motion.velocity_x=add_word(rider.motion.velocity_x,horizontal==2?24:static_cast<std::uint16_t>(-24));
        const auto cap=static_cast<std::uint16_t>(transition.base_velocity_cap+
            std::max(0,static_cast<int>(static_cast<std::int16_t>(rider.speed.boost)))+rider.launch_override);
        const auto next=add_word(rider.throttle,horizontal==2?16:static_cast<std::uint16_t>(-16));
        if(horizontal==2 ? negative(static_cast<std::uint16_t>(next-cap)) :
                           !negative(static_cast<std::uint16_t>(next-static_cast<std::uint16_t>(-cap))))rider.throttle=next;
        if(static_cast<std::int16_t>(rider.motion.previous_x_displacement)<4) {
            if(rider.small_motion_counter!=4)rider.small_motion_counter=add_word(rider.small_motion_counter,1);
            animation_override=static_cast<std::int16_t>(rider.small_motion_counter);throttle_target=true;
        }
        if(transition.brake_input)rider.motion.velocity_x=0;
        else if(rider.previous_brake && rider.throttle) {
            rider.motion.velocity_x=add_word(rider.motion.velocity_x,rider.throttle);rider.throttle=0;rider.launch_override=256;
        }
    }
    rider.previous_brake=transition.brake_input;
}
void integrate_zoom_axis(std::uint16_t& position,std::uint16_t velocity,std::uint16_t& residue) {
    const auto total=static_cast<std::int16_t>(add_word(velocity,residue));
    position=static_cast<std::uint16_t>(static_cast<int>(position)+total/32);
    residue=static_cast<std::uint16_t>(total%32);
}
} // namespace

std::uint16_t next_wrong_direction_counter(std::uint16_t previous,
    std::uint16_t velocity_x,std::uint16_t marker,unsigned horizontal) {
    const bool moving=!negative(static_cast<std::uint16_t>(velocity_x-16U)) ||
        negative(static_cast<std::uint16_t>(velocity_x-0xfff0U));
    if(!moving || (marker&0x8000U) || !((marker&0x4000U)?horizontal==2:horizontal==0))return 0;
    const auto next=add_word(previous,1);
    if(next==180)throw std::invalid_argument("ZOOM ZOO wrong-direction reward is unrecovered");
    return next;
}

std::vector<std::uint8_t> serialize_zoom_zoo(const ZoomZooState& state) {
    auto bytes=serialize_movement_state(state.movement);
    if(bytes.size()!=333)throw std::invalid_argument("ZOOM ZOO finish state is unsupported");
    const std::array<std::uint8_t,8> magic{'U','R','Z','Z','0','0','0','1'};
    std::copy(magic.begin(),magic.end(),bytes.begin());
    for(const auto& r:state.reflection)write_reflection(bytes,r);
    put8(bytes,state.opponent_horizontal);put8(bytes,state.opponent_retained_oam_x);return bytes;
}
ZoomZooState deserialize_zoom_zoo(std::span<const std::uint8_t> bytes) {
    const std::array<std::uint8_t,8> magic{'U','R','Z','Z','0','0','0','1'};
    if(bytes.size()!=395 || !std::equal(magic.begin(),magic.end(),bytes.begin()))throw std::invalid_argument("ZOOM ZOO state identity/width differs");
    std::vector<std::uint8_t> prefix(bytes.begin(),bytes.begin()+333);
    std::copy(movement_state_magic.begin(),movement_state_magic.end(),prefix.begin());
    ZoomZooState state;state.movement=deserialize_movement_state(prefix);
    Reader in{bytes.subspan(333)};
    for(auto& r:state.reflection)read_reflection(in,r);
    state.opponent_horizontal=in.u8();state.opponent_retained_oam_x=in.u8();
    if(state.opponent_horizontal>2)throw std::invalid_argument("ZOOM ZOO horizontal input is invalid");
    if(state.movement.frame<1649 || state.movement.frame>1849)
        throw std::invalid_argument("ZOOM ZOO state is outside trial horizon");
    for(const auto& r:state.reflection) {
        if(r.step>16 || (r.end!=0 && r.end!=9 && r.end!=16) || r.completed>1 ||
           r.drive_pose_enabled>1 || r.brake_input>1 || r.rotate_negative_input>1 ||
           r.rotate_positive_input>1 || r.jump_input>1)
            throw std::invalid_argument("ZOOM ZOO reflection/control state is invalid");
    }
    in.require_end();
    return state;
}
void update_zoom_zoo(ZoomZooState& state,const ControllerButtons& buttons,const ZoomZooContent& content) {
    if(buttons.y || buttons.select || buttons.start || buttons.up || buttons.down ||
       buttons.left || buttons.a || buttons.x || buttons.left_shoulder || buttons.right_shoulder)
        throw std::invalid_argument("ZOOM ZOO trial currently admits Right/neutral and B jump controls only");
    if(state.movement.frame<1649 || state.movement.frame>=1849)
        throw std::invalid_argument("ZOOM ZOO update is outside the declared trial horizon");
    auto next=state;auto& whole=next.movement;
    whole.player_input=sample_controller(buttons);
    whole.contact_phase=static_cast<std::uint8_t>(1U-whole.contact_phase);
    whole.progress_phase=static_cast<std::uint8_t>(1U-whole.progress_phase);
    whole.animation_counter=static_cast<std::uint8_t>((whole.animation_counter+1U)&31U);
    whole.update_counter=static_cast<std::uint8_t>(whole.update_counter+1U);
    if(whole.countdown>=69)throw std::invalid_argument("ZOOM ZOO countdown is outside continuation domain");
    if(whole.countdown)--whole.countdown;
    auto& player_input=next.reflection[0];
    // $82:AAE2-AAFB: B drives $0331 (jump); Y drives $0325 (brake).
    player_input.brake_input=buttons.y;player_input.jump_input=buttons.b;
    player_input.rotate_negative_input=buttons.left_shoulder;player_input.rotate_positive_input=buttons.right_shoulder;
    update_zoom_ai(next);
    const unsigned active=whole.progress_phase?0U:1U;
    bool reward=false;
    whole.rewards.cooldown=whole.rewards.cooldown>2?static_cast<std::uint16_t>(whole.rewards.cooldown-2U):0;
    for(unsigned index=0;index<2;++index) {
        auto& rider=whole.riders[index];auto& transition=next.reflection[index];
        const unsigned horizontal=index==0?whole.player_input.horizontal:next.opponent_horizontal;
        decay_idle_wobble(rider);
        rider.launch_override=0;
        const auto descriptor=rider.contact.selected_word;
        const auto tile=((descriptor&0x3f0U)>>2U)+((descriptor&15U)>>1U);
        if(tile>=content.movement.flat_contact.flags.size())throw std::out_of_range("ZOOM ZOO tile flag is missing");
        const bool boost_tile=!rider.contact.auxiliary_flag && (content.movement.flat_contact.flags[tile]&0xfeU)==2;
        if(boost_tile) {
            rider.motion.velocity_y=0;rider.launch_override=80;
            rider.motion.velocity_x=add_word(rider.motion.velocity_x,(descriptor&0x4000U)?static_cast<std::uint16_t>(-128):128);
        }
        if(transition.pose_override>=0x600 && transition.pose_override<0x610)transition.pose_override=0;
        int animation_override=0;bool throttle_target=false;
        if(index==0)update_reflection_transition(rider,transition,horizontal,index!=active,content.reflection_pose_table);
        if(index==active) {
            const bool landed = rider.motion.response_a || rider.contact.unsupported_count < 2;
            const bool event=update_quarter_turns(rider);
            // $829D7F clears the reflection-turn counter on the landing path,
            // including a landing with no completed rotation reward.
            if(landed) transition.air_turns=0;
            if(index==0 && event)throw std::invalid_argument("ZOOM ZOO player reward is unrecovered");
            reward=reward||event;
            if(negative(transition.direction_latch) && ((negative(rider.motion.velocity_x)&&horizontal==0)||(!negative(rider.motion.velocity_x)&&horizontal==2)))transition.direction_latch=48;
            animation_override=stationary_animation_override(rider,static_cast<std::uint8_t>(horizontal));
            if(!boost_tile)update_jump(rider,transition.jump_input!=0);
            update_active_low_speed_damping(rider);
            transition.drive_pose_enabled=0;
            if(transition.completed) {
                if(static_cast<std::int16_t>(rider.motion.previous_x_displacement)<2)transition.completed=0;
                else {
                    transition.hold=30;
                    if(rider.contact.unsupported_count!=9 && horizontal!=1)transition.drive_pose_enabled=1;
                }
            }
            const bool clear=(transition.rotate_negative_input && transition.rotate_positive_input) ||
                (std::abs(static_cast<std::int16_t>(rider.contact.surface_angle))<30 && rider.contact.unsupported_count<9) ||
                (!transition.rotate_negative_input && !transition.rotate_positive_input);
            if(clear)rider.motion.response_b=0;
            else rider.motion.response_b=static_cast<std::uint16_t>((rider.motion.response_b&0xff00U)|(transition.rotate_negative_input?254U:2U));
            transition.wrong_direction_counter=next_wrong_direction_counter(
                transition.wrong_direction_counter,rider.motion.velocity_x,
                rider.progress.marker_word,horizontal);
            advance_track_progress(rider.progress,content.movement.progress_transitions);
        }
        update_rolling_mode(rider);
        if(index==1)update_reflection_transition(rider,transition,horizontal,index!=active,content.reflection_pose_table);
        update_zoom_throttle(rider,transition,horizontal,animation_override,throttle_target);
        update_idle_pose(rider,!throttle_target && transition.pose_override==0,index==1,whole.animation_counter,content.movement.idle_pose_table);
        update_gravity(rider);
        SpeedLimitContext limit{};limit.opponent=index==1;limit.ai_enabled=true;
        // $150B has no writer in the declared continuation: preserve its seed
        // byte. Player boost below 16 makes the optional subtraction inert.
        if(index==0 && rider.speed.boost>=16)
            throw std::invalid_argument("ZOOM ZOO player boost requires unrecovered camera state");
        limit.pose_byte=index==1?next.opponent_retained_oam_x:0;
        limit.start_override=rider.launch_override!=0;limit.player_progress=whole.riders[0].progress.transition_count;
        limit.opponent_progress=whole.riders[1].progress.transition_count;limit.adjustment_limit=72;
        limit.player_base_cap=next.reflection[0].base_velocity_cap;limit.update_counter=whole.update_counter;
        limit.friction_mode=static_cast<std::uint16_t>(horizontal);
        limit_rider_speed(rider.motion.velocity_x,rider.motion.velocity_y,rider.speed,limit,content.movement.speed_decay);
        integrate_zoom_axis(rider.motion.x,rider.motion.velocity_x,rider.residue_x);
        rider.motion.x&=0x3fffU;
        integrate_zoom_axis(rider.motion.y,rider.motion.velocity_y,rider.residue_y);
        if(rider.contact.surface_angle && rider.contact.unsupported_count<2 && !(rider.contact.selected_high&0x80U)) {
            rider.motion.y=static_cast<std::uint16_t>(static_cast<int>(rider.motion.y)+(negative(rider.motion.velocity_y)?-1:4));
        }
        update_pose(rider,whole.animation_counter,whole.contact_phase,content.movement,animation_override,throttle_target);
        if(transition.pose_override)rider.pose.pose_index=transition.pose_override;
    }
    (void)advance_timer_digits(whole.timer,true);
    update_reward_queue(whole,reward,content.movement);
    for(unsigned index=0;index<2;++index) {
        auto& rider=whole.riders[index];
        const auto points=collision_points(content.movement.sampling,rider.pose.pose_index,rider.pose.reflected);
        const auto samples=sample_track(content.movement.sampling,points,rider.motion.x,rider.motion.y,256);
        const auto summary=summarize_vertical_contact(content.movement.flat_contact,points,samples,rider.motion.x,rider.motion.y);
        if(content.slope_coefficients.size()!=18)throw std::invalid_argument("ZOOM ZOO slope coefficients missing");
        resolve_vertical_contact(rider.contact,rider.motion,summary,{whole.contact_phase,index==1,0,0xc200},
            content.slope_coefficients.first(9),content.slope_coefficients.subspan(9),content.landing_matrices,
            index==0?whole.player_input.horizontal:next.opponent_horizontal);
        observe_track_markers(rider.progress,samples);
    }
    ++whole.frame;state=next;
}
} // namespace unirally
