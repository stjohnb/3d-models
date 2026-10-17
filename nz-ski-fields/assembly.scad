// NZ ski fields — assembly preview: all three parts stacked into the full
// model. Blue lake, grey terrain, white snow caps. THUMBNAIL-ONLY: the
// interactive viewers no longer load assembly.stl (a monochrome STL export
// discards these colours) — they render the coloured part STLs directly as a
// composite (see nz-ski-fields/meta.json "assembly"). This file exists purely
// as the gallery thumbnail source, so it renders Z-up (no rotate) — that lets
// OpenSCAD's default thumbnail camera look down onto the terrain and the
// blue/grey/white read clearly, instead of edge-on. Modules come from
// _ski_fields.scad and are unrotated there.
include <_ski_fields.scad>

// Preview-resolution override: this file is a viewing aid, not a printable
// part, so it renders from the 128 px copy of the heightmap. The full-res
// (512 px) assembly produced a ~100 MB-class STL that crashed browsers on the
// viewer page, and took ~31 min to render in CI. heightmap_preview.png is
// heightmap.png downsampled with Pillow (Image.LANCZOS); regenerate with:
//   python3 -c "from PIL import Image; Image.open('heightmap.png')
//     .resize((128, 128), Image.LANCZOS).save('heightmap_preview.png')"
heightmap_file = "heightmap_preview.png";
px_count = 128;

color("#64b5f6") lake_solid();     // Blue  (filament palette "Blue")
color("#9e9e9e") terrain_part();   // Grey  (filament palette "Grey")
color("#f5f5f5") snow_solid();     // White (filament palette "White")
