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
platter_d   = 222;  // rotating platter diameter
base_d      = 238;  // base plate diameter — keep >= platter_d + 12 so the rim
                    // stays visible around the platter for the index pointer
base_t      = 6;    // base plate thickness
platter_t   = 8;    // platter thickness — must clear the groove apex by >= 3mm;
                    // below ~6mm the V-groove breaks through the top face, which
                    // is why platter_t is not exposed in the customizer manifest
race_r      = 82;   // V-race ring centreline radius — must match on both parts
ridge_h     = 4;    // V-ridge height; 45-degree flanks, so support-free
race_clear  = 0.4;  // groove-vs-ridge clearance
spindle_d   = 20;   // centring spindle diameter
spindle_up  = 7;    // spindle protrusion above the base top — stays 1mm below
                    // the platter top face at the default platter_t
bore_clear  = 0.3;  // platter bore radial clearance over the spindle
tick_count  = 24;   // rotation tick marks (24 => 15-degree steps)
grip_flutes = 88;   // finger-grip scallops around the platter rim
numerals    = true; // engrave a numeral in each tick sector (see below)
foot_pads      = true; // recess stick-on anti-slip pads into the base underside
foot_pad_d     = 12;   // pad recess diameter
foot_pad_depth = 1.2;  // pad recess depth (leaves 4.8mm of plate above it)
foot_pad_count = 3;    // three pads self-level on an uneven desk
foot_pad_r     = 100;  // pad centre radius — clear of the spindle and the V-race

// Anti-rotation keys (issue #468). Two notches in the base rim take two ribs on
// the rig link's collar bore, so hand-turning the platter cannot twist the base
// inside the collar. Both parts derive them from these SAME variables, and
// neither customizer manifest exposes them, so they cannot drift apart.
key_angle = 60;   // key centre, degrees off +X — clear of the index pointer at 0
key_w     = 14;   // key width, tangential
key_depth = 4;    // key depth, radially into the base rim
key_clear = 0.35; // per-face clearance, rib vs notch

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
// drag the base across the desk. The collar end is a drop-in capture, keyed
// against rotation; the far end is a low open-top rail that the scan boost (or
// the setback spacer) drops its saddle over. The link carries no stand pocket —
// the stand always mounts on the scan boost (#468). See docs/model-projects.md.
link_clear  = 0.5;  // radial clearance, collar bore vs base rim
collar_wall = 4;    // collar wall thickness
collar_wrap = 200;  // collar arc (degrees) — MUST stay > 180 for form closure
spar_w      = 16;   // spar width
spar_h      = 10;   // spar height
stand_gap   = 6;    // clear gap, collar OD to the rail's front face
rail_w    = 40;  // rail outer width — the boost/setback saddles grip these faces
rail_h    = 12;  // rail height above the desk
rail_len  = 97;  // rail length; its REAR face is the boost's stop. rail_x1 is
                 // derived from collar_r_out, not frozen — see cam_run0.
rail_wall = 3;   // floor / wall thickness

// === Scan boost parameters (mm unless noted) ===
// Optional setback plinth (issues #436, #444, #468). It stands on the desk
// directly behind the rig link's rail, straddling the rail's rear end so its
// distance from the turntable repeats between captures, and carries the only
// drop-in stand pocket in the rig, boost_setback behind that rail and with its
// floor an absolute boost_floor_h above the desk, pitched nose-down.
boost_setback = 26;   // pocket front behind the rail's REAR face; see boost_x0
                      // and cam_run0 for where that puts the camera.
boost_floor_h = 90;   // pocket floor height above the desk at the pocket front.
                      // This is the boost's OWN baseline height. The 222mm
                      // platter (#486) needs a camera roughly 300mm above the
                      // platter top; putting 45mm of that into this wide
                      // desk-borne plinth keeps riser_h inside its existing
                      // manifest ceiling rather than needing a ~200mm tower.
                      // Fit scan_riser on top of it for the camera-elevation
                      // correction; see riser_checks() for the combined
                      // prediction. Boost alone this is only ~34 degrees
                      // (ry/rx ~0.55), under the 0.64 floor below which
                      // low-texture objects stop registering — the riser is not
                      // optional equipment.
boost_tilt    = 20;   // nose-down pitch handed to the docked stand (degrees)
boost_clear   = 0.35; // clearance, plinth vs the rig link's rail
dock_clear    = 0.5;  // stand-foot pocket clearance per side (scan boost)
ledge_t       = 4;    // ledge thickness
boost_wall    = 3;    // shell wall thickness
boost_ledge   = 5;    // top ledge width the stand foot rests on
boost_kerb_h  = 6;    // kerb height above the pocket floor (stand foot is 7mm)
boost_grip    = 40;   // saddle arm length hugging the rail's outer side walls

