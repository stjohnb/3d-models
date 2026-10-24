# Climbing frame: working notes on timber and materials (2026-10-20)

Geometry per issue clw_01M5CCN6MVAVKNHS7807JEQQJK: 2500 x 2000 x 2300 frame, deck 500 x 2000 at 1500,
slide off Y=0, ladder off Y=2000, two swings on the front beam X 500-2500.

## Sections (PAR, planed before treatment, finished sizes in brackets)
- Posts: 100x100 planed round-edge (~94x94, 3-6 mm radii), treated UC4, concreted 700 mm (2300 above ground), 6 x 3.0 m.
- Swing beam: 100x150 planed eased-edge C24 treated (~94x145) on edge, 1 x 3.0 m. Alt: 2 x 47x150 C24 bolted.
- Other top rails: 100x100 planed round-edge treated, rear 1 x 3.0 m, sides 2 x 2.4 m.
- Ladder stiles and braces: 47x100 planed eased-edge C24 treated (~44x94), 4 x 2.4 m.
- Deck frame (hidden): 47x100 regularised C24 treated, 3 x 2.4 m.
- Decking: 32x125 treated (27x120 finished), 16 boards x 0.5 m, 2 x 4.8 m.
- Rungs: 35 mm hardwood dowel, 6 x 0.5 m.
Model: use finished sizes; parameters for post size (default 94), corner radius, beam section.

## Beam check (two swings, 90 kg + seat, dynamic factor 3, span 2.0 m, loads 0.55 m in)
100x100 C16 80% utilised, 10 mm deflection -> no. 100x100 C24 54%, 7 mm -> marginal.
100x150 C24 on edge 24%, 2 mm (planed 94x145: 27%, 2.5 mm) -> recommended. 2 x 47x150 C24 25%, 2 mm -> same, cheaper.

## Belfast prices found (inc VAT unless noted)
- Haldane Fisher (Ladas Drive, Balmoral): 100x100 UC4 post 3.0 m £17.55 sale / £21.06; weathered-top 100x100 £5.40/m. Site blocks scripted fetch; stock at Belfast not confirmed.
- Murdock (Duncrue, Kennedy Way): 100x100 UC4 square post £8.49 (length not stated).
- JP Corry (Springfield Rd, Hillview Rd, Castlereagh): sawn treated from £0.74/m, unsized; decking from £3.20.
- MacBlair/Brooks, Toner: no online prices.
- UK reference: 47x100 C24 2.4 m £5-8; 47x150 C24 3.6 m £16-17; 100x150 2.4 m £23.65; decking 32x125 £3.2-3.6/m.

## Hardware and play items
- M12 galvanised coach bolts ~24 (~£35); swing hangers M12 through-bolt x4 (~£8 each); postcrete 12 bags (~£85); screws (~£20).
- 3 m wave slide for 1.5 m deck: £125-180 (Tuin £133, Garden Games £125, Caledonia Play £160, Liberty £179). NI delivery unconfirmed.
- Swing seats 2 x ~£25.

- Planed round-edge 100x100 UC4 (Bendrey Bros, England): £23.33 at 2.4 m, £34.99 at 3.6 m. No Belfast listing; ask Haldane Fisher / JP Corry.

## Rough total: timber ~£350-400 planed, hardware ~£170, play items ~£200 -> ~£700-800 (sawn would save £60-110).

## Stability (20 Oct, after the user asked about dropping depth to 1.5 m)
- Posts will be concreted: 3.0 m lengths, 700 in the ground, 2300 above. Decided by the user.
- Peak sideways chain pull: 0.6 mg at 45 deg, 0.84 mg at 60 deg, 1.5 mg at 90 deg. Two 30 kg kids at 60 deg ~0.5 kN at 2.3 m; two adults ~1.5 kN.
- Free-standing: FS vs tipping over the front posts 1.45 (2 m) / 1.0 (1.5 m) for two kids; tips for adults. Concreted: push/pull per rear post 0.19/0.25 kN kids, 0.57/0.76 kN adults; 300x700 collar ~120 kg. Post bending 94x94 C16, adults: 37% (6 share) / 74% (front 3 only).
- Conclusion: with concreted posts, 1.5 m depth is fine; add knee braces front post to side rail, M12 coach bolts. Concrete ~0.2-0.26 m3 (20-26 postcrete bags or site mix).
- Seat spacing vs EN 1176-2 (560 to post, 660 between): 2 m bay can't meet it; EN 71-8 home-use is less strict. Argues against narrowing the swing bay.
- Numbers from scratchpad/stability.js.

## Swing seats (20 Oct)
- Seats 42-44 cm wide: BERG PlayBase £29 (44x18, 80 kg, ropes for 1.8-3.0 m beams), Rebo rubber £35.95 (B&Q marketplace), Tuin rubber+2 m chains £98.68, Garden Games plastic 42x17 70 kg.
- Clear bay is 1800 (post faces at X=600 and 2400), not 2000. Two 44 cm seats: 307 mm equal gaps; spec as drawn is 225/450/225. BERG manual wants 450/450 -> 3.0 m frame. Plum domestic double swing is 2.22 m overall, so ~300 mm gaps is normal for kits.
- Options: equalise centres to 1125/1875 on 2.5 m; widen X to 3.0 m; or one seat + trapeze.
- DECIDED 20 Oct: 2.5 m is a hard limit; frame is for younger children; two seats stay. Equal gaps (centres 1125/1875) still worth proposing to the planner.

## 20 Oct, later: first issue shipped (PR #27, 6c08d91). Follow-up NOT to be filed yet (user's instruction).
Follow-up scope agreed so far: equalise seats 1125/1875 @440; PAR finished sizes + params (post size, corner radius, beam section); knee braces bool; frame_y param 1500-2500; buried 700 stubs in assembly only; cut list with Belfast prices.

