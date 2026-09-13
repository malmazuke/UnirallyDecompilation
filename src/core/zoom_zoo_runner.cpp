#include "zoom_zoo_movement.hpp"
#include "content_pack.hpp"

#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
std::vector<std::uint8_t> read_bytes(const std::filesystem::path& path) {
    std::ifstream input(path,std::ios::binary);
    if (!input) throw std::runtime_error("cannot open native movement input: " + path.string());
    return {std::istreambuf_iterator<char>(input),std::istreambuf_iterator<char>()};
}

unirally::ControllerButtons buttons(std::uint16_t mask) {
    unirally::ControllerButtons value{};
    value.b=mask&(1U<<0); value.y=mask&(1U<<1); value.select=mask&(1U<<2);
    value.start=mask&(1U<<3); value.up=mask&(1U<<4); value.down=mask&(1U<<5);
    value.left=mask&(1U<<6); value.right=mask&(1U<<7); value.a=mask&(1U<<8);
    value.x=mask&(1U<<9); value.left_shoulder=mask&(1U<<10);
    value.right_shoulder=mask&(1U<<11);
    return value;
}

void emit(const unirally::ZoomZooState& state) {
    std::cout << state.movement.frame << ' ';
    for(auto byte:unirally::serialize_zoom_zoo(state))std::cout << std::hex << std::setw(2) << std::setfill('0') << unsigned(byte);
    std::cout << std::dec << '\n';
}
}
int main(int argc,char** argv) try {
    if(argc!=7)throw std::invalid_argument("usage: zoom_zoo_runner --seed FILE --content-dir DIR --inputs FILE");
    std::filesystem::path seed,content,inputs;
    bool native_start=false;
    for(int i=1;i<argc;i+=2) {
        const std::string option=argv[i];
        if(option=="--seed")seed=argv[i+1];
        else if(option=="--start") {
            if(std::string(argv[i+1])!="classic.crawler.zoom-zoo")throw std::invalid_argument("unknown scenario");
            native_start=true;
        }
        else if(option=="--content-dir")content=argv[i+1];
        else if(option=="--inputs")inputs=argv[i+1];
        else throw std::invalid_argument("unknown ZOOM ZOO runner option");
    }
    if((seed.empty()&&!native_start)||content.empty()||inputs.empty())throw std::invalid_argument("missing ZOOM ZOO runner option");
    auto state=native_start?unirally::ZoomZooState{}:unirally::deserialize_zoom_zoo(read_bytes(seed));
    if(native_start)state.complete_race=state.sustained=true;
    const auto track=read_bytes(content/"track-data.bin");
    const auto poses=read_bytes(content/"collision-poses.bin");
    const auto templates=read_bytes(content/"collision-templates.bin");
    const auto columns=read_bytes(content/"tile-tables.bin");
    const auto flags=read_bytes(content/"tile-flags.bin");
    const auto progress=read_bytes(content/"progress-transitions.bin");
    const auto slopes=read_bytes(content/"pose-slopes.bin");
    const auto displacement=read_bytes(content/"displacement-table.bin");
    const auto idle=read_bytes(content/"idle-pose-table.bin");
    const auto reward=read_bytes(content/(state.complete_race?"race-finish-reward-values.bin":state.sustained?"sustained-reward-values.bin":"rotation-reward.bin"));
    const auto reward_class=read_bytes(content/(state.complete_race?"race-finish-reward-classes.bin":state.sustained?"sustained-reward-classes.bin":"rotation-class.bin"));
    const auto masks=read_bytes(content/"speed-masks.bin");
    const auto decrements=read_bytes(content/"speed-decrements.bin");
    const auto coefficients=read_bytes(content/(state.sustained?"sustained-slope-coefficients.bin":"reflected-vertical-slope-coefficients.bin"));
    const auto reflection=read_bytes(content/"reflection-pose-table.bin");
    const unirally::MovementContent movement{{track,poses,templates},{columns,flags},progress,slopes,displacement,idle,reward,reward_class,{masks,decrements}};
    const auto landing=read_bytes(content/"landing-response-matrices.bin");
    const auto finish_poses=state.complete_race?read_bytes(content/"race-finish-poses.bin"):std::vector<std::uint8_t>{};
    const unirally::ZoomZooContent data{movement,coefficients,reflection,landing,finish_poses};
    if(native_start)state=unirally::classic_crawler_zoom_zoo_start(data);
    std::ifstream stream(inputs);
    if(!stream)throw std::runtime_error("cannot open ZOOM ZOO controller stream");
    emit(state);
    std::string line;
    while(std::getline(stream,line)) {
        unsigned frame,player,opponent;std::string trailing;
        std::istringstream row(line);
        if(!(row>>frame>>player>>opponent) || (row>>trailing))
            throw std::invalid_argument("malformed ZOOM ZOO controller row");
        if(frame!=state.movement.frame+1 || player>4095 || opponent!=0)throw std::invalid_argument("invalid ZOOM ZOO controller row");
        try {unirally::update_zoom_zoo(state,buttons(static_cast<std::uint16_t>(player)),data);}
        catch(const std::exception& e){std::cerr << "frame " << frame << ": " << e.what() << '\n';return 1;}
        emit(state);
    }
    if(!stream.eof())throw std::invalid_argument("malformed ZOOM ZOO controller stream");
    return 0;
} catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
