# D-0005 — User-supplied ROM and local Classic content pack

- Status: accepted
- Date and owner: 12 September 2026, user direction recorded by the coordinator
- Related milestone/tasks: M3-02A, M3-02, M3-03, M3-04
- Evidence records: [R-0008](../research/R-0008-track-decode.md),
  [R-0012](../research/R-0012-complete-race-evidence.md),
  [M3-02A](../../tasks/M3-02A.md)

## Problem

Classic presentation and gameplay require data recovered from the original
game, but the public source repository and downloadable program must not carry
the original ROM or extracted original graphics, audio, tracks or other asset
payloads. The research workflow already keeps these inputs ignored, but M3 did
not define how an end user obtains a runnable native content set.

This is an engineering and distribution boundary, not a conclusion that any
particular use or release is legally cleared. Publication, project licensing
and jurisdiction-specific legal review remain separate decisions.

## Options and experiment

Three established technical patterns were considered:

1. Read the user's ROM on every launch. This keeps assets out of releases but
   couples normal play to the ROM layout and makes content/version validation a
   runtime concern.
2. Require the ROM during every build and leave extracted files in a loose
   local tree. This matches many decompilation repositories but gives players a
   developer-oriented setup and an underspecified cache boundary.
3. Verify a supported ROM once, extract a versioned local content pack, and run
   the native game against logical entries in that pack. This is the pattern
   used by native ports such as
   [Ship of Harkinian](https://github.com/HarbourMasters/Shipwright) and
   [Zelda3](https://github.com/snesrev/zelda3), and it matches the repository's
   existing `MovementContent` and ignored `local/` separation. Those upstream
   workflows were consulted on 12 September 2026 as engineering precedent, not
   as legal authority.

The accepted M2 runtime already consumes thirteen named, hash-bound static
files from ignored `local/native/`; it neither reads nor executes the ROM.
Their extraction offsets, lengths and expected hashes are tracked in content
manifests. No original asset binary is tracked at this decision point.

## Decision and consequences

Use option 3 for the Classic profile:

- A user supplies a supported ROM obtained outside the project. The extractor
  verifies the exact original bytes against a tracked identity before reading
  content.
- A repository-owned, reproducible extractor writes a versioned local Classic
  content pack. The pack records its schema, extractor/rules identity, source
  ROM hash and a manifest of logical entry IDs, sizes and hashes.
- The native simulation and frontend consume logical content entries. ROM file
  offsets remain extraction provenance and do not become the public runtime
  interface.
- After successful extraction, ordinary play can use the generated pack
  without the ROM being present. A corrupt, partial or incompatible pack is
  rejected rather than silently regenerated or partially used.
- ROMs, normalized ROM copies, generated Classic packs, loose extracted
  original content, save data, captures and traces remain ignored and are not
  release artifacts. Extraction uses an atomic temporary-output/rename flow so
  interruption cannot leave a plausible valid pack.
- Public CI stays ROM-free and exercises the pack reader/writer with authored
  fixtures. Exact extraction and native differential checks use an authorized
  private ROM fixture and bind their reports to the tested commit.
- Custom and replacement content uses the same logical identities through a
  separately versioned format. A future Extended distribution may become
  ROM-free when it has complete distributable replacement content; Classic
  fallback never causes original extracted assets to enter the repository.
- The current research-only WRAM/SRAM seed importer remains evidence. M3 must
  provide an explicit native playable-start constructor or equivalent semantic
  seed that does not require private captures in an end-user installation.

M3-01's native finish/state work is unaffected. M3-02A establishes the pack
before presentation extraction expands the content inventory; M3-03 owns the
first-launch selection/cache experience; M3-04 accepts both fresh extraction
and a later archive-only launch.

## Revisit trigger

Revisit this decision if legal review requires a stricter boundary, a supported
store/platform forbids user-ROM import, or complete independently distributable
replacement content makes a ROM-free Classic-compatible package possible. A
superseding design must retain stable logical IDs or provide a migration so the
simulation, replays and custom packs do not depend on ROM offsets.
