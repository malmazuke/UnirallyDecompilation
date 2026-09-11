#include "input_timer.hpp"
#include <iostream>
#include <stdexcept>

namespace {
void require(bool value) {
    if (!value) throw std::runtime_error("input/timer expectation failed");
}
}
int main() {
    try {
        unirally::ControllerButtons buttons;
        auto sample = unirally::sample_controller(buttons);
        require(sample.low_image == 0 && sample.high_image == 0 &&
                sample.horizontal == 1 && sample.vertical == 1);
        buttons.up = buttons.down = buttons.left = buttons.right = true;
        sample = unirally::sample_controller(buttons);
        require(sample.high_image == 15 && sample.vertical == 0 && sample.horizontal == 0);
        buttons.up = buttons.left = false;
        sample = unirally::sample_controller(buttons);
        require(sample.high_image == 5 && sample.vertical == 2 && sample.horizontal == 2);
        buttons.a = buttons.b = buttons.x = buttons.y = true;
        buttons.left_shoulder = buttons.right_shoulder = buttons.select = buttons.start = true;
        sample = unirally::sample_controller(buttons);
        require(sample.low_image == 240 && sample.high_image == 245);

        // Separate bits catch swaps hidden when every button is held together.
        struct ButtonCase {
            bool unirally::ControllerButtons::* button;
            unsigned low, high;
        };
        const std::array<ButtonCase, 12> single_buttons{{
            {&unirally::ControllerButtons::a, 128, 0},
            {&unirally::ControllerButtons::x, 64, 0},
            {&unirally::ControllerButtons::left_shoulder, 32, 0},
            {&unirally::ControllerButtons::right_shoulder, 16, 0},
            {&unirally::ControllerButtons::b, 0, 128},
            {&unirally::ControllerButtons::y, 0, 64},
            {&unirally::ControllerButtons::select, 0, 32},
            {&unirally::ControllerButtons::start, 0, 16},
            {&unirally::ControllerButtons::up, 0, 8},
            {&unirally::ControllerButtons::down, 0, 4},
            {&unirally::ControllerButtons::left, 0, 2},
            {&unirally::ControllerButtons::right, 0, 1},
        }};
        for (const auto& test : single_buttons) {
            buttons = {};
            buttons.*(test.button) = true;
            sample = unirally::sample_controller(buttons);
            require(sample.low_image == test.low && sample.high_image == test.high);
        }

        unirally::RaceTimerDigits timer{0, 0, 9, 9, 4};
        const auto before = unirally::serialize_timer(timer);
        require(!unirally::advance_timer_digits(timer, false));
        require(unirally::serialize_timer(timer) == before);
        require(!unirally::advance_timer_digits(timer, true));
        require(timer.tens_seconds == 1 && timer.seconds == 0 &&
                timer.tenths == 0 && timer.subframe == 0);
        timer = {0, 5, 9, 9, 4};
        require(!unirally::advance_timer_digits(timer, true));
        require(timer.minutes == 1 && timer.tens_seconds == 0 && timer.seconds == 0);
        timer = {9, 5, 9, 9, 4};
        require(unirally::advance_timer_digits(timer, true));
        require(timer.minutes == 9 && timer.tens_seconds == 5 && timer.seconds == 9 &&
                timer.tenths == 9 && timer.subframe == 0);
        const unirally::TimerBytes expected{9, 0, 5, 0, 9, 0, 9, 0, 0, 0};
        require(unirally::serialize_timer(timer) == expected);
        require(unirally::serialize_timer(unirally::deserialize_timer(expected)) == expected);
        bool rejected = false;
        try { (void)unirally::deserialize_timer(std::span(expected).first(9)); }
        catch (const std::invalid_argument&) { rejected = true; }
        require(rejected);
        rejected = false;
        auto malformed = expected;
        malformed[1] = 1;
        try { (void)unirally::deserialize_timer(malformed); }
        catch (const std::invalid_argument&) { rejected = true; }
        require(rejected);
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
