#include "movement.hpp"

#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>

static void require(bool value,const char* message) {
    if(!value)throw std::runtime_error(message);
}

static std::uint64_t extend_hash(std::uint64_t hash,
                                 const std::vector<std::uint8_t>& bytes) {
    for(const auto byte:bytes) {
        hash^=byte;
        hash*=1099511628211ULL;
    }
    return hash;
}

int main() {
    unirally::MovementState initial{};
    initial.frame=1533;initial.countdown=69;
    initial.contact_phase=1;initial.progress_phase=1;
    initial.animation_counter=13;initial.update_counter=205;
    initial.rewards.write_cursor=1;initial.rewards.cooldown=2;
    initial.rewards.event_one_weight=4;
    for(auto& rider:initial.riders) {
        rider.motion.x=1088;rider.motion.y=64;
        rider.pose.previous_x=1088;rider.pose.previous_y=64;
        rider.throttle=432;rider.previous_brake=1;
        rider.pose.reflected=true;
    }
    initial.riders[0].residue_x=0xffff;

    const std::array<std::uint8_t,9> masks{0xff,0x7f,0x3f,0x1f,0x0f,0x07,0x03,0x01,0x00};
    const std::array<std::uint8_t,18> decrements{
        4,0,4,0,4,0,4,0,4,0,4,0,4,0,4,0,4,0};
    std::vector<std::uint8_t> track(33815),poses(32768),templates(17249);
    std::vector<std::uint8_t> transitions(80),columns(640),flags(20),slopes(128);
    std::vector<std::uint8_t> displacement(512),idle_pose(64),reward(2),reward_class(1);
    displacement[28]=196;
    const unirally::MovementContent content{{track,poses,templates},{columns,flags},
        transitions,slopes,displacement,idle_pose,reward,reward_class,{masks,decrements}};

    std::vector<unirally::ControllerButtons> inputs(32);
    for(std::size_t index=0;index<inputs.size();++index) {
        inputs[index].right=index<12 || (index>=20 && index<27);
    }
    std::vector<std::vector<std::uint8_t>> uninterrupted;
    uninterrupted.push_back(unirally::serialize_movement_state(initial));
    auto baseline=initial;
    for(const auto input:inputs) {
        unirally::update_movement(baseline,input,content);
        uninterrupted.push_back(unirally::serialize_movement_state(baseline));
    }
    std::uint64_t hash=14695981039346656037ULL;
    for(const auto& state:uninterrupted)hash=extend_hash(hash,state);
    require(hash==0x7c799b4393d171f2ULL,"portable canonical series hash");
    std::cout<<std::hex<<hash<<'\n';

    for(const std::size_t boundary:{1U,13U,25U}) {
        auto prefix=initial;
        for(std::size_t index=0;index<boundary;++index) {
            unirally::update_movement(prefix,inputs[index],content);
        }
        const auto saved=unirally::serialize_movement_state(prefix);
        require(saved.size()==333,"saved movement state width");
        require(saved==uninterrupted[boundary],"prefix state differs");
        auto restored=unirally::deserialize_movement_state(saved);
        require(unirally::serialize_movement_state(restored)==saved,"restore round trip differs");
        for(std::size_t index=boundary;index<inputs.size();++index) {
            unirally::update_movement(restored,inputs[index],content);
            require(unirally::serialize_movement_state(restored)==uninterrupted[index+1],
                    "restored continuation differs");
        }
    }
}
