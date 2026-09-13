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
    // Review case delayed Right exposed the omitted low-speed clear. The
    // original interval is asymmetric: -16 clears, +16 increments.
    for(int speed:{-16,-1,0,15})
        require(next_wrong_direction_counter(7,static_cast<std::uint16_t>(speed),0x4000,2)==0);
    for(int speed:{-17,16})
        require(next_wrong_direction_counter(7,static_cast<std::uint16_t>(speed),0x4000,2)==8);
    require(next_wrong_direction_counter(7,100,0x4000,1)==0);
    require(next_wrong_direction_counter(7,100,0xc000,2)==0);
    require(next_wrong_direction_counter(7,100,0,0)==8);
    rejects([]{(void)next_wrong_direction_counter(179,100,0x4000,2);});
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
    // M4-13: the matrix uses the initial displacement angle; the orientation
    // impulse uses the subsequent quadrant clamp. Authored coordinates differ
    // from the captured landings, and both impulse signs are exercised.
    std::array<std::uint8_t,1512> matrices{};
    auto landing=[&](int dx,int dy,int angle) {
        RiderContactState contact{};contact.unsupported_count=9;
        contact.unsupported_duration=60;contact.previous_uncorrected_x=500;
        contact.previous_uncorrected_y=500;
        ContactMotion moved{};moved.x=static_cast<std::uint16_t>(500+dx);
        moved.y=static_cast<std::uint16_t>(500+dy);moved.previous_x_displacement=19;
        VerticalContactSummary surface{};surface.supported=true;
        surface.any_nonnegative_probe=true;surface.angle=static_cast<std::int16_t>(angle);
        resolve_vertical_contact(contact,moved,surface,{1,false,0,0xc200},shifts,multipliers,matrices);
        require(contact.recontact && contact.unsupported_count==0);
        return moved.orientation_impulse;
    };
    require(landing(18,18,-3)==5);
    require(landing(-18,-18,0)==static_cast<std::uint16_t>(-5));
    require(landing(-18,18,0)==0);

}
