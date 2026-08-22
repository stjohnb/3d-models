# Playbook: Photogrammetry — Capture Video to Mesh

`scripts/scan_pipeline.py` turns a scanning-rig capture video into a scaled STL. It is an operator tool: nothing in it runs in CI, and the dense stages take hours, so it is driven by hand rather than by a workflow.

Everything it shells out to lives in a dedicated devShell:

```bash
nix develop .#scan
```

The first entry can take a long time — `rembg` pulls `onnxruntime`, which is not always fully cached and may build from source. If you do not want to wait, `--mask-mode roi` skips segmentation entirely (see below) but still needs the shell for ffmpeg and OpenCV.

The COLMAP option names in `scripts/scan_colmap.py` are version-sensitive — COLMAP 4.0 renamed `SiftExtraction.*` to `FeatureExtraction.*` and `SiftMatching.*` to `FeatureMatching.*`, and the old spellings abort the `sfm` stage on its first binary call. After any `flake.lock` bump, run `nix develop .#scan --command python3 -m unittest scripts.test_scan_colmap` from the repo root before starting a long capture: inside that shell it checks every option the pipeline passes against `colmap <subcommand> --help`.

## Start here: get the platter ellipse right

The whole masking design assumes the camera never moves, so the platter sits at a fixed place in the image and is specified once as an ellipse `cx,cy,rx,ry` in pixels. Getting that ellipse right is the only part of the run that needs your eyes, so do it first and on its own.

1. Run the first two stages with no `--platter`:

   ```bash
   python3 scripts/scan_pipeline.py ~/captures/IMG_3814.MOV --to masks
   ```

   The frames stage extracts and ranks frames; the masks stage then prints a suggestion and exits 1 without extracting any masks:

   ```
   no --platter given; suggestion: --platter 540,1420,470,150
   wrote .cache/scan/IMG_3814/roi-preview.jpg — open it and confirm the ellipse sits on the platter rim
   ```

2. Open `roi-preview.jpg`. The green ellipse should sit **inside** the platter rim, not on the base. `scanning-rig/_scanning_rig.scad` has `platter_d = 150` and `base_d = 166`, so a static base annulus and the raised index pointer surround the rotating platter. Those do not turn with the object; including them injects static geometry into a scene that has to be entirely rigid with the platter, and SfM will fight itself over it. Inset the ellipse by several pixels rather than tracing the outermost visible circle.

3. Rerun with the ellipse you confirmed. The suggestion is never applied unattended:

   ```bash
   python3 scripts/scan_pipeline.py ~/captures/IMG_3814.MOV --platter 540,1420,460,146 --only masks
   ```

   Check `roi-preview.jpg` once more — it is rewritten every masks run, now with the column outline you actually asked for.

### Also check --object-height

`--object-height` is in **pixels above the platter centre**, not millimetres, and the 400 default was calibrated at 720p. At 4K everything is roughly three times taller in pixels, so 400 slices through the object.

The failure is silent: `column_mask()` in `scripts/scan_masks.py` fills each image column between the ellipse drawn at the platter and the same ellipse translated up by `--object-height`, so anything above that band is masked out of every frame and the mesh comes back flat-topped/decapitated with no warning printed.

The check: `roi-preview.jpg` draws the column outline — confirm the object's top sits inside it.

Grounded example: `--object-height 900` was right for a ~90 mm-tall object at 4K with the camera at ~46°.

## The full run

Once the ellipse is confirmed, the remaining stages need no supervision — unattended, and about 15 minutes end-to-end at 720p or roughly 45 minutes at 4K on `ryzen`, long enough to walk away from (but not an overnight job):

```bash
python3 scripts/scan_pipeline.py ~/captures/IMG_3814.MOV \
    --platter 540,1420,460,146 \
    -o /tmp/widget.stl
```

## Stages

| Stage    | What it does | 720p | 4K |
|----------|--------------|------|-----|
| `frames` | ffmpeg-decodes every frame to JPEG, then selects frames per `--capture-mode`: `continuous` (default) scores each by variance-of-Laplacian and keeps the sharpest frame from each of `--frames` contiguous bins; `holds` detects step-and-hold pauses and keeps one sharp frame per hold (see below) | ~30 s | ~5 min |
| `masks`  | Writes `roi-preview.jpg`, then a masked copy of each selected frame plus its COLMAP mask PNG | ~80 s with `rembg`; seconds with `--mask-mode roi` | not separately timed; scales with pixel count (`roi` mode stays seconds) |
| `sfm`    | COLMAP feature extraction, exhaustive matching and sparse reconstruction | ~4 min | ~15 min |
| `dense`  | COLMAP undistortion, then OpenMVS densification | see note | see note |
| `mesh`   | OpenMVS mesh reconstruction | see note | see note |
| `clean`  | Fits the platter plane for scale, crops to the object, exports the STL | ~5 s | ~5 s |
| `reference` | Closes the cleaned shell into a watertight, size-budgeted reference mesh; optionally installs it under `scans/` | seconds | seconds |

