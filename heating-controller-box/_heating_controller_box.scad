// =====================================
// Heating controller project box
// Two-part, fully 3D-printed wall enclosure for the ESP32-2432S028R ("CYD")
// heating and hot-water controller that replaces a Danfoss FP720 programmer.
// The faceplate carries the delivered 97 x 100 mm carrier PCB (v2), which
// holds the relay module, PSU, fuse and every mains terminal, so the whole
// assembly is wired on the bench; the board, its rules and the wiring order
// are in St-John-Software/electronics docs/heating-controller/PCB.md and
// BUILD.md.
// =====================================
// Parts:
//   heating_controller_base -> heating_controller_base.stl
//       Plain wall shell, 72 mm deep (sized to the 70 mm as-built wiring
//       measured from the faceplate front, not to the board stack): corner lid-screw posts, wall-screw holes, a
//       floor-flush slot in the bottom wall for the two incoming cables
//       (surface-run up the wall) with a cable-tie anchor under each, an
//       optional floor knockout for cables from behind, vent slots and a stylus sleeve on the outside of the
//       right-hand (+X) wall.
//   heating_controller_lid  -> heating_controller_lid.stl
//       Faceplate: framed display window with CYD bosses behind it, four
//       insert posts carrying the carrier PCB behind the CYD on its
//       89 x 92 mm H1-H4 pattern, a rib frame tying the post feet together,
//       two keyed Hand-Off-Auto toggle holes, two indicator-lamp holes,
//       locating lip (notched round the corner posts) and four countersunk
//       lid screws.
//
// Orientation: both parts are modelled in print orientation (Z-up), centred
// on X/Y with their bed face at z=0. The base opens toward +Z; the lid lies
// outer face down, so its bosses, posts, ribs and lip rise toward +Z.
//
// Layout frame: every position is given in "front view" coordinates -
// looking at the installed box from the room, X right, Y up. The open base
// is viewed from the same side, so it uses them directly; the lid is mirrored
// in X in heating_controller_lid() so its face-down print matches.
//
//   board        : left of the cavity, hanging from the faceplate posts
//                  behind the CYD, component side toward the wall. Seen from
//                  the room it is mirrored, so layout X = board_right - board
//                  x; its terminal row still faces a board_clear_bottom
//                  wiring channel along the bottom (-Y) wall, J3's CPC
//                  entries face the toggle gap on its right, and the
//                  board_clear_left and board_clear_top strips carry the
//                  SELV leads to the CYD
//   CYD          : on the lid in front of the board's solder side,
//                  cyd_board_clear from it, between the carrier posts
//   right column : toggles and lamps hang from the lid right of the board,
//                  never over it, at least cpc_entry_clear from its edge
//
// Segregation is on the DRC-checked carrier PCB, so the box has no partition
// rib; the asserts keep the gaps above instead. Nothing is earthed: J3 pin 3
// stays empty and no metal touches the faceplate.
//
// Fixings: every screw goes into an M3 heat-set insert (12 in total) in a
// printed boss or post - 4 CYD bosses and 4 carrier posts on the lid, 4
// corner posts in the base. No standoffs are used.
//
// Dimensions marked VERIFY are assumptions; the CYD, toggle and stylus
// figures were calipered on 23 September 2026, and the board figures come
// from the carrier's generator (generate.py) and PCB.md.

$fn = 64;

// === Enclosure (mm) ===
inner_w      = 158;   // cavity width (X)
inner_h      = 132;   // cavity height (Y)
inner_d      = 72;    // cavity depth, floor top to lid underside
wiring_depth = 70;    // as-built wiring, measured on the bench 3 November 2026: faceplate front to the deepest lead
wiring_clear = 5;     // air kept between the deepest lead and the floor
wall         = 2.4;   // side wall thickness
floor_t      = 3;     // base floor thickness (holds the wall-screw countersinks)
corner_r     = 4;     // outer corner radius
lid_t        = 3.0;   // lid plate thickness (backs the CYD insert pockets)
lip_t        = 1.6;   // locating lip thickness
lip_d        = 4;     // locating lip depth into the base
lip_clear    = 0.3;   // lip to cavity wall clearance, per side