## 20 Oct: centre-hung swings + monkey bars (user's idea, proposed on the page, not filed)
- Two 94x145 C24 cross beams along X at Y=700 and 1300, X 500..2500, housed on a NEW divider rail (X 500-600, 94x145) and the far side rail (upgrade to 94x145). Front rail back to 94x94.
- 7 rungs 35 mm at X 750..2250 (250 pitch), 506 clear between beam faces. Swing 1 X=1125 on Y=700 beam; swing 2 X=1875 on Y=1300 beam. Chains 1655 (hang from 2155).
- Checks (crossbeam_check.js): beam 94x145 18%, 94x94 C24 44%; divider rail 94x145 17%, 94x94 C24 40%. Reactions 1.9/0.8 kN.
- Hazards: bars over swing arcs (one activity at a time); rung height 2.3 m, hanging feet ~0.9-1.0 m for a 1.0-1.1 m child -> impact surface; arcs exit front face by 470 (45 deg) / 733 (60 deg).
- Budget -> ~£800-950. Alternative: single central beam at Y=1000 + separate light rails.
- diagrams_v1_edge_beam.js is the old drawing script.

## 20 Oct: next piece (user: "don't file until we pin it down") — the two 2 m ends are free
- Climbing wall on the X=0 (deck) end: horizontal 44x94 PAR boards on the outer post faces, mid stile 44x94 at Y=1000, 14 boards Z 100-1494, 6 mm gaps (<8 finger trap), ~9-12 bolt-on holds (UK 10-packs £16-25), M10x80 bolts for 44 mm boards. Board check (sides_check.js): 44x94 C16 at 1000 span 67% child; 134% without stile; adult 134% C24. Ply 18 mm fine but delaminates.
- End ladder on the X=2500 (swing) end: 44x94 stiles outside the far side rail at Y=700/1300 (under beam ends), 7 rungs 35 mm at 300 pitch Z 250-2050, 556 clear; top rung 88 below the rail underside; reach over the rail to the first bar at X=2250. Dowel 72% child / 215% adult -> tube if adults.
- Flagged for the next issue's defaults: rung pitch 300 (gap 265) instead of 250 (gap 215, inside the 89-230 head-entrapment band); swing 2 to X=1800 for 480 clearance to the ladder face (405 now).
- Added cost ~£175-235 -> project ~£975-1180. Params listed on the page. ends.svg added; diagrams_v2_crossbeams.js is the pre-wall drawing script.
- 20 Oct, later: user prefers a ROPE NET up the swing end instead of the rung ladder. Net 1.5 x 2.0 m, 16 mm rope, 250-300 mesh, six M10 eye bolts under the far side rail (Y 250-1750), bottom tied to a 94x94 bearer between the X=2500 posts at Z 150-250 (1905 of face, ~100 slack). Ladder kept as the cheap alternative (param). Prices: eBay used £20+£33; Online Playgrounds £134 (OOS); O'Rourke Playscapes NI £225-365 made to order; Huck £89-96/m2. CPSC flexible-opening entrapment band: perimeter 430-710 mm -> 250-300 mesh is clear. Added cost with net ~£280-475 -> project ~£1080-1430. diagrams_v3_ladder_end.js is the ladder drawing script.
- Applied Refined to clw_01M5CGXXBB1NEF5ZTRRGN78QF3 at ~11:50 after the user said "let that issue go through".
- DIY net (user's idea, 20 Oct): 6 verticals x 7 horizontals, 42 crossings, ~58 m of 16 mm rope -> buy 70-90 m. Knots: two-rope overhand at crossings (simplest) or stopper + clove hitch + half hitch; carrick/sheet bend are for pieced nets (Animated Knots). 16 mm blue PP 30 m coil £12.59 (SafetyLiftinGear); polyhemp 20 m reel £68 (Rope Services UK). DIY ~£70-180 vs bought £134-365.
- 20 Oct: third issue FILED as clw_01M5CMH1MTPKEK6YHW1ZP3DG97 (wall + net + rung pitch 300/6 rungs + swing 2 at 1800; ladder alternative out of scope), requirements approved, depends_on clw_01M5CGXXBB1NEF5ZTRRGN78QF3.

## A-frame swing end (draft, 2026-10-20, not filed)
- PR #28 merged; clw_01M5CMH1MTPKEK6YHW1ZP3DG97 was planned, refined from the dashboard and is PR #30 (Ready, awaiting merge).
- User: "change the rope net side to be a A-frame rather than cube". Read as the A in the end view (legs splayed along Y): the outward X rake breaks the 2.5 m limit (+620-840), inward loses swing 2.
- Legs 94x94 from the ground corners (Y 47/1953) to under the beam ends (Y 700/1300): rake 15.8 deg, 2391 above ground + 728 buried = 3.6 m stock. Apex tie 94x94 Z 2061-2155 (615 clear), bearer Z 150-244 (1700 clear). Side rails past the divider and far braces go; far side rail replaced by the tie.
- Net trapezoid 1673 bottom / 642 top / 1817 tall, 2.1 m2, 6 rows + 4 columns, 26 crossings, ~40 m rope (buy 60 m, 2 coils £25). V between strand and leg points up (safe); leg crosses rows at 74 deg.
- Checks: leg column 4%, bearer 28%, seat edge to leg face 386 / net plane 433. Cost change about -£30 to -£80.
- Model: aframe_end boolean default true; rake from beam_frac and frame_depth. Version 0.4.0. Open: leg feet at corners vs pulled in; keep cube path; merge #30 first.
- Scripts: aframe_check.js, aframe_diagram.js -> aframe_ends.svg, aframe_plan.svg; section in pages/index.html before Timber sections.
