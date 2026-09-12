#include "presentation.hpp"
#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
namespace unirally {
namespace {
std::uint16_t word(std::span<const std::uint8_t> b, std::size_t at) {
  if (at > b.size() || b.size() - at < 2)
    throw std::invalid_argument(
        "Dragster BG1 gather exceeds decoded track data");
  return static_cast<std::uint16_t>(b[at] |
                                    (static_cast<unsigned>(b[at + 1]) << 8U));
}
void pixel(RgbFrame &f, int x, int y, std::array<std::uint8_t, 3> c) {
  if (x < 0 || y < 0 || x >= 256 || y >= 224)
    return;
  const auto at =
      (static_cast<std::size_t>(y) * 256 + static_cast<std::size_t>(x)) * 3;
  std::copy(c.begin(), c.end(),
            f.pixels.begin() + static_cast<std::ptrdiff_t>(at));
}
void rect(RgbFrame &f, int x, int y, int w, int h,
          std::array<std::uint8_t, 3> c) {
  for (int py = y; py < y + h; ++py)
    for (int px = x; px < x + w; ++px)
      pixel(f, px, py, c);
}

std::uint8_t channel8(std::uint16_t value) {
  const auto expanded = static_cast<unsigned>((value << 3U) | (value >> 2U));
  const auto wide = expanded * 257U;
  if (wide > 32767U)
    return static_cast<std::uint8_t>(wide >> 8U);
  const auto corrected = 32767.0 * std::pow(wide / 32767.0, 1.5);
  return static_cast<std::uint8_t>(static_cast<unsigned>(corrected) >> 8U);
}

std::array<std::uint8_t, 3> colour(const std::array<std::uint8_t, 512> &cgram,
                                   std::uint8_t index) {
  const auto at = static_cast<std::size_t>(index) * 2;
  const auto value = static_cast<std::uint16_t>(
      cgram[at] | (static_cast<unsigned>(cgram[at + 1]) << 8U));
  return {channel8(value & 31U), channel8((value >> 5U) & 31U),
          channel8((value >> 10U) & 31U)};
}

std::uint8_t tile_pixel(const std::array<std::uint8_t, 65536> &vram,
                        std::size_t tile_byte, std::uint16_t tile, int x,
                        int y) {
  const auto at = (tile_byte + (tile & 0x3ffU) * 32U) & 0xffffU;
  const auto bit = static_cast<unsigned>(7 - x);
  const auto plane01 = at + static_cast<std::size_t>(y) * 2;
  const auto plane23 = plane01 + 16;
  return static_cast<std::uint8_t>(((vram[plane01] >> bit) & 1U) |
                                   (((vram[plane01 + 1] >> bit) & 1U) << 1U) |
                                   (((vram[plane23] >> bit) & 1U) << 2U) |
                                   (((vram[plane23 + 1] >> bit) & 1U) << 3U));
}

std::uint8_t background_pixel(const std::array<std::uint8_t, 65536> &vram,
                              std::size_t map_base, bool wide, bool tall,
                              std::size_t tile_base, bool tiles16, int hofs,
                              int vofs, int screen_x, int screen_y) {
  const int tile_size = tiles16 ? 16 : 8;
  const int map_width = wide ? 64 : 32;
  const int map_height = tall ? 64 : 32;
  const int px = (screen_x + hofs) & (map_width * tile_size - 1);
  const int py = (screen_y + vofs + 1) & (map_height * tile_size - 1);
  int map_x = px / tile_size, map_y = py / tile_size, screen = 0;
  if (map_x >= 32) {
    ++screen;
    map_x -= 32;
  }
  if (map_y >= 32) {
    screen += wide ? 2 : 1;
    map_y -= 32;
  }
  const auto entry_at = (map_base + static_cast<std::size_t>(screen) * 0x800U +
                         static_cast<std::size_t>(map_y * 32 + map_x) * 2U) &
                        0xffffU;
  const auto entry = static_cast<std::uint16_t>(
      vram[entry_at] | (static_cast<unsigned>(vram[entry_at + 1]) << 8U));
  int tile_x = px % tile_size, tile_y = py % tile_size;
  if (entry & 0x4000U)
    tile_x = tile_size - 1 - tile_x;
  if (entry & 0x8000U)
    tile_y = tile_size - 1 - tile_y;
  auto tile = static_cast<std::uint16_t>(entry & 0x3ffU);
  if (tiles16) {
    const auto subtile =
        static_cast<unsigned>((tile_x >> 3) + ((tile_y >> 3) << 4));
    tile = static_cast<std::uint16_t>((tile + subtile) & 0x3ffU);
    tile_x &= 7;
    tile_y &= 7;
  }
  const auto value = tile_pixel(vram, tile_base, tile, tile_x, tile_y);
  return value == 0
             ? 0
             : static_cast<std::uint8_t>(((entry >> 10U) & 7U) * 16U + value);
}

void render_race_background(RgbFrame &frame, const PresentationSample &sample,
                            const PresentationContent &content,
                            const std::array<std::uint16_t, 480> &map) {
  std::array<std::uint8_t, 65536> vram{};
  std::copy(content.bg2_tiles.begin(), content.bg2_tiles.end(),
            vram.begin() + 0x2000);
  std::copy(content.bg2_map.begin(), content.bg2_map.end(),
            vram.begin() + 0xe000);
  constexpr std::array<std::uint16_t, 40> bg1_words{
      {8192, 8448, 8224, 8480, 8256, 8512, 8288, 8544, 8320, 8576,
       8352, 8608, 8384, 8640, 8416, 8672, 8704, 8960, 8736, 8992,
       8768, 9024, 8800, 9056, 8832, 9088, 8864, 9120, 8896, 9152,
       8928, 9184, 9216, 9472, 9248, 9504, 9280, 9536, 9312, 9568}};
  for (std::size_t piece = 0; piece < bg1_words.size(); ++piece)
    std::copy_n(content.bg1_tiles.begin() +
                    static_cast<std::ptrdiff_t>(piece * 64),
                64, vram.begin() + bg1_words[piece] * 2);
  for (std::size_t y = 0; y < 16; ++y)
    for (std::size_t x = 0; x < 30; ++x) {
      const auto at = 0x1800U + (y * 32U + x) * 2U;
      const auto entry = map[y * 30 + x];
      vram[at] = static_cast<std::uint8_t>(entry);
      vram[at + 1] = static_cast<std::uint8_t>(entry >> 8U);
    }
  std::array<std::uint8_t, 512> cgram{};
  constexpr std::array<std::size_t, 6> targets{{0, 224, 256, 352, 480, 384}};
  constexpr std::array<std::size_t, 6> lengths{{192, 32, 32, 32, 32, 32}};
  std::size_t source{};
  for (std::size_t piece = 0; piece < targets.size(); ++piece) {
    std::copy_n(content.palette.begin() + static_cast<std::ptrdiff_t>(source),
                lengths[piece],
                cgram.begin() + static_cast<std::ptrdiff_t>(targets[piece]));
    source += lengths[piece];
  }
  rect(frame, 0, 0, 256, 224, colour(cgram, 0));
  for (int y = 0; y < 224; ++y)
    for (int x = 0; x < 256; ++x) {
      const auto bg2 =
          background_pixel(vram, 0xe000, true, true, 0x2000, false,
                           sample.bg2_scroll_x, sample.bg2_scroll_y, x, y);
      if (bg2)
        pixel(frame, x, y, colour(cgram, bg2));
      const auto bg1 =
          background_pixel(vram, 0x1800, false, false, 0x4000, true,
                           sample.bg1_scroll_x, sample.bg1_scroll_y, x, y);
      if (bg1)
        pixel(frame, x, y, colour(cgram, bg1));
    }
}
} // namespace
RiderFrameSelection rider_frame_for_pose(std::uint16_t pose, bool reflected) {
  RiderFrameId id{};
  switch (pose) {
  case 0x04f9:
    id = RiderFrameId::LeanForward;
    break;
  case 0x0263:
    id = RiderFrameId::CoastForward;
    break;
  case 0x0855:
    id = RiderFrameId::RollingForward;
    break;
  case 0x0895:
    id = reflected ? RiderFrameId::RollingReflected
                   : RiderFrameId::RollingForward;
    break;
  case 0x08d5:
    id = RiderFrameId::RollingReflected;
    break;
  case 0x04fe:
    id = reflected ? RiderFrameId::SettledReflected
                   : RiderFrameId::SettledForward;
    break;
  case 0x037c:
    id =
        reflected ? RiderFrameId::FinishReflected : RiderFrameId::FinishForward;
    break;
  default:
    throw std::invalid_argument(
        "unsupported semantic rider pose for Classic presentation");
  }
  return {id, "presentation.rider.mike.race-tiles.v1", reflected};
}
std::vector<std::uint16_t>
gather_dragster_bg1(std::span<const std::uint8_t> track, std::uint16_t source_x,
                    std::uint16_t stride, std::size_t count) {
  if (stride == 0 || (stride & 1U))
    throw std::invalid_argument(
        "Dragster BG1 stride must be a positive even byte count");
  std::vector<std::uint16_t> out;
  out.reserve(count);
  std::size_t cursor = 0x0fU + source_x;
  for (std::size_t i = 0; i < count; ++i) {
    out.push_back(word(track, cursor));
    if (i + 1 < count) {
      if (cursor > std::numeric_limits<std::size_t>::max() - stride)
        throw std::invalid_argument("Dragster BG1 gather offset overflow");
      cursor += stride;
    }
  }
  return out;
}
std::array<std::uint16_t, 480>
expand_dragster_bg1(std::span<const std::uint8_t> track) {
  constexpr std::size_t base = 0x800f, column_bytes = 32;
  if (track.size() < base + 30 * column_bytes)
    throw std::invalid_argument(
        "decoded track lacks the observed Dragster BG1 map region");
  std::array<std::uint16_t, 480> out{};
  for (std::size_t x = 0; x < 30; ++x)
    for (std::size_t y = 0; y < 16; ++y)
      out[y * 30 + x] = word(track, base + x * column_bytes + y * 2);
  return out;
}
RgbFrame render_dragster_headless(const PresentationSample &s,
                                  const PresentationContent &content) {
  if (content.bg1_tiles.size() != 2560 || content.bg2_tiles.size() != 992 ||
      content.bg2_map.size() != 8192 || content.palette.size() != 352 ||
      content.font.size() != 2048 || content.rider_tiles.size() != 3456 ||
      content.result_assets.size() != 5224)
    throw std::invalid_argument(
        "Classic presentation entry size is unsupported");
  const auto map = expand_dragster_bg1(content.track);
  RgbFrame f{};
  render_race_background(f, s, content, map);
  const auto &t = s.movement.timer;
  const std::array<unsigned, 4> d{
      {t.minutes, t.tens_seconds, t.seconds, t.tenths}};
  for (std::size_t i = 0; i < 4; ++i)
    rect(f, 8 + static_cast<int>(i) * 9, 8, 3 + static_cast<int>(d[i] % 5), 10,
         {238, 238, 224});
  for (std::size_t i = 0; i < 2; ++i) {
    const auto &r = s.movement.riders[i];
    (void)rider_frame_for_pose(r.pose.pose_index, r.pose.reflected);
    const int x = 128 +
                  (static_cast<std::int16_t>(r.motion.x) - s.camera_x) / 32,
              y = static_cast<std::int16_t>(r.motion.y) / 32 - 12;
    const auto c = i ? std::array<std::uint8_t, 3>{220, 72, 70}
                     : std::array<std::uint8_t, 3>{250, 220, 48};
    rect(f, x - 8, y - 8, 16, 16, c);
    rect(f, x - 3, y - 13, 6, 5, c);
  }
  if (s.movement.finish.phase == RacePhase::ResultScreen) {
    rect(f, 36, 48, 184, 112, {12, 18, 38});
    rect(f, 52, 64, 152, 8, {238, 238, 224});
  }
  return f;
}
} // namespace unirally