// === Heat-set inserts (every fixing) ===
// M3 heat-set insert, 4.6 mm OD, 4 to 5.7 mm long. Set insert_hole_d = 2.6
// for a self-tapping M3 pilot when printing without inserts.
insert_hole_d  = 4.0;
insert_depth   = 6;    // pocket depth below the boss or post top
insert_chamfer = 0.5;  // entry chamfer at the pocket mouth
lid_skin       = 1.2;  // minimum lid left behind a CYD insert pocket

// --- Lid screws (countersunk M3 into inserts in the corner posts) ---
post_r       = 4;     // 8 mm posts leave a full wall round the chamfered pocket
post_fuse    = 0.3;   // post overlap into the walls so it fuses
lid_screw_l  = 10;    // M3 x 10 countersunk
screw_clear  = 3.4;   // lid through hole
screw_head   = 6.8;   // countersink diameter, ISO M3 countersunk head

// === Carrier PCB v2 (generate.py, PCB.md) ===
// Board frame: x right, y down from the board's top-left corner, as in
// generate.py; seen from the component side, which faces the wall, so the
// layout frame mirrors it in X (layout x = board_right - board x).
board_w       = 97;
board_h       = 100;
board_t       = 1.6;
board_hole_dx = 89;   // H1-H4 pattern, each hole inset 4 mm from a corner
board_hole_dy = 92;
board_hole_d  = 3.2;  // M3 clearance in the board (reference only, not used)
board_clear_left   = 10;  // board edge to the left wall: SELV lead strip
board_clear_bottom = 22;  // wiring channel under the bottom-edge terminal row
board_clear_top    = 10;  // board top edge to the top wall: SELV flying leads
cpc_entry_clear = 12;     // board right edge (J3 CPC entries) to the toggle bodies
carrier_post_d  = 8;      // faceplate post tip, holding the insert
carrier_post_d1 = 10;     // faceplate post foot
carrier_screw_l = 6;      // M3 x 6 from the component side, nylon preferred
cyd_board_clear = 6;      // CYD's rear to the carrier's solder side
module_standoff_h = 8;    // relay module on 4 x M3 x 8 nylon standoffs
module_h      = 16.78;    // module, PCB to relay tops
u1_h          = 20;       // HLK-10M05B PSU above the carrier
module_x0     = 16.5;     // module outline in the board frame (X checked against the toggles)
module_y0     = 3.08;
module_w      = 38.36;
module_l      = 50.07;    // header edge (top) to terminal edge
u1_x0         = 61.45;    // U1 outline X in the board frame (vents follow it)
u1_x1         = 92.45;
board_mains_gap = 10;     // lamp bodies to the board edge
stack_floor_clear = 5;    // relay tops / U1 to the base floor

// === CYD (ESP32-2432S028R) - measured ===
cyd_hole_x    = 78;   // mounting hole pitch, long side
cyd_hole_y    = 42;   // mounting hole pitch, short side
cyd_hole_d    = 3;
cyd_pcb_l     = 86.5; // PCB outline (VERIFY; published spec)
cyd_pcb_w     = 50.5;
cyd_pcb_t     = 1.6;
cyd_thickness = 9;    // absolute, glass front to tallest rear component
cyd_display_h = 4;    // glass/frame height above the PCB face (VERIFY)
cyd_module_l  = 69;   // display module outline, frame included
cyd_module_w  = 50;
cyd_boss_d    = 7.5;  // 8 would clear the display module by only 0.25 mm
cyd_boss_gap  = 0.3;  // glass to lid underside
cyd_screw_l   = 6;    // M3 x 6 from the board side
cyd_dy        = 14;   // CYD centre above the board centre; X follows the board
cyd_post_clear = 1;   // CYD PCB edge to the carrier post feet

// --- Display window: the frame hides the module edge; the 2.8" active area
//     is about 57.6 x 43.2, so the default shows it with a small margin.
window_l      = 59;
window_w      = 45;
window_r      = 2;
// Glass centre sits 2.5 mm right (+X, toward the toggles) of the hole centre:
// the first print (2026-11-05 bench) hid about 1.5 mm (8 px) of the right-hand
// edge and showed bezel on the left. 2.5 mm is the owner's bench estimate from
// that fit (2.5-3 mm), not a calipered hole-to-glass measurement.
window_off_x  = 2.5;
window_off_y  = 0;

