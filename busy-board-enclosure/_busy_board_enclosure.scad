// =====================================
// Busy board enclosure
// Clear polycarbonate front plate, black printed frame, back tray and
// screwed battery door for the busy board PCB v2.0 or v3.0
// (St-John-Software/electronics, hardware/busy-board/ and
// hardware/busy-board-v3/, docs/busy-board/PCB.md and
// docs/busy-board-v3/PCB.md "Mechanical and enclosure"): a toddler's toy, so
// the child-safety rules in docs/busy-board/README.md apply. v3 keeps v2's
// outline, holes and cut-outs, so one enclosure fits both; only its part
// heights differ. The board is seen through the clear plate.
// =====================================
// Parts:
//   busy_board_frame        -> busy_board_frame.stl
//       Black printed frame: a rounded lip over the plate's outer 4 mm, so
//       no cut edge is reachable from the play side; a rebate the plate
//       drops into from behind; the locating lip and eight tray posts with
//       M3 heat-set inserts. Every play-side edge and corner is rounded.
//   busy_board_plate        -> busy_board_plate.stl (for viewing only) and
//                              busy_board_plate.dxf (the cut sheet; CI build)
//       3 mm clear polycarbonate sheet, 225.4 mm square with R3 corners,
//       routed and drilled by a cut-to-size service. Its only openings are
//       holes for six 24 mm arcade buttons, three panel pots, the EC11
//       encoder and three toggles, their anti-rotation tab holes, the slide
//       switch's two screw holes and full-radius actuator slot, and a buzzer
//       grille of holes at most 2 mm across. No LED holes and no windows:
//       the board shows through the sheet.
//   busy_board_tray         -> busy_board_tray.stl
//       Back tray: one square cavity behind the plate for the board, whose
//       cut-outs the controls pass through; eight PCB posts on the floor
//       under H1-H8; a compartment for three 14500 cell holders behind the
//       board with a rebated door opening in the floor; a PCM pocket beside
//       it; the CR-TL24 charger in a C-channel cradle over two floor windows
//       for its charge LEDs, its USB-C socket at the inner end of a plug
//       pocket in the left (-X) wall; eight countersunk post screws through
//       the floor (no fixing is reachable from the play side).
//   busy_board_battery_door -> busy_board_battery_door.stl
//       Flat door: two hook tabs at one end, one countersunk M3 screw at
//       the other, so the compartment needs a tool to open.
//
// Stack-up: eight M3 x 15 M-F nylon standoffs screw through H1-H8 into the
// tray's PCB posts and hold the board front pcb_to_panel behind the plate;
// their tops press the plate into the frame lip. The frame screws to the
// tray from the back, so nothing is fixed through the plate's play face but
// the two slide-switch screws (an owner-approved exception).
//
// Orientation: Z-up, print orientation for every part, no supports. The
// frame and plate are modelled play face down (play face on the bed, the
// frame's posts rising); the tray prints floor down; the door prints outer
// face down.
//
// Layout frame: front view, X right, Y up, origin at the PCB centre, as
// seen by the child. busy_board_frame() and busy_board_plate() mirror in X
// so their face-down models read correctly once turned over;
// plate_profile() is the unmirrored play-side view the DXF is cut from. The
// tray is seen from the same side as the plate, so it uses the frame
// directly. Board-document coordinates (mm from the board's top-left
// corner, X right, Y DOWN, PCB.md "Layout") convert with bpos().
//
// Every board figure comes from PCB.md. VERIFY marks values that should be
// checked against the delivered parts before the final print.

$fn = 64;

// === Busy board PCB v2.0 (mm) - PCB.md "Mechanical and enclosure" ===
// v3.0 shares every position here; its heights follow in the v3 block below.
pcb_l         = 222;    // outline along X
pcb_w         = 222;    // outline along Y
pcb_t         = 1.6;    // FR4
pcb_holes     = [[5, 5], [111, 5], [217, 5], [5, 111], [217, 111],
                 [5, 217], [111, 217], [217, 217]];  // H1-H8 M3 centres, board frame
pcb_keepout_r = 3.5;    // copper keepout round each hole: boss d <= 7
pcb_clear     = 0.5;    // board edge to anything, per side
below_pcb     = 3;      // clearance behind the board for the trimmed leads
ds1_c         = [111, 36];      // 4-digit display centre
ds1_body      = [50.4, 19.0];   // body outline
ds1_h         = 8;              // body height above the board front
bar_x         = [73, 111, 149]; // bar 1-3 columns (D41-D50, D51-D60, D61-D70)
bar_y         = [62, 116];      // LED 10 and LED 1 centres, 6 mm pitch
bar_led       = 5.0;            // WS2812B 5050
bar_h         = 1.6;
ring_c        = [[17, 8], [44, 8], [71, 8], [98, 8],                  // D1-D4
                 [124, 8], [151, 8], [178, 8], [205, 8],              // D5-D8
                 [214, 30], [214, 60], [214, 98],                     // D9-D11
                 [214, 132], [214, 168], [214, 196],                  // D12-D14
                 [205, 214], [178, 214], [151, 214], [124, 214],      // D15-D18
                 [98, 214], [71, 214], [44, 214], [17, 214],          // D19-D22
                 [8, 196], [8, 168], [8, 132],                        // D23-D25
                 [8, 98], [8, 60], [8, 30]];                          // D26-D28
enc_bc        = [40, 44];       // encoder cut-out centre
enc_ring_r    = 15.5;           // D29-D40, 30 degrees apart, D29 at the top
enc_ring_n    = 12;
btn_bc        = [[35, 184], [73, 184], [111, 184], [149, 184], [187, 184],  // BTN1-BTN5
                 [182, 44]];                                                 // PWR
btn_led_c     = [[35, 160], [73, 160], [111, 160], [149, 160], [187, 160],  // D71-D75
                 [182, 74]];                                                 // D76
