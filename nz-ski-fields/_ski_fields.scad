// NZ ski fields — shared parameters and modules. See README.md.
// Heightmap is 8-bit grayscale, 0..255 mapped to elev_min..elev_max metres
// (real values in heightmap.json). Elevation source: AWS Open Data Terrain
// Tiles (Mapzen terrarium).
$fn = 64;

// User-tunable
model_size_mm     = 100;
base_thickness_mm = 3;
z_exaggeration    = 2.00;
lake_level_m      = 310;   // Lake Wakatipu surface elevation (m)

// Global snow line (m): all terrain above this elevation is capped as snow,
// everywhere on the map. The valley floor sits well below this, so it stays
// bare; every alpine massif above the line gets a cap. Raise it to expose more
// rock, lower it for more snow. (~16% of the model is above 1300 m.)
snow_line_m       = 1300;

// Heightmap constants (keep in sync with heightmap.json)
px_count     = 512;
real_area_km = 35;
elev_min_m   = 278.14453125;
elev_range_m = 2028;

// Derived
xy_scale     = model_size_mm / (px_count - 1);
mm_per_metre = model_size_mm / (real_area_km * 1000);
z_mm_total   = elev_range_m * mm_per_metre * z_exaggeration;
// OpenSCAD's surface() maps an 8-bit PNG's 0..255 grey range to height 0..100
// (NOT 0..255). Divide by 100 so a full-white pixel reaches z_mm_total and the
// model achieves the stated z_exaggeration. This also makes elev_to_z() agree
// with the actual surface height, so the snow-line plane lands inside the
// terrain (a /255 divisor put the snow line above the peaks, rendering the
// snow part empty).
z_scale      = z_mm_total / 100;

function elev_to_z(e) = (e - elev_min_m) / elev_range_m * z_mm_total;

// The terrain heightfield surface (no base). Bottom sits at z = 0.
module terrain_surface() {
  scale([xy_scale, xy_scale, z_scale])
    surface(file = "heightmap.png", center = true,
            invert = false, convexity = 10);
}

// The flat base slab: from the model bottom up to z = 0, where it meets the
// surface (whose floor also sits at z = 0). Its top stays below the lake water
// line, so no base material is left capping the lake.
module terrain_base() {
  translate([0, 0, -base_thickness_mm / 2])
    cube([model_size_mm, model_size_mm, base_thickness_mm], center = true);
}

module terrain_solid() {
  union() { terrain_surface(); terrain_base(); }
}

// Axis-aligned Z slab spanning the whole XY footprint (+2 mm margin).
module zslab(z_lo, z_hi) {
  translate([0, 0, (z_lo + z_hi) / 2])
    cube([model_size_mm + 2, model_size_mm + 2, z_hi - z_lo], center = true);
}

// Pure geometric mask for everything above the global snow line — no terrain
// dependency. A single Z slab spanning the whole footprint, so every massif
// that pokes above snow_line_m is captured.
module snow_mask() {
  zslab(elev_to_z(snow_line_m), z_mm_total + 2);
}

// ---- Lake (printed as a separate material) ---------------------------------
// The lake is a solid insert filling its footprint up to the water surface. Its
// bed is an estimated sloped basin: flat-deep down the middle, ramping up to the
// shoreline so the banks incline believably instead of dropping straight down.
// The bed shape is baked into lake_bed.png (a bathymetry heightfield) by
// scripts/generate_lake_bed.py — grey 255 = bed at the water surface (no lake),
// grey 0 = bed at the model bottom (full depth).
//
// Because the bed narrows with depth, the deep lake no longer spans the narrow
// neck near the SW corner, so the terrain stays a single connected piece via the
// bank beneath the neck — no separate land bridge is needed.
lake_surface_z = elev_to_z(lake_level_m);

// lake_bed.png is rendered at its own (lower) resolution; surface() lays one
// sample per pixel, so an N-px map spans 0..N-1 units. Must match
// scripts/generate_lake_bed.py --px.
lake_bed_px = 128;
lake_bed_xy_scale = model_size_mm / (lake_bed_px - 1);

// The lakebed as a solid: grey 0..255 maps to bed height over
// [-base_thickness_mm .. lake_surface_z]. Spans from the model bottom up to the
// bed; the water column is whatever lies above it. Outside the lake the bed sits
// at the water surface, so nothing is above it there.
module lakebed_solid() {
  translate([0, 0, -base_thickness_mm])
    scale([lake_bed_xy_scale, lake_bed_xy_scale,
           (lake_surface_z + base_thickness_mm) / 100])
      surface(file = "lake_bed.png", center = true,
              invert = false, convexity = 10);
}

// The lake water column: between the sloped bed and the flat water surface.
// Empty outside the lake (bed == water surface there). The water slab is clipped
// to the lakebed footprint (exactly model_size_mm), NOT the +2 mm-oversized
// zslab: beyond the bed there is nothing to subtract, which would leave a
// full-height water strip wrapping the entire model perimeter. The bed surface
// spans precisely model_size_mm, so the slab must match it.
module lake_region() {
  difference() {
    translate([0, 0, (lake_surface_z - base_thickness_mm) / 2])
      cube([model_size_mm, model_size_mm, lake_surface_z + base_thickness_mm],
           center = true);
    lakebed_solid();
  }
}

module lake_solid() { lake_region(); }

// Snow caps: the surface above the snow line (the base never reaches it).
module snow_solid() {
  intersection() { terrain_surface(); snow_mask(); }
}

// Everything that is neither lake nor snow. The lake water column is carved out
// of the terrain; the terrain keeps the bank wedge below the bed, which slopes
// up to meet the shoreline. The Manifold backend handles this heightfield
// boolean cheaply.
module terrain_part() {
  difference() { terrain_solid(); lake_region(); snow_mask(); }
}
