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

std::array<std::uint8_t, 512>
build_race_cgram(const PresentationSample &sample,
                 std::span<const std::uint8_t> packed_palette) {
  std::array<std::uint8_t, 512> cgram{};
  constexpr std::array<std::size_t, 6> targets{{0, 224, 256, 352, 480, 384}};
  constexpr std::array<std::size_t, 6> lengths{{192, 32, 32, 32, 32, 32}};
  std::size_t source{};
  for (std::size_t piece = 0; piece < targets.size(); ++piece) {
    std::copy_n(packed_palette.begin() + static_cast<std::ptrdiff_t>(source),
                lengths[piece],
                cgram.begin() + static_cast<std::ptrdiff_t>(targets[piece]));
    source += lengths[piece];
  }
  static constexpr std::array<std::uint8_t, 32> racing_cycle{
      16, 66, 181, 86, 107, 45, 0, 0, 255, 127, 0, 0, 148, 82, 255, 127,
      106, 73, 164, 48, 65, 20, 164, 48, 106, 73, 81, 102, 122, 127,
      81, 102};
  static constexpr std::array<std::uint8_t, 32> finish_cycle{
      16, 66, 0, 0, 255, 127, 181, 86, 107, 45, 0, 0, 148, 82, 255, 127,
      81, 102, 122, 127, 81, 102, 106, 73, 164, 48, 65, 20, 164, 48,
      106, 73};
  const bool late_finish =
      sample.movement.riders[1].pose.pose_index == 0x08d5 ||
      sample.movement.riders[0].pose.pose_index == 0x04fe;
  const auto &cycle = late_finish ? finish_cycle : racing_cycle;
  std::copy(cycle.begin(), cycle.end(), cgram.begin() + 192);
  if (late_finish) {
    cgram[0] = 173;
    cgram[1] = 125;
  } else {
    cgram[0] = 255;
    cgram[1] = 127;
  }
  return cgram;
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
                            const std::array<std::uint16_t, 1024> &map) {
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
  for (std::size_t y = 0; y < 32; ++y)
    for (std::size_t x = 0; x < 32; ++x) {
      const auto at = 0x1800U + (y * 32U + x) * 2U;
      const auto entry = map[y * 32 + x];
      vram[at] = static_cast<std::uint8_t>(entry);
      vram[at + 1] = static_cast<std::uint8_t>(entry >> 8U);
    }
  const auto cgram = build_race_cgram(sample, content.palette);
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

struct RiderAtlasGroup {
  std::size_t first_tile;
  std::span<const std::uint16_t> vram_words;
};

RiderAtlasGroup rider_atlas_group(const PresentationSample &sample) {
  static constexpr std::array<std::uint16_t, 27> frame1600{
      24608, 24624, 26800, 26816, 26832, 24864, 24880, 24896, 27056,
      27072, 27088, 25136, 25152, 25168, 27296, 27312, 27328, 27344,
      25392, 25408, 25424, 27552, 27568, 25664, 25680, 27808, 27824};
  static constexpr std::array<std::uint16_t, 20> frame2000{
      24848, 24864, 24880, 27024, 27040, 27056, 25136, 25152, 25168,
      25184, 27312, 27328, 27344, 27360, 25408, 25424, 25440, 27584,
      27600, 27616};
  static constexpr std::array<std::uint16_t, 21> frame2400{
      26784, 24848, 24864, 24880, 27024, 27040, 27056, 25136, 25152,
      25168, 25184, 27312, 27328, 27344, 27360, 25408, 25424, 25440,
      27584, 27600, 27616};
  static constexpr std::array<std::uint16_t, 21> frame3213{
      24608, 24848, 24864, 24880, 27024, 27040, 27056, 25136, 25152,
      25168, 25184, 27312, 27328, 27344, 27360, 25408, 25424, 25440,
      27584, 27600, 27616};
  static constexpr std::array<std::uint16_t, 19> frame3453{
      24624, 24640, 24880, 24896, 25136, 25152, 25376, 25392, 25408,
      27552, 27568, 27584, 25648, 25664, 25680, 27792, 27808, 27824,
      27840};
  const auto player = sample.movement.riders[0].pose.pose_index;
  const auto opponent = sample.movement.riders[1].pose.pose_index;
  if (player == 0x04f9 && opponent == 0x0263)
    return {0, frame1600};
  if (player == 0x0855 && opponent == 0x0895)
    return {27, frame2000};
  if (player == 0x0895 && opponent == 0x0895)
    return {47, frame2400};
  if (player == 0x0855 && opponent == 0x08d5)
    return {68, frame3213};
  if (player == 0x04fe && opponent == 0x037c)
    return {89, frame3453};
  throw std::invalid_argument("unsupported Classic rider atlas combination");
}

void load_rider_tiles(std::array<std::uint8_t, 65536> &vram,
                      const PresentationSample &sample,
                      std::span<const std::uint8_t> atlas) {
  const auto group = rider_atlas_group(sample);
  for (std::size_t tile = 0; tile < group.vram_words.size(); ++tile) {
    const auto source = (group.first_tile + tile) * 32U;
    const auto destination = static_cast<std::size_t>(group.vram_words[tile]) * 2U;
    std::copy_n(atlas.begin() + static_cast<std::ptrdiff_t>(source), 32,
                vram.begin() + static_cast<std::ptrdiff_t>(destination));
  }
}

void render_rider(RgbFrame &frame, const std::array<std::uint8_t, 65536> &vram,
                  const std::array<std::uint8_t, 512> &cgram, int x, int y,
                  std::uint16_t base_tile, std::uint8_t attributes) {
  constexpr std::size_t object_tile_base = 0xc000;
  for (int tile_y = 0; tile_y < 8; ++tile_y)
    for (int tile_x = 0; tile_x < 8; ++tile_x) {
      const int source_x = 7 - tile_x;
      const auto tile_offset = static_cast<unsigned>(source_x + (tile_y << 4));
      const auto tile = static_cast<std::uint16_t>(
          (base_tile & 0x100U) |
          ((static_cast<unsigned>(base_tile) + tile_offset) & 0xffU));
      for (int pixel_y = 0; pixel_y < 8; ++pixel_y)
        for (int pixel_x = 0; pixel_x < 8; ++pixel_x) {
          const auto value = tile_pixel(vram, object_tile_base, tile,
                                        7 - pixel_x, pixel_y);
          if (value == 0)
            continue;
          const auto palette = static_cast<std::uint8_t>(
              128U + ((attributes >> 1U) & 7U) * 16U + value);
          pixel(frame, x + tile_x * 8 + pixel_x, y + tile_y * 8 + pixel_y,
                colour(cgram, palette));
        }
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

std::array<std::uint16_t, 1024>
build_dragster_bg1_map(std::span<const std::uint8_t> track,
                       std::int16_t scroll_x, std::int16_t scroll_y) {
  constexpr int horizontal_origin_tiles = 16;
  constexpr int vertical_origin_tiles = 10;
  constexpr std::size_t selector_base = 0x5831;
  constexpr std::size_t selector_plane_bytes = 0x800;
  constexpr std::size_t definition_base = 0x800f;

  const int first_tile_x = static_cast<std::uint16_t>(scroll_x) / 16;
  const int first_tile_y = static_cast<std::uint16_t>(scroll_y) / 16;
  std::array<std::uint16_t, 1024> map{};
  for (int ring_y = 0; ring_y < 32; ++ring_y) {
    const int global_y =
        first_tile_y + ((ring_y - first_tile_y) & 31);
    const int relative_y = global_y - vertical_origin_tiles;
    if (relative_y < 0)
      continue;
    const auto selector_plane = static_cast<std::size_t>(relative_y / 4);
    const auto definition_y = static_cast<std::size_t>(relative_y & 3);
    if (selector_plane >= 5)
      continue;
    for (int ring_x = 0; ring_x < 32; ++ring_x) {
      const int global_x =
          first_tile_x + ((ring_x - first_tile_x) & 31);
      const int relative_x = global_x - horizontal_origin_tiles;
      if (relative_x < 0)
        continue;
      const auto selector_column = static_cast<std::size_t>(relative_x / 4);
      const auto definition_x = static_cast<std::size_t>(relative_x & 3);
      const auto selector_at = selector_base +
                               selector_plane * selector_plane_bytes +
                               selector_column * 2U;
      const auto selector = word(track, selector_at);
      const auto definition_at = definition_base + selector * 32U +
                                 definition_y * 8U + definition_x * 2U;
      map[static_cast<std::size_t>(ring_y * 32 + ring_x)] =
          word(track, definition_at);
    }
  }
  return map;
}
RgbFrame render_dragster_headless(const PresentationSample &s,
                                  const PresentationContent &content) {
  if (content.bg1_tiles.size() != 2560 || content.bg2_tiles.size() != 992 ||
      content.bg2_map.size() != 8192 || content.palette.size() != 352 ||
      content.font.size() != 2048 || content.rider_tiles.size() != 3456 ||
      content.result_assets.size() != 5224)
    throw std::invalid_argument(
        "Classic presentation entry size is unsupported");
  const auto map = build_dragster_bg1_map(content.track, s.bg1_scroll_x,
                                          s.bg1_scroll_y);
  RgbFrame f{};
  render_race_background(f, s, content, map);
  const auto &t = s.movement.timer;
  const std::array<unsigned, 4> d{
      {t.minutes, t.tens_seconds, t.seconds, t.tenths}};
  for (std::size_t i = 0; i < 4; ++i)
    rect(f, 8 + static_cast<int>(i) * 9, 8, 3 + static_cast<int>(d[i] % 5), 10,
         {238, 238, 224});
  std::array<std::uint8_t, 65536> rider_vram{};
  load_rider_tiles(rider_vram, s, content.rider_tiles);
  const auto rider_cgram = build_race_cgram(s, content.palette);
  for (std::size_t rider_index = 0; rider_index < 2; ++rider_index) {
    const auto &rider = s.movement.riders[rider_index];
    (void)rider_frame_for_pose(rider.pose.pose_index, rider.pose.reflected);
    const int x = static_cast<std::int16_t>(rider.motion.x) - s.camera_x - 832;
    const int y = static_cast<std::int16_t>(rider.motion.y) - 752;
    render_rider(f, rider_vram, rider_cgram, x, y,
                 rider_index == 0 ? 0 : 136,
                 rider_index == 0 ? 0x66 : 0x68);
  }
  if (s.movement.finish.phase == RacePhase::ResultScreen) {
    rect(f, 36, 48, 184, 112, {12, 18, 38});
    rect(f, 52, 64, 152, 8, {238, 238, 224});
  }
  return f;
}
} // namespace unirally
