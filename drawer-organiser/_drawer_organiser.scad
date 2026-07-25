// =====================================
// Drawer Organiser — shared library
// Gridfinity-compatible baseplate tiles and storage bins
// =====================================
// Library file: defines parameters and modules only, no top-level geometry.
// Included by the renderable files in this directory.
//
// Drawer this was sized for (see layout.md):
//   628mm wide at the bottom, flaring to 665mm at the top
//   424mm deep, 69mm tall
//
// All rounded rectangles in this project share the same corner-arc *centres*;
// only the arc radius changes with height. For a single cell the four centres
// sit at (+/-17, +/-17) from the cell centre, so the outer size of any ring is
// 2 * (17 + r). Every tapered section is built as a hull() between two 0.01mm
// slabs at the two z heights — the repo's beveled-transition convention — which
// gives an exact 45-degree frustum because the slabs are convex.

$fn = 64;

// === Grid constants (mm) ===
cell_pitch    = 42;      // Gridfinity cell pitch
corner_centre = 17;      // corner-arc centre offset from a cell centre
height_unit   = 7;       // bin height unit; bin height = z_units * height_unit

// === Bin base pad profile ===
// Radius of the corner arc at each z height, measured up from z = 0.
//   z 0.00  r 0.80  -> 35.6mm across
//   z 0.80  r 1.60  -> 37.2mm
//   z 2.60  r 1.60  -> 37.2mm
//   z 4.75  r 3.75  -> 41.5mm
pad_r_bot    = 0.8;
pad_z_mid    = 0.8;
pad_r_mid    = 1.6;
pad_z_flare  = 2.6;      // straight section runs pad_z_mid .. pad_z_flare
pad_height   = 4.75;     // total bin base height
pad_r_top    = 3.75;

// === Baseplate socket profile (the cut) ===
// Same shape offset outward, giving a uniform 0.25mm per-side minimum
// clearance between pad and socket at every height. Do not "improve" these.
//   z 0.00  r 1.15  -> 36.3mm across
//   z 0.70  r 1.85  -> 37.7mm
//   z 2.50  r 1.85  -> 37.7mm
//   z 4.65  r 4.00  -> 42.0mm
sock_r_bot   = 1.15;
sock_z_mid   = 0.7;
sock_r_mid   = 1.85;
sock_z_flare = 2.5;
plate_height = 4.65;     // baseplate thickness
sock_r_top   = 4.0;

// The socket cut runs 0.1mm below the plate and 0.5mm above it, continuing the
// same 45-degree taper. The upward continuation matters: at the plate perimeter
// the socket top is exactly flush with the plate's outer wall, and letting the
// cut exit above the top face avoids coincident-face CSG artifacts that could
// produce a non-manifold STL and fail ADMesh validation.
sock_z_under = 0.1;
sock_z_over  = 0.5;

// === Stacking lip profile ===
// Radii at depths below the bin's top face; mirrors the base pad so a bin
// stacks into the one below it.
lip_height   = 4.4;      // total lip depth below the top face
lip_r_bot    = 1.15;
lip_z_mid    = 2.5;      // depth below top face where the straight section ends
lip_r_mid    = 3.05;
lip_z_flare  = 0.7;      // depth below top face where the final flare starts
lip_r_top    = 3.35;
lip_z_rim    = 0.4;      // depth of the flat top rim

// === Tile seam (interlocking barbed tabs) ===
// Tabs sit at the CENTRE of each cell along a tile edge. The +X and +Y edges
// carry tabs; the -X and -Y edges carry the matching notches. Because the
// profile is periodic with the 42mm pitch and referenced to the tile's own
// cell centres, every tile mates with every other tile of the same edge length
// — there is no male/female variant to keep track of.
//
// Do not move these back onto the cell junctions (issue #309). At a junction
// the only material is the 4.3mm rib that joins the perimeter rail to the rest
// of the plate, and any notch big enough to hold a tab cuts straight through
// it: the printed tiles came off the bed with the whole perimeter rail hanging
// off the four corners. At a cell centre the rail is instead backed by material
// running the full length of the edge, so a notch takes a slot out of the rail
// and leaves it attached at the junctions either side.
//
// The trade is depth. At a cell centre the rail is only 4 - sock_r deep —
// 2.15mm through the socket's straight section — so the tab has to work in
// about 2mm. That rules out a round jigsaw head (a circle tangent to the seam
// has almost no undercut) and a dovetail (its angled face cams out under load).
// A barb does fit: the shoulder is perpendicular to the seam, so pulling two
// tiles apart loads it in compression instead of wedging them open.
seam_tab_neck_w   = 1.6;   // neck width at the seam line
seam_tab_neck_len = 0.6;   // seam line -> shoulder
seam_tab_head_w   = 3.6;   // head width
seam_tab_depth    = 2.0;   // seam line -> tab tip
seam_tab_root     = 1.0;   // how far the neck runs back inside the tile
seam_tab_fillet   = 0.3;   // corner radius on the tab/notch profile
seam_clearance    = 0.4;   // total fit gap across a seam (0.2 per side)

