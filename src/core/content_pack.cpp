#include "content_pack.hpp"

#include <algorithm>
#include <array>
#include <fstream>
#include <iterator>
#include <limits>
#include <stdexcept>

namespace unirally {
namespace {
class Reader {
public:
    explicit Reader(std::span<const std::uint8_t> bytes):bytes_(bytes){}
    std::uint16_t u16(){require(2);const auto v=static_cast<std::uint16_t>(bytes_[at_]|(static_cast<unsigned>(bytes_[at_+1])<<8U));at_+=2;return v;}
    std::uint32_t u32(){const auto lo=u16();return static_cast<std::uint32_t>(lo)|(static_cast<std::uint32_t>(u16())<<16U);}
    std::uint64_t u64(){const auto lo=u32();return static_cast<std::uint64_t>(lo)|(static_cast<std::uint64_t>(u32())<<32U);}
    std::array<std::uint8_t,32> digest(){std::array<std::uint8_t,32> value{};for(auto& byte:value){byte=u8();}return value;}
    std::uint8_t u8(){require(1);return bytes_[at_++];}
    std::string text(){const auto width=u16();require(width);std::string value(bytes_.begin()+static_cast<std::ptrdiff_t>(at_),bytes_.begin()+static_cast<std::ptrdiff_t>(at_+width));at_+=width;if(value.empty())throw std::invalid_argument("Classic pack contains an empty identity");return value;}
    void skip(std::size_t width){require(width);at_+=width;}
    std::size_t offset()const{return at_;}
private:
    void require(std::size_t width)const{if(width>bytes_.size()-at_)throw std::invalid_argument("Classic pack is truncated");}
    std::span<const std::uint8_t> bytes_;std::size_t at_{};
};

struct RequiredEntry {std::string_view id;std::size_t size;std::string_view sha256;};
const std::array<RequiredEntry,13> required{{
    {"physics.track.dragster.data",33815,"8f5cef67dc57977af8ff614b8178514a26e9fe0059e02ed27aad5978185580d4"},
    {"physics.rider.collision-poses",32768,"9d1754d38c20cb2900239557550211ab6fc23d9b0237e17b78fb29f3bf272c32"},
    {"physics.rider.collision-templates",17249,"2f03a8cb985899436603ef36b233b28f7b4213e4ba106fca328a6b02cdb081c7"},
    {"physics.track.progress-transitions",80,"8a90513f349bc7836513d3495a9bbb90563b9eb7a716fd4aff5b9a4c74fc83df"},
    {"physics.track.dragster.tile-columns",640,"bb95427aa2a307c9874b6140b145dce5a4e279112d57a5efcae77eb444951a72"},
    {"physics.track.dragster.tile-flags",20,"590e52f2640bb1b70f602622aa07285ed51d7c4b84707b4d77c5cc33fc230846"},
    {"physics.speed.masks",9,"0ca19a78da56137e0926c4ba602d8041648a422b9cf5d0a7c3de4a30998cf58b"},
    {"physics.speed.decrements",18,"c1fab1d9aa1e691d34c1a78e8658cfd52b8334cc5bdec8efb23bedc672988068"},
    {"physics.rider.pose-slopes",128,"f6b1ea6a34c78336ca25449c8ddbd23e2417ef829ec09765e695f957cd714584"},
    {"physics.rider.displacement-table",512,"27894923de2aaeb58ca24dedbddadcf0d4d154fbc61ea484e7c248d066e24e1b"},
    {"physics.rider.idle-pose-table",64,"05d2af9f8c0d1d8d8dd1915086f4f4c58456510f3daf357dbd7fdd66e4a8031e"},
    {"physics.reward.rotation-value",2,"8509b81230019d2ad970d970f791dfbdc8caf54f5c594fcd327cef9feed206c1"},
    {"physics.reward.rotation-class",1,"6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d"}}};

std::array<std::uint8_t,32> hex_digest(std::string_view text) {
    if(text.size()!=64)throw std::logic_error("invalid compiled Classic SHA-256");
    const auto nibble=[](char value)->std::uint8_t{
        if(value>='0'&&value<='9')return static_cast<std::uint8_t>(value-'0');
        if(value>='a'&&value<='f')return static_cast<std::uint8_t>(value-'a'+10);
        throw std::logic_error("invalid compiled Classic SHA-256 digit");
    };
    std::array<std::uint8_t,32> out{};
    for(std::size_t i=0;i<out.size();++i)out[i]=static_cast<std::uint8_t>((nibble(text[i*2])<<4U)|nibble(text[i*2+1]));
    return out;
}

std::array<std::uint8_t,32> sha256(std::span<const std::uint8_t> source) {
    constexpr std::array<std::uint32_t,64> constants{{
        0x428a2f98U,0x71374491U,0xb5c0fbcfU,0xe9b5dba5U,0x3956c25bU,0x59f111f1U,0x923f82a4U,0xab1c5ed5U,
        0xd807aa98U,0x12835b01U,0x243185beU,0x550c7dc3U,0x72be5d74U,0x80deb1feU,0x9bdc06a7U,0xc19bf174U,
        0xe49b69c1U,0xefbe4786U,0x0fc19dc6U,0x240ca1ccU,0x2de92c6fU,0x4a7484aaU,0x5cb0a9dcU,0x76f988daU,
        0x983e5152U,0xa831c66dU,0xb00327c8U,0xbf597fc7U,0xc6e00bf3U,0xd5a79147U,0x06ca6351U,0x14292967U,
        0x27b70a85U,0x2e1b2138U,0x4d2c6dfcU,0x53380d13U,0x650a7354U,0x766a0abbU,0x81c2c92eU,0x92722c85U,
        0xa2bfe8a1U,0xa81a664bU,0xc24b8b70U,0xc76c51a3U,0xd192e819U,0xd6990624U,0xf40e3585U,0x106aa070U,
        0x19a4c116U,0x1e376c08U,0x2748774cU,0x34b0bcb5U,0x391c0cb3U,0x4ed8aa4aU,0x5b9cca4fU,0x682e6ff3U,
        0x748f82eeU,0x78a5636fU,0x84c87814U,0x8cc70208U,0x90befffaU,0xa4506cebU,0xbef9a3f7U,0xc67178f2U}};
    auto rotate=[](std::uint32_t value,unsigned bits){return (value>>bits)|(value<<(32U-bits));};
    std::vector<std::uint8_t> message(source.begin(),source.end());
    const auto bit_length=static_cast<std::uint64_t>(message.size())*8U;
    message.push_back(0x80);
    while(message.size()%64U!=56U)message.push_back(0);
    for(int shift=56;shift>=0;shift-=8)message.push_back(static_cast<std::uint8_t>(bit_length>>static_cast<unsigned>(shift)));
    std::array<std::uint32_t,8> hash{{0x6a09e667U,0xbb67ae85U,0x3c6ef372U,0xa54ff53aU,0x510e527fU,0x9b05688cU,0x1f83d9abU,0x5be0cd19U}};
    for(std::size_t base=0;base<message.size();base+=64){
        std::array<std::uint32_t,64> words{};
        for(std::size_t i=0;i<16;++i){const auto at=base+i*4;words[i]=(static_cast<std::uint32_t>(message[at])<<24U)|(static_cast<std::uint32_t>(message[at+1])<<16U)|(static_cast<std::uint32_t>(message[at+2])<<8U)|message[at+3];}
        for(std::size_t i=16;i<64;++i){const auto s0=rotate(words[i-15],7)^rotate(words[i-15],18)^(words[i-15]>>3U);const auto s1=rotate(words[i-2],17)^rotate(words[i-2],19)^(words[i-2]>>10U);words[i]=words[i-16]+s0+words[i-7]+s1;}
        auto a=hash[0],b=hash[1],c=hash[2],d=hash[3],e=hash[4],f=hash[5],g=hash[6],h=hash[7];
        for(std::size_t i=0;i<64;++i){const auto s1=rotate(e,6)^rotate(e,11)^rotate(e,25);const auto choice=(e&f)^((~e)&g);const auto t1=h+s1+choice+constants[i]+words[i];const auto s0=rotate(a,2)^rotate(a,13)^rotate(a,22);const auto majority=(a&b)^(a&c)^(b&c);const auto t2=s0+majority;h=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;}
        hash[0]+=a;hash[1]+=b;hash[2]+=c;hash[3]+=d;hash[4]+=e;hash[5]+=f;hash[6]+=g;hash[7]+=h;
    }
    std::array<std::uint8_t,32> out{};
    for(std::size_t i=0;i<hash.size();++i)for(unsigned byte=0;byte<4;++byte)out[i*4+byte]=static_cast<std::uint8_t>(hash[i]>>(24U-byte*8U));
    return out;
}
}

ClassicContentPack::ClassicContentPack(const std::filesystem::path& path) {
    std::ifstream input(path,std::ios::binary);
    if(!input)throw std::runtime_error("cannot open Classic content pack: "+path.string());
    bytes_={std::istreambuf_iterator<char>(input),std::istreambuf_iterator<char>()};
    if(bytes_.size()<12 || std::string(bytes_.begin(),bytes_.begin()+8)!="URCP0001")throw std::invalid_argument("Classic pack magic is unsupported");
    Reader in(bytes_);in.skip(8);
    if(in.u32()!=1)throw std::invalid_argument("Classic pack schema is unsupported");
    const auto source_identity=in.digest();
    const auto rules_identity=in.digest();
    if(source_identity!=hex_digest("a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e"))throw std::invalid_argument("Classic pack source ROM identity is unsupported");
    if(rules_identity!=hex_digest("f500d016726495c435be81c6d3e05b9fa64b38edb8e322788c37927e1022a620"))throw std::invalid_argument("Classic pack extraction-rules identity is unsupported");
    if(in.text()!="classic.pal.crawler.dragster.v1")throw std::invalid_argument("Classic pack profile is unsupported");
    if(in.text()!="classic.crawler.dragster.race-start.v1")throw std::invalid_argument("Classic pack start state is unsupported");
    const auto count=in.u16();
    struct Row {std::string id;std::uint64_t offset,size;std::array<std::uint8_t,32> digest;};
    std::vector<Row> rows;rows.reserve(count);
    for(unsigned index=0;index<count;++index){
        auto id=in.text();const auto offset=in.u64();const auto size=in.u64();
        const auto digest=in.digest();
        if(entries_.contains(id))throw std::invalid_argument("Classic pack contains a duplicate logical ID");
        entries_.emplace(id,Entry{});rows.push_back({std::move(id),offset,size,digest});
    }
    std::uint64_t cursor=in.offset();
    if(entries_.size()!=required.size())throw std::invalid_argument("Classic pack inventory is incomplete");
    for(const auto& expected:required){
        const auto found=entries_.find(std::string(expected.id));
        if(found==entries_.end())throw std::invalid_argument("Classic pack required logical entry is missing");
        const auto row=std::find_if(rows.begin(),rows.end(),[&](const Row& value){return value.id==expected.id;});
        if(row==rows.end()||row->size!=expected.size||row->digest!=hex_digest(expected.sha256))throw std::invalid_argument("Classic pack required entry identity is unsupported: "+std::string(expected.id));
    }
    for(const auto& row:rows){
        if(row.offset!=cursor || row.size>std::numeric_limits<std::size_t>::max() || row.offset>bytes_.size() || row.size>bytes_.size()-static_cast<std::size_t>(row.offset))throw std::invalid_argument("Classic pack payload layout is invalid");
        const auto payload=std::span<const std::uint8_t>(bytes_).subspan(static_cast<std::size_t>(row.offset),static_cast<std::size_t>(row.size));
        if(sha256(payload)!=row.digest)throw std::invalid_argument("Classic pack entry payload hash differs: "+row.id);
        entries_.at(row.id)={static_cast<std::size_t>(row.offset),static_cast<std::size_t>(row.size)};cursor+=row.size;
    }
    if(cursor!=bytes_.size())throw std::invalid_argument("Classic pack has trailing data");
}

std::span<const std::uint8_t> ClassicContentPack::entry(const std::string& logical_id) const {
    const auto found=entries_.find(logical_id);
    if(found==entries_.end())throw std::invalid_argument("Classic pack logical entry is absent: "+logical_id);
    return std::span<const std::uint8_t>(bytes_).subspan(found->second.offset,found->second.size);
}
} // namespace unirally