pot_bc        = [[73, 140], [111, 140], [149, 140]];   // POT1-POT3
tgl_bc        = [[34, 88], [34, 122], [188, 88]];      // TGL1-TGL3
tgl_led_c     = [[54, 88], [54, 122], [168, 88]];      // D77-D79
slide_bc      = [188, 122];     // SLIDE
slide_led_c   = [168, 122];     // D80
buzzer_bc     = [184, 146];     // BZ1, 12 mm piezo
buzzer_d      = 12;
buzzer_h      = 9.5;
enc_cut_d     = 16;     // board cut-outs the plate's controls pass through
btn_cut_d     = 32;
tgl_cut_d     = 17;
pot_cut_d     = 20;
slide_cut     = [22, 12];
led_lens_d    = 5;      // v2's WS2812D-F5, 5 mm
led_flange_d  = 5.8;
led_h         = 8.6;    // body height, seated on the board
jst_h         = 10;     // JST-XH housings
jst_lead_h    = 15;     // leads leave the connectors upward: allow this above the board
u1_h          = 9;      // socketed MCU
u2_h          = 11;     // U3V16F5 boost on its header
f1_h          = 12;     // radial PTC: tallest part bar the connectors
j9_h          = 8.5;    // programming header pins; J9 stays inside the enclosure

// === Busy board PCB v3.0 heights (mm) - docs/busy-board-v3/PCB.md ===
// Factory assembled: all 80 LEDs are WS2812B 5050s, the boost is on-board
// and F1 is an 1812 PTC. U1, J1-J16, J9 and DS1 heights are v2's.
v3_led_span   = 7.1;    // WS2812B 5050 diagonal: its footprint on the board
v3_led_h      = 1.6;    // 5050 body height: tops 13.4 mm behind the plate
v3_boost_h    = 3;      // TPS61023, L1 and caps: L1 tallest, about 1.8 mm
v3_f1_h       = 2;      // 1812 PTC, at most 1.5 mm
v3_buzzer_h   = 7.5;    // BZ1 piezo

// === Clear plate, frame and board ===
panel_t       = 3;      // clear polycarbonate plate thickness (not acrylic)
plate_clear   = 0.4;    // plate edge to the frame rebate wall, per side
plate_r       = 3;      // plate corner radius (R3 on the cut sheet)
frame_lip_t   = 2.4;    // frame lip in front of the plate
frame_overlap = 4;      // lip overlap onto the plate: hides its cut edge
lip_r         = 1.2;    // play-side round on the lip's window edge
pcb_to_panel  = 15;     // plate back to board front: clears the upward
                        // JST-XH leads, F1, U2 and the buzzer (v2 and v3)
led_raise     = 0;      // LEDs sit on the board, no spacers: tips 6.4 mm (v2) or 13.4 mm (v3) behind the plate
boss_d        = 7;      // PCB posts: == 2 * pcb_keepout_r
standoff_l    = 15;     // M3 x 15 M-F nylon hex standoff body: == pcb_to_panel
standoff_thread_l = 6;  // its male thread, through the board into the PCB post insert

// === Play-side controls (all plate-mount; the PCB carries no control) ===
// Each passes through its board cut-out; centres are the cut-out centres.
// Plate openings are circles or a full-radius slot only, because UK
// cut-to-size services route and drill polycarbonate; anti-rotation tabs
// go through round holes in the sheet.
button_hole_d = 24.5;   // 24 mm arcade button, panel-nut type
button_bezel_d = 28;    // bezel on the play side (VERIFY)
button_nut_d  = 30;     // nut / body footprint behind the plate (VERIFY)
button_depth  = 34;     // plate back to microswitch bottom (VERIFY)
button_switch_reach = 15;  // microswitch reach from the centre; must pass the 32 mm cut-out (VERIFY)
// Pots: Switch Electronics 133042 (RK163 mono, solder lugs) or the stereo
// fallback 133085 (RK163G, PCB pins, one gang wired); 10k linear.
pot_hole_d    = 7.4;    // M7 x 0.75, seller cut-out 7 mm, plus allowance
pot_body_d    = 17.5;   // 17 mm RK163 body plus clearance
pot_depth     = 12;     // 9.3 mono, 11.5 stereo behind the plate (VERIFY)
pot_lug       = true;   // anti-rotation tab hole, turned to pot_lug_a
pot_lug_r     = 7.8;    // tab centre radius from the shaft (RK163 drawing)
pot_lug_d     = 3.2;    // tab hole through the plate (VERIFY)
pot_lug_a     = -90;    // tab at 3 o'clock: lugs and pins sit 90 degrees
                        // counter-clockwise, up at the bars, clear of J3/J5 (VERIFY)
// Encoder: Switch Electronics 482026 (MPN 483363), 24 detents, push switch.
enc_hole_d    = 7.4;    // M7 x 0.5, seller cut-out 7 mm, plus allowance
enc_body      = 14.5;   // 14 x 13.2 body plus clearance
enc_body_h    = 6.5;    // body depth behind the plate; only its 3.5 mm pins go deeper
enc_depth     = 12;     // 6.5 body + 3.5 pins, plus margin (VERIFY)
enc_lug       = false;  // seller drawing shows no tab, so no hole (VERIFY)
enc_lug_r     = 6.5;    // tab hole at 12 o'clock if enc_lug (VERIFY)
enc_lug_d     = 2.0;
knob_d        = 20;     // CLIFF K15 (SKU 484151) set-screw knobs, 20 mm across
// Toggles: APEM 5636A On-On (Switch Electronics 486015) with a U215 locking
// washer; APEM 5000-series catalogue pp. A-26/A-27. The 3 mm plate takes one
// 8 mm A/F nut (APEM: 4 mm with one nut, 2.5 mm with two); nut and
// lockwasher go on the play face, the locking ring's tab in its hole.
tgl_hole_d    = 6.6;    // 1/4-40 UNS bushing, APEM/seller cut-out 6.5, plus allowance
tgl_lug       = true;   // locking-ring tab hole at 12 o'clock
tgl_lug_r     = 5.2;    // APEM anti-rotation hole centre; U215 tab assumed to match (VERIFY)
tgl_lug_d     = 2.4;    // APEM Ø2.2 anti-rotation hole plus clearance (VERIFY)
tgl_face_d    = 18;     // nut, lockwasher and 10.5 mm lever's 24 degree throw (VERIFY)
tgl_body_d    = 15.4;   // 13.2 x 7.0 case, 14.88 diagonal, plus clearance
tgl_depth     = 17;     // 12.0 case + 3.7 solder lugs below the locking ring (VERIFY ring)
// Slide switch: Switch Electronics 124002, On-On SPDT, 15.5 x 6.2 body.
// Two M2 x 10 pan-head screws from the play side through the plate, a
// spacer and the switch's ears into M2 nyloc nuts: the one approved
// play-side fastener besides the control nuts.
slide_slot    = [9, 4.4];  // full-radius actuator slot, travel along X
slide_screw_pitch = 19; // mounting-ear screw centres, along X (screw size VERIFY, M2 assumed).
                        // At least 19: the heads keep 1 mm from the slot's finger room
                        // (face_clash); the plate manifest's min matches.