Figures measured on `ryzen` against the issue #414 captures at 150 selected frames and the default `--max-image-size 1600`. `dense` and `mesh` were timed together — **≈4 min at 720p and ≈25 min at 4K**, with densification alone about 4 min in both cases, because `--max-image-size 1600` caps the images OpenMVS densifies, so the extra 4K cost is in meshing the much larger point cloud (3.5 k faces at 720p vs 103 k at 4K).

Select stages with `--only <stage>` or `--from <stage> --to <stage>`. Each completed stage drops a `.stamp-<stage>.json` in the work dir and is skipped on the next run; `--force` re-runs it anyway. The stamp is deleted *before* its stage runs, so an interrupted run never looks complete.

Everything is CPU-only. COLMAP's `patch_match_stereo` is CUDA-only and hard-errors on the flake's build, so COLMAP stops after `image_undistorter` and OpenMVS (`InterfaceCOLMAP` → `DensifyPointCloud` → `ReconstructMesh`) does densification and meshing. `--max-image-size` (default 1600) is the knob that trades detail for time, and at 4K the meshing step, not densification, is what grows.

Both OpenMVS stages are invoked with `-w <work-dir>/mvs`, the folder holding `scene.mvs`. `InterfaceCOLMAP` stores each image's path relative to the scene file, while `DensifyPointCloud` and `ReconstructMesh` resolve those paths against their working folder — which defaults to wherever you happened to run the pipeline from. Without the flag, `dense` fails a few seconds in with `failed loading image header`; the scene path itself is passed absolute so OpenMVS does not join it onto the working folder as well.

## What `clean` does, and what to do when it looks wrong

Structure-from-motion recovers geometry only up to an arbitrary similarity transform: the reconstruction has no scale and no idea which way is up. Both come from the platter. `clean` RANSAC-fits the dominant plane in the reconstructed mesh's vertices (`mvs/scene_dense_mesh.ply` — that plane is the platter surface), measures the platter's radius within it, and — knowing `platter_d = 150` from `scanning-rig/_scanning_rig.scad` — converts the whole scene to millimetres with the platter centred at the origin and its surface at z=0. The fit is seeded, so the same capture always exports at the same scale. The fit deliberately reads the mesh rather than the dense cloud: `DensifyPointCloud` attaches per-vertex list properties (`view_indices`, `view_weights`) to `scene_dense.ply`, and trimesh's PLY reader rejects those with `PLY is unexpected length!`.

Everything after that is cropping, all in millimetres:

| Flag | Default | What it drops |
|------|---------|---------------|
| `--z-min` | `1.0` | The platter surface itself |
| `--z-max` | `200.0` | Background reconstructed above the object |
| `--r-max` | `72.0` | The rim, its tick marks, and fingers — the 75 mm platter radius less 3 mm. Anything overhanging the platter goes too: a ~200 mm pair of wooden pliers on the 150 mm platter lost its handle tips. Raise `--r-max` for an object larger than the platter and accept the rim and finger geometry that comes back with it. |
| `--keep-components` | `1` | Every connected component but the largest by surface area |
| `--platter-diameter` | `150.0` | Nothing; it is the scale reference, for a non-standard platter |
| `--mm-per-unit` | — | Skips the platter fit entirely. The mesh then keeps the reconstruction's own axes, so the crop bounds no longer mean "above the platter" — widen them or expect an empty result |

`clean` writes `<work-dir>/scan-report.json` with the numbers worth checking before printing: `mm_per_unit`, `platter_radius_units`, `plane_inlier_count`, face counts before and after cropping, and the final `bbox_mm`. If the bounding box is not roughly the size of the real object, the platter fit is what to distrust first.

`sfm` prints a warning when the mapper registers fewer than 60% of the selected frames:

```
warning: only 61/150 frames registered — open .cache/scan/IMG_3814/roi-preview.jpg; a platter ellipse that misses the rim texture is the usual cause
```

That is not a threshold to tune. It nearly always means the masks are wrong — go back to `roi-preview.jpg` and the ellipse. The same is true of `mapper reconstructed no model`, which is the same failure taken to its conclusion.

## `--mask-mode roi`: the no-ML fallback

`--mask-mode salient` (the default) runs `rembg` on every selected frame to segment the object above the platter. On first use it downloads `u2net.onnx` (~176 MB) to `~/.u2net`, which needs network once.

`--mask-mode roi` keeps the entire swept column above the platter instead — no model, no download, no ONNX runtime at inference time. It is the right choice when the background behind the object is already clean, when the ONNX build is not worth the wait, or when the run bails with `too few frames with a segmented object`.

