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
// scan can be stepped through even increments. Each tick is also engraved with
// its own numeral, since the tick/knurl texture alone is rotationally periodic
// and aliases photogrammetry feature matching between step-and-hold frames.
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
numerals    = true; // engrave a numeral in each tick sector (see below)
foot_pads      = true; // recess stick-on anti-slip pads into the base underside
foot_pad_d     = 12;   // pad recess diameter
foot_pad_depth = 1.2;  // pad recess depth (leaves 4.8mm of plate above it)
foot_pad_count = 3;    // three pads self-level on an uneven desk
foot_pad_r     = 62;   // pad centre radius — clear of the spindle and the V-race

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

// === Rig link parameters (mm unless noted) ===
// The link ties the turntable base to the phone stand so hand-turning cannot
// drag the base across the desk. Both ends are drop-in captures, so neither
// existing part changes shape. See docs/model-projects.md.
link_clear  = 0.4;  // radial clearance, collar bore vs base rim
collar_wall = 4;    // collar wall thickness
collar_wrap = 200;  // collar arc (degrees) — MUST stay > 180 for form closure
spar_w      = 16;   // spar width
spar_h      = 10;   // spar height
stand_gap   = 6;    // clear gap, collar OD to the dock's front face
stand_lift  = 25;   // dock floor height above the desk — sets camera elevation
dock_clear  = 0.5;  // pocket clearance per side around the stand foot
dock_wall   = 3;    // dock wall thickness
dock_ledge  = 5;    // ledge width the stand foot rests on
ledge_t     = 4;    // ledge thickness
kerb_h      = 5;    // kerb height above the dock floor (stand foot is 7mm)

// === Scan boost parameters (mm unless noted) ===
// Optional setback plinth (issues #436, #444). It stands on the desk directly
// behind the rig link's dock, straddling the dock's rear end so its distance
// from the turntable repeats between captures, and presents the same drop-in
// stand pocket boost_setback further back and boost_lift higher, pitched
// nose-down. Remove it and the stand drops straight back into the link's dock.
boost_setback = 120;  // pocket shift rearward from the dock's own pocket (#444)
boost_lift    = 20;   // pocket-floor rise above the dock floor, at the pocket front
boost_tilt    = 20;   // nose-down pitch handed to the docked stand (degrees)
boost_clear   = 0.35; // clearance, plinth vs the rig link's dock
boost_wall    = 3;    // shell wall thickness
boost_ledge   = 5;    // top ledge width the stand foot rests on
boost_kerb_h  = 6;    // kerb height above the pocket floor (stand foot is 7mm)
boost_grip    = 40;   // saddle arm length hugging the dock's outer side walls

// === Scan setback spacer parameters (mm unless noted) ===
// Optional second stage (issue #465). Even with the boost's 120mm setback the
// 150mm platter still spans ~77% of a 4K portrait frame and the base plate is
// clipped at both edges, so an object overhanging the platter leaves frame at
// some rotation angles. This spacer straddles the rig link's dock and presents
// a dock-shaped rail setback_shift further back; the scan boost's own saddle
// then grips that rail instead of the dock, moving the boost — and the camera —
// rearward by exactly setback_shift with height and pitch unchanged.
setback_shift = 100;  // extra setback handed to the scan boost (#465)
setback_wall  = 3;    // wall / floor thickness
setback_clear = 0.35; // clearance, spacer vs the rig link's dock
setback_grip  = 40;   // saddle arm length hugging the dock's outer side walls

// === Platter numeral parameters (mm) ===
// The platter rim is rotationally PERIODIC: knurl teeth and evenly-spaced ticks
// map onto themselves when the platter is stepped by one tick, so SIFT matches
// between step-and-hold frames alias (tooth N matches tooth N+1) and COLMAP's
// sparse model collapses or fragments. Measured on real captures (issue #414):
// a hold-only selection registered 2/47 frames; a hybrid selection fragmented
// into 5 models. A distinct numeral per sector makes every angular sector
// visually unique, and doubles as an operator-readable increment index.
//
// Glyphs are hand-built from 7-segment strokes rather than text(): the deployed
// openscad-wasm customizer ships no font bundle (scripts/fetch_openscad_wasm.py
// omits the 8.1MB openscad.fonts.js), so text() would render the numerals in
// CI's STL but silently drop them from any customizer download.
numeral_h      = 7;    // glyph cap height (radial extent)
numeral_w      = 4;    // per-digit cell width (tangential)
numeral_stroke = 1;    // segment thickness — >= 2 nozzle widths so it prints
numeral_kern   = 1;    // gap between the two digits of a 2-digit label
numeral_depth  = 0.5;  // engrave depth below the platter top face
numeral_gap    = 3;    // radial gap from the tick marks' inner edge