eps = 0.01;              // thin-slab thickness for hull() transitions

// Every profile below is a stack of tapered and straight sections that meet at
// shared z heights. Adjoining sections must *overlap* by eps rather than merely
// touch: when two solids in a union() share only a boundary plane, CGAL can keep
// that plane as a paper-thin internal membrane instead of dissolving it. Such a
// membrane is itself a closed 2-manifold sliver, so ADMesh reports the mesh as
// watertight and CI's validation cannot see it — but it seals the bin's interior
// and stops the socket cut reaching full depth. The overlaps are load-bearing;
// do not tidy them away.

// === Primitives ===

// Rounded rectangle: hull of four cylinders of radius r and height h placed at
// (+/-cx, +/-cy). Outer size is 2*(cx + r) by 2*(cy + r).
module rrect(cx, cy, r, h) {
    hull() {
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * cx, sy * cy, 0]) cylinder(r = r, h = h);
    }
}

// A tapered section between two z heights with two corner radii, built as a
// hull of two thin rrect slabs (repo beveled-transition convention).
module rrect_taper(cx, cy, r1, z1, r2, z2) {
    hull() {
        translate([0, 0, z1])       rrect(cx, cy, r1, eps);
        translate([0, 0, z2 - eps]) rrect(cx, cy, r2, eps);
    }
}

// Place children() at the centre of every cell of a gx by gy grid, with the
// whole grid centred on the origin.
module cell_grid(gx, gy) {
    for (ix = [0 : gx - 1], iy = [0 : gy - 1])
        translate([(ix - (gx - 1) / 2) * cell_pitch,
                   (iy - (gy - 1) / 2) * cell_pitch,
                   0])
            children();
}

// A rounded rectangle in 2D, w by h, centred on the origin, corner radius r.
module rrect_2d(w, h, r) {
    offset(r = r) square([w - 2 * r, h - 2 * r], center = true);
}

// One barbed tab, in 2D, protruding in +X from a seam line at x = 0: a narrow
// neck out to the shoulder, then a wider head. Every corner is rounded, so the
// clearance offset() stays well behaved and the notch it cuts has no sharp
// internal corners for the nozzle to round off on its own.
//
// The neck runs back to -seam_tab_root inside the tile: that inward half is
// what keeps the tab attached to the tile body after the clearance offset
// shrinks it. Do NOT shorten it to a thin eps overlap — the offset() below
// would then detach every tab into a free-floating island.
//
// For the same reason the neck runs all the way out to the tip rather than
// stopping at the shoulder, so it overlaps the head across its full length
// instead of merely abutting it. Two rounded rectangles that only touch meet
// at a single point, and offset(delta = -clearance/2) pulls that point apart:
// every tab head then prints as a loose island (admesh reported five parts for
// a 2x2 tile). The union's outline is the same barb either way.
module seam_tab_2d() {
    neck_l = seam_tab_root + seam_tab_depth;
    head_l = seam_tab_depth - seam_tab_neck_len;
    union() {
        translate([(seam_tab_depth - seam_tab_root) / 2, 0])
            rrect_2d(neck_l, seam_tab_neck_w, seam_tab_fillet);
        translate([(seam_tab_depth + seam_tab_neck_len) / 2, 0])
            rrect_2d(head_l, seam_tab_head_w, seam_tab_fillet);
    }
}

// Positions of the cell centres along an edge of n cells. Tabs sit on these,
// not on the junctions between them — see the seam notes above.
function seam_offsets(n) =
    [ for (i = [0 : n - 1]) (i - (n - 1) / 2) * cell_pitch ];