Because the suggestion step itself runs `rembg`, `roi` mode cannot print a `--platter` suggestion — the "Start here" workflow above only applies to the default `salient` mode. In `roi` mode, `--to masks` with no `--platter` exits immediately and points you at the raw first frame; open it yourself, measure the platter rim by eye, and pass `--platter cx,cy,rx,ry --only masks` to get `roi-preview.jpg`.

## `--capture-mode holds`: step-and-hold captures

`--capture-mode continuous` (the default) always picks the sharpest frame from each of `--frames` contiguous bins. On a step-and-hold capture — the operator steps the platter one tick, withdraws their hand, and holds it still — this backfires: the mid-reach frames are *sharp* too, because a steady gripping hand is not blurred, so the binned selector happily keeps hand-dominated frames. Those frames register fine in `sfm`, but the hand occludes the object and the platter and starves `dense`'s densification.

`--capture-mode holds` fixes this by picking frames only from the holds, which are hand-free by construction. It downscales each decoded frame to 128 px wide (aspect preserved) and takes the mean absolute difference between consecutive frames; anything below `max(0.35, 1.5 × 25th-percentile of the diffs)` counts as static, since holds are the low mode of the diff distribution. Runs of at least 10 consecutive static frames (~⅓ s at 30 fps) are holds. Within each hold it skips a settle margin of `min(5, run_len/4)` frames at each end (the platter is still damping down right after the step), then keeps the sharpest remaining frame — one frame per hold. `--frames` becomes an upper cap in this mode: if more holds are found than that, they are thinned evenly across the capture rather than dropped from one end.

**Hard prerequisite: the platter must carry non-repeating marks** — sharpie numerals, or #432's engraved per-tick numerals. Without them, the knurl and tick marks are rotationally periodic, so hold-to-hold feature matches alias onto the wrong tick and SfM collapses: on issue #414, hold-only selection on an unmarked platter registered only 2 of 47 frames, and a hybrid holds+bridges run fragmented into 5 separate models. The same rig with sharpied numerals registered 150/150 in a single model. If your platter is unmarked, use `--capture-mode continuous`.

If fewer than `--min-holds` (default 20) holds are detected, the stage fails with the diff statistics (threshold, median, max) and points at `<work-dir>/hold-report.json`. The usual cause is that the capture was actually shot as one continuous rotation rather than step-and-hold; re-run with `--capture-mode continuous`. If the whole video reads as a single hold, the platter never turned.

The `frames` stage stamps itself once it completes, so switching `--capture-mode` on a work dir that already ran `frames` does nothing by default — the previous mode's `selected.json` silently carries through unchanged. Pass `--from frames --force` (or delete `.stamp-frames.json`) to force it to re-select.

## Stage 7: `reference` — a mesh you can `difference()`

