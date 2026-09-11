#include "track_progress.hpp"
#include <iostream>
#include <stdexcept>
#include <vector>

static void require(bool value) { if (!value) throw std::runtime_error("progress expectation failed"); }
int main() {
    try {
        std::vector<std::uint8_t> tables(80, 0xFF);
        // Authored transition old-tag 2 to new tags 4,6,8,10. Later tables
        // must not be considered past an earlier negative entry.
        for (unsigned row = 0; row < 4; ++row) {
            tables[row * 16 + 2] = static_cast<std::uint8_t>(4 + row * 2);
            tables[row * 16 + 3] = 0;
        }
        for (unsigned row = 0; row < 4; ++row) {
            unirally::TrackProgress rider{static_cast<std::uint16_t>((4 + row * 2) << 9), 2, 100, false};
            unirally::advance_track_progress(rider, tables);
            const std::array<unsigned, 4> expected{101,102,99,98};
            require(rider.transition_count == expected[row] && !rider.transition_rejected);
        }
        unirally::TrackProgress overflow{0x0800, 2, 65535, false};
        unirally::advance_track_progress(overflow, tables);
        require(overflow.transition_count == 0);
        tables[2] = 0xFF; tables[3] = 0xFF;
        unirally::TrackProgress rejected{0x0C00, 2, 123, false};
        unirally::advance_track_progress(rejected, tables);
        require(rejected.transition_rejected && rejected.transition_count == 123 && rejected.previous_tag == 2);
        tables[2] = 4; tables[3] = 0;
        unirally::ProgressUpdateState state{{{{0x0800,2,10,false}, {0x0800,2,20,false}}}, 1};
        const std::array<unirally::TrackSamples,2> blank{};
        unirally::update_track_progress(state, blank, tables);
        require(state.phase == 0 && state.riders[0].transition_count == 10 && state.riders[1].transition_count == 21);
        const auto bytes = unirally::serialize_progress(state);
        const auto restored = unirally::deserialize_progress(bytes);
        require(unirally::serialize_progress(restored) == bytes);
        require(bytes[0] == 0 && bytes[1] == 8 && bytes[4] == 10 && bytes[11] == 21 && bytes[14] == 0);
        unirally::update_track_progress(state, blank, tables);
        require(state.phase == 1 && state.riders[0].transition_count == 11 && state.riders[1].transition_count == 21);
        // This frame's marker observation must not affect its earlier progress
        // update. Reviewer-authored ordering boundary: each rider sees the new
        // tag only on its next active phase ($82:8C4E–8C6B before $81:8BB5).
        unirally::ProgressUpdateState delayed{{{{0x0400,2,0,false}, {0x0400,2,0,false}}}, 0};
        std::array<unirally::TrackSamples,2> new_markers{};
        new_markers[0][0] = 0x0800; new_markers[1][0] = 0x0800;
        unirally::update_track_progress(delayed, new_markers, tables);
        require(delayed.phase == 1 && delayed.riders[0].transition_count == 0 &&
                delayed.riders[0].previous_tag == 2 && delayed.riders[0].marker_word == 0x0800);
        unirally::update_track_progress(delayed, new_markers, tables);
        require(delayed.phase == 0 && delayed.riders[0].transition_count == 0 &&
                delayed.riders[1].transition_count == 1);
        delayed = unirally::deserialize_progress(unirally::serialize_progress(delayed));
        unirally::update_track_progress(delayed, new_markers, tables);
        require(delayed.riders[0].transition_count == 1 && delayed.riders[1].transition_count == 1);
        unirally::TrackSamples markers{};
        markers[9] = 0x2400; markers[0] = 0x2800;
        unirally::observe_track_markers(state.riders[0], markers);
        require(state.riders[0].marker_word == 0x2800);
        auto malformed = bytes; malformed[14] = 2; bool caught = false;
        try { (void)unirally::deserialize_progress(malformed); }
        catch (const std::invalid_argument&) { caught = true; }
        require(caught);
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n'; return 1;
    }
}