// 2D footprint of one tile: exactly gx*42 by gy*42 with r=4 corners, plus tabs
// on +X (and +Y unless rear_tabs is false) and notches on -X/-Y. The clearance
// offset is applied to the tab and notch features ONLY, never to the whole
// outline — shrinking the outline would drift the 42mm pitch across every seam
// and a bin spanning two tiles would no longer seat.
module tile_outline_2d(gx, gy, rear_tabs = true) {
    hx = gx * cell_pitch / 2;
    hy = gy * cell_pitch / 2;
    difference() {
        union() {
            offset(r = 4) square([2 * hx - 8, 2 * hy - 8], center = true);
            offset(delta = -seam_clearance / 2) {
                for (t = seam_offsets(gy)) translate([hx, t]) seam_tab_2d();
                if (rear_tabs)
                    for (t = seam_offsets(gx))
                        translate([t, hy]) rotate(90) seam_tab_2d();
            }
        }
        offset(delta = seam_clearance / 2) {
            for (t = seam_offsets(gy)) translate([-hx, t]) seam_tab_2d();
            for (t = seam_offsets(gx)) translate([t, -hy]) rotate(90) seam_tab_2d();
        }
    }
}

// 2D footprint of one side filler strip: w by gy*42, with notches on BOTH X
// edges and tabs on neither.
//
// On the +X side of the assembly the notches swallow the baseplate's
// protruding tabs; on the -X side, where the baseplate presents notches of its
// own, the two notched edges simply butt. Doing it this way makes the strip
// symmetric — there is no way to fit it back to front — and keeps the assembled
// width exactly 588 + 2*w, with nothing protruding towards the drawer wall.
// A tab on the outer edge would add its 1.8mm to the overall width.
module filler_outline_2d(gy, w) {
    hx = w / 2;
    hy = gy * cell_pitch / 2;
    difference() {
        offset(r = 4) square([2 * hx - 8, 2 * hy - 8], center = true);
        offset(delta = seam_clearance / 2)
            for (t = seam_offsets(gy)) {
                translate([-hx, t]) seam_tab_2d();
                translate([ hx, t]) rotate(180) seam_tab_2d();
            }
    }
}

// === Profiles ===

// One cell's bin base pad, z = 0 .. pad_height.
module bin_base_pad() {
    c = corner_centre;
    rrect_taper(c, c, pad_r_bot, 0, pad_r_mid, pad_z_mid);
    translate([0, 0, pad_z_mid - eps])
        rrect(c, c, pad_r_mid, pad_z_flare - pad_z_mid + 2 * eps);
    rrect_taper(c, c, pad_r_mid, pad_z_flare, pad_r_top, pad_height);
    // Cap overlapping into the bin body above, so the pad tops do not survive
    // as a membrane across the body's underside.
    translate([0, 0, pad_height - eps]) rrect(c, c, pad_r_top, 2 * eps);
}

// One cell's socket, as a solid to subtract from the baseplate slab.
module plate_socket() {
    c = corner_centre;
    translate([0, 0, -sock_z_under]) rrect(c, c, sock_r_bot, sock_z_under + eps);
    rrect_taper(c, c, sock_r_bot, 0, sock_r_mid, sock_z_mid);
    translate([0, 0, sock_z_mid - eps])
        rrect(c, c, sock_r_mid, sock_z_flare - sock_z_mid + 2 * eps);
    // Flare continues past the top face at the same 45 degrees, so the cut
    // exits cleanly rather than ending on a coincident face.
    rrect_taper(c, c, sock_r_mid, sock_z_flare,
                sock_r_top + sock_z_over, plate_height + sock_z_over);
}

// === Assemblies ===

// A baseplate tile of gx by gy cells. The outer slab is exactly
// gx*cell_pitch by gy*cell_pitch with zero added margin, so tiles butt
// together and the 42mm pitch continues across the seams. The perimeter ends
// in a feather edge at the top — that is correct Gridfinity behaviour.
//
// With interlock = true the tile also grows genderless barbed tabs on its +X
// (and, unless rear_tabs is false, +Y) edge and the matching notches on -X/-Y.
// The nominal footprint is unchanged: a mated tab sits inside its neighbour's
// notch, so the assembled pitch stays 42mm. rear_tabs = false is for the back
// row of the drawer, where the protruding tabs serve no purpose (see layout.md).
//
// The notch is cut with a prism that runs the full height of the plate while
// the tab is clipped by the phantom sockets, so the tab's cross-section is a
// subset of the notch's at every z. That is what makes the seam assemble:
// tiles cannot be pressed together in the plane — the barb shoulder is
// perpendicular, by design — but a tile lowered onto its already-placed
// neighbours drops its tabs straight down into their slots.
module baseplate(gx, gy, interlock = false, rear_tabs = true) {
    ox = gx * cell_pitch / 2 - 4;
    oy = gy * cell_pitch / 2 - 4;

