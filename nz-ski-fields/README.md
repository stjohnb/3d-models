# NZ Ski Fields

Topographic 3D-printable terrain model of the Wakatipu and Cardrona Valley
region (South Island, NZ): a 35 km x 35 km bbox centred on -44.97, 168.80
that contains every named landmark below with several km of buffer.

Requested via issue #222.

## Landmarks

- Fernhill (Queenstown)
- Coronet Peak
- Coronet Peak Flight Park
- The Remarkables
- Snow Park NZ / Pisa Range (the former Snow Park NZ site; resort closed 2012)

## Multi-material split

The terrain ships as three separately-printable parts so it can be printed in
multiple filaments:

| Part | File | Suggested filament |
|------|------|--------------------|
| Lake Wakatipu | `lake.scad` | Blue |
| Lower terrain (base up to snow line) | `terrain.scad` | Tan / green |
| Snow caps (snow line to mountain tops) | `snow.scad` | White |

`terrain.scad` and `snow.scad` together partition the non-lake terrain exactly
— the lower piece has a flat ceiling at the snow-line elevation, and the upper
piece starts at that same flat plane and continues to the peaks. The three parts
share the same footprint and stack back into the full model.

> **Height calibration:** OpenSCAD's `surface()` maps an 8-bit PNG's 0–255 grey
> range to height 0–100, so `_ski_fields.scad` divides the Z scale by 100 (not
> 255). This realizes the stated `z_exaggeration` and keeps `elev_to_z()` in
> step with the actual surface height — otherwise the snow-line plane lands
> above the terrain and the snow part renders empty.

### Snow line

Snow is a single global elevation cut: all terrain above `snow_line_m` (default
**1300 m**) is capped, everywhere on the map. The valley floor that stretches
from the lake to Arrowtown sits well below the line, so it stays bare, while
every alpine massif above the line — Coronet Peak, The Remarkables and the
Hector Mountains to the south, the Pisa Range, and the eastern ranges — gets a
cap. Roughly 16% of the model lies above the line.

A global cut (rather than per-mountain boxes) keeps the snow following true
elevation contours: there are no rectangular region edges to leave vertical
facets across a ridge, and a peak does not need to be inside a hand-drawn box to
be included. Only terrain that merely grazes the line gets a token cap, which is
the intended behaviour.

`snow_line_m` lives at the top of `_ski_fields.scad`. To tune coverage, change
it and preview with
`openscad --export-format csg -o /dev/null nz-ski-fields/snow.scad` (or render a
low-`$fn` preview): raise it to expose more rock, lower it for more snow. The
snow part is typically several disconnected solids (the separate ranges), which
you would normally print individually.

### Lake

The lake prints as a separate insert that fills its footprint up to the water
surface (`lake_level_m`, default 310 m). The heightmap encodes water as a flat
surface with no bathymetry, so the lakebed is **estimated as a sloped basin**:
flat and deep down the middle, ramping up to the shoreline so the banks incline
believably instead of dropping straight down. `lake.scad` and `terrain.scad`
share the same bed surface, so the two parts interlock with no overlap — the lake
nests into the terrain basin and the terrain keeps the bank wedge below the bed.

The bed shape comes from **`lake_bed.png`**, a bathymetry heightfield baked from
the heightmap by `scripts/generate_lake_bed.py`:

- grey **255** = bed at the water surface (no lake) — every non-lake pixel and
  the immediate shoreline;
- grey **0** = bed at the model bottom (full depth);
- in between = the sloped bank.

The slope is a distance transform of the lake footprint: bed depth grows with
distance from the nearest internal shore, reaching full depth `--bank-run-mm`
(default 5.5 mm) offshore. The model's outer (bbox) edges count as
lake-continues, so the lake stays full-depth where the map merely crops it; only
true internal shores get the incline. `_ski_fields.scad` maps grey 0–255 back to
bed-z over `[model bottom .. water surface]`, and the map is deliberately
low-resolution (128 px) to keep the bed surface low-facet.

**Land connectivity.** Lake Wakatipu reaches the SW corner of the bbox and cuts a
wedge of land off from the main mass at the waterline. Because the sloped bed
narrows with depth, the *deep* lake no longer spans the narrow neck, so the
terrain stays a single connected piece via the bank beneath the neck — no
separate bridge is needed. `--bank-run-mm` is tuned (5.5 mm) so this holds; a
much steeper bank (smaller value) deepens the lake but re-islands the corner, so
if you change the lake level or bank run, re-check that the terrain is still one
connected solid at the model bottom.

## Elevation data

[AWS Open Data Terrain Tiles](https://aws.amazon.com/blogs/publicsector/announcing-terrain-tiles-on-aws-a-qa-with-mapzen/)
(Mapzen terrarium encoding), zoom 14. Heightmap-fetch logic adapted from
[ModelRift/terrain-to-3d](https://github.com/ModelRift/terrain-to-3d) —
public reference implementation.

## Regenerating `heightmap.png`

```
python3 scripts/fetch_terrain_heightmap.py \
  --lat -44.97 --lon 168.80 --area-km 35 --zoom 14 --px 512 \
  --output nz-ski-fields/heightmap.png \
  --metadata-output nz-ski-fields/heightmap.json
```

When regenerating, also update `elev_min_m` and `elev_range_m` in
`_ski_fields.scad` to the `elev_min_m` and `round(elev_max_m - elev_min_m)`
values from the sidecar JSON, so the Z scaling and snow-line math stay accurate.

## Regenerating `lake_bed.png`

`lake_bed.png` (the lakebed bathymetry) is baked from the heightmap and must be
regenerated whenever `heightmap.png`, the default `lake_level_m`, the model size,
or the bank slope changes:

```
python3 scripts/generate_lake_bed.py \
  --heightmap nz-ski-fields/heightmap.png \
  --metadata nz-ski-fields/heightmap.json \
  --lake-level 310 --bank-run-mm 5.5 --model-size-mm 100 \
  --output nz-ski-fields/lake_bed.png
```

After regenerating, sanity-check that the terrain is still a single connected
solid at the model bottom (see "Land connectivity" above).