slide_screw_d = 2.4;    // M2 clearance hole through the plate
slide_spacer_h = 2;     // ears stand this far behind the plate, so the 7 mm
                        // actuator ends 2 mm proud of the play face (VERIFY)
slide_body    = [16, 7];   // 15.5 x 6.2 body plus clearance; passes the 22 x 12 cut-out
slide_screw_l = 10;     // M2 x 10 pan-head screw, under-head length
slide_head_d  = 3.8;    // M2 pan head on the play face (VERIFY)
slide_nut_d   = 4.6;    // M2 nyloc across corners, behind the ear (VERIFY)
slide_depth   = 15;     // body and lugs behind the plate (VERIFY)
grille_hole_d = 1.5;    // buzzer grille: no finger or probe passes (rule 8)
grille_pitch  = 3.5;    // centre hole plus six on this radius
plate_web     = 1.5;    // least polycarbonate between two plate openings
lug_web       = 0.6;    // least between a tab hole and its own bushing hole (VERIFY)

// === Enclosure ===
wall          = 2.4;
floor_t       = 4;      // back of the tray; holds the door rebate and countersinks
corner_r      = 6;      // plan-view corner radius, frame and tray
edge_r        = 2;      // play-face and back-face edge radius
inner_d       = 38;     // plate back to floor top: arcade buttons + 4 mm
lip_t         = 1.6;
lip_d         = 4;
lip_clear     = 0.3;
post_r        = 4;      // tray posts hang from the frame, 8 mm across
post_gap      = 1.6;    // board clearance zone to the posts, per side

// === Fixings: M3 heat-set inserts in every post ===
insert_hole_d  = 4.0;   // 4.6 mm OD insert; 2.6 for a self-tapping M3 pilot
insert_depth   = 6;
insert_chamfer = 0.5;
tray_screw_l   = 10;    // M3 x 10 countersunk through the floor into the posts
door_screw_l   = 8;     // M3 x 8 countersunk through the door
screw_clear    = 3.4;
screw_head     = 6.8;

// === Pack: three 14500 (AA-format) holders with leads, behind the board ===
batt_l        = 58;     // holder length along X (VERIFY)
batt_w        = 50;     // three holders side by side along Y (VERIFY)
batt_h        = 16;     // holder thickness (VERIFY)
batt_clear    = 1;
batt_cx       = 0;      // compartment centre, layout frame
batt_cy       = 20;
batt_wall     = 2;
batt_lip      = 1.5;    // retaining lip at the wall tops, all four walls
batt_lip_t    = 1.5;
lead_notch_w  = 6;      // lead slot in the compartment's -X wall, toward the PCM and J1
door_t        = 2.4;    // door plate; the rebate is this deep
door_flange   = 4;      // door overlap onto the floor, per side
door_flange_screw = 9;  // overlap at the screw end, covering the boss
door_clear    = 0.3;
door_r        = 1.5;
door_tab_x    = 15;     // hook tabs at +/- this x
door_tab_w    = 8;
door_tab_l    = 3;      // reach beyond the door edge
door_tab_t    = 1.2;
door_boss_d   = 8;

// === 1S LiFePO4 protection board (PCM), on foam tape beside the compartment ===
pcm_l         = 30;     // along X (VERIFY)
pcm_w         = 8;      // (VERIFY)
pcm_clear     = 0.5;
pcm_gap       = 6;      // compartment wall to the pocket rim
pcm_rim       = 1.2;
pcm_rim_h     = 2;

// === CR-TL24 charger and its USB-C plug pocket in the left (-X) wall ===
usb_y         = 45;     // pocket centre, layout frame
usb_pocket    = [16, 10];  // plug pocket width (Y) and height (Z)
usb_pocket_d  = 20;     // outer face to the socket: a plug's overmould sits flush
usb_sock      = [9, 3.2];  // receptacle shell, passes the end wall (VERIFY)
usb_sock_clear = 0.2;   // per side
usb_end_t     = 0.8;    // pocket end wall round the socket
usb_wall      = 1.6;    // pocket side walls and roof
chg_l         = 26;     // module length along X, socket end first (VERIFY)
chg_w         = 18;     // (VERIFY)
chg_pcb_t     = 1.6;
chg_seat      = 6.6;    // floor top to the module's underside: component side
                        // down, its socket centred in the pocket (VERIFY)
chg_clear     = 0.4;
chg_rail_t    = 1.6;    // C-channel rail wall
chg_ledge     = 1.2;    // seat ledge under each module edge
chg_lip       = 1.2;    // retaining lip over each module edge
chg_lip_t     = 1.2;
chg_led       = [[8, -3], [8, 3]];  // charge LEDs, from the socket end and centre line (VERIFY)
chg_win_d     = 3;      // floor windows under the charge LEDs

// === Derived ===
function bpos(p) = [p[0] - pcb_l/2, pcb_w/2 - p[1]];   // board frame -> layout frame
inner_w    = pcb_l + 2 * (pcb_clear + post_gap + 2 * post_r + lip_clear);
inner_h    = pcb_w + 2 * (pcb_clear + post_gap + 2 * post_r + lip_clear);
outer_w    = inner_w + 2 * wall;
outer_h    = inner_h + 2 * wall;
inner_r    = max(0.5, corner_r - wall);
post_x     = inner_w/2 - lip_clear - post_r;           // fused into the lip
post_y     = inner_h/2 - lip_clear - post_r;
post_pts   = [for (sx = [-1, 0, 1], sy = [-1, 0, 1]) if (sx != 0 || sy != 0)
                  [sx * post_x, sy * post_y]];          // corners and mid-sides
