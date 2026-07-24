// =====================================
// Elegant Arch Dual Laptop Stand
// A swept arch into which two closed laptops slide edge-down, side by side.
// Each slot is a flat-floored channel cut straight DOWN from the crest: the
// laptop's bottom edge seats on a level floor (an XY face) between two
// vertical side walls, rather than a groove that follows the curved arch band.
// Same arch profiles as laptop_stand.scad (sampled from
// elegant-arch-macbookpro-stand.stl), scaled to a deeper base so two slots
// and a divider wall fit side by side.
//
// Coordinate system: Z up, base on Z=0. X = width (foot-to-foot),
// Y = depth (front-to-back), slots run along X.
// Upright/symmetric model — no viewer rotation (prints base-down).
// =====================================

$fn = 64;

// === Parameters (mm) ===
slot_gap_1   = 18;    // front slot width — laptop 1 thickness + clearance
slot_gap_2   = 16;    // rear slot width  — laptop 2 thickness + clearance
slot_spacing = 40;    // centre-to-centre distance between the two slots (Y)
groove_depth = 70;    // how deep each laptop sinks into the arch band
stand_width  = 240;   // overall width, foot-to-foot (X)
stand_depth  = 180;   // overall depth at the base, front-to-back (Y)
stand_height = 100;   // overall height (Z)

// === Derived scale factors ===
// Arch profiles below are sampled at the reference size 240 x 150 x 100.
sx = stand_width  / 240;   // X scale
sy = stand_depth  / 150;   // Y (depth) scale
sz = stand_height / 100;   // Z scale

// Run the slot wider than the arch (full width = stand_width) so it always
// spans the whole crest, with no un-slotted band left at the shoulders. The
// feet sit below the slot floor, so the overhang never touches them.
slot_length  = stand_width + 20;

// === Sampled arch profiles (reference 240w x 100h), x = 0 .. 120 ===
// Outer silhouette: the dome top edge (front view).
outer_half = [
    [0,100.0],[5,99.8],[10,99.3],[15,98.4],[20,97.2],[25,95.7],[30,93.7],
    [35,91.5],[40,88.9],[45,85.9],[50,82.6],[55,79.0],[60,75.0],[65,70.7],
    [70,66.0],[75,60.9],[80,55.6],[85,49.8],[90,43.7],[95,37.3],[100,30.6],
    [105,23.4],[110,16.0],[115,8.2],[120,0.0]
];
// Inner silhouette: the underside of the arch opening.
inner_half = [
    [0,92.0],[5,91.7],[10,90.9],[15,89.6],[20,87.6],[25,85.2],[30,82.2],
    [35,78.7],[40,74.6],[45,70.0],[50,64.8],[55,59.1],[60,52.9],[65,46.1],
    [70,38.7],[75,30.9],[80,22.4],[85,13.5],[90,4.0],[93,0.0]
];
// Depth taper: half-depth (|Y|) of the body vs. height. Gives the scalloped
// front/back faces — wide at the base, narrowing toward the crown.
depth_half = [
    [0,75.0],[5,71.7],[20,60.8],[40,49.6],[60,41.8],[80,37.0],[90,35.7],[100,35.1]
];

// Build a full symmetric profile (x = -120 .. 120) from a positive-x half,
// scaled to the requested width/height.
function mirror_profile(half) =
    concat(
        [ for (i = [len(half)-1 : -1 : 1]) [-half[i][0]*sx, half[i][1]*sz] ],
        [ for (p = half) [p[0]*sx, p[1]*sz] ]
    );

// Filled dome silhouette (outer edge only).
module outer_2d() { polygon(mirror_profile(outer_half)); }

// === 2D arch band: filled dome minus the underside opening ===
module arch_2d() {
    difference() {
        outer_2d();
        polygon(mirror_profile(inner_half));
    }
}

// === Depth-taper mask: tapered slab stack spanning the full width ===
module depth_mask() {
    w = stand_width + 2;
    for (i = [0 : len(depth_half)-2]) {
        z0 = depth_half[i][0]   * sz;  hd0 = depth_half[i][1]   * sy;
        z1 = depth_half[i+1][0] * sz;  hd1 = depth_half[i+1][1] * sy;
        hull() {
            translate([0, 0, z0]) cube([w, 2*hd0, 0.01], center = true);
            translate([0, 0, z1]) cube([w, 2*hd1, 0.01], center = true);
        }
    }
}

// === Two laptop slots — parallel flat-floored channels cut into the arch band ===
// Same construction as the single-slot stand, duplicated at two Y offsets. The
// front slot is centred at Y = -slot_spacing/2, the rear at Y = +slot_spacing/2,
// leaving a solid divider wall between them.
module slot_cut() {
    floor_z = stand_height - groove_depth;   // height of the flat seating floor
    h       = stand_height + 2 - floor_z;

    // Front slot (laptop 1)
    translate([-slot_length/2, -slot_spacing/2 - slot_gap_1/2, floor_z])
        cube([slot_length, slot_gap_1, h]);

    // Rear slot (laptop 2)
    translate([-slot_length/2, slot_spacing/2 - slot_gap_2/2, floor_z])
        cube([slot_length, slot_gap_2, h]);
}

// === Assembly ===
module dual_laptop_stand() {
    difference() {
        intersection() {
            rotate([90, 0, 0])
                linear_extrude(height = stand_depth + 2, center = true)
                    arch_2d();
            depth_mask();
        }
        slot_cut();
    }
}

dual_laptop_stand();
