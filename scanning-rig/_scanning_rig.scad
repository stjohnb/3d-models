// =====================================
// 3D Scanning Rig
// Hand-rotated turntable + generic leaning phone stand
// =====================================
// A fully printed photogrammetry rig for scanning small objects with a phone
// camera. Nothing non-printed is required — no bearings, no bolts.
//
// Turntable — two parts. The base carries a 45-degree V-ridge race ring plus a
// short centring spindle; the platter has the matching V-groove on its underside
// and a clearance bore over the spindle. Dropped together, the V pair and the
// spindle hold the platter concentric while it is turned by hand. The platter's
// flat underside rides on the flat top of the base plate; the V flanks are held
// race_clear / sqrt(2) (~0.21mm at the defaults) apart so the race locates the
// platter without binding on it. Tick marks every 360/tick_count degrees on the
// platter top line up against a raised pointer on the exposed base rim, so a
// scan can be stepped through even increments.
//
// Phone stand — a single side profile extruded along Z. That makes the exported
// STL already print-oriented (flat side face on the bed, every layer the same
// cross-section, so overhangs are impossible) and, because the profile's "up" is
// +Y, it also displays upright in the Y-up Three.js viewer with no rotation at
// all. The slot width is the main thing to customize: a bare iPhone 15 Pro is
// 8.25mm thick and most cases take it under 13mm, so the 14mm default holds
// either. The backrest is deliberately shorter than a phone's long edge so that
// in landscape the camera-bump corner overhangs past the stand rather than
// resting on the backrest and tipping the phone forward.
//
// This is a shared library — it defines parameters and modules only, and
// produces no top-level geometry. Render the sibling files instead.

$fn = 64;

// === Turntable parameters (mm) ===
platter_d   = 150;  // rotating platter diameter
base_d      = 166;  // base plate diameter — keep >= platter_d + 12 so the rim
                    // stays visible around the platter for the index pointer
base_t      = 6;    // base plate thickness
platter_t   = 8;    // platter thickness — must clear the groove apex by >= 3mm;
                    // below ~6mm the V-groove breaks through the top face, which
                    // is why platter_t is not exposed in the customizer manifest
race_r      = 55;   // V-race ring centreline radius — must match on both parts
ridge_h     = 4;    // V-ridge height; 45-degree flanks, so support-free
race_clear  = 0.3;  // groove-vs-ridge clearance
spindle_d   = 16;   // centring spindle diameter
spindle_up  = 7;    // spindle protrusion above the base top — stays 1mm below
                    // the platter top face at the default platter_t
bore_clear  = 0.3;  // platter bore radial clearance over the spindle
tick_count  = 24;   // rotation tick marks (24 => 15-degree steps)
grip_flutes = 60;   // finger-grip scallops around the platter rim

// === Phone stand parameters (mm unless noted) ===
slot_w         = 14;  // phone slot width: bare iPhone 15 Pro is 8.25, most cases <= 13
lean           = 15;  // backrest lean from vertical (degrees)
lip_h          = 14;  // front lip height above the slot floor
backrest_h     = 55;  // back support height above the slot floor
cradle_floor_t = 4;   // slot floor thickness
wall_t         = 5;   // lip and backrest thickness
stand_w        = 80;  // stand width / extrusion depth
foot_front     = 12;  // foot reach ahead of the cradle
foot_rear      = 78;  // foot reach behind the cradle (takes the lean-back load)
stand_base_t   = 7;   // foot plate thickness
port_gap_w     = 24;  // cable notch width through the lip and slot floor

// === Derived ===
groove_hw     = ridge_h + race_clear;    // V-groove half-width == depth (45 deg)
bore_d        = spindle_d + 2 * bore_clear;
pointer_outer = base_d / 2 - 2;          // pointer base, just inside the base rim
pointer_inner = pointer_outer - 5;       // pointer apex, aimed at the platter ticks
pointer_h     = 1.2;                     // raised height of the index pointer
pointer_w     = 6;                       // pointer width at its base

// Phone stand: the cradle is a U tipped back by 'lean'. Its floor spans
// slot_span along the slot, so tipping drops the floor's rear end cradle_drop
// below its front end — 6.2mm at the defaults, which is most of the foot plate's
// thickness. The cradle is therefore lifted clear of the foot by cradle_y and
// carried on a solid wedge (see stand_profile), rather than being sunk into the
// foot where the rear of the slot floor would disappear into it.
slot_span   = 2 * wall_t + slot_w;
cradle_drop = slot_span * sin(lean);
cradle_y    = stand_base_t - 1 + cradle_drop;

