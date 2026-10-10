// =====================================
// ha-carlink carrier PCB enclosure
// Two-part, fully printed under-dash enclosure for the ha-carlink carrier
// PCB v0.1 (St-John-Software/electronics, hardware/ha-carlink/; dimensions
// from docs/ha-carlink/PCB.md "Mechanical and enclosure"), fitted near a
// car's OBD-II port.
// =====================================
// Parts:
//   carlink_enclosure_base -> carlink_enclosure_base.stl
//       Tray: four M3 insert standoffs under the board's mounting holes, a
//       14500 cell trough along the -Y wall behind a divider rib (notched for
//       the cell lead to reach J2), a USB-C window in the +X wall, the OBD-II
//       wire slot in the -X wall and a cable-tie strain-relief shelf outside it.
//   carlink_enclosure_lid  -> carlink_enclosure_lid.stl
//       Plate with a locating lip, four long clamp bosses that press the
//       board onto its standoffs (one M3 x 30 countersunk screw each, into
//       the standoff insert) and a rib that keeps the cell in its trough.
//
// Orientation: Z-up. The base prints floor-down as exported. The lid is
// modelled outer-face-down (plate on the bed, lip, bosses and rib rising)
// and is turned over onto the base; see carlink_enclosure_lid().
//
// Layout frame: model X/Y are centred on the PCB, looking down at the
// component side with X right and Y up. Board-document coordinates (mm from
// the board's top-left corner, X right, Y DOWN) convert with bpos().
// The cell trough extends the cavity toward -Y, so the outer box is centred
// on cav_cy, not on the board.
//
// Every board figure comes from electronics docs/ha-carlink/PCB.md. VERIFY
// marks values that should be checked against the real board before the final
// print.

$fn = 64;

// === Carrier PCB v0.1 (mm) ===
pcb_l        = 100;    // outline along X
pcb_w        = 70;     // outline along Y
pcb_t        = 1.6;    // FR4
pcb_holes    = [[4, 4], [96, 4], [4, 66], [96, 66]];  // M3 centres, board frame
pcb_keepout_r = 3.5;   // parts-free radius round each hole: standoff/boss d <= 7
pcb_clear    = 0.5;    // board edge to cavity wall or divider rib, per side
above_pcb    = 22;     // clearance over the board top (TO-220, fuse, DevKitC)
below_pcb    = 3;      // clearance under the board for through-hole leads
usb_by       = 22.7;   // USB-C pair centre on the +X edge (board Y)
usb_span     = 26;     // window width along Y; DevKitC-1 is 28 wide (VERIFY)
usb_z0       = 6;      // window bottom above the board top (VERIFY)
usb_h        = 12;     // window height; both plugs' overmoulds (VERIFY)
obd_by0      = 27;     // J1 wire-entry span on the -X edge (board Y)
obd_by1      = 53;
obd_z0       = 0.5;    // slot bottom above the board top
obd_h        = 11;     // slot height; MKDS 1.5 wire entries sit 3-8 mm up (VERIFY)
jst_bx       = 53;     // J2 cell connector (board frame); cable exits upward
fuse_bx      = [10, 26];  // mini-blade fuse (board frame), reached by lifting the lid
fuse_by      = [5, 12];
antenna_bx   = [29.5, 36.8];  // DevKitC-1 antenna end: no metal here
antenna_by   = [14.5, 31];

// === Backup cell: 14500 LiFePO4 ===
cell_d       = 14.5;   // wrapped 14500 (VERIFY; nominal 14)
cell_l       = 50.5;   // (VERIFY; nominal 50)
trough_gap   = 1;      // trough is cell_d + gap wide and cell_l + gap long
rib_t        = 1.6;    // divider and end-stop rib thickness
lead_notch_w = 8;      // divider notch for the cell lead, centred on J2
lead_sill    = 2;      // notch floor above the board top
cell_retainer = true;  // lid rib over the trough that stops the cell lifting
retainer_gap = 0.5;    // rib underside to cell top

// === Enclosure ===
wall         = 2.4;
floor_t      = 3;
corner_r     = 3;      // outer vertical corner radius (inner corners stay sharp
                       // enough for the square board corners)
standoff_h   = 5;      // floor top to board underside (>= below_pcb)
standoff_d   = 7;      // == 2 * pcb_keepout_r
lid_t        = 2.4;
lip_t        = 1.6;
lip_d        = 4;
lip_clear    = 0.3;
boss_extra   = 0;      // shorten (negative) the lid bosses if the lid rim sits proud

// === Fixings: M3 heat-set insert in each standoff, one long screw per corner ===
insert_hole_d  = 4.0;  // 4.6 mm OD insert; 2.6 for a self-tapping M3 pilot
insert_depth   = 6;
insert_chamfer = 0.5;
screw_l        = 30;   // M3 x 30 countersunk (VERIFY length once printed)
screw_clear    = 3.4;
screw_head     = 6.8;

