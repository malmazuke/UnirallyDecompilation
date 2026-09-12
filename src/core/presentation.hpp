#pragma once
#include "movement.hpp"
#include <array>
#include <cstdint>
#include <span>
#include <string_view>
#include <vector>
namespace unirally {
struct PresentationSample { const MovementState& movement; std::int32_t camera_x{}; std::int16_t bg1_scroll_x{},bg1_scroll_y{},bg2_scroll_x{},bg2_scroll_y{}; };
enum class RiderFrameId : std::uint8_t { LeanForward,CoastForward,RollingForward,RollingReflected,FinishForward,FinishReflected,SettledForward,SettledReflected };
struct RiderFrameSelection { RiderFrameId id; std::string_view logical_id; bool reflected; };
RiderFrameSelection rider_frame_for_pose(std::uint16_t pose_index,bool reflected);
// Exact $81:B3CF/$81:B3D3 decoded-track gather: $000F+X, then X += stride.
std::vector<std::uint16_t> gather_dragster_bg1(std::span<const std::uint8_t>,std::uint16_t source_x,std::uint16_t stride_bytes,std::size_t word_count);
// Observed $8000 region: 30 columns of 16 little-endian map words.
std::array<std::uint16_t,30*16> expand_dragster_bg1(std::span<const std::uint8_t>);
struct RgbFrame { static constexpr std::size_t width=256,height=224; std::array<std::uint8_t,width*height*3> pixels{}; };
RgbFrame render_dragster_headless(const PresentationSample&,std::span<const std::uint8_t> decoded_track);
}
