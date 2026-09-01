# Playbook: Render-and-Iterate on OpenSCAD Models

Use `render_view.py` to inspect a model from multiple angles between edits instead of waiting for CI to produce thumbnails. This is especially important for models with interior cavities (`complex_interior: true`) where a single isometric view hides geometry that determines whether a part works.

## The loop

1. Edit the `.scad` file.
2. Render the view most relevant to the change:
   ```bash
   python3 scripts/render_view.py power-workshop/drill_socket.scad --view top
   ```
3. Open the printed path and verify the geometry looks correct.
4. If not, go back to step 1.
5. Once satisfied, push — CI will run STL export, mesh validation, and interference checks.

Each default-output render creates a new temp directory; pass `-o <path>` when you want to overwrite the same file while iterating, and clean the temp dirs up when you're done.

## Memory and time caps

Every render runs under `scripts/capped-openscad.sh`, which defaults to `RENDER_MEM_MAX=2G` / `RENDER_TIMEOUT=300` on this script (CI uses larger values). Override either by setting the env var before the command:

```bash
RENDER_MEM_MAX=4G python3 scripts/render_view.py power-workshop/drill_socket.scad --view top
```

A cap hit (exit 124 for timeout, ≥128 for SIGKILL) means "reduce geometry or resolution," not "retry" — see `AGENTS.md`'s "Rendering on the constrained build host" section. If `systemd-run --user` is unavailable, the wrapper falls back to `ulimit -v`, which caps virtual address space rather than RSS; OpenSCAD's EGL/llvmpipe path can need more headroom there, so raise `RENDER_MEM_MAX` (e.g. `4G` or higher) rather than assuming the render itself is too heavy.

## View presets

| Preset   | What it shows |
|----------|--------------|
| `iso`    | Standard isometric (default, matches CI thumbnail) |
| `top`    | Looking straight down — reveals cavity openings |
| `bottom` | Looking straight up — reveals stand-off rings and base geometry |
| `front`  | Orthographic front — reveals depth of bores and boss protrusions |
| `back`   | Orthographic rear |
| `left`   | Orthographic left side |
| `right`  | Orthographic right side |

## Examples for drill_socket.scad

```bash
# Check the boss cavity depth from above
python3 scripts/render_view.py power-workshop/drill_socket.scad --view top

# Check the annular void and stand-off ring from below
python3 scripts/render_view.py power-workshop/drill_socket.scad --view bottom

# Check bore depth and wall thickness from the front
python3 scripts/render_view.py power-workshop/drill_socket.scad --view front

# Custom angle for a specific feature (gimbal coords: tx,ty,tz,rx,ry,rz,dist)
python3 scripts/render_view.py power-workshop/drill_socket.scad --camera=0,0,0,75,0,25,500 --projection=perspective
```

## Files with Y-up orientation

Every `.scad` in this repo is OpenSCAD Z-up (issue #382) — the web viewers apply the Z-up→Y-up conversion themselves — so the default preset table is always the right one here and you never need `--y-up` for a repo file.

The flag is retained for ad-hoc rendering of an externally-sourced Y-up model, where it switches the preset names to the correct semantic axes:

```bash
python3 scripts/render_view.py /tmp/some-downloaded-model.scad --view top --y-up
```

## What CI checks that render_view.py does not

`render_view.py` is for visual inspection only. It does not run:
- ADMesh mesh validation (detects non-manifold geometry, zero-area faces)
- Interference checks between mating parts (`check_interference.py`)
- Bounding-box extraction or wall-thickness warnings

These gates run automatically in CI on every push. A model that renders correctly can still fail mesh validation — that failure is caught before deployment, not before your local preview.