// === Derived ===
groove_hw     = ridge_h + race_clear;    // V-groove half-width == depth (45 deg)
bore_d        = spindle_d + 2 * bore_clear;
pointer_outer = base_d / 2 - 2;          // pointer base, just inside the base rim
pointer_inner = pointer_outer - 5;       // pointer apex, aimed at the platter ticks
pointer_h     = 1.2;                     // raised height of the index pointer
pointer_w     = 6;                       // pointer width at its base

collar_h     = base_t + 1;                       // 1mm proud, so anti-slip pads
                                                 // cannot lift the rim out of grip
collar_r_in  = base_d / 2 + link_clear;
collar_r_out = collar_r_in + collar_wall;
foot_len     = foot_front + foot_rear;
pocket_x     = foot_len + 2 * dock_clear;
pocket_y     = stand_w + 2 * dock_clear;
dock_x0      = collar_r_out + stand_gap;         // dock front face, on the +X axis
dock_x1      = dock_x0 + 2 * dock_wall + pocket_x;
dock_w       = pocket_y + 2 * dock_wall;
stand_origin_x = dock_x0 + dock_wall + dock_clear + foot_rear;  // docked stand's
                                                 // profile origin (assembly preview).
                                                 // Uses foot_rear, not foot_front: the
                                                 // assembly previews drop the stand in
                                                 // mirror([1, 0, 0])'d, so the long rear
                                                 // foot — not the cradle — lands against
                                                 // the dock's front wall. That puts the
                                                 // backrest (and a phone's camera, which
                                                 // rests against it) nearest the platter
                                                 // instead of facing away from it.

// Scan boost derived. The plinth's front face butts the dock's rear face, so
// boost_setback MUST leave the pocket front behind that face by at least
// boost_wall: boost_setback >= dock_wall + pocket_x + boost_clear + boost_wall
// (~97.35mm at the defaults). The customizer manifest floors boost_setback at
// 100 and deliberately exposes no slider that can push the requirement above
// that floor: foot_rear and dock_clear, which size pocket_x, are not offered
// on scan_boost, so the only term that still moves is boost_clear (max 1mm,
// giving 98mm worst case). boost_checks() below is the backstop for hand edits;
// it is called from scan_boost() rather than run here at top level, because
// rig_link and phone_stand include this library too and their own manifests do
// expose foot_rear / dock_clear — a top-level assert would fail their renders
// over a variable belonging to a part they never build.
dock_pocket_x0 = dock_x0 + dock_wall;             // the dock's own pocket front
boost_x0       = dock_pocket_x0 + boost_setback;  // boost pocket front, on the +X axis
boost_floor_z  = stand_lift + boost_lift;         // pocket floor at its front edge
boost_out_y    = pocket_y + 2 * boost_wall;       // plinth width, flush with the dock's
boost_body_x0  = dock_x1 + boost_clear;           // plinth front face
// Corbel under the pocket ledge. The corbel is cut in boost_local()'s tilted
// frame, so insetting boost_ledge over an equal boost_ledge of rise — 45
// degrees locally, the way rig_dock() does it in the global frame — would
// print at 45 + boost_tilt from vertical on the cavity's rear face (65 at the
// 20-degree default): a real overhang inside a closed cavity. Stretching the
// rise to boost_ledge * tan(45 + boost_tilt) lands that rear face at exactly
// 45 degrees GLOBALLY at any tilt, with the front face shallower still
// (45 - boost_tilt) and the two side faces under 34 degrees.
boost_corbel_rise = boost_ledge * tan(45 + boost_tilt);
boost_corbel_z    = ledge_t + boost_corbel_rise;  // corbel underside, below the floor
// Rear face: the tilt shifts the cavity's deepest point rearward by
// boost_corbel_z * sin(boost_tilt), so clear that before adding wall.
boost_body_x1  = boost_x0 + pocket_x * cos(boost_tilt)
                 + boost_corbel_z * sin(boost_tilt) + boost_wall;
