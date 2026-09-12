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
    state.riders[0].pose.displacement_history={1,2,3}; state.rewards.write_cursor=1;
    state.rewards.cooldown=2; state.rewards.event_one_weight=4;
    const auto encoded=unirally::serialize_movement_state(state);
    require(encoded.size()==295); require(encoded[0]=='U' && encoded[7]=='1');
    require(unirally::serialize_movement_state(unirally::deserialize_movement_state(encoded))==encoded);
    auto malformed=encoded; malformed[100]=2; // first rider rolling flag
    bool rejected=false; try { (void)unirally::deserialize_movement_state(malformed); } catch(const std::invalid_argument&) { rejected=true; }
    require(rejected);
    malformed=encoded; malformed.push_back(0); rejected=false;
    try { (void)unirally::deserialize_movement_state(malformed); } catch(const std::invalid_argument&) { rejected=true; }
    require(rejected);
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
        require(unirally::serialize_movement_state(imported)==seed);
    }
}