    if (!interlock) {
        difference() {
            rrect(ox, oy, 4, plate_height);
            cell_grid(gx, gy) plate_socket();
        }
    } else {
        // Build one phantom ring of cells around the tile, then clip to the
        // tile outline. The tabs reach into the neighbouring tile's territory,
        // so that territory must already carry the neighbour's socket cut or
        // the grid would not continue across the seam. Clipping a
        // (gx+2)x(gy+2) plate reproduces the plain tile's perimeter exactly:
        // at the tile edge the real and phantom sockets both reach the
        // boundary at z = plate_height, giving the same feather edge.
        intersection() {
            difference() {
                rrect(ox + cell_pitch, oy + cell_pitch, 4, plate_height);
                cell_grid(gx + 2, gy + 2) plate_socket();
            }
            translate([0, 0, -1])
                linear_extrude(plate_height + 2) tile_outline_2d(gx, gy, rear_tabs);
        }
    }
}

// A side filler strip, w wide by gy cells long, the same thickness as a
// baseplate tile so the drawer floor finishes flush. The 14 x 10 grid covers
// 588 x 420mm of a 628 x 424mm drawer floor, so a pair of these takes up the
// 40mm of width slack and stops the assembled baseplate sliding about
// (see layout.md).
//
// w must stay above 8mm: the outline is an r=4 rounded rectangle, and below
// that the two corner arcs would overlap and the square() would go negative.
module filler(gy, w) {
    assert(w > 8, "filler: w must be greater than 8mm");
    linear_extrude(plate_height) filler_outline_2d(gy, w);
}

// === Flared display container (assembly preview only) ===
// A Gridfinity-footed tub used by drawer_assembly.scad to show the drawer
// filled. Unlike bin(), a container can flare one or more of its outer walls
// OUTWARD with height, to follow the drawer's sides — the drawer is 628mm wide
// at the floor but flares to 665mm at the top over its 69mm height, so a
// container standing against a side wall can lean out and reclaim that volume.
//
// Pass the outward top offset in mm for each side in fnx/fpx/fny/fpy (negative-X,
// positive-X, negative-Y, positive-Y). 0 keeps that wall vertical. Only the side
// facing a flaring drawer wall is given a non-zero offset by drawer_assembly.scad.
//
// This is a VIEWING AID, not a printable part: it has plain straight-tapered
// walls, no stacking lip, and no split for the print bed. It still stands on
// Gridfinity base pads, so in the assembly it registers on the baseplate sockets
// exactly like a real bin (0.25mm pad-to-socket clearance keeps the two disjoint,
// so seating a container costs the union nothing).

// Outer or inner shell as a straight-tapered frustum: a rounded rect of half-
// extents (bx,by) + corner r at z0, hulled to the same rect at z1 with each of
// the four sides pushed outward by its per-side flare. A side with flare 0 stays
// vertical, so an all-zero call is just a prism (same footprint as an rrect).
//
// The flare is measured against the reference span ref0..ref1, NOT against
// z0..z1: a side reaches its full offset (fnx/fpx/fny/fpy) at ref1 and is
// vertical at ref0, so two shells covering different z-ranges — the outer wall
// and the inner cavity, which starts a floor thickness higher — share one
// taper slope instead of each spreading its offset over its own span.
module container_shell(bx, by, r, z0, z1, fnx, fpx, fny, fpy, ref0, ref1) {
    f0 = (z0 - ref0) / (ref1 - ref0);   // flare fraction reached at z0
    f1 = (z1 - ref0) / (ref1 - ref0);   // ... and at z1
    hull() {
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * bx + (sx < 0 ? -fnx : fpx) * f0,
                       sy * by + (sy < 0 ? -fny : fpy) * f0,
                       z0]) cylinder(r = r, h = eps);
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * bx + (sx < 0 ? -fnx : fpx) * f1,
                       sy * by + (sy < 0 ? -fny : fpy) * f1,
                       z1 - eps]) cylinder(r = r, h = eps);
    }
}