boost_body_h   = boost_floor_z + (boost_body_x1 - boost_x0) * tan(boost_tilt)
                 + boost_kerb_h + 10;             // trimmed back by the kerb plane
boost_saddle_y = dock_w + 2 * (boost_clear + boost_wall);
boost_saddle_h = stand_lift + kerb_h;             // flush with the dock's top
boost_hole_x   = pocket_x - 2 * boost_ledge;
boost_hole_y   = pocket_y - 2 * boost_ledge;
// Front lip of the corbel's underside, in the global frame, and the front edge
// of the hollow core below it. The core closes in from the plinth's inner
// footprint to the pocket footprint; past a certain setback the plinth outruns
// the pocket by more than the corbel lip stands above the desk, and that
// ceiling flattens past 45 degrees. Starting the core no further forward than a
// 45-degree run down from the lip leaves the plinth's nose solid instead of
// unprintably roofed — the same trade rig_dock() documents when its own taper
// degenerates. At the 120mm default the clamp is inactive.
boost_lip_x    = boost_x0 + boost_corbel_z * sin(boost_tilt);
boost_lip_z    = boost_floor_z - boost_corbel_z * cos(boost_tilt);
boost_core_x0  = max(boost_body_x0 + boost_wall, boost_lip_x - boost_lip_z);
BOOST_BIG      = 600;                             // half-space / through-cut size

// Scan setback derived. The rail's outer side faces are dock_w apart and its
// top is flush with the dock's, so the boost's saddle grips it with exactly the
// geometry it was cut for. setback_shift is measured from the dock's rear face,
// which is also where the boost's saddle bottoms out, so the boost's shift is
// setback_shift exactly — the boost_clear slack at the butt joint is present in
// both configurations and cancels.
setback_saddle_y = dock_w + 2 * (setback_clear + setback_wall);
setback_h        = stand_lift + kerb_h;   // rail top, flush with the dock top
setback_rail_x0  = dock_x1 + setback_clear + setback_wall;  // rail front
setback_rail_x1  = dock_x1 + setback_shift;                 // rail rear = new stop

// Numerals sit just inside the tick band. The ticks are cubes spanning
// platter_d/2 - 6 .. platter_d/2 + 2 radially, so tick_inner_r is their inner
// edge and MUST stay in sync with the tick cube's translate() below.
tick_inner_r    = platter_d / 2 - 6;
numeral_outer_r = tick_inner_r - numeral_gap;   // glyph baseline radius
// Tangential arc available per tick at the glyph mid-radius, vs the widest
// label (two digits) plus a 1.5mm gutter. When tick_count crowds the ring,
// engrave every Nth tick instead of every tick.
numeral_pitch = 2 * PI * (numeral_outer_r - numeral_h / 2) / tick_count;
numeral_span  = 2 * numeral_w + numeral_kern + 1.5;
numeral_every = numeral_pitch >= numeral_span
                    ? 1 : ceil(numeral_span / numeral_pitch);

// Phone stand: the cradle is a U tipped back by 'lean'. Its floor spans
// slot_span along the slot, so tipping drops the floor's rear end cradle_drop
// below its front end — 6.2mm at the defaults, which is most of the foot plate's
// thickness. The cradle is therefore lifted clear of the foot by cradle_y and
// carried on a solid wedge (see stand_profile), rather than being sunk into the
// foot where the rear of the slot floor would disappear into it.
slot_span   = 2 * wall_t + slot_w;
cradle_drop = slot_span * sin(lean);
cradle_y    = stand_base_t - 1 + cradle_drop;

// === 7-segment numerals (no font dependency) ===
// Segment order [a, b, c, d, e, f, g] = top, upper-right, lower-right, bottom,
// lower-left, upper-left, middle. Standard seven-segment digit encodings.
seg_table = [
    [1,1,1,1,1,1,0], // 0
    [0,1,1,0,0,0,0], // 1
    [1,1,0,1,1,0,1], // 2
    [1,1,1,1,0,0,1], // 3
    [0,1,1,0,0,1,1], // 4
    [1,0,1,1,0,1,1], // 5
    [1,0,1,1,1,1,1], // 6
    [1,1,1,0,0,0,0], // 7
    [1,1,1,1,1,1,1], // 8
    [1,1,1,1,0,1,1]  // 9
];