// === Hand-Off-Auto toggles (2x XURUI XT-13A) - body and hole measured ===
toggle_body_l = 30;   // along the throw direction (Y)
toggle_body_w = 15;
toggle_depth  = 32;   // behind the panel, terminals included
toggle_hole_d = 12;   // panel hole for the bushing
toggle_key_depth = 1; // key tab into the hole at 6 o'clock (bottom); 0 removes it
toggle_key_w  = 1.5;  // key tab width (VERIFY: estimated from a photo)
toggle_plate_w = 12;  // legend plate footprint, clearance only (VERIFY)
toggle_plate_h = 31;
toggle_plate_boss_d = 18;
toggle_x      = 48;
row_dy        = 17;   // rows sit at the CYD's Y centre +/- row_dy:
                      // heating above (y=37), hot water below (y=3)

// === 230 V panel indicator lamps - not yet in hand ===
lamp_hole_d   = 10;   // typical 8 or 10 mm cut-out; confirm on arrival
lamp_body_d   = 12;   // body behind the panel, clearance only (VERIFY)
lamp_bezel_d  = 14;   // clearance only (VERIFY)
lamp_x        = 68;

// === Cable entry ===
// The cables run up the wall surface into a slot in the bottom (-Y) wall and
// on to J1 (left) and J2 (right). The floor knockout is the option for
// cables emerging from the wall behind the box.
cable_x        = -18;    // slot centre, midway between J1 and J2
cable_w        = 24;     // takes both incoming cables side by side
cable_wall     = true;   // slot through the bottom wall, flush with the floor
cable_wall_h   = 12;     // slot height above the floor
cable_floor    = false;  // knockout through the floor (cables from behind)
cable_floor_w  = 8;      // knockout size across the channel (Y)

// === Strain relief: one cable-tie anchor under each cable ===
// The tie runs along X through a slot under a bar the cable lies along.
tie_anchors    = true;
tie_w          = 4.8;    // cable-tie width
tie_slot_h     = 2.5;    // slot height, for the tie's thickness
tie_anchor_w   = 10;     // bar length along X (the tie's run)
tie_anchor_l   = 10;     // bar width along Y (the cable's run)
tie_anchor_h   = 6;
tie_anchor_gap = 3;      // between the two bars

// === Wall fixing (countersunk from the cavity side) ===
// Outside the board's projection: one in the top SELV-lead gap, two in the
// wiring channel, one in the right column. The Y of the channel and top
// screws follows the board (see channel_y below).
mount_hole_d   = 4.5;
mount_head_d   = 9;

// === Ventilation slots in the +/-Y walls above and below U1 ===
vents          = true;
vent_w         = 2;     // narrow enough to keep fingers out of a mains box
vent_pitch     = 5;
vent_margin    = 2.5;   // slot run inset from U1's outline in X
vent_z0        = 5;     // slot bottom above the floor
vent_z1        = inner_d - lip_d - 2;    // slot top above the floor, below the lid lip

// === Faceplate rib frame along the board outline ===
rib_w          = 2.4;
rib_h          = 4;

// === Stylus sleeve (the CYD's DS-style stylus) - stylus measured ===
stylus_sleeve       = true;
stylus_l            = 87.3;  // overall length
stylus_cap_l        = 12;    // cap length along the axis, about 7.7 across
stylus_bore_d       = 5.6;   // shaft bore (4.89 shaft)
stylus_cap_d        = 8.4;   // cap counterbore
stylus_cap_depth    = 8;     // leaves 4 mm of the cap proud to grip
stylus_sleeve_w     = 12.4;  // sleeve block size in X and Z
stylus_sleeve_top_y = 55;    // sleeve top edge in the layout frame

// === Derived ===
outer_w    = inner_w + 2 * wall;
outer_h    = inner_h + 2 * wall;
inner_r    = max(0.5, corner_r - wall);
base_h     = floor_t + inner_d;
post_x     = inner_w/2 - post_r + post_fuse;
post_y     = inner_h/2 - post_r + post_fuse;
cyd_boss_h = cyd_display_h + cyd_boss_gap;
cs_h       = (mount_head_d - mount_hole_d) / 2;   // 90 degree countersink depth
board_cx     = -inner_w/2 + board_clear_left + board_w/2;
board_cy     = -inner_h/2 + board_clear_bottom + board_h/2;
board_left   = board_cx - board_w/2;
board_right  = board_cx + board_w/2;
board_top    = board_cy + board_h/2;
board_bottom = board_cy - board_h/2;
channel_y    = -inner_h/2 + board_clear_bottom/2;   // wiring channel centre line
top_screw_y  = (board_top + inner_h/2) / 2;         // centre of the SELV-lead gap
mount_clear_r = mount_head_d / 2;                   // screw head radius
cable_floor_y = -inner_h/2 + 1.5 + cable_floor_w/2;   // hugs the bottom wall
channel_screw_x0 = -58;                             // channel wall screws, clear of the
channel_screw_x1 = 55;                              // knockout and the tie anchors
mount_holes  = [[-45, top_screw_y], [55, 50],
                [channel_screw_x0, channel_y], [channel_screw_x1, channel_y]];
