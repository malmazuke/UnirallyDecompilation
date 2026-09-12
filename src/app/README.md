# Minimal desktop frontend

Build SDL 3.4.10 from its pinned source archive inside an isolated build tree:

```sh
python3 tools/project.py build --preset app-debug
```

First launch exact-gates a user-supplied supported PAL ROM and atomically writes
the local ignored Classic pack:

```sh
python3 tools/project.py frontend run --rom /path/to/Unirally.sfc
```

Later launches need only the validated pack at
`local/classic-crawler-dragster.pack`:

```sh
python3 tools/project.py frontend run
```

Pass `--pack PATH` to use another pack location. An existing corrupt or
incompatible pack is rejected and never silently replaced. The application
reports SDL/window/renderer failures as failed launches.

Keyboard controls are arrows, Z=B, X=Y, A=A, S=X, Q=L, W=R, Enter=Start and
Backspace=Select. Standard gamepad buttons follow the equivalent SNES layout.
The current recovered slice consumes controller port 0 only.

Audio is intentionally not implemented in M3. Intermediate rider animation
poses outside the five M3-02 recovered atlas pairs hold the last supported
visual frame without changing simulation state. See
`docs/research/R-0016-minimal-frontend.md` for the exact scheduler, input,
display, dependency and first-launch contracts.
