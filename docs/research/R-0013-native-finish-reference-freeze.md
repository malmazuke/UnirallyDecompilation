# R-0013 — Native-finish reference freeze

- Task: [M3-01](../../tasks/M3-01.md)
- Status: reference contract frozen before native finish implementation
- ROM/core: PAL identity and pinned bsnes identity from R-0012
- Machine contract: `tests/manifests/native/full-race-finish.reference.json`

## Bounded experiment

The accepted M3-00 access inventory first bounded the candidate fields. Two new
cold-start access captures then replayed the already frozen continuous-Right
and release-3000–3299 inputs. They derived accesses only for frames 3000–3680
and 3180–3800 respectively, watched the candidate result fields and retained an
ignored `$7E0D00`–`$7E11FF` series. Both runs reproduced their accepted sample
and final-state digests. The access records contain zero unresolved stores.

The continuous access/series SHA-256 values are `f4d9b77d...77d26` and
`acb04381...95a5`; the variation values are `f9a7c250...91a8` and
`ad6950f9...a818`. ROM, samples, access records and series remain ignored.

## Stored finish state

`$81:80C1/$80D2/$80E3/$80F4/$810A` copy the five timer components to the
interleaved per-rider words `$7E0E43`–`$7E0E51` and `$7E0E3F/$0E41` when a
rider crosses. The resulting digits are player `0:33.57`, opponent `0:33.58`
in continuous, and player `0:35.66`, opponent `0:33.58` in the variation.

The same routine builds a u16 centisecond value. `$81:814A/$81:8183` store it
at cartridge-RAM `$77:0755/$77:07BF`; `$81:81E3/$81:81E9` store identical
copies at `$77:0769/$77:07D3`. Values are 3357/3358 in continuous and
3566/3358 in the variation. These writes occur before `$81:823B` sets the
corresponding `$7E0EFF/$7E0F01` finish flag in the same frame.

No additional persistent winner/loser word was written among the candidate
result fields. In the controlled pair, the later visible outcome follows the
state already required for continuation: when the player crosses with the
opponent flag clear the result is winner; when the opponent flag is already set
the result is loser. M3-01 therefore serializes a named semantic outcome for
clarity, but derives it once from that observed order rather than inventing a
separate original storage address.

The next-frame dispatcher contract remains R-0012: `$83:E81D` increments
`$7E0F0F` through values 1–240, then the following frame enters result loading.
The native state must name and serialize racing, finish-delay, result-loading
and stable-result phases; these semantic phases are not claims about one
original enum address.

## Reproduction

Run `access capture` on the two M3-00 manifests with the frame ranges above,
watching the addresses enumerated in the machine contract and requesting
`--wram-series-range 0x0D00 0x500 --wram-series-every 1`. The complete commands
and reports are retained under ignored `artifacts/m3-01-result-{continuous,variation}`.

This freeze defines one PAL, one track, one rider pair and two inputs. It does
not establish general ranking, records, awards or another race mode.