// === OBD-II strain relief: shelf outside the -X wall, cable tied down ===
shelf_l        = 20;   // shelf reach along -X
shelf_w        = 30;   // shelf width along Y, centred on the wire slot
cable_d        = 7;    // pigtail jacket (VERIFY)
tie_slot_l     = 6;    // slot length along X
tie_slot_w     = 2;    // slot width along Y (3.6 mm ties are 1.3 thick)
tie_pairs      = 2;    // tie positions along the shelf

// === Derived ===
function bpos(p) = [p[0] - pcb_l/2, pcb_w/2 - p[1]];   // board frame -> model
pcb_top    = floor_t + standoff_h + pcb_t;
inner_d    = standoff_h + pcb_t + above_pcb;           // floor top to lid underside
inner_l    = pcb_l + 2 * pcb_clear;
trough_w   = cell_d + trough_gap;
trough_l   = cell_l + trough_gap;
cav_y_top  = pcb_w/2 + pcb_clear;
rib_y      = -(pcb_w/2 + pcb_clear) - rib_t/2;         // divider rib centre
trough_cy  = rib_y - rib_t/2 - trough_w/2;
cav_y_bot  = trough_cy - trough_w/2;
inner_w    = cav_y_top - cav_y_bot;
cav_cy     = (cav_y_top + cav_y_bot)/2;
outer_l    = inner_l + 2 * wall;
outer_w    = inner_w + 2 * wall;
inner_r    = max(0.5, corner_r - wall);
base_h     = floor_t + inner_d;
rib_h      = trough_w;                                 // divider rib height above the floor
end_rib_h  = cell_d/2 + 2;
boss_h     = above_pcb + boss_extra;                   // lid underside to board top
retainer_h = inner_d - cell_d - retainer_gap;
trough_cx  = bpos([jst_bx, 0])[0];
usb_cy     = bpos([0, usb_by])[1];
obd_cy     = bpos([0, (obd_by0 + obd_by1)/2])[1];
obd_w      = obd_by1 - obd_by0 + 2;
tie_pitch  = cable_d + 2 * tie_slot_w + 1;             // slot centres straddle the cable
cs_h       = (screw_head - screw_clear)/2;

assert(standoff_h >= below_pcb, "standoff_h must give below_pcb under the board");
assert(standoff_d <= 2 * pcb_keepout_r, "standoffs intrude on the 3.5 mm hole keep-out");
assert(inner_r <= pcb_clear * sqrt(2) / (sqrt(2) - 1),
       "inner corner radius clips the PCB corners: lower corner_r or raise wall");
assert(insert_hole_d <= standoff_d - 2.5, "insert pocket leaves too thin a standoff wall");
assert(insert_depth <= standoff_h + floor_t - 1.5, "insert pocket breaks through the floor");
assert(screw_l >= lid_t + boss_h + pcb_t + 4 && screw_l <= lid_t + boss_h + pcb_t + insert_depth,
       "screw_l must reach 4 mm into the insert without bottoming out");
assert(cs_h < lid_t, "lid too thin for the countersink");
assert(usb_z0 + usb_h <= above_pcb, "USB window runs into the lid");
assert(obd_z0 + obd_h <= above_pcb, "OBD wire slot runs into the lid");
assert(obd_cy - obd_w/2 > cav_y_bot && obd_cy + obd_w/2 < cav_y_top, "OBD slot leaves the cavity");
assert(retainer_h > 2, "cell too tall for the cavity: lower cell_d or raise above_pcb");
assert(trough_cx - trough_l/2 > -inner_l/2 + rib_t && trough_cx + trough_l/2 < inner_l/2 - rib_t,
       "cell trough runs into the end walls");
assert(shelf_w >= obd_w, "strain-relief shelf narrower than the wire slot");
assert(tie_pitch + tie_slot_w + 2 <= shelf_w, "tie slots run off the shelf");
assert(tie_pairs * (tie_slot_l + 2) <= shelf_l, "too many tie pairs for shelf_l");
// No metal over the antenna end: every insert/screw position stays outside
// the keep-out rectangle by more than the standoff radius.
for (p = pcb_holes)
    assert(p[0] + standoff_d/2 < antenna_bx[0] || p[0] - standoff_d/2 > antenna_bx[1]
           || p[1] + standoff_d/2 < antenna_by[0] || p[1] - standoff_d/2 > antenna_by[1],
           "a fixing sits in the antenna keep-out");

// === Modules ===

// Rounded-rect vertical prism, centred on X/Y, base at z=0.
module rbox(l, w, h, r) {
    hull()
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * (l/2 - r), sy * (w/2 - r), 0])
                cylinder(r = r, h = h);
}

// Heat-set insert pocket running along -Z from its mouth at z=0.
module insert_hole(depth) {
    translate([0, 0, -depth]) cylinder(d = insert_hole_d, h = depth + 0.01);
    translate([0, 0, -insert_chamfer])
        cylinder(d1 = insert_hole_d, d2 = insert_hole_d + 2 * insert_chamfer,
                 h = insert_chamfer + 0.01);
}

