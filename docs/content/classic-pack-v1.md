# Classic Crawler/Dragster pack schema 1

This contract freezes the first logical content boundary before M3-02A pack
implementation. It is limited to the accepted PAL CRAWLER/DRAGSTER slice.
Extraction provenance is tracked in
`tests/manifests/content/classic-crawler-dragster-pack.json`; consumers address
entries only by the logical IDs in that file and never by ROM offsets or loose
filenames.

The current native runner reads exactly thirteen immutable byte spans once,
before its first update. They populate `SamplingContent` (track data, collision
poses and templates), `FlatContactContent` (tile columns and flags), progress,
pose/displacement/idle-pose, rotation reward/class, and speed mask/decrement
tables. Controller input and canonical continuation state are process inputs,
not content entries. No other static-content read occurs in the accepted
M3-01 runner.

Schema 1 is a single deterministic binary file. It has an eight-byte
`URCP0001` magic, a canonical metadata section, and concatenated entry payloads
in the rules-manifest order. Metadata binds the format/profile, source ROM
SHA-256, exact extraction-rules SHA-256, semantic start-state identity, and for
each entry its logical ID, byte offset, size and SHA-256. Integer fields are
little-endian. Readers reject a changed magic/schema/profile/source/rules/start
identity, duplicate/missing/unknown IDs, non-canonical layout, trailing bytes,
or any entry size/hash mismatch before exposing an entry.

The presentation namespace is reserved under `presentation.*`; adding such an
entry changes the rules/profile identity and requires a new compatible pack
contract. Schema 1 does not promise arbitrary extension or another ROM.

## Semantic playable start

`classic.crawler.dragster.race-start.v1` constructs the public end-of-frame
1533 race start as named `MovementState` fields. Its canonical `URMV0001`
serialization is 333 bytes with SHA-256
`7cd034fcdee04e8f306712707c01c05ae02a50f2e91668127a7c3ef64492b4ab`.
The constructor takes no WRAM, SRAM, emulator state, ROM, clock or random input.
The private observation accepted in R-0011 remains validation provenance only.
Save/restore continues to use the existing canonical serialization; a playable
start is selected by semantic ID rather than supplied as a tracked save file.

This freezes a precise tested start, not a general new-game/menu constructor.
