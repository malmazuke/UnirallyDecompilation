#include "content_pack.hpp"

#include <array>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
struct Entry {std::string_view id;std::uint64_t size;std::string_view digest;};
constexpr std::array<Entry,13> entries{{
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

void put16(std::vector<std::uint8_t>& out,std::uint16_t value){out.push_back(static_cast<std::uint8_t>(value));out.push_back(static_cast<std::uint8_t>(value>>8U));}
void put64(std::vector<std::uint8_t>& out,std::uint64_t value){for(unsigned i=0;i<8;++i)out.push_back(static_cast<std::uint8_t>(value>>(i*8U)));}
std::uint8_t nibble(char value){return static_cast<std::uint8_t>(value<='9'?value-'0':value-'a'+10);}
void put_digest(std::vector<std::uint8_t>& out,std::string_view text){for(std::size_t i=0;i<32;++i)out.push_back(static_cast<std::uint8_t>((nibble(text[i*2])<<4U)|nibble(text[i*2+1])));}
void put_text(std::vector<std::uint8_t>& out,std::string_view text){put16(out,static_cast<std::uint16_t>(text.size()));out.insert(out.end(),text.begin(),text.end());}

std::pair<std::vector<std::uint8_t>,std::size_t> authored_pack() {
    std::vector<std::uint8_t> out{'U','R','C','P','0','0','0','1',1,0,0,0};
    put_digest(out,"a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e");
    put_digest(out,"f500d016726495c435be81c6d3e05b9fa64b38edb8e322788c37927e1022a620");
    put_text(out,"classic.pal.crawler.dragster.v1");put_text(out,"classic.crawler.dragster.race-start.v1");put16(out,13);
    std::size_t table_bytes{};for(const auto& entry:entries)table_bytes+=2+entry.id.size()+48;
    std::uint64_t cursor=static_cast<std::uint64_t>(out.size()+table_bytes);std::size_t first_digest{};
    for(const auto& entry:entries){put_text(out,entry.id);put64(out,cursor);put64(out,entry.size);if(first_digest==0)first_digest=out.size();put_digest(out,entry.digest);cursor+=entry.size;}
    out.resize(static_cast<std::size_t>(cursor),0);return {out,first_digest};
}

void require_rejection(std::vector<std::uint8_t> bytes,std::size_t mutation,std::string_view expected) {
    bytes.at(mutation)^=1;
    const auto path=std::filesystem::temp_directory_path()/"unirally-authored-invalid.pack";
    {std::ofstream stream(path,std::ios::binary|std::ios::trunc);stream.write(reinterpret_cast<const char*>(bytes.data()),static_cast<std::streamsize>(bytes.size()));}
    try{(void)unirally::ClassicContentPack(path);std::filesystem::remove(path);throw std::runtime_error("invalid Classic pack was accepted");}
    catch(const std::invalid_argument& error){std::filesystem::remove(path);if(std::string(error.what()).find(expected)==std::string::npos)throw;}
}
}

int main(){
    auto [bytes,first_digest]=authored_pack();
    require_rejection(bytes,12,"source ROM identity");
    require_rejection(bytes,44,"extraction-rules identity");
    require_rejection(bytes,first_digest,"required entry identity");
    // With all compiled identities intact, authored zero payload reaches the
    // independent payload SHA-256 check rather than failing an earlier gate.
    require_rejection(bytes,bytes.size()-1,"payload hash differs");
}
