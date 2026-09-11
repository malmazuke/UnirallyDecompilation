#include "input_timer.hpp"
#include <iostream>
#include <stdexcept>

// Isolated component probe. The harness supplies timer enable; this binary
// does not implement race-start state or any movement.
int main() {
    try {
        unirally::RaceTimerDigits timer;
        if (!(std::cin >> timer.minutes >> timer.tens_seconds >> timer.seconds >>
              timer.tenths >> timer.subframe)) throw std::runtime_error("missing seed");
        unsigned frame{};
        while (std::cin >> frame) {
            bool enabled{};
            unirally::ControllerButtons buttons;
            if (!(std::cin >> enabled >> buttons.a >> buttons.b >> buttons.x >> buttons.y >>
                  buttons.left_shoulder >> buttons.right_shoulder >> buttons.select >> buttons.start >>
                  buttons.up >> buttons.down >> buttons.left >> buttons.right)) {
                throw std::runtime_error("incomplete component input");
            }
            const auto controller = unirally::sample_controller(buttons);
            (void)unirally::advance_timer_digits(timer, enabled);
            timer = unirally::deserialize_timer(unirally::serialize_timer(timer));
            std::cout << frame << ' ' << static_cast<unsigned>(controller.low_image) << ' '
                << static_cast<unsigned>(controller.high_image) << ' '
                << static_cast<unsigned>(controller.vertical) << ' '
                << static_cast<unsigned>(controller.horizontal) << ' '
                << timer.minutes << ' ' << timer.tens_seconds << ' ' << timer.seconds << ' '
                << timer.tenths << ' ' << timer.subframe << '\n';
        }
        if (!std::cin.eof()) throw std::runtime_error("invalid frame input");
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