tie_anchor_y  = board_bottom - 1 - tie_anchor_l/2;   // just under the terminal row
tie_anchor_dx = tie_anchor_gap/2 + tie_anchor_w/2;
tie_anchor_xs = [cable_x - tie_anchor_dx, cable_x + tie_anchor_dx];
cyd_cx       = board_cx;
cyd_cy       = board_cy + cyd_dy;
row_cy       = cyd_cy;                               // toggle and lamp rows share it
// Faceplate stack, from the lid's inner face toward the wall
carrier_post_h = cyd_boss_gap + cyd_thickness + cyd_board_clear;
cyd_rear       = lid_t + cyd_boss_gap + cyd_thickness;  // from the lid's outer face
stack_depth    = carrier_post_h + board_t + max(module_standoff_h + module_h, u1_h);
post_foot_gap  = post_r + carrier_post_d1/2 + 1;
cyd_insert_depth     = min(insert_depth, cyd_boss_h + lid_t - lid_skin);
post_insert_depth    = max(insert_depth, lid_screw_l - lid_t + 1);
carrier_insert_depth = min(insert_depth, carrier_post_h - 2);
min_boss_d = min(cyd_boss_d, carrier_post_d, 2 * post_r);
// U1 in the layout frame (mirrored board) and the vent run above and below it
u1_lx0     = board_right - u1_x1;
u1_lx1     = board_right - u1_x0;
vent_x0    = u1_lx0 + vent_margin;
vent_x1    = u1_lx1 - vent_margin;
sleeve_l   = stylus_l - (stylus_cap_l - stylus_cap_depth) + 1;

assert(window_l < cyd_module_l && window_w < cyd_module_w,
       "window must stay inside the display module outline to hide its edge");
assert(cs_h < floor_t, "floor too thin for the wall-screw countersink");

// --- Depth ---
assert(inner_d >= 47, "cavity under 47 mm deep: the carrier stack needs it");
assert(lid_t + inner_d >= wiring_depth + wiring_clear, "cavity too shallow for the as-built wiring: raise inner_d");
assert(inner_d - stack_depth >= stack_floor_clear,
       "relay module or U1 too close to the base floor: raise inner_d");
assert(cyd_board_clear >= 5,
       "carrier solder side too close to the CYD's rear: raise cyd_board_clear");
assert(toggle_depth + 2 <= inner_d, "toggles deeper than the cavity");

// --- Toggles and lamps ---
assert(toggle_key_depth >= 0 && toggle_key_depth < toggle_hole_d/2
       && toggle_key_w < toggle_hole_d,
       "toggle key tab must fit inside the toggle hole");
assert(2 * row_dy >= toggle_plate_h + 2,
       "toggle legend plates overlap: increase row_dy");
assert(lamp_x - toggle_x >= toggle_plate_boss_d/2 + lamp_bezel_d/2 + 1,
       "lamp bezels overlap the toggle legend plates");
assert(row_cy + row_dy + toggle_plate_h/2 <= inner_h/2 + wall,
       "upper toggle legend plate runs off the lid face");
assert(row_cy + row_dy + toggle_body_l/2 < inner_h/2 - lip_clear - lip_t,
       "upper toggle body hits the lid lip");
assert(row_cy - row_dy - toggle_body_l/2 > -inner_h/2 + lip_clear + lip_t,
       "lower toggle body hits the lid lip");
assert(toggle_x - toggle_body_w/2 - board_right >= cpc_entry_clear,
       "no room for the J3 CPC entries between the board and the toggles: raise toggle_x");
assert(lamp_x - lamp_body_d/2 - board_right >= board_mains_gap,
       "lamp bodies too close to the carrier board: raise lamp_x");
assert(lamp_x + lamp_body_d/2 + 2 <= inner_w/2,
       "lamp bodies run into the right-hand wall: raise inner_w");