// === Scan setback spacer parameters (mm unless noted) ===
// A spacer (issue #465). Even with the boost's setback the 222mm platter
// still spans ~79% of a 4K portrait frame and the base plate is clipped at
// both edges, so an object overhanging the platter leaves frame at some
// rotation angles. This spacer straddles the rig link's rail and presents a
// matching rail setback_shift further back; the scan boost's own saddle then
// grips that rail instead of the link's, moving the boost — and the camera —
// rearward by exactly setback_shift with height and pitch unchanged. At the
// 222mm platter (#486) it is required for framing, not optional.
setback_shift = 135;  // extra setback handed to the scan boost (#465, halved in
                      // #468, re-derived for #486). 135 with the scan_riser
                      // fitted at its default riser_h gives a 460mm slant
                      // range at ry/rx 0.66 — parity with the pre-#486 63%
                      // framing. See riser_checks().
setback_wall  = 3;    // wall / floor thickness
setback_clear = 0.35; // clearance, spacer vs the rig link's rail
setback_grip  = 40;   // saddle arm length hugging the rail's outer side walls

// === Scan riser parameters (mm unless noted) ===
// Height-only correction (issue #468 review): rather than redesign the scan
// boost's own plinth height — which would obsolete whatever boost the user
// has already printed — this drops into the boost's EXISTING foot pocket
// exactly where the phone stand's foot sits today, and re-presents an
// identical pocket riser_h further up the SAME boost_tilt ramp, for the phone
// stand to drop into instead. The boost itself does not change shape.
riser_h      = 140; // added height, boost's pocket floor to the riser's own
                    // pocket floor, along boost_local()'s tilted Z. See
                    // riser_checks() for the resulting camera-elevation
                    // prediction.
riser_wall   = 3;   // wall thickness around the new pocket
riser_kerb_h = 6;   // kerb height above the riser's pocket floor (stand foot
                    // is 7mm)

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
numeral_h      = 10;   // glyph cap height (radial extent)
numeral_w      = 6;    // per-digit cell width (tangential)
numeral_stroke = 1.5;  // segment thickness — >= 2 nozzle widths so it prints
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
rail_x0      = collar_r_out + stand_gap;         // rail front face, on the +X axis
rail_x1      = rail_x0 + rail_len;               // rail rear face — the boost's stop
stand_pocket_x = dock_clear + foot_rear;         // docked stand's profile origin,
                                                 // measured from the pocket front and
                                                 // mirrored, so the long rear foot —
                                                 // not the cradle — lands against the
                                                 // pocket's front wall. That puts the
                                                 // backrest (and a phone's camera,
                                                 // which rests against it) nearest the
                                                 // platter instead of facing away.

// Scan boost derived. boost_setback is measured from the rail's REAR face,
// which is also where the plinth's own front face lands, so the pocket front
// must clear that face by boost_clear + boost_wall.
// boost_checks() below is the backstop for hand edits; it is called from
// scan_boost() rather than run here at top level, because rig_link and
// phone_stand include this library too and a top-level assert would fail their
// renders over a variable belonging to a part they never build.
boost_x0       = rail_x1 + boost_setback;         // boost pocket front, on the +X axis

// Calibrated camera model (#468 review, re-derived for #486). The phone's rear
// camera sits cam_z_lead above the boost's pocket floor and cam_x_lead behind
// the pocket front; the platter top is base_t + platter_t above the desk. Both
// leads are stand geometry, not rig size, so they survive the scale-up — but
// the run must be derived from boost_x0, never frozen at the old 222.4.
cam_x_lead = 6;
cam_z_lead = 96;
cam_run0   = boost_x0 + cam_x_lead;                            // 258.5 at defaults
cam_rise0  = boost_floor_h + cam_z_lead - base_t - platter_t;  // 172 at defaults

// Framing. tan(half the 4K portrait horizontal FOV, 41.6 deg), back-solved from
// the #465 measurement: the 150mm platter filled ~77% of frame width at the
// 256mm boost-alone slant. Fit the setback spacer while the fraction is above
// ~0.60 — see playbooks/scan_a_capture.md. This lived only in prose before
// #486, which is how a platter scale-up could silently outgrow the frame.
cam_fov_tan = 0.3803;
function cam_frame_frac(rise, run) =
    platter_d / (2 * cam_fov_tan * sqrt(rise * rise + run * run));