module hole_positions() {
    for (p = pcb_holes) translate(bpos(p)) children();
}

// Cavity outline (used for the tray cut and the lid lip).
module cavity(l, w, h, r) {
    translate([0, cav_cy, 0]) rbox(l, w, h, r);
}

// Divider rib between the board zone and the trough, notched for the lead,
// plus the two trough end stops.
module trough_ribs() {
    translate([0, 0, floor_t - 0.01]) {
        difference() {
            translate([-inner_l/2 - 0.3, rib_y - rib_t/2, 0])
                cube([inner_l + 0.6, rib_t, rib_h + 0.01]);
            translate([trough_cx - lead_notch_w/2, rib_y - rib_t/2 - 1,
                       pcb_top + lead_sill - floor_t])
                cube([lead_notch_w, rib_t + 2, rib_h + 2]);
        }
        for (sx = [-1, 1])
            translate([trough_cx + sx * (trough_l/2 + rib_t/2) - rib_t/2,
                       trough_cy - trough_w/2 - 0.3, 0])
                cube([rib_t, trough_w + 0.6, end_rib_h + 0.01]);
    }
}

// Strain-relief shelf outside the -X wall, at floor level, with a shallow
// cable groove and cable-tie slot pairs straddling it.
module shelf() {
    x0 = -outer_l/2;
    difference() {
        translate([x0 - shelf_l, obd_cy - shelf_w/2, 0])
            cube([shelf_l + 1, shelf_w, floor_t]);
        // groove keys the jacket along X
        translate([x0 - shelf_l - 1, obd_cy, floor_t + cable_d/2 - 1])
            rotate([0, 90, 0]) cylinder(d = cable_d, h = shelf_l + 2);
        for (i = [0 : tie_pairs - 1], sy = [-1, 1])
            translate([x0 - shelf_l + 2 + i * (shelf_l - 2) / tie_pairs
                       + (shelf_l - 2) / (2 * tie_pairs) - tie_slot_l/2,
                       obd_cy + sy * tie_pitch/2 - tie_slot_w/2, -1])
                cube([tie_slot_l, tie_slot_w, floor_t + 2]);
    }
}

// Base tray: floor at z=0, opening toward +Z.
module carlink_enclosure_base() {
    difference() {
        union() {
            difference() {
                cavity(outer_l, outer_w, base_h, corner_r);
                translate([0, 0, floor_t]) cavity(inner_l, inner_w, inner_d + 1, inner_r);
            }
            hole_positions()
                translate([0, 0, floor_t - 0.01])
                    cylinder(d = standoff_d, h = standoff_h + 0.01);
            trough_ribs();
            shelf();
        }
        hole_positions()
            translate([0, 0, floor_t + standoff_h]) insert_hole(insert_depth);
        // USB-C window through the +X wall
        translate([inner_l/2 - 1, usb_cy - usb_span/2, pcb_top + usb_z0])
            cube([wall + 2, usb_span, usb_h]);
        // OBD-II wire slot through the -X wall
        translate([-inner_l/2 - wall - 1, obd_cy - obd_w/2, pcb_top + obd_z0])
            cube([wall + 2, obd_w, obd_h]);
    }
}

// Lid in the layout frame: outer face at z=0, features rising toward +Z.
module lid_frame() {
    difference() {
        union() {
            cavity(outer_l, outer_w, lid_t, corner_r);
            // Locating lip inside the cavity walls
            translate([0, 0, lid_t - 0.01])
                difference() {
                    cavity(inner_l - 2 * lip_clear, inner_w - 2 * lip_clear,
                           lip_d + 0.01, max(0.5, inner_r - lip_clear));
                    translate([0, 0, -1])
                        cavity(inner_l - 2 * (lip_clear + lip_t),
                               inner_w - 2 * (lip_clear + lip_t), lip_d + 3,
                               max(0.5, inner_r - lip_clear - lip_t));
                }
            // Clamp bosses down to the board top at the mounting holes
            hole_positions()
                translate([0, 0, lid_t - 0.01])
                    cylinder(d = standoff_d, h = boss_h + 0.01);
            // Cell retainer rib over the trough
            if (cell_retainer)
                translate([trough_cx - (trough_l - 2)/2, trough_cy - rib_t/2, lid_t - 0.01])
                    cube([trough_l - 2, rib_t, retainer_h + 0.01]);
        }
        // Countersunk lid screws, through the bosses
        hole_positions() {
            translate([0, 0, -1]) cylinder(d = screw_clear, h = lid_t + boss_h + 2);
            translate([0, 0, -0.01]) cylinder(d1 = screw_head, d2 = screw_clear, h = cs_h);
        }
    }
}

// Lid in print orientation. Turning the fitted lid over onto the bed is a
// 180 degree turn about X, which mirrors Y, so the trough rib and the
// off-centre lip line up with the base once the printed lid is flipped back.
module carlink_enclosure_lid() {
    mirror([0, 1, 0]) lid_frame();
}