assert(vent_z0 > 0 && vent_z1 <= inner_d - lip_d,
       "vent slots run into the floor or the lid lip");
assert(!cable_wall || cable_x + cable_w/2 + 2 < vent_x0
       || cable_x - cable_w/2 - 2 > vent_x1,
       "cable slot collides with the vent slots");
assert(!cable_wall || floor_t + cable_wall_h <= base_h - lip_d - 2,
       "cable slot reaches the lid lip");

// --- Carrier board on the faceplate posts ---
assert(board_top + board_clear_top <= inner_h/2,
       "no room for the SELV leads above the board: raise inner_h");
assert(board_clear_bottom >= 20,
       "wiring channel under the terminal row under 20 mm");
assert(board_clear_left >= 8, "no room for the SELV leads at the left wall");
assert(board_left + (board_w - board_hole_dx)/2 - carrier_post_d1/2
       > -inner_w/2 + lip_t + lip_clear,
       "left carrier posts run into the lid lip");
assert(board_top + rib_w/2 < inner_h/2 - lip_t - lip_clear,
       "top rib runs into the lid lip");
assert((board_cx - board_hole_dx/2 + post_x) * (board_cx - board_hole_dx/2 + post_x)
       + (board_cy + board_hole_dy/2 - post_y) * (board_cy + board_hole_dy/2 - post_y)
       > post_foot_gap * post_foot_gap,
       "top-left carrier post hits the corner post");
assert((board_cx - board_hole_dx/2 + post_x) * (board_cx - board_hole_dx/2 + post_x)
       + (board_cy - board_hole_dy/2 + post_y) * (board_cy - board_hole_dy/2 + post_y)
       > post_foot_gap * post_foot_gap,
       "bottom-left carrier post hits the corner post");
assert(board_right - module_x0 < toggle_x - toggle_body_w/2,
       "relay module overlaps the toggle column: raise toggle_x");

// --- Wall fixing and floor knockout stay out of the board's footprint ---
assert(channel_y + mount_clear_r <= board_bottom,
       "channel wall screws run under the board: raise board_clear_bottom");
assert(cable_floor_y + cable_floor_w/2 <= board_bottom,
       "floor knockout runs under the board: raise board_clear_bottom");
assert(top_screw_y - mount_clear_r >= board_top,
       "top wall screw runs under the board: raise board_clear_top");

// --- Cable-tie anchors in the wiring channel ---
assert(tie_anchor_y + tie_anchor_l/2 <= board_bottom
       && tie_anchor_y - tie_anchor_l/2 >= -inner_h/2 + 1,
       "tie anchors run out of the wiring channel");
assert(tie_anchor_xs[0] - tie_anchor_w/2 >= channel_screw_x0 + mount_clear_r + 1
       && tie_anchor_xs[1] + tie_anchor_w/2 <= channel_screw_x1 - mount_clear_r - 1,
       "tie anchors hit the channel wall screws");
assert(tie_anchor_h <= inner_d - lip_d - 2, "tie anchors reach the lid lip");
assert(tie_anchor_l - tie_w - 0.6 >= 4, "tie slot leaves the anchor walls too thin");
assert(tie_anchor_h >= 1.5 + tie_slot_h + 1.5, "tie anchor bar too thin above its slot");
assert(cable_w >= 2 * tie_anchor_w + tie_anchor_gap,
       "cable entry narrower than the two tie anchors it feeds");
assert(tie_anchor_xs[0] - tie_anchor_w/2 >= cable_x - cable_w/2
       && tie_anchor_xs[1] + tie_anchor_w/2 <= cable_x + cable_w/2,
       "tie anchors lie outside the cable entry");
assert(cable_floor_y + cable_floor_w/2 + 1 <= tie_anchor_y - tie_anchor_l/2,
       "floor knockout runs into the tie anchors: lower cable_floor_w");

// --- CYD ---
assert(cyd_cx - cyd_pcb_l/2 > -inner_w/2 + lip_t + lip_clear + 1
       && cyd_cx + cyd_pcb_l/2 < toggle_x - toggle_body_w/2 - 1,
       "CYD runs into the left wall or the toggles");
assert(cyd_cy + cyd_pcb_w/2 < inner_h/2 - lip_t - lip_clear - 1,
       "CYD runs into the top lid lip: lower cyd_dy");
