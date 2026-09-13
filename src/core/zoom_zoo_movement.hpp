#pragma once
#include "movement.hpp"

namespace unirally {
struct ReflectionTransition {
    std::uint16_t step{}, end{}, pose_base{}, pose_override{}, completed{}, hold{};
    std::uint16_t drive_pose_enabled{}, air_turns{}, direction_latch{}, base_velocity_cap{};
    std::uint16_t brake_input{}, rotate_negative_input{}, rotate_positive_input{}, jump_input{};
    std::uint16_t wrong_direction_counter{};
};
struct SurfaceTransition {
    std::uint16_t mode{}, angle{}, tile_mode{}, leading_support{}, tile_pose{}, animation_delta{}, tile_pose_enabled{};
};
struct ZoomZooState {
    bool sustained{};
    std::array<SurfaceTransition,2> surface;
    MovementState movement;
    std::array<ReflectionTransition,2> reflection;
    std::uint8_t opponent_horizontal{};
    std::uint8_t opponent_retained_oam_x{};
};
struct ZoomZooContent {
    MovementContent movement;
    std::span<const std::uint8_t> slope_coefficients;
    std::span<const std::uint8_t> reflection_pose_table;
    std::span<const std::uint8_t> landing_matrices;
};
// $82:9715–979D: count active updates opposing the track direction, with
// original wrapped word comparisons at velocities -16 and +16 (1/32 units).
std::uint16_t next_wrong_direction_counter(std::uint16_t previous,
    std::uint16_t velocity_x,std::uint16_t marker,unsigned horizontal);
std::vector<std::uint8_t> serialize_zoom_zoo(const ZoomZooState& state);
ZoomZooState deserialize_zoom_zoo(std::span<const std::uint8_t> bytes);
// Experimental M4-12 continuation; no production frontend dispatch uses this.
void update_zoom_zoo(ZoomZooState& state,const ControllerButtons& buttons,
                     const ZoomZooContent& content);
} // namespace unirally
