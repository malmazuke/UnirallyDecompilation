#include "movement.hpp"
#include "presentation.hpp"
#include <stdexcept>
#include <vector>
namespace {
void require(bool v) {
  if (!v)
    throw std::runtime_error("presentation assertion failed");
}
} // namespace
int main() {
  std::vector<std::uint8_t> track(33815);
  for (std::size_t x = 0; x < 30; ++x)
    for (std::size_t y = 0; y < 16; ++y) {
      const auto v = static_cast<std::uint16_t>(x * 16 + y);
      const auto at = 0x800f + x * 32 + y * 2;
      track[at] = static_cast<std::uint8_t>(v);
      track[at + 1] = static_cast<std::uint8_t>(v >> 8U);
    }
  const auto map = unirally::expand_dragster_bg1(track);
  require(map[0] == 0 && map[1] == 16 && map[30] == 1 && map[479] == 479);
  const auto col = unirally::gather_dragster_bg1(track, 0x8000, 2, 16);
  require(col.front() == 0 && col.back() == 15);
  bool rejected = false;
  try {
    (void)unirally::gather_dragster_bg1(track, 0, 3, 1);
  } catch (const std::invalid_argument &) {
    rejected = true;
  }
  require(rejected);
  rejected = false;
  try {
    (void)unirally::expand_dragster_bg1(
        std::span<const std::uint8_t>(track).first(0x800f));
  } catch (const std::invalid_argument &) {
    rejected = true;
  }
  require(rejected);
  require(unirally::rider_frame_for_pose(0x855, false).logical_id ==
          "presentation.rider.mike.race-tiles.v1");
  rejected = false;
  try {
    (void)unirally::rider_frame_for_pose(0xffff, false);
  } catch (const std::invalid_argument &) {
    rejected = true;
  }
  require(rejected);
  auto state = unirally::classic_crawler_dragster_start();
  state.riders[0].pose.pose_index = 0x855;
  state.riders[1].pose.pose_index = 0x895;
  const auto before = unirally::serialize_movement_state(state);
  std::vector<std::uint8_t> bg1(2560), bg2(992), bg2_map(8192), palette(352),
      font(2048), rider(3456), result(5224);
  const unirally::PresentationContent content{track,   bg1,  bg2,   bg2_map,
                                              palette, font, rider, result};
  const auto first = unirally::render_dragster_headless({state, 0, 0, 0, 0, 0},
                                                        content),
             second = unirally::render_dragster_headless({state, 0, 0, 0, 0, 0},
                                                         content);
  require(first.pixels == second.pixels);
  require(before == unirally::serialize_movement_state(state));
  rejected = false;
  try {
    auto short_content = content;
    short_content.palette = std::span<const std::uint8_t>(palette).first(351);
    (void)unirally::render_dragster_headless({state, 0, 0, 0, 0, 0},
                                             short_content);
  } catch (const std::invalid_argument &) {
    rejected = true;
  }
  require(rejected);
}