post_insert_depth = max(insert_depth, tray_screw_l - floor_t + 0.5);
boss_insert_depth = insert_depth;
door_pocket  = door_screw_l - door_t + 0.5;
cs_h         = (screw_head - screw_clear)/2;           // 90 degree countersink depth
batt_il      = batt_l + batt_clear;                    // compartment interior
batt_iw      = batt_w + batt_clear;
batt_wall_h  = door_t + batt_h + batt_clear - floor_t + batt_lip_t;  // above the floor top
door_boss_off = batt_iw/2 + door_boss_d/2 + 0.2;       // boss centre from the compartment centre
door_boss_h  = door_t + door_pocket + 2 - floor_t;      // above the floor top
reb_w        = batt_il + 2 * door_flange;
reb_y0       = -batt_iw/2 - door_flange;
reb_y1       = batt_iw/2 + door_flange_screw;
led_tip      = led_h + led_raise;                      // lens tip above the board front
v3_led_tip   = v3_led_h + led_raise;                   // v3 5050 top above the board front
pcb_back     = pcb_to_panel + pcb_t;                   // plate back to board back
pcb_post_h   = inner_d - pcb_back;                     // tray PCB posts above the floor top
under_pcb    = inner_d - pcb_back - below_pcb;         // floor top to the lead stubs
enc_ring_c   = [for (i = [0 : enc_ring_n - 1])
                    enc_bc + enc_ring_r * [sin(i * 360 / enc_ring_n), -cos(i * 360 / enc_ring_n)]];
led_c        = concat(ring_c, enc_ring_c, btn_led_c, tgl_led_c, [slide_led_c]);  // D1-D40, D71-D80
grille_pts   = concat([[0, 0]], [for (a = [0 : 60 : 300]) grille_pitch * [cos(a), sin(a)]]);
grille_r     = grille_pitch;
slide_screw_pts = [for (sx = [-1, 1]) bpos(slide_bc) + [sx * slide_screw_pitch/2, 0]];
frame_t      = frame_lip_t + panel_t;                  // play face to the plate back plane
plate_w      = pcb_l + 2 * (pcb_clear + post_gap) - 2 * plate_clear;  // square clear plate
rebate_w     = plate_w + 2 * plate_clear;              // frame rebate the plate drops into
frame_win    = plate_w - 2 * frame_overlap;            // lip window, square
frame_win_r  = plate_r;
pot_lug_off  = pot_lug_r * [-sin(pot_lug_a), cos(pot_lug_a)];
// Plate openings, layout frame. Circles are [centre, diameter, owner]: a tab
// hole shares its bushing hole's owner, so their web is checked against
// lug_web, every other pair against plate_web. Slots are [centre, [l, w]],
// full radius, along X.
plate_circles = concat(
    [for (b = btn_bc) [bpos(b), button_hole_d, ""]],
    [for (i = [0 : len(pot_bc) - 1]) [bpos(pot_bc[i]), pot_hole_d, str("pot", i)]],
    [for (i = [0 : len(pot_bc) - 1]) if (pot_lug)
        [bpos(pot_bc[i]) + pot_lug_off, pot_lug_d, str("pot", i)]],
    [[bpos(enc_bc), enc_hole_d, "enc"]],
    [if (enc_lug) [bpos(enc_bc) + [0, enc_lug_r], enc_lug_d, "enc"]],
    [for (i = [0 : len(tgl_bc) - 1]) [bpos(tgl_bc[i]), tgl_hole_d, str("tgl", i)]],
    [for (i = [0 : len(tgl_bc) - 1]) if (tgl_lug)
        [bpos(tgl_bc[i]) + [0, tgl_lug_r], tgl_lug_d, str("tgl", i)]],
    [for (p = slide_screw_pts) [p, slide_screw_d, ""]],
    [for (g = grille_pts) [bpos(buzzer_bc) + g, grille_hole_d, ""]]);
plate_slots  = [[bpos(slide_bc), slide_slot]];
pcm_c        = [batt_cx - batt_il/2 - batt_wall - pcm_gap - pcm_rim - pcm_l/2 - pcm_clear, batt_cy];
pcm_size     = [pcm_l + 2 * (pcm_clear + pcm_rim), pcm_w + 2 * (pcm_clear + pcm_rim)];
usb_end_x    = -outer_w/2 + usb_pocket_d;              // pocket inner end, layout frame
usb_cz       = chg_seat - usb_sock[1]/2;               // socket centre above the floor top
usb_z0       = usb_cz - usb_pocket[1]/2;               // pocket floor above the floor top
usb_top      = usb_z0 + usb_pocket[1] + usb_wall;
chg_x0       = usb_end_x + usb_end_t;                  // module's socket end
chg_len      = chg_l + chg_clear;
chg_yi       = chg_w/2 + chg_clear;                    // rail inner face from the centre line
chg_top      = chg_seat + chg_pcb_t + chg_clear + chg_lip_t;
// Tray features standing on the floor: [centre, size, height above the floor top].
batt_box     = [[batt_cx, batt_cy + (door_boss_off + door_boss_d/2 - batt_iw/2 - batt_wall)/2],
                [batt_il + 2 * batt_wall, batt_iw + 2 * batt_wall + door_boss_off + door_boss_d/2
                                          - batt_iw/2 - batt_wall],
                batt_wall_h];
chg_box      = [[(-inner_w/2 + chg_x0 + chg_len)/2, usb_y],
                [chg_x0 + chg_len + inner_w/2,
                 2 * max(usb_pocket[0]/2 + usb_wall, chg_yi + chg_rail_t)],
                max(usb_top, chg_top)];
pcm_box      = [pcm_c, pcm_size, pcm_rim_h];
floor_boxes  = [batt_box, chg_box, pcm_box];
// Plate controls behind the plate: [layout centre, body radius, depth].
controls     = concat(
    [for (b = btn_bc) [bpos(b), max(button_nut_d/2, button_switch_reach), button_depth]],
    [for (p = pot_bc) [bpos(p), pot_body_d/2, pot_depth]],
    [[bpos(enc_bc), enc_body * sqrt(2)/2, enc_depth]],
    [for (t = tgl_bc) [bpos(t), tgl_body_d/2, tgl_depth]],
    [[bpos(slide_bc), norm(slide_body)/2, slide_depth]]);
