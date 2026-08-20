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

## The full run

Once the ellipse is confirmed, the remaining stages need no supervision — but they do take hours, so start them when you can leave them alone:

```bash
python3 scripts/scan_pipeline.py ~/captures/IMG_3814.MOV \
    --platter 540,1420,460,146 \
    -o /tmp/widget.stl
```

## Stages

| Stage    | What it does | Wall clock on `ryzen` |
|----------|--------------|-----------------------|
| `frames` | ffmpeg-decodes every frame to JPEG, scores each by variance-of-Laplacian, keeps the sharpest frame from each of `--frames` contiguous bins | ~1 min |
| `masks`  | Writes `roi-preview.jpg`, then a masked copy of each selected frame plus its COLMAP mask PNG | ~5 min with `rembg`; seconds with `--mask-mode roi` |
| `sfm`    | COLMAP feature extraction, exhaustive matching and sparse reconstruction | ~20 min |
| `dense`  | COLMAP undistortion, then OpenMVS densification | 1–3 h |
| `mesh`   | OpenMVS mesh reconstruction | ~10 min |
| `clean`  | Fits the platter plane for scale, crops to the object, exports the STL | ~1 min |

Select stages with `--only <stage>` or `--from <stage> --to <stage>`. Each completed stage drops a `.stamp-<stage>.json` in the work dir and is skipped on the next run; `--force` re-runs it anyway. The stamp is deleted *before* its stage runs, so an interrupted run never looks complete.

Everything is CPU-only. COLMAP's `patch_match_stereo` is CUDA-only and hard-errors on the flake's build, so COLMAP stops after `image_undistorter` and OpenMVS (`InterfaceCOLMAP` → `DensifyPointCloud` → `ReconstructMesh`) does densification and meshing. Densification dominates the run; `--max-image-size` (default 1600) is the knob that trades detail for hours.

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

## The work dir is disposable

By default everything lands in `.cache/scan/<video-stem>/` — already gitignored. A single capture is roughly 1900 JPEGs at about 150 MB, before COLMAP and OpenMVS add their own intermediates. Delete the directory when the STL is good; there is nothing in there worth keeping.

## Capture guidance

The reconstruction is only as good as the video, and the failure modes are almost all avoidable at capture time.

- **Keep the phone and the desk absolutely still.** This matters more than anything else on the list. The fixed-ellipse masking design rests entirely on the camera not moving; if the phone shifts partway through, the ellipse stops matching the platter and every mask after that point is wrong. Use a tripod or prop the phone against something heavy, start the recording, then do not touch the desk.
- **Shoot 4K.** Detail lost at capture is not recoverable later, and the sharpness selector can only pick the best of what it is given.
- **Diffuse, even light.** Hard shadows move with the object and get reconstructed as geometry; specular highlights slide across surfaces and break matching outright.
- **One slow, continuous rotation.** Turn the platter through a single full revolution over 60–90 seconds. Stopping and restarting produces motion blur exactly where the frames cluster.
- **Keep fingers off the platter rim** where you can. The rim's texture is what SfM tracks, and the `clean` stage measures the platter to set scale — a hand across it costs both. Nudge the platter from the underside of the base if the rig allows.
- **Give the object contrast against the background.** A plain matte backdrop of a different colour from the part is worth more than any amount of post-processing.
