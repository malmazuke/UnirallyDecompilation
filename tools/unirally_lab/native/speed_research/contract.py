"""Readable arithmetic model of $82:A6F8–A8C8 for isolated research.

Words remain unsigned bit patterns. Branch tests use the sign of wrapped
16-bit subtraction, matching BMI/BPL rather than assuming unbounded comparisons.
This takes captured arguments in its probe and is not native gameplay code.
"""
from dataclasses import dataclass, replace


def word(value):
    return value & 0xffff


def negative(value):
    return bool(value & 0x8000)


@dataclass
class SpeedState:
    horizontal: int
    vertical: int
    boost: int
    vertical_boost: int
    progress_adjustment: int


@dataclass
class SpeedContext:
    rider: int
    skip: int
    drag: int
    pose_byte: int
    start_override: int
    ai_mode: int
    player_progress: int
    opponent_progress: int
    ai_adjustment: int
    adjustment_limit: int
    base_cap: int
    counter: int
    friction: int
    cartridge_mode: int


def update_speed(state, context, masks, decay_words):
    state = replace(state)
    if context.skip:
        return state
    if context.cartridge_mode in (2, 42):
        raise ValueError("alternate vertical-cap cartridge mode is not recovered")
    # The pose-byte branch only chooses fast boost decay. Its DEC/INC of A
    # is discarded by LDA11D7; it does not modify horizontal velocity.
    fast_decay = False
    if context.drag:
        state.horizontal = word(state.horizontal + (3 if negative(state.horizontal) else -3))
        fast_decay = True
    elif not negative(state.horizontal):
        fast_decay = context.pose_byte >= 0xb0
    else:
        fast_decay = context.pose_byte < (0x10 if context.rider == 0 else 0x40)
    if fast_decay:
        candidate = word(state.boost - 16)
        if not negative(candidate):
            state.boost = candidate

    adjustment = 0
    if context.start_override:
        extra = 80
    else:
        if context.ai_mode and context.rider == 1:
            difference = word(context.player_progress - context.opponent_progress)
            if difference and not negative(difference):
                adjustment = word(context.ai_adjustment * 2)
        else:
            own, other = ((context.player_progress, context.opponent_progress)
                          if context.rider == 0 else (context.opponent_progress, context.player_progress))
            difference = word(other - own)
            if negative(difference):
                candidate = word(state.progress_adjustment - 1)
                if not negative(candidate):
                    state.progress_adjustment = adjustment = candidate
            else:
                if difference:
                    candidate = word(state.progress_adjustment + 1)
                    if negative(word(candidate - context.adjustment_limit)):
                        state.progress_adjustment = candidate
                adjustment = state.progress_adjustment
        extra = word(state.boost + adjustment)
        extra = 0 if negative(extra) else min(extra, 384)

    cap = word((extra >> 1) + context.base_cap)
    if negative(state.horizontal):
        cap = word(-cap)
        if not negative(word(cap - state.horizontal)):
            state.horizontal = cap
    elif negative(word(cap - state.horizontal)):
        state.horizontal = cap

    cap = (extra >> 1) + 768
    if negative(state.vertical):
        cap = word(-cap)
        if not negative(word(cap - state.vertical)):
            state.vertical = cap
    elif negative(word(cap - state.vertical)):
        state.vertical = cap
    candidate = word(state.vertical_boost - 1)
    if not negative(candidate):
        state.vertical_boost = candidate

    bucket = min(extra >> 4, 8)
    mask = masks[bucket]
    if context.counter & mask == mask:
        candidate = word(state.boost - decay_words[bucket])
        if not negative(candidate):
            state.boost = candidate
    if context.friction == 1:
        if negative(state.horizontal):
            candidate = word(state.horizontal + 1)
            if negative(candidate):
                state.horizontal = candidate
        else:
            candidate = word(state.horizontal - 1)
            if not negative(candidate):
                state.horizontal = candidate
    return state