// Play-face features (controls, slide slot, buzzer grille, slide screw heads):
// [layout centre, radius].
face         = concat(
    [for (b = btn_bc) [bpos(b), button_bezel_d/2]],
    [for (p = concat(pot_bc, [enc_bc])) [bpos(p), knob_d/2]],
    [for (t = tgl_bc) [bpos(t), tgl_face_d/2]],
    [[bpos(slide_bc), slide_slot[0]/2 + 2]],
    [[bpos(buzzer_bc), grille_r + grille_hole_d/2]],
    [for (p = slide_screw_pts) [p, slide_head_d/2]]);
// Distance from point p to the rectangle of size sz centred on c (0 inside).
function rect_gap(p, c, sz) =
    norm([max(0, abs(p[0] - c[0]) - sz[0]/2), max(0, abs(p[1] - c[1]) - sz[1]/2)]);
// Depth of point p inside the origin-centred rounded rectangle of size sz
// and corner radius r (negative outside).
function rrect_inset(p, sz, r) =
    let(q = [abs(p[0]) - (sz[0]/2 - r), abs(p[1]) - (sz[1]/2 - r)])
    r - norm([max(q[0], 0), max(q[1], 0)]) - min(max(q[0], q[1]), 0);
// Distance from point p to the edge of the full-radius slot [l, w] along X
// centred on c (negative inside).
function slot_gap(p, c, sz) =
    norm([max(0, abs(p[0] - c[0]) - (sz[0] - sz[1])/2), p[1] - c[1]]) - sz[1]/2;

// --- Board behind the plate ---
// A standoff meets an LED on the board, so it clears the wider of v2's
// flange and v3's 5050; the slide nuts and the frame lip sit 13 mm above a
// v3 5050, so only v2's flange bounds them.
assert(pcb_to_panel >= jst_h + 2 && pcb_to_panel >= jst_lead_h,
       "pcb_to_panel must clear the JST-XH housings and their upward leads");
assert(pcb_to_panel >= max(u1_h, u2_h, f1_h, j9_h, buzzer_h) + 1,
       "pcb_to_panel must clear U1, U2, F1, J9 and the buzzer");
assert(pcb_to_panel >= max(u1_h, v3_boost_h, v3_f1_h, j9_h, jst_h, ds1_h, v3_buzzer_h) + 1,
       "pcb_to_panel must clear v3's U1, boost, F1, J9, JST-XH, DS1 and the buzzer");
assert(pcb_to_panel >= max(ds1_h, bar_h) + 1, "display bodies press on the plate");
assert(led_tip <= pcb_to_panel - 1, "LED tips press on the plate");
assert(v3_led_tip <= pcb_to_panel - 1, "v3 LED tops press on the plate");
assert(abs(standoff_l - pcb_to_panel) < 0.01,
       "pcb_to_panel is set by the standoffs: change standoff_l with it");
assert(len(ring_c) == 28 && len(led_c) == 50, "expected D1-D40 and D71-D80");
assert(boss_d <= 2 * pcb_keepout_r, "PCB posts intrude on the 3.5 mm hole keepout");
for (c = led_c, h = pcb_holes)
    assert(norm(c - h) >= boss_d/2 + max(led_flange_d, v3_led_span)/2 + 1,
           "an LED runs into a PCB standoff");
for (p = slide_screw_pts, c = led_c)
    assert(norm(p - bpos(c)) >= slide_nut_d/2 + led_flange_d/2 + 0.5,
           "a slide-switch nut or screw hits an LED");
assert(slide_screw_l - panel_t <= pcb_to_panel - 1, "slide-switch screws reach the board");
for (h = pcb_holes, q = controls)
    assert(norm(bpos(h) - q[0]) >= boss_d/2 + q[1] + 1, "a control body hits a PCB post");
for (h = pcb_holes, b = floor_boxes)
    assert(rect_gap(bpos(h), b[0], b[1]) >= boss_d/2 + 1, "a PCB post hits a floor feature");
assert(pcb_l/2 + pcb_clear + post_gap <= post_x - post_r
       && pcb_w/2 + pcb_clear + post_gap <= post_y - post_r, "tray posts must stand outside the board");
assert(outer_w <= 250 && outer_h <= 250, "enclosure no longer fits the A1's 250 mm bed");

// --- Play face ---
face_clash = [for (i = [0 : len(face) - 2], j = [i + 1 : len(face) - 1])
                  if (norm(face[i][0] - face[j][0]) < face[i][1] + face[j][1] + 1) [i, j]];
assert(len(face_clash) == 0, str("play-face features overlap (face indices): ", face_clash));
assert(grille_hole_d <= 2, "buzzer grille holes must be at most 2 mm across");
assert(grille_pitch - grille_hole_d >= 1, "grille webs too thin");
assert(grille_r + grille_hole_d/2 <= buzzer_d/2, "grille runs past the piezo");

// --- Clear plate: openings are controls, tab holes, slide switch and grille only ---
assert(len(plate_slots) == 1
       && len(plate_circles) == len(btn_bc) + len(pot_bc) * (pot_lug ? 2 : 1) + (enc_lug ? 2 : 1)
                                + len(tgl_bc) * (tgl_lug ? 2 : 1) + 2 + len(grille_pts),
       "the plate has an opening beyond the controls, tab holes, slide switch and buzzer grille");
assert(len(btn_bc) == 6 && len(pot_bc) == 3 && len(tgl_bc) == 3 && len(grille_pts) == 7,
       "expected six buttons, three pots, three toggles and a seven-hole grille");
assert(min([for (c = plate_circles) c[1]]) >= 1.5, "a plate hole is below the 1.5 mm the service drills");
plate_thin = [for (i = [0 : len(plate_circles) - 2], j = [i + 1 : len(plate_circles) - 1])
                  let(a = plate_circles[i], b = plate_circles[j])
                  if (norm(a[0] - b[0]) - (a[1] + b[1])/2
                      < (a[2] != "" && a[2] == b[2] ? lug_web : plate_web)) [i, j]];
assert(len(plate_thin) == 0, str("plate webs too thin (plate_circles indices): ", plate_thin));
for (s = plate_slots, c = plate_circles)
    assert(slot_gap(c[0], s[0], s[1]) - c[1]/2 >= plate_web, "a plate hole runs into the slide slot");
for (f = face)
    assert(rrect_inset(f[0], [frame_win, frame_win], frame_win_r) >= f[1] + 1,
           "a control, slide screw head or the grille runs under the frame lip");