assert(cyd_cy + cyd_pcb_w/2 + cyd_post_clear
       <= board_cy + board_hole_dy/2 - carrier_post_d1/2,
       "CYD hits the top carrier posts: lower cyd_dy");
assert(cyd_cy - cyd_pcb_w/2 - cyd_post_clear
       >= board_cy - board_hole_dy/2 + carrier_post_d1/2,
       "CYD hits the bottom carrier posts: raise cyd_dy");
assert(cyd_cx + cyd_pcb_l/2 < board_right - rib_w/2
       && cyd_cx - cyd_pcb_l/2 > board_left + rib_w/2
       && cyd_cy - cyd_pcb_w/2 > board_bottom + rib_w/2,
       "CYD hits the faceplate rib frame");
assert((cyd_cx - cyd_hole_x/2 - board_cx + board_hole_dx/2)
       * (cyd_cx - cyd_hole_x/2 - board_cx + board_hole_dx/2)
       + (cyd_cy + cyd_hole_y/2 - board_cy - board_hole_dy/2)
       * (cyd_cy + cyd_hole_y/2 - board_cy - board_hole_dy/2)
       > (cyd_boss_d/2 + carrier_post_d1/2 + 1) * (cyd_boss_d/2 + carrier_post_d1/2 + 1),
       "top CYD bosses hit the carrier post feet");

// --- Heat-set inserts ---
assert(insert_hole_d >= 2.4 && insert_hole_d <= min_boss_d - 2.5,
       "insert_hole_d must leave a wall in every boss and post");
assert(min_boss_d >= 7, "insert bosses and posts must be at least 7 mm across");
assert(insert_depth >= 6, "insert pockets must be at least 6 mm deep");
assert(cyd_insert_depth >= 6,
       "CYD insert pocket under 6 mm: raise cyd_display_h or lid_t");
assert(cyd_screw_l - cyd_pcb_t <= cyd_insert_depth,
       "CYD screws bottom out in their insert pockets");
assert(carrier_insert_depth >= 6,
       "carrier insert pocket under 6 mm: raise cyd_board_clear");
assert(carrier_screw_l - board_t <= carrier_insert_depth,
       "carrier screws bottom out in their insert pockets");
assert(lid_screw_l - lid_t <= post_insert_depth - 0.5,
       "lid screws bottom out in the corner posts");
assert(post_insert_depth <= inner_d - 2, "corner post insert pockets too deep");
assert(cyd_hole_x/2 - cyd_boss_d/2 >= cyd_module_l/2 + 0.5,
       "CYD bosses hit the display module");
assert((screw_head - screw_clear)/2 < lid_t, "lid too thin for the countersink");

// --- Stylus sleeve ---
assert(stylus_bore_d > 4.89 && stylus_bore_d < stylus_cap_d && stylus_cap_d > 7.65,
       "stylus bores must clear the 4.89 mm shaft and the 7.65 mm cap");
assert(stylus_cap_depth < stylus_cap_l,
       "stylus cap would sit at or below the sleeve rim");
assert(stylus_sleeve_top_y <= outer_h/2 - corner_r,
       "stylus sleeve runs into the rounded top corner");
assert(stylus_sleeve_top_y - sleeve_l >= -outer_h/2,
       "stylus sleeve runs past the bottom of the box");
assert(stylus_cap_d/2 + 0.6 + 1.2 <= stylus_sleeve_w/2,
       "stylus sleeve too thin around the cap counterbore");

// === Modules ===

// Rounded-rect vertical prism: hull of four corner cylinders.
// Centred on X/Y, base at z=0.
module rbox(w, l, h, r) {
    hull()
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * (w/2 - r), sy * (l/2 - r), 0])
                cylinder(r = r, h = h);
}

// Heat-set insert pocket: blind hole running along -Z from its mouth at z=0,
// with an entry chamfer. Both extend 0.01 above the mouth.
module insert_hole(depth) {
    translate([0, 0, -depth])
        cylinder(d = insert_hole_d, h = depth + 0.01);
    translate([0, 0, -insert_chamfer])
        cylinder(d1 = insert_hole_d, d2 = insert_hole_d + 2 * insert_chamfer,
                 h = insert_chamfer + 0.01);
}

// Teardrop with its apex toward +Y, cut flat 0.6 above the circle, so a
// horizontal bore prints without supports.
module flat_teardrop(d) {
    intersection() {
        hull() {
            circle(d = d);
            rotate(45) square(d/2);
        }
        translate([-d, -d]) square([2 * d, 1.5 * d + 0.6]);
    }
}