`clean`'s STL is an open shell. A single low camera ring never sees the
underside of the object, so `trimesh.is_watertight` is `False` and OpenSCAD's
CSG will not take it as an operand — you cannot subtract a raw scan from a
holder body no matter how you store it. `reference` closes it (issue #439):

| Mode | What it does | When |
|------|--------------|------|
| `hull` (default) | Convex hull of the cleaned mesh | Convex-ish objects — a toothpaste tube, a bottle, a battery. ~1k faces, ~50 KB. Loses every concavity |
| `slabs` | Slices the mesh into `--reference-slabs` overlapping horizontal slabs, hulls each, and boolean-unions them | When concavity matters and it varies with height — a waisted handle, a taper, a stepped body. Larger file; each slab is still convex in plan |

Neither mode preserves a concavity that a horizontal slice cannot see (a hole
bored sideways through the middle stays filled). If you need that, the scan is
not the right tool — measure the feature and model it.

The stage refuses to write a mesh over `--reference-max-bytes` (default
512000), deleting the partial file: these get committed, so the budget is the
point. If `slabs` blows it, lower `--reference-slabs` or fall back to `hull`.

By default it writes `<output>-reference.stl` beside the `clean` STL, in the
disposable work dir. `--install-as <name>` also copies it — with a sanitised
`scan-report.json` — into `scans/<name>/`, which *is* committed:

```bash
python3 scripts/scan_pipeline.py ~/captures/IMG_3826.MOV \
    --only reference --reference-mode slabs --install-as pliers
```

The name must be within `[A-Za-z0-9._ -]`, the same charset CI enforces on
`.scad` basenames, and `--force` is what overwrites an existing install. The
report is sanitised because the raw one records the absolute capture path under
your home directory and `scans/` mirrors to the public repo.

See `scans/README.md` for what a committed reference mesh guarantees and how a
`.scad` should import one.

## The work dir is disposable

By default everything lands in `.cache/scan/<video-stem>/` — already gitignored. A single capture is roughly 1900 JPEGs at about 150 MB, before COLMAP and OpenMVS add their own intermediates. Delete the directory when the STL is good; there is nothing in there worth keeping.

## Capture guidance

The reconstruction is only as good as the video, and the failure modes are almost all avoidable at capture time.

- **Transfer the original file, not a re-encode.** "Export Unmodified Original" (or AirDrop without conversion); Photos/AirDrop "compatible" export silently downscales 4K to 720p. The tell is file size and bitrate: a downscaled clip was 720×1280 at ~3.6 Mbps, 47 MB for 108 s, where a true 4K original is hundreds of MB. Verify before starting a run with `ffprobe -v error -select_streams v:0 -show_entries stream=width,height,bit_rate -of default=nw=1 <video>` (ffprobe comes with ffmpeg in `nix develop .#scan`); expect `3840`/`2160`.
- **Shoot 4K.** Detail lost at capture is not recoverable later, and the sharpness selector can only pick the best of what it is given — the same tube capture went from 3,452 to 102,718 dense faces pre-crop and from a nonsense 186×177×103 mm bbox to a plausible 161×119×54 mm.
- **The platter must carry non-repeating marks.** The knurl and tick texture is rotationally periodic, so hold-to-hold matches alias (tooth N matching tooth N+1) and either fragment the reconstruction or produce twin-surface ghosting. `_scanning_rig.scad` engraves a numeral per tick sector (`numerals = true`), but the proven fix is high-contrast ink: sharpie numerals 0–11 on the platter top took a uniform-grey object from 11/150 registered with no dense cloud at all to 150/150 in a single model with a clean, recognisable 87,552-face mesh. Engraved white-on-white numerals rely on shadowing and are untested — if registration is weaker than the sharpie baseline, ink the engraving (it makes a good stencil).
- **Keep the phone and the desk absolutely still.** This matters more than anything else on the list. The fixed-ellipse masking design rests entirely on the camera not moving; if the phone shifts partway through, the ellipse stops matching the platter and every mask after that point is wrong. Hand-turning the platter can drag the whole turntable base a couple of millimetres across the desk — the durable fix is `scanning-rig/rig_link.scad`: it collars the base and docks the phone stand so the two move as one rigid assembly, and a slide takes the camera with it instead of leaving it behind. If your rig isn't linked yet, put a non-slip mat or a bit of museum putty under the base as a stopgap, and after the capture compare `roi-preview.jpg`'s ellipse against a late frame from the video — a visible offset means the masks are wrong for the tail of that capture. A slide of ~3–4 mm over one revolution can be absorbed by insetting the ellipse to cover the platter at both extremes of the drift, which works but costs rim coverage.
- **The scene must stay rigid for the whole revolution — if the object shifts on the platter, restart the recording.** A nudged capture is not self-announcing: one measured example still reported 150/150 frames registered while merging incompatible poses into 2 models and producing unusable spikes (19.5 k faces, a 140 mm-tall bbox for a flat object). Recapturing is faster than trying to salvage post-nudge frames.
- **Camera elevation ~40–45°** — in `roi-preview.jpg` the ellipse's `ry/rx` ratio is approximately `sin(elevation)`; scan-quality analysis (issue #414) found ~40-45 degrees (`ry/rx` ≈ 0.64-0.71) works best for a single-ring capture. Near-edge-on (~30°) loses top-surface coverage. If you're using `rig_link`, its `stand_lift` customizer parameter is the adjustment — larger values raise the camera and the elevation. `scanning-rig/scan_boost.scad` is a removable plinth that stands behind the rig link and sets the camera 120mm further back as well as higher and pitched nose-down — use it when the platter fills too much of the frame. The extra distance lowers the elevation, so check `ry/rx` on `roi-preview.jpg` after fitting it and raise `boost_lift` if the ratio has fallen below ~0.64.
- **Indirect, even light; no direct overhead or spot lights.** The lights are static while the object rotates, so hard shadows and specular highlights sweep across the surface between frames and break photo-consistency. Bounce or diffuse if more light is needed.
- **Rotation: continuous or step-and-hold.** Slow continuous rotation through one revolution over 60–90 s is the protocol validated first and is the only option on an unmarked platter. Once the platter carries non-repeating marks, step-and-hold plus `--capture-mode holds` is preferable — the selected frames are both hand-free and blur-free by construction; see "`--capture-mode holds`: step-and-hold captures" above. Keep hands out of shot at the increments regardless of which selector you use.
- **Keep fingers off the platter rim** where you can. The rim's texture is what SfM tracks, and the `clean` stage measures the platter to set scale — a hand across it costs both. Nudge the platter from the underside of the base if the rig allows.
- **Give the object contrast against the background.** A plain matte backdrop of a different colour from the part is worth more than any amount of post-processing.