// === Turntable base ===
// Prints as-is, flat on the bed. The V-ridge flanks and the spindle are all
// self-supporting.
module turntable_base() {
    union() {
        cylinder(d = base_d, h = base_t);

        // 45-degree V-ridge race ring
        translate([0, 0, base_t])
            rotate_extrude()
                polygon([[race_r - ridge_h, 0],
                         [race_r + ridge_h, 0],
                         [race_r,           ridge_h]]);

        // Centring spindle, run up from z=0 so it is one solid body with the plate
        cylinder(d = spindle_d, h = base_t + spindle_up);

        // Index pointer on the exposed rim, apex aimed inward at the platter ticks
        translate([0, 0, base_t])
            linear_extrude(pointer_h)
                polygon([[pointer_outer, -pointer_w / 2],
                         [pointer_outer,  pointer_w / 2],
                         [pointer_inner,  0]]);
    }
}

// === Turntable platter ===
// Prints as-is, top face up. The V-groove opens downward, so its converging
// 45-degree walls print support-free.
module turntable_platter() {
    difference() {
        cylinder(d = platter_d, h = platter_t);

        // Underside V-groove — the ridge triangle grown by race_clear
        translate([0, 0, -0.01])
            rotate_extrude()
                polygon([[race_r - groove_hw, 0],
                         [race_r + groove_hw, 0],
                         [race_r,             groove_hw + 0.01]]);

        // Spindle bore
        translate([0, 0, -0.1])
            cylinder(d = bore_d, h = platter_t + 0.2);

        // Finger-grip scallops around the rim
        for (i = [0 : grip_flutes - 1])
            rotate([0, 0, i * 360 / grip_flutes])
                translate([platter_d / 2, 0, -0.1])
                    cylinder(d = 4, h = platter_t + 0.2);

        // Rotation ticks in the top face; the 0-degree reference notch is wider
        for (i = [0 : tick_count - 1])
            rotate([0, 0, i * 360 / tick_count])
                let (tick_w = (i == 0) ? 2.5 : 1)
                    translate([platter_d / 2 - 6, -tick_w / 2, platter_t - 1])
                        cube([8, tick_w, 1.1]);
    }
}

// === Phone stand ===
// Side profile in XY: +Y is up, +X is rearward (the direction the phone leans).
module stand_profile() {
    union() {
        // Foot plate
        translate([-foot_front, 0])
            square([foot_front + foot_rear, stand_base_t]);

        // Wedge carrying the cradle: bounded above by the tilted slot floor,
        // below by a strip sunk 1mm into the foot plate. The hull between the
        // two is the solid riser, so the slot floor stays perpendicular to the
        // slot across its whole width and the lip/backrest have material under
        // them everywhere. Every layer of the extrusion is identical, so no
        // part of this can overhang however steep the wedge gets.
        hull() {
            translate([0, cradle_y])
                rotate(-lean)
                    square([slot_span, cradle_floor_t]);
            translate([0, stand_base_t - 1])
                square([slot_span * cos(lean), 1]);
        }

        // Lip and backrest, in the cradle's tipped-back frame.
        // OpenSCAD's 2D rotate() is counter-clockwise, so the NEGATIVE angle
        // tips the top toward +X, out over the long rear foot. Flipping this
        // sign leans the phone over the short front foot and tips the stand.
        translate([0, cradle_y])
            rotate(-lean) {
                // front lip
                square([wall_t, cradle_floor_t + lip_h]);
                // back support
                translate([wall_t + slot_w, 0])
                    square([wall_t, cradle_floor_t + backrest_h]);
            }
    }
}

// Cross-section of the cable notch: the front lip and slot floor in the slot's
// own tipped-back frame. Its deepest point is the rear bottom corner, which lands
// at stand_base_t - 1 + 4*sin(lean) - 0.5*cos(lean) — never below ~5.8mm over the
// customizer's lean range, so a good 5mm of the 7mm foot plate always survives
// underneath and the notch cannot sever the foot.
module notch_profile() {
    translate([0, cradle_y])
        rotate(-lean)
            translate([-0.5, -0.5])
                square([wall_t + slot_w + 1, cradle_floor_t + lip_h + 2]);
}

module phone_stand() {
    difference() {
        linear_extrude(height = stand_w) stand_profile();

        // Cable notch, centred across the stand width
        translate([0, 0, (stand_w - port_gap_w) / 2])
            linear_extrude(height = port_gap_w) notch_profile();
    }
}