// tick_count maxes out at 48 in the customizer manifest, so one or two digits.
function digits_of(n) = n < 10 ? [n] : [floor(n / 10), n % 10];

// 2D digit in a numeral_w x numeral_h cell with its origin at the bottom-left.
module digit_2d(d) {
    s = seg_table[d];
    W = numeral_w; H = numeral_h; t = numeral_stroke;
    union() {
        if (s[0]) translate([0,     H - t])       square([W, t]);
        if (s[1]) translate([W - t, (H - t) / 2]) square([t, (H + t) / 2]);
        if (s[2]) translate([W - t, 0])           square([t, (H + t) / 2]);
        if (s[3])                                 square([W, t]);
        if (s[4])                                 square([t, (H + t) / 2]);
        if (s[5]) translate([0,     (H - t) / 2]) square([t, (H + t) / 2]);
        if (s[6]) translate([0,     (H - t) / 2]) square([W, t]);
    }
}

// 2D label, horizontally centred on x = 0, sitting on the y = 0 baseline.
module number_2d(n) {
    ds = digits_of(n);
    total_w = len(ds) * numeral_w + (len(ds) - 1) * numeral_kern;
    for (k = [0 : len(ds) - 1])
        translate([-total_w / 2 + k * (numeral_w + numeral_kern), 0])
            digit_2d(ds[k]);
}

// All platter labels as ONE 2D shape. Every numeral lies in the same plane, so
// unioning in 2D and extruding once keeps difference() down to a single extra
// child instead of ~170 prisms. rotate(90) turns the glyph's +Y ("up") to point
// radially inward, so a numeral reads upright to an operator looking in over
// the base's index pointer at that tick.
module platter_numerals_2d() {
    for (i = [0 : tick_count - 1])
        if (i % numeral_every == 0)
            rotate(i * 360 / tick_count)
                translate([numeral_outer_r, 0])
                    rotate(90)
                        number_2d(i + 1);
}

