# Recovered native components

`track_sampling.hpp/.cpp` implements one dependency of riding movement: expand
an indexed collision pose into ten points, then gather the track words under
those points. It does **not** update a rider, accept controller input, advance
an opponent or implement `native compare`. Its captured-argument probe validates
the component only; every call currently receives the original's incoming
position and pose. That research mechanism must not become simulation input.

The original runs the pose expansion at `$81:9E1B–9FAF`, followed by the spatial
gather `$81:8A2A–8B74`. R-0010 gives the source identity, full tested domain,
provenance and arithmetic. Coordinates are unsigned original position units;
point offsets wrap at 8 bits, grid intermediates at 16 bits. The grid has
64-unit coarse cells and 16-unit fine cells. Pose records and templates are
static extracted content. Table meanings beyond this exact lookup are not
assumed. Negative y, the rightmost coarse-cell branch and out-of-range content
are explicitly rejected because their behavior is not recovered here.

`SamplingContent` supplies byte spans, never host-layout structs. Content is
read explicitly little-endian. The component has no global mutable state,
frontend, network, emulator, or asset-extraction dependency.

Build and authored tests:

```sh
python3 tools/project.py build --preset lab-debug
python3 tools/project.py test --suite synthetic
```

ROM-dependent isolated experiment (after regenerating the access capture in
R-0010):

```sh
python3 tools/project.py content decode --manifest tests/manifests/native/movement-sampling.content.json --out artifacts/m2-01/content-expanded
python3 -m tools.unirally_lab.native.probe_sampling --access artifacts/m2-01/sampling-access/access.json --content-manifest tests/manifests/native/movement-sampling.content.json --content artifacts/m2-01/content-expanded --probe build/lab-debug/tests/native/sampling_probe --coarse-width 1024 --report artifacts/m2-01/sampling-probe.json
```

The three C++ tests use authored data for pose reflection/overflow, four grid
quadrants, and unsupported or missing inputs. The Python checks guard the
reference freeze and prevent incomplete captures from passing the probe. No
ROM or extracted table is included in those tests.

`track_progress.hpp/.cpp` observes marker words and advances a transition
counter through the original ordered tables. `ProgressUpdateState` stores both
riders' marker/tag/count/rejection state and the explicit alternating `$0302`
phase. `serialize_progress`/`deserialize_progress` define a 15-byte representation
without padding or host byte-order assumptions. The isolated recurrence matches
both riders through frame 2999 from one frame-1533 seed, but its sampled words
still originate from captured positions/poses. See R-0010 for commands and the
post-gather collision-response dependency that remains before autonomous riding.

## Semantic movement continuation state

`movement.*` defines the first shared autonomous-state boundary. Each rider has
one `ContactMotion`, `RiderContactState`, `SpeedModifiers` and `TrackProgress`
record, plus the named jump, pose, quarter-turn, residue and throttle fields
identified in R-0011-motion. Global state owns the alternating phases, counters,
timer, opponent continuation and reward queue. The canonical 297-byte encoding
is fixed-order little-endian, begins `URMV0001` plus a u32 frame, validates its
binary flags and cursors, and contains no CPU registers or captured calls.

`tools/unirally_lab/native/prepare.py` accepts only the identity-verified
end-of-frame 1533 WRAM/SRAM observation and a complete named 12-file static
inventory. It emits an ignored semantic seed, static content and runtime
metadata. `movement_runner` then advances that state using only controller
inputs and the bound static content. The update order is input/counters and AI,
each rider's active and every-frame motion, timer/reward handling, pose-based
sampling/contact, and alternating marker progress. The full primary and
cadence-17 cases agree exactly; the release-2347 case currently reaches a
source-confirmed idle-pose state outside the implemented continuation fields.
