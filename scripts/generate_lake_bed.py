#!/usr/bin/env python3
"""Bake a lakebed bathymetry map PNG from a terrain heightmap.

The nz-ski-fields model prints the lake as a separate material. Rather than a
flat-bottomed block with sheer vertical shores, the lake gets an estimated
**sloped lakebed**: the bed sits at the water surface right at the shoreline and
ramps down to full model depth a short distance offshore, so the banks incline
believably instead of dropping straight down.

This script encodes that bed as a grayscale heightfield `lake_bed.png` that
OpenSCAD's `surface()` reads:

* grey **255** = bed at the water surface (no lake column above it) — this is
  every non-lake pixel and the immediate shoreline;
* grey **0**   = bed at the model bottom (full-depth lake);
* in between    = the sloped bank.

The slope is driven by a city-block distance transform of the lake footprint:
bed depth is proportional to distance from the nearest internal shore, clamped to
full depth at `bank_run_mm` offshore. The model's outer (bbox) edges are treated
as lake-continues, so the lake stays full-depth where it is simply cropped by the
map boundary — only true internal shores get the slope.

`_ski_fields.scad` maps grey 0..255 back to bed-z over [model bottom .. water
surface], so this map carries only the *shape* of the bed, not absolute mm.

Run as a one-off generator like ``scripts/fetch_terrain_heightmap.py`` — not
wired into CI. Re-run whenever ``heightmap.png``, ``lake_level_m``, the model
size, or the bank slope changes.

Usage:
    python3 scripts/generate_lake_bed.py \\
      --heightmap nz-ski-fields/heightmap.png \\
      --metadata nz-ski-fields/heightmap.json \\
      --lake-level 310 --bank-run-mm 6 --model-size-mm 100 \\
      --output nz-ski-fields/lake_bed.png
"""

import argparse
import json
import sys
from collections import deque

import numpy as np
from PIL import Image


def largest_components(mask: np.ndarray, min_fraction: float) -> np.ndarray:
    """Keep connected components (4-connectivity) whose area is at least
    ``min_fraction`` of the largest. Returns a cleaned boolean mask.

    Implemented without scipy (not a repo dependency) via iterative BFS over the
    set pixels — cheap for the small number of water pixels involved.
    """
    h, w = mask.shape
    labels = np.zeros((h, w), dtype=np.int32)
    sizes = [0]  # index 0 = background
    nxt = 1
    for sy in range(h):
        for sx in range(w):
            if not mask[sy, sx] or labels[sy, sx]:
                continue
            q = deque([(sy, sx)])
            labels[sy, sx] = nxt
            count = 0
            while q:
                y, x = q.popleft()
                count += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] \
                            and not labels[ny, nx]:
                        labels[ny, nx] = nxt
                        q.append((ny, nx))
            sizes.append(count)
            nxt += 1

    if len(sizes) <= 1:
        return mask
    biggest = max(sizes[1:])
    threshold = biggest * min_fraction
    keep = {i for i, s in enumerate(sizes) if i != 0 and s >= threshold}
    return np.isin(labels, list(keep))


def fill_holes(mask: np.ndarray) -> np.ndarray:
    """Fill interior holes in a boolean mask (4-connectivity), scipy-free.

    Flood-fills the background inward from the image border; any background pixel
    never reached is enclosed by the mask and gets filled. Removes tiny land
    specks left inside the lake by downsampling.
    """
    h, w = mask.shape
    outside = np.zeros((h, w), dtype=bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if not mask[y, x] and not outside[y, x]:
                outside[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if not mask[y, x] and not outside[y, x]:
                outside[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not mask[ny, nx] \
                    and not outside[ny, nx]:
                outside[ny, nx] = True
                q.append((ny, nx))
    return mask | ~outside


def distance_to_shore(mask: np.ndarray) -> np.ndarray:
    """City-block distance (in pixels) from each lake pixel to the nearest
    internal shore, via iterative 4-connectivity erosion.

    Out-of-bounds is treated as lake (padded True), so pixels on the image border
    are NOT counted as shore — the lake stays full-depth where the map merely
    crops it, and only true internal shores produce a slope. A pixel one step in
    from an internal shore gets distance 1.
    """
    dist = np.zeros(mask.shape, dtype=np.int32)
    cur = mask.copy()
    step = 0
    while cur.any():
        step += 1
        dist[cur] = step
        p = np.pad(cur, 1, constant_values=True)
        cur = (p[1:-1, 1:-1] & p[2:, 1:-1] & p[:-2, 1:-1]
               & p[1:-1, 2:] & p[1:-1, :-2])
    return dist


def _parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Bake a sloped lakebed bathymetry map from a heightmap.",
    )
    p.add_argument("--heightmap", required=True,
                   help="Input 8-bit grayscale heightmap PNG.")
    p.add_argument("--metadata", required=True,
                   help="Sidecar JSON with elev_min_m / elev_range_m.")
    p.add_argument("--lake-level", type=float, default=310.0,
                   help="Water surface elevation in metres (default: 310).")
    p.add_argument("--output", required=True,
                   help="Output bathymetry PNG path.")
    p.add_argument("--min-fraction", type=float, default=0.05,
                   help="Drop components smaller than this fraction of the "
                        "largest (default: 0.05).")
    p.add_argument("--px", type=int, default=128,
                   help="Output resolution (default: 128). Kept below the "
                        "heightmap so the bed surface stays low-facet; the same "
                        "bed defines both the lake block and the terrain void, "
                        "so their shared boundary matches at any resolution.")
    p.add_argument("--bank-run-mm", type=float, default=6.0,
                   help="Horizontal distance offshore over which the bed ramps "
                        "from the water surface to full depth (default: 6).")
    p.add_argument("--model-size-mm", type=float, default=100.0,
                   help="Model width in mm, to convert bank-run to pixels "
                        "(default: 100).")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    hm = np.array(Image.open(args.heightmap).convert("L"))
    meta = json.load(open(args.metadata))
    emin = float(meta["elev_min_m"])
    erange = float(meta["elev_range_m"]) or 1.0

    grey = int(round((args.lake_level - emin) / erange * 255))
    mask = hm <= grey
    cleaned = largest_components(mask, args.min_fraction)

    img = Image.fromarray(np.where(cleaned, 255, 0).astype(np.uint8), mode="L")
    if args.px and args.px != img.width:
        img = img.resize((args.px, args.px), Image.NEAREST)
    lake = fill_holes(np.array(img) > 0)

    # Sloped bed: depth fraction ramps 0 -> 1 over bank_run pixels offshore.
    bank_run_px = max(1.0, args.bank_run_mm / args.model_size_mm * (args.px - 1))
    dist = distance_to_shore(lake)
    depth_frac = np.clip(dist / bank_run_px, 0.0, 1.0)
    # grey 255 = bed at water (no lake); grey 0 = bed at model bottom (deep).
    bed = np.where(lake, np.round(255 * (1.0 - depth_frac)), 255).astype(np.uint8)
    Image.fromarray(bed, mode="L").save(args.output)

    full_depth_px = int((lake & (depth_frac >= 1.0)).sum())
    print(f"lake level {args.lake_level:.0f} m -> grey<={grey}; "
          f"{int(lake.sum())} lake px, bank_run={bank_run_px:.1f}px, "
          f"{full_depth_px} px at full depth -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