for (c = led_c)
    assert(rrect_inset(bpos(c), [frame_win, frame_win], frame_win_r) >= led_flange_d/2 + 1,
           "an LED is hidden under the frame lip");
for (c = plate_circles)
    assert(rrect_inset(c[0], [frame_win, frame_win], frame_win_r) >= c[1]/2 + 1,
           "a plate hole runs under the frame lip");
assert(frame_overlap >= 3, "the frame lip must overlap the plate's cut edge by 3 mm or more");
assert(post_x - post_r - plate_w/2 >= 0.3 && post_y - post_r - plate_w/2 >= 0.3,
       "the plate runs into the frame posts");
assert(pcb_l/2 + pcb_clear <= plate_w/2 && pcb_w/2 + pcb_clear <= plate_w/2,
       "the board is wider than the plate");
assert(lip_r <= frame_lip_t - 0.8, "lip_r must fit the frame lip");

// --- Controls ---
assert(inner_d >= button_depth + 2, "arcade buttons are deeper than the cavity");
for (q = controls) assert(q[2] + 2 <= inner_d, "a control is deeper than the cavity");
assert(button_nut_d <= btn_cut_d && button_switch_reach <= btn_cut_d/2,
       "arcade buttons do not pass the board cut-outs");
assert(pot_body_d <= pot_cut_d, "pots do not pass the board cut-outs");
assert(enc_body_h <= pcb_to_panel - 1 || enc_body * sqrt(2) <= enc_cut_d,
       "encoder body does not pass the board cut-out");
assert(tgl_body_d <= tgl_cut_d, "toggles do not pass the board cut-outs");
assert(slide_body[0] <= slide_cut[0] && slide_body[1] <= slide_cut[1],
       "slide switch does not pass the board cut-out");
for (q = controls, p = post_pts)
    assert(norm(q[0] - p) >= post_r + q[1] + 1, "a control hits a tray post");

// --- Tray floor: compartment, PCM pocket, charger and USB pocket ---
for (b = floor_boxes) {
    assert(b[2] + 0.5 <= under_pcb, "a floor feature reaches the board's solder side");
    for (q = controls)
        assert(q[2] + 1 <= inner_d - b[2] || rect_gap(q[0], b[0], b[1]) >= q[1] + 1,
               "a control body hits a floor feature");
    for (p = post_pts)
        assert(rect_gap(p, b[0], b[1]) >= post_r + 1, "a floor feature hits a tray post");
    assert(abs(b[0][0]) + b[1][0]/2 <= inner_w/2 + 0.01 && abs(b[0][1]) + b[1][1]/2 <= inner_h/2,
           "a floor feature runs out of the cavity");
}
for (i = [0 : len(floor_boxes) - 2], j = [i + 1 : len(floor_boxes) - 1])
    assert(abs(floor_boxes[i][0][0] - floor_boxes[j][0][0]) >= (floor_boxes[i][1][0] + floor_boxes[j][1][0])/2 + 1
           || abs(floor_boxes[i][0][1] - floor_boxes[j][0][1]) >= (floor_boxes[i][1][1] + floor_boxes[j][1][1])/2 + 1,
           "floor features overlap");
assert(abs(batt_cx) + batt_il/2 + batt_wall <= inner_w/2 - lip_clear - lip_t - 1
       && batt_cy - batt_iw/2 - batt_wall >= -inner_h/2 + lip_clear + lip_t + 1
       && batt_cy + door_boss_off + door_boss_d/2 <= inner_h/2 - lip_clear - lip_t - 1,
       "battery compartment runs into the cavity walls");
for (p = post_pts)
    assert(abs(p[0] - batt_cx) > reb_w/2 + post_r + 1
           || p[1] < batt_cy + reb_y0 - post_r - 1 || p[1] > batt_cy + reb_y1 + post_r + 1,
           "a post screw lands in the door rebate");
assert(usb_z0 >= 0, "USB pocket dips into the floor: raise chg_seat");
assert(usb_pocket[0] >= usb_sock[0] + 4 && usb_pocket[1] >= usb_sock[1] + 4,
       "USB pocket too tight for a plug overmould");
assert(chg_x0 >= -inner_w/2 + 2, "USB pocket shallower than the wall");
for (l = chg_led)
    assert(l[0] - chg_win_d/2 >= 1 && l[0] + chg_win_d/2 <= chg_l - 1
           && abs(l[1]) + chg_win_d/2 <= chg_yi - chg_ledge - 0.5,
           "a charge LED window runs under a cradle rail or off the module");
assert(door_t < floor_t, "door must be thinner than the floor");
assert(door_tab_t + 0.4 <= floor_t - door_t, "hook tabs too thick for the floor");
assert(door_flange_screw >= door_boss_off - batt_iw/2 + door_boss_d/2,
       "door flange does not cover the screw boss");
assert(door_tab_x + door_tab_w/2 + door_clear <= batt_il/2, "hook tabs run off the door");
assert(batt_lip < min(batt_il, batt_iw)/2 && batt_lip_t <= batt_wall_h - 2, "battery lips oversize");

// --- Fixings and edges ---
assert(insert_hole_d >= 2.4 && insert_hole_d <= min(boss_d, 2 * post_r, door_boss_d) - 2.5,
       "insert_hole_d must leave a wall in every post and boss");
assert(standoff_thread_l - pcb_t <= boss_insert_depth, "standoff threads bottom out in the PCB posts");
assert(boss_insert_depth <= inner_d - pcb_back - 1, "PCB post pockets too deep");
assert(tray_screw_l - floor_t <= post_insert_depth - 0.5, "tray screws bottom out in the posts");
assert(post_insert_depth <= inner_d - 2, "post pockets too deep");
assert(door_screw_l - door_t <= door_pocket, "door screw bottoms out");
assert(cs_h < floor_t && cs_h + 0.6 <= door_t, "floor or door too thin for the countersink");
assert(edge_r < corner_r && edge_r <= frame_t - 0.8, "edge radii must fit the frame");

// === Modules ===

// Rounded-rect vertical prism: hull of four corner cylinders.
// Centred on X/Y, base at z=0.
module rbox(w, l, h, r) {
    hull()
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * (w/2 - r), sy * (l/2 - r), 0])
                cylinder(r = r, h = h);
}