// Toggle panel cut-out, matching the legend plate: round hole with a key tab
// of lid material intruding at 6 o'clock (bottom, -Y in the layout frame).
module toggle_cutout() {
    difference() {
        circle(d = toggle_hole_d);
        translate([-toggle_key_w/2, -toggle_hole_d/2 - 1])
            square([toggle_key_w, toggle_key_depth + 1]);
    }
}

module corner_positions() {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * post_x, sy * post_y, 0]) children();
}

// The carrier's H1-H4 holes, centred on the board (symmetric, so the
// mirrored mounting does not move them).
module carrier_positions() {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([board_cx + sx * board_hole_dx/2,
                   board_cy + sy * board_hole_dy/2, 0]) children();
}

module cyd_positions() {
    for (sx = [-1, 1], sy = [-1, 1])
        translate([cyd_cx + sx * cyd_hole_x/2,
                   cyd_cy + sy * cyd_hole_y/2, 0]) children();
}

// Cable-tie anchor standing on the floor at z=0: a block with a slot along X
// starting 1.5 mm above the floor, so the tie passes under the bar the cable
// lies across.
module tie_anchor() {
    difference() {
        translate([-tie_anchor_w/2, -tie_anchor_l/2, 0])
            cube([tie_anchor_w, tie_anchor_l, tie_anchor_h]);
        translate([-tie_anchor_w/2 - 1, -(tie_w + 0.6)/2, 1.5])
            cube([tie_anchor_w + 2, tie_w + 0.6, tie_slot_h]);
    }
}

// 2D profile of the bottom-wall cable slot: flat bottom, rounded top corners.
module cable_slot() {
    hull() {
        translate([-cable_w/2, 0]) square([cable_w, 1]);
        for (sx = [-1, 1])
            translate([sx * (cable_w/2 - 2), cable_wall_h - 2]) circle(r = 2);
    }
}

// Vertical stylus sleeve on the outside of the +X wall, standing on the wall
// face. Its bores run along Y and stay wholly outside the box wall, so the
// sleeve never opens into the cavity. The shaft bore is open at the
// bottom to push a stuck stylus out; the cap drops into a counterbore at the
// top and stands proud of it.
module stylus_sleeve() {
    x0 = outer_w/2 - 0.8;
    bore_x = x0 + stylus_sleeve_w/2;
    bore_z = stylus_sleeve_w/2;
    difference() {
        translate([x0, stylus_sleeve_top_y - sleeve_l, 0])
            cube([stylus_sleeve_w, sleeve_l, stylus_sleeve_w]);
        // rotate([90, 0, 0]) maps the profile's +Y to +Z and extrudes toward -Y
        translate([bore_x, stylus_sleeve_top_y + 1, bore_z])
            rotate([90, 0, 0]) {
                linear_extrude(sleeve_l + 2) flat_teardrop(stylus_bore_d);
                linear_extrude(stylus_cap_depth + 1) flat_teardrop(stylus_cap_d);
            }
    }
}

// Base shell: floor at z=0, opening toward +Z.
module heating_controller_base() {
    difference() {
        union() {
            difference() {
                rbox(outer_w, outer_h, base_h, corner_r);
                translate([0, 0, floor_t])
                    rbox(inner_w, inner_h, inner_d + 1, inner_r);
            }
            // Corner posts for the lid screws (fused into the walls)
            corner_positions()
                translate([0, 0, floor_t - 0.01])
                    cylinder(r = post_r, h = inner_d + 0.01);
            // Cable-tie anchors, one under each cable
            if (tie_anchors)
                for (x = tie_anchor_xs)
                    translate([x, tie_anchor_y, floor_t - 0.01]) tie_anchor();
        }

        // Lid screw inserts in the corner post tops
        corner_positions()
            translate([0, 0, base_h]) insert_hole(post_insert_depth);

        // Wall-fixing holes: through hole plus a countersink that opens into
        // the cavity, since the screws are driven from inside the open base.
        for (p = mount_holes)
            translate([p[0], p[1], 0]) {
                translate([0, 0, -1]) cylinder(d = mount_hole_d, h = floor_t + 2);
                translate([0, 0, floor_t - cs_h])
                    cylinder(d1 = mount_hole_d, d2 = mount_head_d + 2, h = cs_h + 1);
            }

        // Cable entries
        if (cable_wall)
            translate([cable_x, -inner_h/2 + 1, floor_t]) rotate([90, 0, 0])
                linear_extrude(wall + 2) cable_slot();
        if (cable_floor)
            translate([cable_x, cable_floor_y, -1])
                rbox(cable_w, cable_floor_w, floor_t + 2, 2);

        // Vent slots through both long walls
        if (vents)
            for (sy = [-1, 1], x = [vent_x0 : vent_pitch : vent_x1])
                translate([x, sy * (inner_h/2 + wall/2), floor_t + (vent_z0 + vent_z1)/2])
                    cube([vent_w, wall + 2, vent_z1 - vent_z0], center = true);
    }