// A display container of gx by gy cells, z_units tall, with per-side outward
// flare. Both shells flare against the same pad_height..H reference span, so a
// flared face keeps a constant wall_t of material between cavity and outside
// (measured horizontally) instead of thickening towards the floor. The cavity
// runs from floor_z (pad_height + floor_t) out through the top face, leaving an
// open tub.
module container(gx, gy, z_units, wall_t, floor_t,
                 fnx = 0, fpx = 0, fny = 0, fpy = 0) {
    H  = z_units * height_unit;
    ox = gx * cell_pitch / 2 - 4;
    oy = gy * cell_pitch / 2 - 4;
    floor_z = pad_height + floor_t;
    difference() {
        union() {
            cell_grid(gx, gy) bin_base_pad();
            container_shell(ox, oy, pad_r_top, pad_height, H,
                            fnx, fpx, fny, fpy, pad_height, H);
        }
        container_shell(ox - wall_t, oy - wall_t, pad_r_top - wall_t,
                        floor_z, H + eps, fnx, fpx, fny, fpy, pad_height, H);
    }
}

// A storage bin of gx by gy cells, z_units tall.
//   wall_t  wall thickness; must stay below pad_r_top (3.75) or the interior
//           corner radius goes negative. The parameter manifest caps it at 3.0.
//   floor_t floor thickness above the base pads
//   lip     whether to cut the stacking lip into the top rim
module bin(gx, gy, z_units, wall_t, floor_t, lip) {
    H  = z_units * height_unit;
    ox = gx * cell_pitch / 2 - 4;
    oy = gy * cell_pitch / 2 - 4;
    floor_z = pad_height + floor_t;

    // Interior cavity stops below the lip when a lip is cut, otherwise it runs
    // clear through the top face. The eps carries it just into the lip cut so
    // the two cuts merge into one void instead of meeting on a shared plane.
    cavity_top = lip ? H - lip_height + eps : H + eps * 10;

    difference() {
        union() {
            cell_grid(gx, gy) bin_base_pad();
            translate([0, 0, pad_height]) rrect(ox, oy, pad_r_top, H - pad_height);
        }

        translate([0, 0, floor_z])
            rrect(ox, oy, pad_r_top - wall_t, cavity_top - floor_z);

        if (lip) {
            // Stacking lip, cut down from the top face. The flare stops at
            // lip_r_top (3.35) rather than pad_r_top (3.75), leaving a 0.4mm
            // flat top rim instead of a zero-thickness knife edge — a knife
            // edge risks degenerate triangles in ADMesh mesh validation, and
            // 0.4mm has no practical effect on stacking fit.
            //
            // The lip's deepest inset is thicker than a 1.6mm wall, leaving a
            // ~1.0mm downward-facing step underneath it. That is standard
            // Gridfinity and prints fine as a short bridge — do not "fix" it
            // by thickening the wall.
            rrect_taper(ox, oy, lip_r_bot,  H - lip_height,
                                lip_r_mid,  H - lip_z_mid);
            translate([0, 0, H - lip_z_mid - eps])
                rrect(ox, oy, lip_r_mid, lip_z_mid - lip_z_flare + 2 * eps);
            rrect_taper(ox, oy, lip_r_mid,  H - lip_z_flare,
                                lip_r_top,  H - lip_z_rim);
            translate([0, 0, H - lip_z_rim - eps])
                rrect(ox, oy, lip_r_top, lip_z_rim + eps + eps * 10);
        }
    }
}

// One piece of a bin too long for the print bed. The bin is split along X into
// `parts` equal pieces at cell boundaries and piece `index` is returned,
// re-centred on the origin for printing. Glue the pieces with CA; seat both on
// a baseplate first — the pads/sockets are the alignment jig, which is why the
// seam needs no printed alignment tabs. (It could not have them: below
// pad_height the split plane runs through the 0.5mm air gap between adjacent
// pads, so any tab there would be an unsupported overhang.)
module bin_part(gx, gy, z_units, wall_t, floor_t, lip, parts, index) {
    assert(gx % parts == 0, "bin_part: gx must be divisible by parts");
    assert(index >= 0 && index < parts, "bin_part: index out of range");
    W  = gx * cell_pitch;
    pw = W / parts;
    cx = -W / 2 + (index + 0.5) * pw;
    H  = z_units * height_unit;

    translate([-cx, 0, 0])
    intersection() {
        bin(gx, gy, z_units, wall_t, floor_t, lip);
        translate([cx, 0, H / 2])
            cube([pw, gy * cell_pitch + 20, H + 20], center = true);
    }
}
