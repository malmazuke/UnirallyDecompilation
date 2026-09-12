#include "presentation.hpp"
#include <algorithm>
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
                                  std::span<const std::uint8_t> track) {
  const auto map = expand_dragster_bg1(track);
  RgbFrame f{};
  rect(f, 0, 0, 256, 224, {18, 24, 52});
  for (int y = 28; y < 224; ++y)
    for (int x = 0; x < 256; ++x) {
      const int tx = (((x + s.bg1_scroll_x) / 8) % 30 + 30) % 30,
                ty = (((y + s.bg1_scroll_y) / 8) % 16 + 16) % 16;
      const auto e = map[static_cast<std::size_t>(ty * 30 + tx)];
      const auto shade = static_cast<std::uint8_t>(40 + (e & 7U) * 20U);
      pixel(f, x, y,
            {static_cast<std::uint8_t>(shade / 2), shade,
             static_cast<std::uint8_t>(shade / 3)});
    }
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