    // Added after the cuts, so the sleeve bores never touch the +X wall
    if (stylus_sleeve) stylus_sleeve();
}

// Lid in the front-view frame: outer face at z=0, features rising toward +Z.
// The outer face carries only the window, the holes and the countersinks, so
// the toggle legend plates and lamp bezels sit on flat material.
module lid_frame() {
    difference() {
        union() {
            rbox(outer_w, outer_h, lid_t, corner_r);

            // Locating lip inside the cavity walls, notched around the corner
            // posts.
            translate([0, 0, lid_t - 0.01])
                difference() {
                    rbox(inner_w - 2 * lip_clear, inner_h - 2 * lip_clear,
                         lip_d + 0.01, max(0.5, inner_r - lip_clear));
                    translate([0, 0, -1])
                        rbox(inner_w - 2 * (lip_clear + lip_t),
                             inner_h - 2 * (lip_clear + lip_t),
                             lip_d + 3, max(0.5, inner_r - lip_clear - lip_t));
                    corner_positions()
                        translate([0, 0, -1])
                            cylinder(r = post_r + lip_clear, h = lip_d + 3);
                }

            // CYD bosses: the glass sits cyd_boss_gap behind the lid
            cyd_positions()
                translate([0, 0, lid_t - 0.01])
                    cylinder(d = cyd_boss_d, h = cyd_boss_h + 0.01);

            // Carrier posts: the board hangs solder side down on their tips,
            // cyd_board_clear behind the CYD, component side toward the wall
            carrier_positions()
                translate([0, 0, lid_t - 0.01])
                    cylinder(d1 = carrier_post_d1, d2 = carrier_post_d,
                             h = carrier_post_h + 0.01);

            // Rib frame along the board outline, tying the post feet together
            translate([0, 0, lid_t - 0.01]) {
                for (x = [board_left, board_right])
                    translate([x - rib_w/2, board_bottom - rib_w/2, 0])
                        cube([rib_w, board_h + rib_w, rib_h + 0.01]);
                for (y = [board_bottom, board_top])
                    translate([board_left - rib_w/2, y - rib_w/2, 0])
                        cube([board_w + rib_w, rib_w, rib_h + 0.01]);
            }
        }

        // Display window
        translate([cyd_cx + window_off_x, cyd_cy + window_off_y, -1])
            rbox(window_l, window_w, lid_t + 2, window_r);

        // CYD inserts: open at the boss tips and run toward the lid face,
        // leaving at least lid_skin behind them
        cyd_positions()
            translate([0, 0, lid_t + cyd_boss_h]) insert_hole(cyd_insert_depth);

        // Carrier inserts in the post tips
        carrier_positions()
            translate([0, 0, lid_t + carrier_post_h]) insert_hole(carrier_insert_depth);

        // Keyed toggle bushings and lamp bezels, one row per circuit
        for (sy = [-1, 1]) {
            translate([toggle_x, row_cy + sy * row_dy, -1])
                linear_extrude(lid_t + 2) toggle_cutout();
            translate([lamp_x, row_cy + sy * row_dy, -1])
                cylinder(d = lamp_hole_d, h = lid_t + 2);
        }

        // Lid screws, countersunk on the outer face
        corner_positions() {
            translate([0, 0, -1]) cylinder(d = screw_clear, h = lid_t + 2);
            translate([0, 0, -0.01])
                cylinder(d1 = screw_head, d2 = screw_clear,
                         h = (screw_head - screw_clear)/2);
        }
    }
}

// Lid in print orientation: outer face on the bed. Mirrored so the layout
// reads correctly from the front once the lid is turned over onto the base.
module heating_controller_lid() {
    mirror([1, 0, 0]) lid_frame();
}