// === Turntable base ===
// Prints as-is, flat on the bed. The V-ridge flanks and the spindle are all
// self-supporting.
module turntable_base() {
    difference() {
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

        // Anti-slip pad recesses in the underside (issue #434). They open
        // downward, so they print as a short 12mm bridge a couple of layers up.
        if (foot_pads)
            for (i = [0 : foot_pad_count - 1])
                rotate([0, 0, i * 360 / foot_pad_count])
                    translate([foot_pad_r, 0, -0.1])
                        cylinder(d = foot_pad_d, h = foot_pad_depth + 0.1);
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

        // Per-tick numerals engraved into the top face. Tick i is labelled
        // i + 1, so the widened 0-degree reference notch reads "1".
        if (numerals)
            translate([0, 0, platter_t - numeral_depth])
                linear_extrude(numeral_depth + 0.1)
                    platter_numerals_2d();
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

// === Rig link ===
// Prints flat on the bed as authored: every face is either vertical, a top
// face, or a 45-degree taper under the dock ledge, so nothing needs support.
module rig_dock() {
    hole_x  = pocket_x - 2 * dock_ledge;
    hole_y  = pocket_y - 2 * dock_ledge;
    ledge_z = stand_lift - ledge_t;
    taper_z = ledge_z - dock_ledge;
    difference() {
        translate([dock_x0, -dock_w / 2, 0])
            cube([dock_x1 - dock_x0, dock_w, stand_lift + kerb_h]);

        // Hollow core. Full pocket footprint at the bottom, tapering in at 45
        // degrees to the ledge footprint, so the ledge is corbelled rather than
        // bridged and the plinth stays a shell (52cm3 total, not 115, at the
        // 25mm default). Below stand_lift = ledge_t + dock_ledge (9mm) taper_z
        // goes negative, the lower cube is empty, and the hull degenerates to
        // the ledge plate alone — the plinth is then solid under the ledge
        // rather than shelled. That is deliberate: it costs filament, but a
        // shortened taper would inset dock_ledge over less than dock_ledge of
        // rise, i.e. a steeper-than-45-degree cavity overhang needing support.
        // The ledge itself is unaffected, so the foot still lands at stand_lift.
        union() {
            hull() {
                translate([dock_x0 + dock_wall, -pocket_y / 2, -0.1])
                    cube([pocket_x, pocket_y, taper_z + 0.1]);
                translate([dock_x0 + dock_wall + dock_ledge, -hole_y / 2, ledge_z - 0.01])
                    cube([hole_x, hole_y, 0.01]);
            }
            translate([dock_x0 + dock_wall + dock_ledge, -hole_y / 2, ledge_z - 0.01])
                cube([hole_x, hole_y, stand_lift + kerb_h + 0.2]);
        }

        // Foot pocket: the phone stand's foot plate drops in here.
        translate([dock_x0 + dock_wall, -pocket_y / 2, stand_lift])
            cube([pocket_x, pocket_y, kerb_h + 0.1]);
    }
}

module rig_link() {
    union() {
        // Collar around the turntable base rim. The wrap exceeds 180 degrees,
        // so the base is captured in-plane and can only be lifted straight out.
        // The mouth faces -X, away from the stand, leaving the platter reachable.
        rotate([0, 0, -collar_wrap / 2])
            rotate_extrude(angle = collar_wrap)
                translate([collar_r_in, 0])
                    square([collar_wall, collar_h]);

        // Spar, desk level. Overlaps 1mm into the collar and runs through the
        // dock's front wall so both joints are solid.
        translate([collar_r_out - 1, -spar_w / 2, 0])
            cube([dock_x0 - collar_r_out + 1 + dock_wall, spar_w, spar_h]);

        rig_dock();
    }
}

// === Scan boost ===
// Prints as authored, flat on the bed: the plinth and saddle walls are all
// vertical off the bed, the hollow core closes in at 45 degrees or less going
// up — measured in the print frame, not in boost_local()'s tilted one, which is
// why the corbel's rise is boost_corbel_rise rather than boost_ledge — and
// every tilted face is an upward-facing top face. Nothing hangs downward, so no
// supports.
//
// The plinth stands on the desk behind the rig link's dock rather than plugging
// into it (#444): at a 120mm setback the loaded stand's centre of mass sits well
// behind the rig's own desk footprint, and a plug in the dock pocket could not
// resist that couple — it would rock back and lift out. The saddle only locates
// the plinth; the desk carries the load.
//
// boost_local() is the tilted frame of the boost's pocket: local z = 0 is the
// pocket floor plane, local +x runs rearward (away from the turntable) and
// rises at boost_tilt, so the docked stand pitches nose-down toward the platter.
module boost_local() {
    translate([boost_x0, 0, boost_floor_z])
        rotate([0, -boost_tilt, 0])
            children();
}

// Geometry preconditions for scan_boost(). Deliberately a module called from
// scan_boost() rather than top-level asserts: the checks constrain the boost's
// own geometry only, and the other parts in this library must stay renderable
// across their own manifests' ranges.
module boost_checks() {
    assert(boost_setback >= dock_wall + pocket_x + boost_clear + boost_wall,
           "boost_setback too small for the current pocket/clearance settings");
    assert(boost_tilt >= 0 && boost_tilt < 45,
           "boost_tilt must be at least 0 and under 45 degrees");
}

module scan_boost() {
    boost_checks();

    difference() {
        union() {
            // Saddle — a U in plan view dropped over the dock's rear end. The
            // cross wall butts the dock's rear face (setting camera distance),
            // the arms hug its outer side walls (setting Y, blocking yaw).
            difference() {
                translate([dock_x1 - boost_grip, -boost_saddle_y / 2, 0])
                    cube([boost_grip + boost_clear + boost_wall,
                          boost_saddle_y, boost_saddle_h]);
                translate([dock_x1 - boost_grip - 1, -(dock_w / 2 + boost_clear), -1])
                    cube([boost_grip + boost_clear + 1,
                          dock_w + 2 * boost_clear, boost_saddle_h + 2]);
            }

            // Plinth, trimmed by the tilted kerb-top plane.
            intersection() {
                translate([boost_body_x0, -boost_out_y / 2, 0])
                    cube([boost_body_x1 - boost_body_x0, boost_out_y, boost_body_h]);
                boost_local()
                    translate([-BOOST_BIG / 2, -BOOST_BIG / 2, boost_kerb_h - BOOST_BIG])
                        cube(BOOST_BIG);
            }
        }

        // Foot pocket — same pocket_x x pocket_y as the dock's, so the same
        // stand foot drops in. Gravity settles the tilted foot against the
        // downhill (front) kerb wall; the fore-aft slack lands at the rear.
        boost_local()
            translate([0, -pocket_y / 2, 0])
                cube([pocket_x, pocket_y, BOOST_BIG]);

        // Hollow core, open to the desk. Rises from the plinth's inner
        // footprint (front edge clamped by boost_core_x0 so this ceiling stays
        // at or under 45 degrees), closes in to the pocket footprint under the
        // ledge, then corbels in again to the hole footprint — the same trick
        // rig_dock() uses, so the ledge is corbelled rather than bridged. The
        // corbel's rise is boost_corbel_rise, not boost_ledge: it is cut in the
        // tilted frame, so a 45-degree local corbel would print at
        // 45 + boost_tilt globally. See the derived block.
        union() {
            hull() {
                translate([boost_core_x0, -pocket_y / 2, -0.1])
                    cube([boost_body_x1 - boost_wall - boost_core_x0,
                          pocket_y, 0.01]);
                boost_local()
                    translate([0, -pocket_y / 2, -boost_corbel_z])
                        cube([pocket_x, pocket_y, 0.01]);
            }
            boost_local()
                hull() {
                    translate([0, -pocket_y / 2, -boost_corbel_z])
                        cube([pocket_x, pocket_y, 0.01]);
                    translate([boost_ledge, -boost_hole_y / 2, -ledge_t - 0.01])
                        cube([boost_hole_x, boost_hole_y, 0.01]);
                }
            boost_local()
                translate([boost_ledge, -boost_hole_y / 2, -ledge_t])
                    cube([boost_hole_x, boost_hole_y, BOOST_BIG]);
        }
    }
}

// === Scan setback spacer ===
// Prints flat on the bed as authored: floor plate on the bed, every wall
// vertical off it, open top. Nothing bridges and nothing hangs, so no supports.
//
// It carries no load — the rig link and the boost both stand on the desk on
// their own. Its only jobs are to fix the boost's distance (rail rear face is a
// hard stop) and to keep the boost tied to the link, so the whole rig still
// slides as one body and scan_masks.py's single fixed platter ellipse stays
// valid (issue #434).

// Geometry precondition for scan_setback(). A module called from
// scan_setback() rather than a top-level assert, for the same reason
// boost_checks() is: the other parts in this library must stay renderable
// across their own manifests' ranges.
module setback_checks() {
    assert(setback_shift >= setback_clear + 2 * setback_wall + boost_grip,
           "setback_shift too small for the scan boost's saddle to grip the rail");
}

module scan_setback() {
    setback_checks();

    union() {
        // Saddle over the dock's rear end — the same grip the boost's saddle
        // uses: cross wall butts the dock's rear face, arms hug its side walls.
        difference() {
            translate([dock_x1 - setback_grip, -setback_saddle_y / 2, 0])
                cube([setback_grip + setback_clear + setback_wall,
                      setback_saddle_y, setback_h]);
            translate([dock_x1 - setback_grip - 1, -(dock_w / 2 + setback_clear), -1])
                cube([setback_grip + setback_clear + 1,
                      dock_w + 2 * setback_clear, setback_h + 2]);
        }

        // Rail — an open-top channel the same outer width and height as the
        // dock, so the boost cannot tell the difference. Floor plate on the
        // desk ties the two side walls together and keeps the channel square.
        translate([setback_rail_x0, -dock_w / 2, 0])
            cube([setback_rail_x1 - setback_rail_x0, dock_w, setback_wall]);
        for (m = [0, 1])
            mirror([0, m, 0])
                translate([setback_rail_x0, dock_w / 2 - setback_wall, 0])
                    cube([setback_rail_x1 - setback_rail_x0, setback_wall, setback_h]);

        // Rear end wall — the boost's new stop face, and the rail's stiffener.
        translate([setback_rail_x1 - setback_wall, -dock_w / 2, 0])
            cube([setback_wall, dock_w, setback_h]);
    }
}