// Corner post for rounded_slab: radius rc in plan, its z=0 rim rounded to
// re. The lowest 45 degrees of the round are replaced by a chamfer so the
// edge prints on the bed without a drooping first layer.
module edge_post(rc, re, h) {
    rotate_extrude()
        polygon(concat(
            [[0, 0], [rc - 2 * re * (1 - cos(45)), 0]],
            [for (a = [-45 : 5 : 0]) [rc - re + re * cos(a), re + re * sin(a)]],
            [[rc, h], [0, h]]));
}

// Rounded-rect slab with its z=0 face edges rounded: the play face of the
// frame and the back face of the tray. Centred on X/Y, base at z=0.
module rounded_slab(w, l, h, rc, re) {
    hull()
        for (sx = [-1, 1], sy = [-1, 1])
            translate([sx * (w/2 - rc), sy * (l/2 - rc), 0])
                edge_post(rc, re, h);
}

// Heat-set insert pocket: blind hole running along -Z from its mouth at
// z=0, with an entry chamfer.
module insert_hole(depth, d = insert_hole_d) {
    translate([0, 0, -depth]) cylinder(d = d, h = depth + 0.01);
    translate([0, 0, -insert_chamfer])
        cylinder(d1 = d, d2 = d + 2 * insert_chamfer, h = insert_chamfer + 0.01);
}

// Countersunk M3 through hole: shank from z=-1, 90 degree head cone at z=0.
module csk_hole(t) {
    translate([0, 0, -1]) cylinder(d = screw_clear, h = t + 2);
    translate([0, 0, -0.01]) cylinder(d1 = screw_head, d2 = screw_clear, h = cs_h);
}

module post_positions() {
    for (p = post_pts) translate([p[0], p[1], 0]) children();
}

module hole_positions() {
    for (p = pcb_holes) translate(bpos(p)) children();
}

// Clear plate outline and openings, layout frame, seen from the play side:
// the DXF the sheet is cut from.
module plate_profile() {
    difference() {
        offset(r = plate_r) square(plate_w - 2 * plate_r, center = true);
        for (c = plate_circles) translate(c[0]) circle(d = c[1]);
        for (s = plate_slots) translate(s[0])
            hull() for (sx = [-1, 1]) translate([sx * (s[1][0] - s[1][1])/2, 0]) circle(d = s[1][1]);
    }
}

// Clear plate, play face down at z=0 and mirrored, like the frame. It is a
// polycarbonate sheet cut from the DXF, not printed: this STL is for
// viewing only.
module busy_board_plate() {
    mirror([1, 0, 0]) linear_extrude(panel_t) plate_profile();
}

// Frame window through the lip, from z=-1 past h, its z=0 (play-side) edge
// rounded to lip_r by hulls of stepped slices. As in edge_post, the lowest
// 45 degrees of the round are a chamfer so the face-down first layer does
// not droop.
module frame_window(w, r, h) {
    c = 2 * lip_r * (1 - cos(45));
    steps = concat([[c, -1], [c, 0]],
                   [for (a = [-45 : 15 : 0]) [lip_r * (1 - cos(a)), lip_r * (1 + sin(a))]]);
    for (i = [0 : len(steps) - 2]) hull()
        for (s = [steps[i], steps[i + 1]])
            translate([0, 0, s[1]]) rbox(w + 2 * s[0], w + 2 * s[0], 0.01, r + s[0]);
    translate([0, 0, -1]) rbox(w, w, h + 2, r);
}

// Frame in the layout frame: play face at z=0, the lip from there to
// frame_lip_t, the plate rebate behind it to the plate back plane at
// frame_t, then the locating lip and the tray posts rising toward +Z. The
// rebate is cut before the posts are added, so it never trims them.
module frame_body() {
    difference() {
        union() {
            difference() {
                rounded_slab(outer_w, outer_h, frame_t, corner_r, edge_r);
                frame_window(frame_win, frame_win_r, frame_t);
                // Rebate depth is exactly panel_t: sheet-thickness tolerance (about +-0.2 mm) is covered by the "standoff stack seats the plate flat" VERIFY note in meta.json.
                translate([0, 0, frame_lip_t])
                    rbox(rebate_w, rebate_w, panel_t + 1, plate_r + plate_clear);
            }
            translate([0, 0, frame_t - 0.01]) {
                // Locating lip inside the tray walls
                difference() {
                    rbox(inner_w - 2 * lip_clear, inner_h - 2 * lip_clear,
                         lip_d + 0.01, max(0.5, inner_r - lip_clear));
                    translate([0, 0, -1])
                        rbox(inner_w - 2 * (lip_clear + lip_t),
                             inner_h - 2 * (lip_clear + lip_t), lip_d + 3,
                             max(0.5, inner_r - lip_clear - lip_t));
                }
                // Tray posts, down to the floor
                post_positions() cylinder(r = post_r, h = inner_d + 0.01);
            }
        }
        // Inserts at the post tips
        post_positions()
            translate([0, 0, frame_t + inner_d]) insert_hole(post_insert_depth);
    }
}

// Frame in print orientation: play face on the bed. Mirrored so the layout
// reads correctly from the front once the printed frame is turned over.
module busy_board_frame() {
    mirror([1, 0, 0]) frame_body();
}

// Battery compartment walls on the floor top (z=0 here), in the
// compartment's own frame, with retaining lips on all four walls, the lead
// notch in the -X wall and the door-screw boss merged into the +Y wall.
module battery_compartment() {
    difference() {
        union() {
            difference() {
                translate([-batt_il/2 - batt_wall, -batt_iw/2 - batt_wall, 0])
                    cube([batt_il + 2 * batt_wall, batt_iw + 2 * batt_wall, batt_wall_h]);
                translate([-batt_il/2, -batt_iw/2, -1])
                    cube([batt_il, batt_iw, batt_wall_h + 2]);
            }
            // Lips, 45 degree underside: along the Y walls, then the X walls
            for (sy = [-1, 1])
                translate([-batt_il/2 + 2, sy * batt_iw/2, batt_wall_h - batt_lip_t])
                    rotate([90, 0, 90]) linear_extrude(batt_il - 4)
                        polygon([[0, 0], [0, batt_lip_t], [-sy * batt_lip, batt_lip_t]]);
            for (sx = [-1, 1])
                translate([sx * batt_il/2, batt_iw/2 - 2, batt_wall_h - batt_lip_t])
                    rotate([90, 0, 0]) linear_extrude(batt_iw - 4)
                        polygon([[0, 0], [0, batt_lip_t], [-sx * batt_lip, batt_lip_t]]);
            translate([0, door_boss_off, 0]) cylinder(d = door_boss_d, h = door_boss_h);
        }
        // Lead notch through the -X wall, full height
        translate([-batt_il/2 - batt_wall - 1, -lead_notch_w/2, -1])
            cube([batt_wall + batt_lip + 2, lead_notch_w, batt_wall_h + 3]);
    }
}

