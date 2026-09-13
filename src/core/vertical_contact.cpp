#include "vertical_contact.hpp"

#include <algorithm>
#include <array>
#include <stdexcept>

namespace unirally {
namespace {
void require(bool condition, const char* message) {
    if (!condition) throw std::invalid_argument(message);
}
std::uint8_t byte(std::span<const std::uint8_t> data, unsigned offset) {
    if (offset >= data.size()) throw std::out_of_range("vertical contact content is incomplete");
    return data[offset];
}
unsigned tile(std::uint16_t word) {
    return ((word & 0x03f0U) >> 2U) + ((word & 15U) >> 1U);
}
bool nonnegative_difference(std::uint8_t left, std::uint8_t right) {
    return ((static_cast<unsigned>(left) - right) & 0x80U) == 0;
}
int signed_word(std::uint16_t value) {
    return value < 0x8000U ? static_cast<int>(value) : static_cast<int>(value) - 65536;
}
std::uint16_t arithmetic_shift(std::uint16_t value, unsigned count) {
    require(count < 16, "vertical slope shift exceeds word width");
    auto result = value;
    for (unsigned i=0; i<count; ++i) {
        result = static_cast<std::uint16_t>((result >> 1U) | (result & 0x8000U));
    }
    return result;
}
struct Probe { std::uint8_t penetration{0xa0}, angle{}; std::uint16_t descriptor{}; };
Probe preprocess(const FlatContactContent& content, SamplePoint point,
                 std::uint16_t descriptor, std::uint16_t x, std::uint16_t y) {
    if ((descriptor & 0x03ffU) == 0) {
        if((descriptor&0x1c00U)==0x1c00U)return {0x7f,0,descriptor};
        return {};
    }
    require((descriptor & 0x8001U) == 0, "vertical contact reaches inverted/special geometry");
    const auto index=tile(descriptor);
    require((byte(content.flags,index)&1U)==0, "vertical contact reaches horizontal geometry");
    auto column=(static_cast<unsigned>(point.x)+(x&15U))&15U;
    const auto local_y=(static_cast<unsigned>(point.y)+(y&15U))&15U;
    const bool mirrored=(descriptor&0x4000U)!=0;
    if (mirrored) column=(~column)&15U;
    const auto height=byte(content.columns,index*32U+column*2U);
    auto angle=byte(content.columns,index*32U+column*2U+1U);
    if (mirrored) angle=static_cast<std::uint8_t>(0U-angle);
    const auto penetration=height==0xa0U ? std::uint8_t{0xa0} :
        static_cast<std::uint8_t>(local_y-static_cast<std::uint8_t>(height-1U));
    return {penetration,angle,descriptor};
}
} // namespace

VerticalContactSummary summarize_vertical_contact(const FlatContactContent& content,
                                              const CollisionPoints& points,
                                              const TrackSamples& samples,
                                              std::uint16_t x,std::uint16_t y) {
    std::array<Probe,10> probes{};
    for (std::size_t i=0;i<probes.size();++i) probes[i]=preprocess(content,points[i],samples[i],x,y);
    require(probes[0].penetration>=0x80U,"vertical contact reaches nonnegative first-probe support");
    VerticalContactSummary result{};
    std::uint8_t support=probes[0].penetration==0xa0U ? 0xff : probes[0].penetration, angle=0xe0;
    for (std::size_t i=1;i<probes.size();++i) {
        const auto& probe=probes[i];
        if (probe.penetration==0xa0U) {
            if ((probe.descriptor&0x01ffU)!=0 && result.selected_word==0) result.selected_word=probe.descriptor;
            continue;
        }
        if (nonnegative_difference(probe.penetration,support)) {
            support=probe.penetration;
            if ((probe.descriptor&1U)!=0 || result.selected_word==0) result.selected_word=probe.descriptor;
            if (nonnegative_difference(probe.angle,angle)) result.selected_high=static_cast<std::uint8_t>(probe.descriptor>>8U);
            angle=probe.angle;
        }
        if(probe.penetration<0x80U)result.any_nonnegative_probe=true;
        if (probe.penetration<0x80U && nonnegative_difference(probe.penetration,result.penetration)) {
            result.penetration=probe.penetration;
            result.angle=static_cast<std::int16_t>(probe.angle<128 ? static_cast<int>(probe.angle) : static_cast<int>(probe.angle)-256);
        }
    }
    result.supported=support<0x80U;
    result.angle=static_cast<std::int16_t>(angle<128 ? static_cast<int>(angle) : static_cast<int>(angle)-256);
    result.boundary_marker=result.penetration==127;
    result.tile_flags=byte(content.flags,tile(result.selected_word));
    return result;
}

void resolve_vertical_contact(RiderContactState& rider,ContactMotion& motion,
                              const VerticalContactSummary& summary,const ContactContext& context,
                              std::span<const std::uint8_t> shifts,
                              std::span<const std::uint8_t> multipliers,
                              std::span<const std::uint8_t> landing_matrices,unsigned horizontal) {
    require(context.phase<=1 && context.mode==0,"unsupported vertical contact phase/mode");
    require(rider.unsupported_count<=9 && summary.penetration<128,"unsupported vertical contact state");
    require((summary.selected_high&0x80U)==0,"unsupported vertical response direction");
    auto next=rider; auto moved=motion;
    next.previous_unsupported_count=rider.unsupported_count;
    next.selected_word=summary.selected_word;
    next.selected_high=summary.selected_high;
    next.recontact=false;
    next.angle_unspecified=true;
    if(!summary.any_nonnegative_probe)next.auxiliary_flag=0;
    if(summary.boundary_marker)next.auxiliary_flag=1;
    if(next.auxiliary_flag==1) {
        next.unsupported_duration=static_cast<std::uint16_t>((rider.unsupported_duration&0xff00U)|static_cast<std::uint8_t>(rider.unsupported_duration+1U));
        next.unsupported_count=std::min<std::uint16_t>(9,static_cast<std::uint16_t>(rider.unsupported_count+1U));
        rider=next;return;
    }
    if (!summary.supported) {
        next.unsupported_count=std::min<std::uint16_t>(9,static_cast<std::uint16_t>(rider.unsupported_count+1U));
        next.unsupported_duration=static_cast<std::uint16_t>(rider.unsupported_duration+1U);
        next.angle_unspecified=true;
        next.auxiliary_flag=0;
    } else {
        const auto magnitude=static_cast<unsigned>(std::abs(static_cast<int>(summary.angle)));
        require(magnitude<=8,"vertical response angle outside recovered coefficients");
        require(summary.tile_flags==0 || summary.tile_flags==2 || summary.tile_flags==18 || summary.tile_flags==20,
                "vertical contact reaches a special response tile");
        next.surface_angle=static_cast<std::uint16_t>(summary.angle);
        next.angle_unspecified=magnitude==31;
        next.unsupported_count=0; next.unsupported_duration=0;
        if (rider.unsupported_count>=9) {
            // R-0025: signed displacement quadrant and coarse-angle sentinel.
            const auto dx=std::abs(signed_word(static_cast<std::uint16_t>(motion.x-rider.previous_uncorrected_x)));
            const auto half_dy=std::abs(signed_word(static_cast<std::uint16_t>(motion.y-rider.previous_uncorrected_y)))/2;
            require(half_dy!=0 && dx!=0,"unrecovered zero-divisor landing angle");
            const int magnitude_angle=dx>=half_dy ? std::max(4,16-4*(dx/half_dy)) :
                std::min(31,16+4*(half_dy/dx));
            const int coarse=signed_word(static_cast<std::uint16_t>(motion.x-rider.previous_uncorrected_x))<0 ? -magnitude_angle : magnitude_angle;
            require(context.opponent && (context.cartridge_options&8U)==0,
                    "unrecovered player/options landing response");
            next.recontact=true;
            // The scoped landings have no incoming orientation response;
            // motion either survives the sentinel or uses a static matrix.
            require(motion.response_a==0 && motion.response_b==0 && motion.orientation_impulse==0,
                    "unrecovered nonzero landing orientation response");
            const auto angle_difference=std::abs(coarse-static_cast<int>(summary.angle));
            if(angle_difference>5) {
                require(landing_matrices.size()==1512,"landing coefficient matrices are missing");
                unsigned matrix=angle_difference<=10?1U:2U;
                int angle=summary.angle;
                const auto velocity=signed_word(motion.velocity_x);
                if((velocity>0 && horizontal==0) || (velocity<0 && horizontal==2)) {
                    angle=std::clamp(angle+(velocity>0?-5:5),-31,31);matrix=2;
                }
                const auto angle_index=static_cast<unsigned>(angle<0?31-angle:angle);
                const auto offset=matrix*504U+angle_index*8U;
                auto multiply=[&](std::uint16_t value,unsigned coefficient) {
                    const auto low=byte(landing_matrices,offset+coefficient*2U);
                    const auto high=byte(landing_matrices,offset+coefficient*2U+1U);
                    const auto raw=high?high:low;
                    const auto signed_coefficient=raw<128?static_cast<int>(raw):static_cast<int>(raw)-256;
                    const int product=signed_word(value)*signed_coefficient;
                    if(high)return static_cast<std::uint16_t>(product);
                    // $0566 is the middle/high product word. ASL follows
                    // selection, so negative products round down before doubling.
                    const int upper=product>=0?product/256:-((-product+255)/256);
                    return static_cast<std::uint16_t>(upper*2);
                };
                moved.velocity_y=static_cast<std::uint16_t>(multiply(motion.velocity_y,0)+multiply(motion.velocity_x,1));
                moved.velocity_x=static_cast<std::uint16_t>(multiply(motion.velocity_y,2)+multiply(motion.velocity_x,3));
            }
        } else {
            if (context.phase==0) {moved.response_a=0; moved.response_b=0;}
            const auto shifted=arithmetic_shift(motion.velocity_x,byte(shifts,magnitude));
            const auto product=static_cast<std::uint16_t>(static_cast<unsigned>(shifted)*byte(multipliers,magnitude));
            moved.velocity_y=summary.angle<0 ? static_cast<std::uint16_t>(1U-product) : product;
            const int contribution=summary.angle<0 ? -static_cast<int>(magnitude/2U) : static_cast<int>(magnitude/2U);
            moved.velocity_x=static_cast<std::uint16_t>(static_cast<int>(motion.velocity_x)+contribution);
        }
    }
    next.previous_uncorrected_x=motion.x; next.previous_uncorrected_y=motion.y;
    moved.y=static_cast<std::uint16_t>(motion.y-summary.penetration);
    rider=next; motion=moved;
}
} // namespace unirally