boost_floor_z  = boost_floor_h;                   // pocket floor at its front edge
boost_out_y    = pocket_y + 2 * boost_wall;       // plinth width
boost_body_x0  = rail_x1 + boost_clear;           // plinth front face
// Corbel under the pocket ledge. The corbel is cut in boost_local()'s tilted
// frame, so insetting boost_ledge over an equal boost_ledge of rise — 45
// degrees locally, the way an untilted corbel would in the global frame — would
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
boost_saddle_y = rail_w + 2 * (boost_clear + boost_wall);
boost_saddle_h = rail_h;                          // flush with the rail's top
boost_hole_x   = pocket_x - 2 * boost_ledge;
boost_hole_y   = pocket_y - 2 * boost_ledge;
// Front lip of the corbel's underside, in the global frame, and the front edge
// of the hollow core below it. The core closes in from the plinth's inner
// footprint to the pocket footprint; past a certain setback the plinth outruns
// the pocket by more than the corbel lip stands above the desk, and that
// ceiling flattens past 45 degrees. Starting the core no further forward than a
// 45-degree run down from the lip leaves the plinth's nose solid instead of
// unprintably roofed. At the shipped defaults the clamp is inactive.
boost_lip_x    = boost_x0 + boost_corbel_z * sin(boost_tilt);
boost_lip_z    = boost_floor_z - boost_corbel_z * cos(boost_tilt);
boost_core_x0  = max(boost_body_x0 + boost_wall, boost_lip_x - boost_lip_z);
BOOST_BIG      = 600;                             // half-space / through-cut size

// Scan setback derived. The spacer's rail repeats the link's rail exactly —
// same rail_w across the outer side faces, same rail_h top — so the boost's
// saddle grips it with exactly the geometry it was cut for. setback_shift is
// measured from the link rail's rear face, which is also where the boost's
// saddle bottoms out, so the boost's shift is setback_shift exactly — the
// boost_clear slack at the butt joint is present in both configurations and
// cancels.
setback_saddle_y = rail_w + 2 * (setback_clear + setback_wall);
setback_h        = rail_h;                // rail top, flush with the link rail's
setback_rail_x0  = rail_x1 + setback_clear + setback_wall;  // rail front
setback_rail_x1  = rail_x1 + setback_shift;                 // rail rear = new stop

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

        // Anti-rotation key notches (#468) — vertical prisms through the full
        // plate thickness, so the base still lifts straight out of the collar.
        for (m = [0, 1])
            mirror([0, m, 0])
                rotate([0, 0, key_angle])
                    translate([base_d / 2 - key_depth, -key_w / 2, -0.1])
                        cube([key_depth + 1, key_w, base_t + 0.2]);
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
// Prints flat on the bed as authored: every face is either vertical or a top
// face, so nothing needs support.

// Open-top channel — the same outer section scan_setback presents, because both
// are gripped by the same saddle. Floor on the bed, walls vertical off it, top
// open: nothing bridges, so no supports. No stand pocket: the stand always
// mounts on scan_boost (#468).
module rig_rail() {
    translate([rail_x0, -rail_w / 2, 0]) cube([rail_len, rail_w, rail_wall]);
    for (m = [0, 1])
        mirror([0, m, 0])
            translate([rail_x0, rail_w / 2 - rail_wall, 0])
                cube([rail_len, rail_wall, rail_h]);
    // End walls: the front takes the spar, the rear is the boost's stop face.
    translate([rail_x0, -rail_w / 2, 0]) cube([rail_wall, rail_w, rail_h]);
    translate([rail_x1 - rail_wall, -rail_w / 2, 0]) cube([rail_wall, rail_w, rail_h]);
}

// Geometry preconditions for rig_link(). A module called from rig_link() rather
// than a top-level assert, for the same reason boost_checks() is.
module link_checks() {
    assert(key_angle > 0 && key_angle + 15 < collar_wrap / 2,
           "key_angle must sit well inside the collar's wrap");
    assert(base_d / 2 - key_depth > platter_d / 2 + 1,
           "key notch must stay outside the platter rim");
}

module rig_link() {
    link_checks();

    union() {
        // Collar around the turntable base rim. The wrap exceeds 180 degrees,
        // so the base is captured in-plane and can only be lifted straight out.
        // The mouth faces -X, away from the stand, leaving the platter reachable.
        rotate([0, 0, -collar_wrap / 2])
            rotate_extrude(angle = collar_wrap)
                translate([collar_r_in, 0])
                    square([collar_wall, collar_h]);

