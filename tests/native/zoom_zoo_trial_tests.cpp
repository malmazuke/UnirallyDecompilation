#include "zoom_zoo_movement.hpp"
#include "vertical_contact.hpp"
#include <array>
#include <stdexcept>

static void require(bool value) {if(!value)throw std::runtime_error("ZOOM ZOO trial expectation failed");}
template<class F> static void rejects(F action) {
    bool rejected=false;try{action();}catch(const std::invalid_argument&){rejected=true;}require(rejected);
}
int main() {
    using namespace unirally;
    ZoomZooState state{};state.movement.frame=1649;state.opponent_retained_oam_x=101;
    state.reflection[1].step=4;state.reflection[1].end=9;state.reflection[1].air_turns=3;
    auto encoded=serialize_zoom_zoo(state);require(encoded.size()==395);
    require(serialize_zoom_zoo(deserialize_zoom_zoo(encoded))==encoded);
    auto invalid=encoded;invalid.pop_back();rejects([&]{(void)deserialize_zoom_zoo(invalid);});
    invalid=encoded;invalid[393]=3;rejects([&]{(void)deserialize_zoom_zoo(invalid);});
    invalid=encoded;invalid[363]=17;rejects([&]{(void)deserialize_zoom_zoo(invalid);});
    ControllerButtons input{};input.left=true;
    rejects([&]{update_zoom_zoo(state,input,{});});require(serialize_zoom_zoo(state)==encoded);
    input={};state.movement.frame=1849;
    rejects([&]{update_zoom_zoo(state,input,{});});

    // Auxiliary boundary return increments only the low byte and preserves the
    // precorrection position. Ordinary unsupported contact increments a word.
    RiderContactState rider{};rider.unsupported_count=8;rider.unsupported_duration=0x12ff;
    rider.previous_uncorrected_x=123;rider.previous_uncorrected_y=456;
    ContactMotion motion{};motion.x=900;motion.y=800;motion.velocity_x=0xff80;
    VerticalContactSummary summary{};summary.boundary_marker=true;summary.any_nonnegative_probe=true;summary.penetration=127;
    resolve_vertical_contact(rider,motion,summary,{0,true,0,0xc200},{},{});
    require(rider.unsupported_duration==0x1200 && rider.unsupported_count==9);
    require(rider.previous_uncorrected_x==123 && motion.y==800 && motion.velocity_x==0xff80);
    summary={};resolve_vertical_contact(rider,motion,summary,{0,true,0,0xc200},{},{});
    require(rider.unsupported_duration==0x1201 && rider.auxiliary_flag==0 && rider.previous_uncorrected_x==900);

    // A negative arithmetic shift rounds toward minus infinity before the
    // wrapped unsigned multiply and negative-slope +1 correction.
    std::array<std::uint8_t,9> shifts{},multipliers{};shifts[4]=2;multipliers[4]=3;
    rider={};motion={};motion.velocity_x=0xfff9;summary={};summary.supported=true;
    summary.any_nonnegative_probe=true;summary.angle=-4;summary.penetration=3;
    resolve_vertical_contact(rider,motion,summary,{0,true,0,0xc200},shifts,multipliers);
    require(motion.velocity_y==7 && motion.velocity_x==0xfff7 && motion.y==0xfffd);
    const auto previous_y=motion.y;summary.angle=9;
    rejects([&]{resolve_vertical_contact(rider,motion,summary,{0,true,0,0xc200},shifts,multipliers);});
    require(motion.y==previous_y);
}
