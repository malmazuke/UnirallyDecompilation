#include "movement.hpp"

#include <array>
#include <stdexcept>

static void require(bool value, const char* expectation) {
    if (!value) throw std::runtime_error(expectation);
}

int main() {
    // These neighboring values pin the finish pre-adjustment's general
    // non-crossing ten-unit arithmetic. In the reviewer-owned full update,
    // incoming37 becomes27 here and the ordinary limiter then produces1.
    require(unirally::finish_speed_toward_zero(12)==2 &&
            unirally::finish_speed_toward_zero(11)==1 &&
            unirally::finish_speed_toward_zero(10)==0 &&
            unirally::finish_speed_toward_zero(9)==9 &&
            static_cast<std::int16_t>(unirally::finish_speed_toward_zero(
                static_cast<std::uint16_t>(-11)))==-1 &&
            static_cast<std::int16_t>(unirally::finish_speed_toward_zero(
                static_cast<std::uint16_t>(-10)))==-10 &&
            static_cast<std::int16_t>(unirally::finish_speed_toward_zero(
                static_cast<std::uint16_t>(-9)))==-9,
            "finish speed changes only without crossing zero");
    unirally::MovementState state{};
    state.frame = 1533;
    state.countdown = 69;
    state.contact_phase = 1;
    state.progress_phase = 1;
    state.animation_counter = 13;
    state.update_counter = 205;
    state.rewards.write_cursor=1;
    state.rewards.cooldown=2;
    state.rewards.event_one_weight=4;
    for (auto& rider : state.riders) {
        rider.motion.x = 1088;
        rider.motion.y = 64;
        rider.pose.previous_x = 1088;
        rider.pose.previous_y = 64;
        rider.throttle = 432;
        rider.previous_brake = 1;
    }
    state.riders[0].residue_x = 0xffff;
    const std::array<std::uint8_t,9> masks{0xff,0x7f,0x3f,0x1f,0x0f,0x07,0x03,0x01,0x00};
    const std::array<std::uint8_t,18> decrements{
        4,0,4,0,4,0,4,0,4,0,4,0,4,0,4,0,4,0};
    std::array<std::uint8_t,33815> track{};
    std::array<std::uint8_t,32768> poses{};
    std::array<std::uint8_t,17249> templates{};
    std::array<std::uint8_t,80> transitions{};
    std::array<std::uint8_t,640> columns{};
    std::array<std::uint8_t,20> flags{};
    std::array<std::uint8_t,128> slopes{};
    std::array<std::uint8_t,512> displacement{};
    std::array<std::uint8_t,64> idle_pose{};
    std::array<std::uint8_t,2> reward{};
    std::array<std::uint8_t,1> reward_class{};
    // Authored empty geometry: coarse cells point at zero-filled sample blocks.
    displacement[28]=196;
    unirally::ControllerButtons buttons{};
    buttons.right = true;
    unirally::update_movement(state,buttons,
        {{track,poses,templates},{columns,flags},transitions,slopes,displacement,idle_pose,reward,reward_class,
         {masks,decrements}});
    require(state.frame == 1534 && state.countdown == 68, "frame/countdown");
    require(state.contact_phase == 0 && state.progress_phase == 0, "phases");
    require(state.update_counter == 206 && state.animation_counter == 14, "counters");
    require(state.player_input.low_image == 0 && state.player_input.high_image == 1, "input images");
    require(state.player_input.vertical == 1 && state.player_input.horizontal == 2, "input axes");
    require(state.riders[0].motion.x == 1102 && state.riders[0].motion.previous_x_displacement == 14, "player position/displacement");
    require(state.riders[0].motion.velocity_x == 456 && state.riders[0].residue_x == 7, "player velocity/residue");
    require(state.riders[0].throttle == 0 && state.riders[0].launch_override == 256, "player launch");
    require(state.riders[1].motion.x == 1102 && state.riders[1].residue_x == 8, "opponent position/residue");
    require(state.riders[1].motion.velocity_x == 456 && state.riders[1].launch_override == 256, "opponent launch");
    require(state.timer.subframe == 0, "timer");

    // $82:A0B7-$82:A236: at rest, a zero orientation reference selects the
    // animation-counter half-cycle. Counter 16 starts the positive recurrence.
    unirally::MovementState idle{};
    idle.frame=2000; idle.animation_counter=15; idle.countdown=0;
    idle.contact_phase=1; idle.progress_phase=1;
    idle.rewards.write_cursor=1; idle.rewards.event_one_weight=4;
    for(auto& rider:idle.riders) {
        rider.motion.y=64; rider.pose.previous_y=64;
        rider.pose.reflected=true; rider.idle_pose.orientation_reference=1;
    }
    idle_pose[0]=1;
    unirally::ControllerButtons neutral{};
    unirally::update_movement(idle,neutral,
        {{track,poses,templates},{columns,flags},transitions,slopes,displacement,idle_pose,reward,reward_class,
         {masks,decrements}});
    require(idle.riders[0].idle_pose.active==1 &&
            idle.riders[0].idle_pose.orientation_reference==0,
            "idle pose activation/reference");
    require(idle.riders[0].idle_pose.velocity==1 &&
            idle.riders[0].idle_pose.wobble_offset==1,
            "idle pose positive recurrence");

    auto zero_crossing=[&](std::uint16_t reflected_orientation,
                           std::uint16_t initial_velocity) {
        unirally::MovementState boundary{};
        boundary.frame=2000; boundary.animation_counter=5; boundary.countdown=0;
        boundary.contact_phase=1; boundary.progress_phase=1;
        boundary.rewards.write_cursor=1; boundary.rewards.event_one_weight=4;
        for(auto& rider:boundary.riders) {
            rider.motion.y=64; rider.pose.previous_y=64;
            rider.pose.reflected=true;
        }
        boundary.riders[0].pose.reflected_orientation=reflected_orientation;
        boundary.riders[0].idle_pose.velocity=initial_velocity;
        unirally::update_movement(boundary,neutral,
            {{track,poses,templates},{columns,flags},transitions,slopes,displacement,idle_pose,reward,reward_class,
             {masks,decrements}});
        return boundary.riders[0].idle_pose;
    };
    const auto negative_crossing=zero_crossing(44,1); // reference 64-44 = 20
    require(static_cast<std::int16_t>(negative_crossing.velocity)==-1 &&
            static_cast<std::int16_t>(negative_crossing.wobble_offset)==-1,
            "idle pose negative zero crossing");
    const auto positive_crossing=zero_crossing(24,0xffff); // reference 40
    require(positive_crossing.velocity==1 && positive_crossing.wobble_offset==1,
            "idle pose positive zero crossing");

    unirally::MovementState low_tail{};
    low_tail.frame=3226; low_tail.contact_phase=0; low_tail.progress_phase=0;
    low_tail.rewards.write_cursor=1; low_tail.rewards.event_one_weight=4;
    low_tail.finish.rider_finished[0]=true;
    low_tail.finish.phase=unirally::RacePhase::FinishDelay;
    low_tail.finish.outcome=unirally::RaceOutcome::PlayerWon;
    low_tail.finish.player_finish_delay=13;
    for(auto& rider:low_tail.riders) {
        rider.motion.y=64; rider.pose.previous_y=64;
        rider.pose.reflected=true;
    }
    low_tail.riders[0].motion.velocity_x=37;
    unirally::update_movement(low_tail,neutral,
        {{track,poses,templates},{columns,flags},transitions,slopes,displacement,idle_pose,reward,reward_class,
         {masks,decrements}});
    require(low_tail.riders[0].motion.velocity_x==1,
            "reviewer finish tail incoming37 reaches1");
    unirally::update_movement(low_tail,neutral,
        {{track,poses,templates},{columns,flags},transitions,slopes,displacement,idle_pose,reward,reward_class,
         {masks,decrements}});
    require(low_tail.riders[0].motion.velocity_x==0,
            "reviewer finish tail reaches0 next update");

    // Authored finish boundaries: crossing is recorded after movement, the
    // dispatcher reacts on the following update, and delay 240 transitions on
    // the update after it was displayed.
    unirally::MovementState finish_state{};
    finish_state.frame=3212; finish_state.countdown=0;
    finish_state.contact_phase=1; finish_state.progress_phase=1;
    finish_state.rewards.write_cursor=1; finish_state.rewards.event_one_weight=4;
    finish_state.timer={0,3,3,5,3};
    for(auto& rider:finish_state.riders) {
        rider.motion.y=64; rider.pose.previous_y=64; rider.pose.reflected=true;
    }
    finish_state.riders[0].motion.x=0x62ac;
    finish_state.riders[0].pose.previous_x=0x62ac;
    unirally::update_movement(finish_state,neutral,
        {{track,poses,templates},{columns,flags},transitions,slopes,displacement,idle_pose,reward,reward_class,
         {masks,decrements}});
    require(finish_state.finish.rider_finished[0] &&
            finish_state.finish.phase==unirally::RacePhase::FinishDelay &&
            finish_state.finish.player_finish_delay==0,
            "crossing/next-frame dispatcher order");
    require(finish_state.finish.finish_time_centiseconds[0]==3357 &&
            finish_state.finish.finish_time_digits[0]==std::array<std::uint16_t,5>{0,3,3,5,7},
            "stored finish time");
    unirally::update_movement(finish_state,neutral,
        {{track,poses,templates},{columns,flags},transitions,slopes,displacement,idle_pose,reward,reward_class,
         {masks,decrements}});
    require(finish_state.finish.player_finish_delay==1 &&
            finish_state.player_input.horizontal==1,
            "first finish delay/neutral override");
    finish_state.finish.player_finish_delay=240;
    const auto frozen_timer=finish_state.timer;
    unirally::update_movement(finish_state,neutral,
        {{track,poses,templates},{columns,flags},transitions,slopes,displacement,idle_pose,reward,reward_class,
         {masks,decrements}});
    require(finish_state.finish.phase==unirally::RacePhase::ResultLoading &&
            finish_state.finish.result_loading_updates==1 &&
            finish_state.timer.minutes==frozen_timer.minutes &&
            finish_state.timer.subframe==frozen_timer.subframe,
            "delay completion/result transition");
}