        // Key ribs — mirror image of the base's notches, key_clear per face
        // tangentially and link_clear radially (collar_r_in - key_depth is
        // link_clear outboard of the notch floor at base_d/2 - key_depth). Do
        // not "tidy" either expression.
        for (m = [0, 1])
            mirror([0, m, 0])
                rotate([0, 0, key_angle])
                    translate([collar_r_in - key_depth, -(key_w / 2 - key_clear), 0])
                        cube([key_depth + collar_wall, key_w - 2 * key_clear, collar_h]);

        // Spar, desk level. Overlaps 1mm into the collar and runs through the
        // rail's front end wall so both joints are solid.
        translate([collar_r_out - 1, -spar_w / 2, 0])
            cube([rail_x0 - collar_r_out + 1 + rail_wall, spar_w, spar_h]);

        rig_rail();
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
// The plinth stands on the desk behind the rig link's rail rather than plugging
// into it (#444): the loaded stand's centre of mass sits well behind the rig's
// own desk footprint, and a plug in a pocket could not resist that couple — it
// would rock back and lift out. The saddle only locates the plinth; the desk
// carries the load.
//
// This is now the rig's ONLY stand mount (#468) — the link's old dock is gone —
// and boost_floor_h is an absolute height above the desk rather than a lift
// above a dock floor, because it is what sets the camera's elevation angle.
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
    assert(boost_setback >= boost_clear + boost_wall,
           "boost_setback too small to clear the plinth's own front wall");
    assert(boost_floor_h > boost_corbel_z,
           "boost_floor_h too small to fit the pocket's corbel above the desk");
    assert(boost_tilt >= 0 && boost_tilt < 45,
           "boost_tilt must be at least 0 and under 45 degrees");
    // Predicted camera elevation (#468), for the setback spacer fitted at the
    // current setback_shift — set setback_shift = 0 to read the boost-alone
    // figure. Calibrated against a measured roi-preview ellipse; a prediction,
    // not a guarantee — always confirm on roi-preview.jpg.
    echo(str("scan_boost: predicted elevation ",
             atan(cam_rise0 / (cam_run0 + setback_shift)),
             " deg with the setback spacer at ", setback_shift,
             "mm, ry/rx ", sin(atan(cam_rise0 / (cam_run0 + setback_shift))),
             ", platter fills ", cam_frame_frac(cam_rise0, cam_run0 + setback_shift),
             " of frame width"));
}

module scan_boost() {
    boost_checks();

