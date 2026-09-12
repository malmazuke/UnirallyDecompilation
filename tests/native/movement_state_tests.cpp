#include "movement.hpp"
#include <fstream>
#include <iterator>
#include <stdexcept>

static void require(bool value) { if(!value) throw std::runtime_error("movement state expectation failed"); }

int main(int argc, char** argv) {
    unirally::MovementState state{};
    state.frame=1533; state.player_input={0,1,1,2}; state.contact_phase=1; state.progress_phase=1;
    state.animation_counter=31; state.update_counter=205; state.countdown=69;
    state.riders[0].motion.x=1088; state.riders[0].throttle=432;
    state.riders[1].motion.velocity_y=0xff80; state.riders[1].contact.recontact=true;
    state.riders[0].pose.displacement_history={1,2,3}; state.riders[0].pose.reflected=true;
    state.rewards.write_cursor=1;
    state.rewards.cooldown=2; state.rewards.event_one_weight=4;
    state.riders[0].idle_pose.wobble_offset=0xffb0;
    state.riders[1].idle_pose.orientation_reference=60;
    const auto encoded=unirally::serialize_movement_state(state);
    require(encoded.size()==333); require(encoded[0]=='U' && encoded[7]=='1');
    require(unirally::serialize_movement_state(unirally::deserialize_movement_state(encoded))==encoded);
    auto rejects=[](const std::vector<std::uint8_t>& bytes) {
        try { (void)unirally::deserialize_movement_state(bytes); }
        catch(const std::invalid_argument&) { return true; }
        return false;
    };
    auto invalid=encoded; invalid[0]='X'; require(rejects(invalid));
    invalid=encoded; invalid.pop_back(); require(rejects(invalid));
    invalid=encoded; invalid[14]=3; require(rejects(invalid));
    invalid=encoded; invalid[320]=32; require(rejects(invalid));
    invalid=encoded; invalid[321]=32; require(rejects(invalid));
    invalid=encoded; invalid[329]=2; require(rejects(invalid));
    invalid=encoded; invalid[330]=2; require(rejects(invalid));
    invalid=encoded; invalid[331]=32; require(rejects(invalid));
    auto malformed=encoded; malformed[100]=2; // first rider rolling flag
    bool rejected=false; try { (void)unirally::deserialize_movement_state(malformed); } catch(const std::invalid_argument&) { rejected=true; }
    require(rejected);
    malformed=encoded; malformed[102]=2; malformed[103]=0; rejected=false;
    try { (void)unirally::deserialize_movement_state(malformed); } catch(const std::invalid_argument&) { rejected=true; }
    require(rejected);
    malformed=encoded; malformed.push_back(0); rejected=false;
    try { (void)unirally::deserialize_movement_state(malformed); } catch(const std::invalid_argument&) { rejected=true; }
    require(rejected);
    state.finish.rider_finished={true,true};
    state.finish.finish_time_centiseconds={3357,3358};
    state.finish.finish_time_digits={{{0,3,3,5,7},{0,3,3,5,8}}};
    state.finish.finish_animation_countdown={119,120};
    state.finish.player_finish_delay=1;
    state.finish.phase=unirally::RacePhase::FinishDelay;
    state.finish.outcome=unirally::RaceOutcome::PlayerLost;
    const auto finish_encoded=unirally::serialize_movement_state(state);
    require(finish_encoded.size()==369);
    require(finish_encoded[0]=='U' && finish_encoded[7]=='2');
    require(unirally::serialize_movement_state(
            unirally::deserialize_movement_state(finish_encoded))==finish_encoded);
    invalid=finish_encoded; invalid[367]=4; require(rejects(invalid));
    invalid=finish_encoded; invalid[368]=3; require(rejects(invalid));
    invalid=finish_encoded; invalid[363]=241; invalid[364]=0; require(rejects(invalid));
    state.finish.opponent_finish_pose_selector=17;
    const auto pose_encoded=unirally::serialize_movement_state(state);
    require(pose_encoded.size()==371);
    require(pose_encoded[0]=='U' && pose_encoded[7]=='3');
    require(unirally::serialize_movement_state(
            unirally::deserialize_movement_state(pose_encoded))==pose_encoded);
    invalid=pose_encoded; invalid[369]=49; invalid[370]=0; require(rejects(invalid));
    const auto playable=unirally::classic_crawler_dragster_start();
    require(playable.frame==1533 && playable.player_input.high_image==1 &&
            playable.player_input.vertical==1 && playable.player_input.horizontal==2);
    require(playable.riders[0].motion.x==1088 && playable.riders[0].motion.y==858 &&
            playable.riders[0].throttle==432 && playable.riders[0].residue_x==0xffff);
    require(playable.riders[1].idle_pose.orientation_reference==60 &&
            playable.countdown==69 && playable.update_counter==205);
    const auto playable_bytes=unirally::serialize_movement_state(playable);
    require(playable_bytes.size()==333 &&
            unirally::serialize_movement_state(unirally::deserialize_movement_state(playable_bytes))==playable_bytes);
    if(argc==2) {
        std::ifstream input(argv[1],std::ios::binary);
        require(input.good());
        const std::vector<std::uint8_t> seed{
            std::istreambuf_iterator<char>(input),std::istreambuf_iterator<char>()};
        const auto imported=unirally::deserialize_movement_state(seed);
        require(imported.frame==1533);
        require(imported.riders[0].motion.x==1088);
        require(imported.riders[0].throttle==432);
        require(imported.riders[0].pose.displacement_history==
                std::array<std::uint16_t,3>{0,0,0});
        require(imported.riders[1].pose.displacement_history==
                std::array<std::uint16_t,3>{0,0,0});
        require(imported.riders[0].idle_pose.wobble_offset==0);
        require(imported.riders[0].pose.reflected && imported.riders[1].pose.reflected);
        require(unirally::serialize_movement_state(imported)==seed);
        require(playable_bytes==seed);
    }
}
