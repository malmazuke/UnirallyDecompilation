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
  // Primary-source examples from bsnes' mode-3 direct-colour and add/halve
  // formulas. These guard the bit placement and per-channel carry semantics.
  require(unirally::snes_direct_colour(0x00, 0x00) == 0x0000);
  require(unirally::snes_direct_colour(0xff, 0x07) == 0x73de);
  require(unirally::snes_direct_colour(0x92, 0x05) == 0x510a);
  require(unirally::snes_add_colour(0x001f, 0x001f, false) == 0x001f);
  require(unirally::snes_add_colour(0x001f, 0x0001, true) == 0x0010);
  require(unirally::snes_add_colour(0x7c00, 0x03e0, false) == 0x7fe0);

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
  // A synthetic selector at the observed first plane expands through the same
  // 32-byte, four-by-four metatile definition used by $81:B270.
  track[0x5831] = 1;
  for (std::size_t plane = 1; plane < 5; ++plane)
    track[0x5831 + plane * 0x800] = 1;
  for (std::size_t i = 0; i < 16; ++i) {
    const auto at = 0x800f + 32 + i * 2;
    track[at] = static_cast<std::uint8_t>(i + 1);
  }
  const auto rolling = unirally::build_dragster_bg1_map(track, 0, 160);
  require(rolling[10 * 32 + 16] == 1);
  require(rolling[10 * 32 + 19] == 4);
  require(rolling[13 * 32 + 16] == 13);
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
      font(2048), rider(3456), result(5224), go_window, winner_window,
      result_base_vram(41536), result_palette(216), result_palette_tail(128);
  const auto empty_window_table = [] {
    std::vector<std::uint8_t> table;
    for (const unsigned lines : {127U, 97U}) {
      table.push_back(static_cast<std::uint8_t>(0x80U | lines));
      for (unsigned line = 0; line < lines; ++line)
        table.insert(table.end(), {255, 0, 255, 0});
    }
    return table;
  };
  go_window = empty_window_table();
  winner_window = empty_window_table();
  const unirally::PresentationContent content{track,   bg1,  bg2,   bg2_map,
                                              palette, font, rider, result,
                                              go_window, winner_window,
                                              result_base_vram, result_palette,
                                              result_palette_tail};
  const auto first = unirally::render_dragster_headless({state, 0, 0, 0, 0, 0},
                                                        content),
             second = unirally::render_dragster_headless({state, 0, 0, 0, 0, 0},
                                                         content);
  require(first.pixels == second.pixels);
  require(before == unirally::serialize_movement_state(state));

  // The retained result copier resets VMADD at byte $7B00. With stable scroll
  // 82, screen pixel (0,0) selects map row 10 and character 293; this byte is
  // reachable only through the second half of that split run.
  auto result_state = state;
  result_state.finish.phase = unirally::RacePhase::ResultScreen;
  result_state.finish.outcome = unirally::RaceOutcome::PlayerWon;
  result[5208] = 'd';
  result[5209] = 'r';
  result[5210] = 'a';
  result[5211] = 'g';
  result[5212] = 's';
  result[5213] = 't';
  result[5214] = 'e';
  result[5215] = 'r';
  result[5216] = 0xff;
  constexpr std::size_t visible_map_word = 8192 + 10 * 64;
  result_base_vram[visible_map_word] = 0x25;
  result_base_vram[visible_map_word + 1] = 0x01;
  result_palette[2] = 0xff;
  result_palette[3] = 0x7f;
  const auto empty_result = unirally::render_dragster_headless(
      {result_state, 0, 0, 0, 0, 0}, content);
  result_base_vram[39814] = 0x80;
  const auto split_result = unirally::render_dragster_headless(
      {result_state, 0, 0, 0, 0, 0}, content);
  require(empty_result.pixels[0] != split_result.pixels[0]);
  require(before == unirally::serialize_movement_state(state));

  auto winner_state = state;
  winner_state.riders[0].pose.pose_index = 0x04fe;
  winner_state.riders[1].pose.pose_index = 0x037c;
  auto visible_window = winner_window;
  visible_window[1] = 10;
  visible_window[2] = 20;
  auto visible_content = content;
  visible_content.winner_window = visible_window;
  const auto masked = unirally::render_dragster_headless(
      {winner_state, 0, 0, 0, 0, 0}, visible_content);
  if (masked.pixels[(15 * 3)] != 98)
    throw std::runtime_error("window mask did not cover its inclusive edge");
  if (masked.pixels == first.pixels)
    throw std::runtime_error("window table mutation did not affect output");
  auto invalid_window = winner_window;
  invalid_window[0] = 0;
  auto invalid_content = content;
  invalid_content.winner_window = invalid_window;
  rejected = false;
  try {
    (void)unirally::render_dragster_headless({winner_state, 0, 0, 0, 0, 0},
                                             invalid_content);
  } catch (const std::invalid_argument &) {
    rejected = true;
  }
  if (!rejected)
    throw std::runtime_error("unsupported window HDMA control was accepted");
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
