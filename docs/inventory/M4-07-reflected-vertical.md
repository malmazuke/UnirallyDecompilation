# M4-07 reflected-vertical inventory checkpoint

This checkpoint was recorded after two fresh primary captures and before any
M4-07 equation implementation. Both captures cover frames 1650--1700 and are
byte-identical at SHA-256
`267ecfbf7223a3c2a9e6844d620feda0c41adb98fd9a5280d10320d3682fab67`.
Each contains 102 ordered calls and 1,020 point paths, zero unresolved stores,
zero PCs outside ROM, and no trace-ring truncation or overflow.

The suffix contains exactly 36 calls/360 points on frames 1683--1700. The 18
player calls first enter `direction_or_special` through descriptor bit
`0x4000`; no player point sets `0x8000`, bit zero or a horizontal tile flag.
The 18 opponent calls remain compatible flat vertical calls. Player winning
surface angles span 0 through +8 and support remains continuous.

Trace widths and order establish the bounded `0x4000` path. `$81:8BE3` and
`$81:8BEB` use 16-bit `AND #$8000` / `AND #$4000` before storing the two
direction words. With an 8-bit accumulator, `$81:8C2C--8C3E` selects axis 3
and computes the reflected collision-point x column as
`(~(point_x + (x & 15))) & 15`, equivalent modulo 16 to
`15 - ((point_x + (x & 15)) & 15)`. `$81:8C9E--8CA9` applies the same
reflection to the table column. `$81:8CBB--8CD3` reads height before angle and
computes the wrapped penetration byte; `$81:8CDD--8CE9` then reads the angle
and byte-negates it when the captured `0x4000` word is nonzero.

The supported response uses signed 16-bit arithmetic. `$81:973D--9747` indexes
the shift and multiplier tables at `$00:822B+abs(angle)` and
`$00:824B+abs(angle)`. `$81:9749--9760` arithmetic-shifts incoming vx and
stores the quotient; `$81:9763--9771` multiplies by repeated addition;
`$81:9774--977E` preserves a positive product or transforms a negative-angle
product to `-product+1`. `$81:97B7--97CA` computes the signed half-angle
contribution, and `$81:97DB--97E1` adds it to vx after the response guard.

The reached new coefficient indices 6--8 are authenticated directly from the
supported PAL ROM as shifts `04 04 01` and multipliers `06 07 01`; their
concatenated six-byte SHA-256 is
`e32ed598f27c7952d051d67438db3bdced18bf69c6963a5cf1450c8cc8c0c184`.
This does not claim any unobserved coefficient index or the alternate tables at
`$00:826B/$00:828B`.

The preregistered worker replay holds Right on frames 1650--1683, releases it
for frame 1684 only, restores it at 1685 and retains all other events. Its only
prediction is exact state through 1683 and first controller divergence at
1684; no contact timing or reconvergence is preclaimed.

## Additive command inventory

`python3 -m tools.unirally_lab.native.zoom_zoo_reflected_vertical_contact`
implements exactly three research subcommands: `extract-content`, `verify` and
`compare-inputs`. Reference capture continues to use the accepted M4-05
`zoom_zoo_contact capture` command and its complete unchanged watch set. There
is no M4-07 stable `tools/project.py` interface and no native-gameplay command.
