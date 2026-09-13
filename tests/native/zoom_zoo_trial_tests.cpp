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

    // M4-15: malformed newly serialized future state must fail before update.
    ZoomZooState race{};race.complete_race=race.sustained=true;race.movement.frame=1649;
    for(auto& lap:race.race.riders)lap.laps_remaining=4;
    auto race_bytes=serialize_zoom_zoo(race);require(race_bytes.size()==565);
    require(serialize_zoom_zoo(deserialize_zoom_zoo(race_bytes))==race_bytes);
    for(unsigned offset:{429U,433U,451U,455U,511U,513U,553U,555U,561U,563U}) {
        auto corrupt=race_bytes;corrupt[offset]=2;
        rejects([&]{(void)deserialize_zoom_zoo(corrupt);});
    }
    for(unsigned offset:{529U,548U}) {
        auto corrupt=race_bytes;corrupt[offset]=1;
        rejects([&]{(void)deserialize_zoom_zoo(corrupt);});
    }
    for(unsigned offset:{549U,557U}) {
        auto corrupt=race_bytes;corrupt[offset]=49;corrupt[offset+2]=1;
        rejects([&]{(void)deserialize_zoom_zoo(corrupt);});
    }
    for(unsigned offset:{551U,553U,555U,559U,561U,563U}) {
        auto corrupt=race_bytes;corrupt[offset]=1;
        rejects([&]{(void)deserialize_zoom_zoo(corrupt);});
    }
    for(unsigned offset:{423U,445U}) {
        auto corrupt=race_bytes;corrupt[offset]=0;
        rejects([&]{(void)deserialize_zoom_zoo(corrupt);});
    }
    auto premature_delay=race_bytes;premature_delay[515]=1;
    rejects([&]{(void)deserialize_zoom_zoo(premature_delay);});
    for(unsigned offset:{521U,523U}) {
        auto corrupt=race_bytes;corrupt[offset]=17;
        rejects([&]{(void)deserialize_zoom_zoo(corrupt);});
    }

    // A restored descriptor must not index checkpoint flags before validation.
    race.movement.riders[0].contact.selected_word=0x03f0;
    std::array<std::uint8_t,20> checkpoint_flags{};
    ZoomZooContent checkpoint_content{};
    checkpoint_content.movement.flat_contact.flags=checkpoint_flags;
    const auto malformed_race=serialize_zoom_zoo(race);
    rejects([&]{update_zoom_zoo(race,{},checkpoint_content);});
    require(serialize_zoom_zoo(race)==malformed_race);

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
    // A first probe may establish support. A later equally deep probe wins
    // in source order and clears the leading-probe predicate.
    std::array<std::uint8_t,64> columns{};
    for(unsigned i=0;i<columns.size();i+=2)columns[i]=0xa0;
    columns[32]=4;
    std::array<std::uint8_t,2> flags{};
    CollisionPoints points{};TrackSamples samples{};
    points[0].y=5;samples[0]=2;
    auto first=summarize_vertical_contact({columns,flags},points,samples,0,0);
    require(first.supported && first.leading_support && first.penetration==2);
    points[2].y=5;samples[2]=2;
    auto later=summarize_vertical_contact({columns,flags},points,samples,0,0);
    require(later.supported && !later.leading_support && later.penetration==2);

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
    require(landing(18,1,-3)==5); // zero half-dy retains horizontal endpoint four
    require(landing(0,18,0)==0); // zero dx clamps vertical endpoint to 31
    require(landing(0,0,0)==5); // equal zero displacements use horizontal path

    // M4-14: full continuation fields must survive an independent restore.
    ZoomZooState extended{};extended.sustained=true;extended.movement.frame=2500;
    extended.surface[0].mode=1;extended.surface[0].angle=0xffe4;
    extended.surface[1].leading_support=1;extended.surface[1].animation_delta=0xfffe;
    const auto extended_bytes=serialize_zoom_zoo(extended);
    require(extended_bytes.size()==423 && deserialize_zoom_zoo(extended_bytes).surface[1].animation_delta==0xfffe);
    auto corrupt=extended_bytes;corrupt[0]='X';rejects([&]{(void)deserialize_zoom_zoo(corrupt);});
    for(unsigned rider_index=0;rider_index<2;++rider_index) {
        for(unsigned field_offset:{0U,4U,6U,8U,12U}) {
            corrupt=extended_bytes;corrupt[395+14*rider_index+field_offset]=2;
            rejects([&]{(void)deserialize_zoom_zoo(corrupt);});
        }
    }

    // Inverted vertical probes complement local Y and correct it upward in
    // source coordinates. Horizontal probes swap axes and retain direction.
    samples={};points={};samples[0]=0x8002;points[0].y=10;
    auto inverted=summarize_vertical_contact({columns,flags},points,samples,0,0);
    require(inverted.penetration==2 && inverted.inverted_vertical && inverted.leading_support);
    flags[1]=1;points[0].x=5;points[0].y=0;samples[0]=2;
    auto side=summarize_vertical_contact({columns,flags},points,samples,0,0);
    require(side.horizontal_penetration==2 && side.horizontal_direction==4 && side.penetration==0);

    // The 31-unit endpoint preserves airborne timing and uses arithmetic /4,
    // while a steep 28-unit contact can derive horizontal motion from vertical.
    std::array<std::uint8_t,32> full_shifts{},full_multipliers{};
    full_shifts[28]=1;full_multipliers[28]=1;
    rider={};rider.unsupported_count=1;motion={};motion.velocity_x=0xfff9;
    summary={};summary.supported=true;summary.any_nonnegative_probe=true;summary.angle=31;
    resolve_vertical_contact(rider,motion,summary,{0,false,0,0},full_shifts,full_multipliers);
    require(motion.velocity_x==0xfffe && rider.unsupported_count==2 && rider.unsupported_duration==1);
    rider={};motion={};motion.velocity_y=40;summary.angle=28;
    resolve_vertical_contact(rider,motion,summary,{0,false,0,0},full_shifts,full_multipliers);
    require(motion.velocity_x==10 && motion.velocity_y==40);

    // R-0033 review landing: the same steep face after nine unsupported
    // updates clears airtime and preserves incoming velocity ($81:9309).
    rider={};rider.unsupported_count=9;rider.unsupported_duration=30;
    motion={};motion.velocity_x=48;motion.velocity_y=40;
    resolve_vertical_contact(rider,motion,summary,{0,false,0,0},full_shifts,full_multipliers);
    require(motion.velocity_x==48 && motion.velocity_y==40 && rider.recontact);
    require(rider.unsupported_count==0 && rider.unsupported_duration==0);

}