    difference() {
        union() {
            // Saddle — a U in plan view dropped over the rail's rear end. The
            // cross wall butts the rail's rear face (setting camera distance),
            // the arms hug its outer side walls (setting Y, blocking yaw).
            difference() {
                translate([rail_x1 - boost_grip, -boost_saddle_y / 2, 0])
                    cube([boost_grip + boost_clear + boost_wall,
                          boost_saddle_y, boost_saddle_h]);
                translate([rail_x1 - boost_grip - 1, -(rail_w / 2 + boost_clear), -1])
                    cube([boost_grip + boost_clear + 1,
                          rail_w + 2 * boost_clear, boost_saddle_h + 2]);
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

        // Foot pocket — pocket_x x pocket_y, sized to the phone stand's foot.
        // Gravity settles the tilted foot against the downhill (front) kerb
        // wall; the fore-aft slack lands at the rear.
        boost_local()
            translate([0, -pocket_y / 2, 0])
                cube([pocket_x, pocket_y, BOOST_BIG]);

        // Hollow core, open to the desk. Rises from the plinth's inner
        // footprint (front edge clamped by boost_core_x0 so this ceiling stays
        // at or under 45 degrees), closes in to the pocket footprint under the
        // ledge, then corbels in again to the hole footprint, so the ledge is
        // corbelled rather than bridged. The
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
// It drops its saddle over the rig link's rail and presents an identical rail
// setback_shift further back. It carries no load — the rig link and the boost
// both stand on the desk on their own. Its only jobs are to fix the boost's
// distance (rail rear face is a hard stop) and to keep the boost tied to the
// link, so the whole rig still
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
        // Saddle over the link rail's rear end — the same grip the boost's
        // saddle uses: cross wall butts the rail's rear face, arms hug its
        // side walls.
        difference() {
            translate([rail_x1 - setback_grip, -setback_saddle_y / 2, 0])
                cube([setback_grip + setback_clear + setback_wall,
                      setback_saddle_y, setback_h]);
            translate([rail_x1 - setback_grip - 1, -(rail_w / 2 + setback_clear), -1])
                cube([setback_grip + setback_clear + 1,
                      rail_w + 2 * setback_clear, setback_h + 2]);
        }

        // Rail — an open-top channel the same outer width and height as the
        // rig link's, so the boost cannot tell the difference. Floor plate on
        // the desk ties the two side walls together and keeps the channel square.
        translate([setback_rail_x0, -rail_w / 2, 0])
            cube([setback_rail_x1 - setback_rail_x0, rail_w, setback_wall]);
        for (m = [0, 1])
            mirror([0, m, 0])
                translate([setback_rail_x0, rail_w / 2 - setback_wall, 0])
                    cube([setback_rail_x1 - setback_rail_x0, setback_wall, setback_h]);

        // Rear end wall — the boost's new stop face, and the rail's stiffener.
        translate([setback_rail_x1 - setback_wall, -rail_w / 2, 0])
            cube([setback_wall, rail_w, setback_h]);
    }
}

// === Scan riser ===
// Prints flat on the bed as authored: floor plate on the bed, every wall
// vertical off it, open top. Solid rather than shelled like the boost and the
// setback spacer — the boost's own hollow core stays open all the way down to
// the desk (see scan_boost()), so its "roof" is only ever the corbelled ledge
// under the pocket. A shelled riser would instead need a fully-enclosed
// floor plate roofing its own cavity, spanning the tower's whole footprint
// with nothing under it: an unsupported bridge, not a corbel. Solid avoids
// that outright; slicer infill settings, not this source model, are what
// actually control how much plastic a solid region prints with.
//
// Authored in its OWN flat frame, not boost_local()'s tilted one: the boost's
// pocket floor is already flat within that tilted frame (the same reason the
// phone stand's foot drops in flush today), so a flat-bottomed riser seats
// against it regardless of boost_tilt, and the riser itself still prints
// upright rather than at boost_tilt off the bed. Its seat spur reproduces the
// phone stand's own foot footprint exactly, so it drops into the boost's
// existing pocket the same way the stand does today; its own new pocket,
// riser_h above that seat, then takes the stand instead.
module scan_riser() {
    riser_checks();

    difference() {
        union() {
            // Seat spur — the phone stand's own foot footprint, so it drops
            // into the boost's existing pocket exactly as the stand does
            // today: flush with the pocket floor, 1mm proud of the kerb.
            translate([0, -stand_w / 2, 0])
                cube([foot_len, stand_w, stand_base_t]);

            // Tower, offset out by riser_wall on every side for its own
            // pocket's straight walls. A short (riser_wall + dock_clear) step
            // up from the spur — well within an FDM printer's self-supporting
            // overhang span, so this prints without support like the rest of
            // the rig.
            translate([-riser_wall, -stand_w / 2 - riser_wall, stand_base_t])
                cube([foot_len + 2 * riser_wall, stand_w + 2 * riser_wall,
                      riser_h + riser_kerb_h - stand_base_t]);
        }

        // New open-top pocket for the phone stand's foot, riser_h above the
        // boost's own pocket floor — the camera-elevation correction (#468
        // review). Same per-side dock_clear the boost's own pocket gives the
        // foot, riser_kerb_h kerb holds it 1mm proud, same fit as today.
        translate([-dock_clear, -stand_w / 2 - dock_clear, riser_h])
            cube([foot_len + 2 * dock_clear, stand_w + 2 * dock_clear,
                  riser_kerb_h + BOOST_BIG]);
    }
}

// Geometry precondition for scan_riser(). A module called from scan_riser()
// rather than a top-level assert, for the same reason boost_checks() is.
module riser_checks() {
    assert(riser_h > stand_base_t,
           "riser_h too small to clear the seat spur it stands on");
    // Predicted camera elevation with the riser fitted (#468 review). The
    // riser adds height along the boost's own tilted local Z, which also
    // pulls the camera slightly closer to the turntable as it rises — unlike
    // boost_floor_h, which is a pure vertical lift. Calibrated against the
    // same measured ellipse boost_checks() uses; a prediction, not a
    // guarantee — always confirm on roi-preview.jpg.
    riser_dz = riser_h * cos(boost_tilt);
    riser_dx = riser_h * sin(boost_tilt);
    echo(str("scan_riser: predicted elevation ",
             atan((cam_rise0 + riser_dz) / (cam_run0 + setback_shift - riser_dx)),
             " deg with the setback spacer at ", setback_shift,
             "mm, ry/rx ", sin(atan((cam_rise0 + riser_dz) / (cam_run0 + setback_shift - riser_dx))),
             ", platter fills ", cam_frame_frac(cam_rise0 + riser_dz, cam_run0 + setback_shift - riser_dx),
             " of frame width"));
}