// Door opening, rebate, hook slots and screw pocket, cut from the tray in
// the compartment's frame with the floor's outer face at z=0.
module battery_door_cuts() {
    translate([-batt_il/2, -batt_iw/2, -1]) cube([batt_il, batt_iw, floor_t + 2]);
    translate([0, (reb_y0 + reb_y1)/2, -1]) rbox(reb_w, reb_y1 - reb_y0, door_t + 1, door_r);
    for (sx = [-1, 1])
        translate([sx * door_tab_x - door_tab_w/2 - door_clear,
                   reb_y0 - door_tab_l - door_clear, door_t])
            cube([door_tab_w + 2 * door_clear,
                  door_tab_l + door_clear + door_flange + 0.01, floor_t - door_t + 0.01]);
    translate([0, door_boss_off, door_t]) mirror([0, 0, 1]) insert_hole(door_pocket);
}

// PCM pocket on the floor top (z=0 here), layout frame: a low rim the PCM
// sits in on foam tape, open at both ends for its leads.
module pcm_pocket() {
    translate([pcm_c[0], pcm_c[1], 0]) difference() {
        translate([-pcm_size[0]/2, -pcm_size[1]/2, 0]) cube([pcm_size[0], pcm_size[1], pcm_rim_h]);
        translate([-pcm_l/2 - pcm_clear, -pcm_w/2 - pcm_clear, -1])
            cube([pcm_l + 2 * pcm_clear, pcm_w + 2 * pcm_clear, pcm_rim_h + 2]);
        translate([-pcm_size[0]/2 - 1, -pcm_w/4, -1]) cube([pcm_size[0] + 2, pcm_w/2, pcm_rim_h + 2]);
    }
}

// USB-C pocket housing on the floor top (z=0 here), layout frame: a closed
// box from the left wall's inner face to the pocket's end wall.
module usb_housing() {
    translate([-inner_w/2 - 0.01, usb_y - usb_pocket[0]/2 - usb_wall, -0.01])
        cube([chg_x0 + inner_w/2 + 0.01, usb_pocket[0] + 2 * usb_wall, usb_top + 0.01]);
}

// CR-TL24 cradle on the floor top (z=0 here), layout frame: two C-channel
// rails along X from the pocket's end wall; the module slides in component
// side down until its socket passes the end wall, and is hot-glued.
module charger_cradle() {
    translate([chg_x0 - 0.01, usb_y, 0])
        for (m = [0, 1]) mirror([0, m, 0]) {
            translate([0, chg_yi, 0]) cube([chg_len + 0.01, chg_rail_t, chg_top]);
            translate([0, chg_yi - chg_ledge, 0]) cube([chg_len + 0.01, chg_ledge + 0.01, chg_seat]);
            translate([0, chg_yi - chg_lip, chg_seat + chg_pcb_t + chg_clear])
                cube([chg_len + 0.01, chg_lip + 0.01, chg_lip_t]);
        }
}

// Plug pocket through the left (-X) wall and the socket opening in its end
// wall, cut from the tray with the floor's outer face at z=0.
module usb_pocket_cuts() {
    translate([-outer_w/2 - 1, usb_y - usb_pocket[0]/2, floor_t + usb_z0])
        cube([usb_pocket_d + 1, usb_pocket[0], usb_pocket[1]]);
    sw = usb_sock[0] + 2 * usb_sock_clear;
    sh = usb_sock[1] + 2 * usb_sock_clear;
    translate([usb_end_x - 0.01, usb_y - sw/2, floor_t + usb_cz - sh/2])
        cube([usb_end_t + 0.02, sw, sh]);
    // Charge-LED windows through the floor, under the module
    for (l = chg_led) translate([chg_x0 + l[0], usb_y + l[1], -1])
        cylinder(d = chg_win_d, h = floor_t + 2);
}

// Back tray: floor at z=0, opening toward +Z.
module busy_board_tray() {
    difference() {
        union() {
            difference() {
                rounded_slab(outer_w, outer_h, floor_t + inner_d, corner_r, edge_r);
                translate([0, 0, floor_t]) rbox(inner_w, inner_h, inner_d + 1, inner_r);
            }
            // PCB posts: the board's back rests on them, pcb_to_panel plus
            // pcb_t behind the plate, and the standoffs screw into them
            hole_positions()
                translate([0, 0, floor_t - 0.01]) cylinder(d = boss_d, h = pcb_post_h + 0.01);
            translate([batt_cx, batt_cy, floor_t - 0.01]) battery_compartment();
            translate([0, 0, floor_t - 0.01]) {
                pcm_pocket();
                usb_housing();
                charger_cradle();
            }
        }
        // Post screws, countersunk on the back face
        post_positions() csk_hole(floor_t);
        // Inserts at the PCB post tips
        hole_positions()
            translate([0, 0, floor_t + pcb_post_h]) insert_hole(boss_insert_depth);
        translate([batt_cx, batt_cy, 0]) battery_door_cuts();
        usb_pocket_cuts();
    }
}

// Battery door in print orientation: outer face at z=0, tabs rising.
module busy_board_battery_door() {
    dw = reb_w - 2 * door_clear;
    y0 = reb_y0 + door_clear;
    y1 = reb_y1 - door_clear;
    difference() {
        union() {
            translate([0, (y0 + y1)/2, 0])
                rbox(dw, y1 - y0, door_t, max(0.5, door_r - door_clear));
            for (sx = [-1, 1])
                translate([sx * door_tab_x - door_tab_w/2, y0 - door_tab_l, door_t - 0.01])
                    cube([door_tab_w, door_tab_l + door_flange - 2 * door_clear,
                          door_tab_t + 0.01]);
        }
        translate([0, door_boss_off, 0]) csk_hole(door_t);
    }
}
