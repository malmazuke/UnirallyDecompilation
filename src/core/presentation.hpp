#pragma once
#include "movement.hpp"
#include <array>
#include <cstdint>
#include <span>
#include <string_view>
#include <vector>
namespace unirally {
struct PresentationSample {
  const MovementState &movement;
  std::int32_t camera_x{};
  std::int16_t bg1_scroll_x{}, bg1_scroll_y{}, bg2_scroll_x{}, bg2_scroll_y{};
};
enum class RiderFrameId : std::uint8_t {
  LeanForward,
  CoastForward,
  RollingForward,
  RollingReflected,
  FinishForward,
  FinishReflected,
  SettledForward,
  SettledReflected
};
struct RiderFrameSelection {
  RiderFrameId id;
  std::string_view logical_id;
  bool reflected;
};
RiderFrameSelection rider_frame_for_pose(std::uint16_t pose_index,
                                         bool reflected);
// Exact $81:B3CF/$81:B3D3 decoded-track gather: $000F+X, then X += stride.
std::vector<std::uint16_t> gather_dragster_bg1(std::span<const std::uint8_t>,
                                               std::uint16_t source_x,
                                               std::uint16_t stride_bytes,
                                               std::size_t word_count);
// Rejected diagnostic interpretation retained for its bounded gather test.
std::array<std::uint16_t, 30 * 16>
    expand_dragster_bg1(std::span<const std::uint8_t>);
// Stateless form of the observed rolling $81:B270 map construction. Scroll
// units are pixels; each selector covers a 64 by 64 pixel metatile.
std::array<std::uint16_t, 32 * 32>
build_dragster_bg1_map(std::span<const std::uint8_t>, std::int16_t scroll_x,
                       std::int16_t scroll_y);
struct RgbFrame {
  static constexpr std::size_t width = 256, height = 224;
  std::array<std::uint8_t, width * height * 3> pixels{};
};
// Exact 15-bit SNES colour operations used by the frozen mode-3 result case.
// `palette_group` is the three-bit tilemap palette field.
std::uint16_t snes_direct_colour(std::uint8_t palette_colour,
                                 std::uint8_t palette_group);
std::uint16_t snes_add_colour(std::uint16_t main_colour,
                              std::uint16_t sub_colour, bool halve);
struct PresentationContent {
  std::span<const std::uint8_t> track, bg1_tiles, bg2_tiles, bg2_map;
  std::span<const std::uint8_t> palette, font, rider_tiles, result_assets;
  std::span<const std::uint8_t> go_window, winner_window;
  std::span<const std::uint8_t> result_base_vram, result_palette;
};
RgbFrame render_dragster_headless(const PresentationSample &,
                                  const PresentationContent &);
} // namespace unirally
