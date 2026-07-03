# Drill Socket Specification

The drill socket is an adapter for the Fisher-Price Power Workshop drill press. It
transfers rotation from the power handle (via the male square shaft at the bottom)
through a 90-degree bevel gear (at the top) into the drill press mechanism. A female
square socket inside the top accepts the drill bit's male shaft.

## Part Structure

From top to bottom, the drill socket consists of:

1. **Nose** — 8mm tall, 16mm OD / 13mm ID hollow cylindrical tip at the very top of the piece
2. **Angled teeth** — 8mm section of bevel gear teeth; tips flush with body/nose OD
3. **Body** — 8mm hollow cylindrical section (25.5mm OD, 2mm wall thickness) with an inner socket boss for the female square socket
4. **Flange** — 2mm thin disc acting as a mechanical stop (28.5mm diameter — the maximum diameter of the piece)
5. **Collar** — 12mm cylindrical transition to male shaft (9.5mm OD — smaller than standard 12.5mm)
6. **Square shaft** — 6.5mm male peg (6.5mm sides — smaller than standard 8.2mm)
7. **Cylindrical piece** — 1mm long, 4mm diameter cylindrical section at the very bottom of the shaft

## Side View

```
  Cross-section (not to scale):

        _________
       |/       \|                 ^
       |  nose   |  16mm OD       | 8mm  (nose, 13mm ID bore)
       |\_______/|                 v
       / /|||||\ \                 ^
      / / ||||| \ \                |
     / /  |||||  \ \               | 8mm  (angled teeth, tips flush w/ body)
    / /   |||||   \ \              |
   / /    |||||    \ \             v
     |  <-25.5mm->   |            ^
     |               |            | 2mm  (ring cavity — boss stand-off)
     |  __       __  |            |
     | |  |     |  | |            | 6mm  (hollow, 2mm walls + boss)
     | |__|     |__| |            |
     |               |            v
 <--------28.5mm-------->
  ___|               |___         ^
 |   |  (21.5mm ID)  |   |        | 2mm  (hollow)
 |___|_______________|___|
        |       |                  ^
        |collar |  9.5mm OD       |
        |       |                  | 12mm
        |       |                  |
        |_______|                  v
          |   |                    ^
          |sq.|  6.5mm sides      | 6.5mm
          |___|                    v
           |_|                     ^ 1mm (cylindrical piece, solid)

  Total length: 8 + 8 + 8 + 2 + 12 + 6.5 + 1 = 45.5mm
```

## Top View

```
  Looking down (not to scale):

         _______________
       /   ___________   \
      /   /   _______  \   \
     |   |   / _____ \  |   |
     |   |  | |     | | |   |
     |   |  | | [ ] | | |   |    [ ] = female square socket
     |   |  | |_____| | |   |          (8.6mm side)
     |   |   \_______/  |   |
      \   \___________/   /
       \_________________/

     |<--- 28.5mm --->|         flange OD (max diameter)
       |<- 25.5mm ->|           body OD = tooth tips at base
         |<- 22.5mm ->|         tooth valleys at base
           |<- 16mm ->|         nose OD = tooth tips at top
             |<13mm>|           nose ID (bore) = tooth valleys at top
```

## Nose

| Dimension | Value | Notes |
|-----------|-------|-------|
| Outer diameter | 16mm | Narrower than body; caliper-measured |
| Inner diameter | 13mm | Hollow bore acts as circular lead-in for drill bit |
| Height | 8mm | Smooth cylindrical tip at the top of the piece |

The nose is a hollow cylindrical section at the very top. The 13mm bore is larger
than the socket diagonal (~12.2mm), so the square socket walls only exist below
the nose — the nose acts as a circular lead-in funnel for the drill bit. It has
no teeth — the angled teeth begin below it.

## Angled Teeth (Bevel Gear)

| Dimension | Value | Notes |
|-----------|-------|-------|
| Height | 8mm | Section where teeth are present |
| Top diameter (tips) | 16mm | Flush with nose OD |
| Bottom diameter (tips) | 25.5mm | Flush with body OD |
| Tooth count | 24 | Corrected per issue #148 |
| Tooth depth | 1.5mm | Valleys recessed inward; valley diameters: 22.5mm at base, 13mm at top |

The angled teeth form a conical bevel gear. Tooth tips are flush with the body and
nose cylindrical edges — they do not protrude beyond those diameters. Valleys between
teeth are recessed 1.5mm inward from the surface. They mesh with the drill press drive gear.

## Body

| Dimension | Value | Notes |
|-----------|-------|-------|
| Outer diameter | 25.5mm | Cylindrical section below the teeth |
| Wall thickness | 2mm | Hollow shell (inner diameter 21.5mm) |
| Height | 8mm | Shorter section; teeth section extended to 8mm |
| Boss stand-off from flange | 2mm | Ring cavity at body base; `socket_boss_gap` |

The body is a hollow cylinder with 2mm walls. A cylindrical core at `collar_diameter`
(9.5mm OD) runs continuously from the collar base through the flange and body interior
to the base of the teeth zone. An inner socket boss (16mm diameter) surrounds this core
within the body, providing material for the square socket walls; the annular ring between
the boss (16mm) and the body inner wall (21.5mm) is open — forming a ring cavity that
continues the hollow interior visible through the flange.

The socket boss does not begin immediately at the flange. A 2mm stand-off
(`socket_boss_gap`) leaves a ring-shaped cavity at the base of the body (21.5mm ID,
2mm tall) for the drill housing to seat into before meeting the boss.

## Female Square Socket (internal)

The socket inside the top of the body accepts the drill bit's male square shaft.
The cross-section matches the standard female connection defined in
[`_connection.scad`](_connection.scad) (8.6mm side, snap ridge details), but the
depth is drill-socket-specific — significantly deeper than the standard 13mm socket.
Both the depth (21mm vs. 13mm standard) **and the ridge position (15.35mm vs. 7.35mm standard) are drill-socket-specific overrides**.

| Dimension | Value | Notes |
|-----------|-------|-------|
| Side length | 8.6mm | Matches standard female socket cross-section |
| Depth | 21mm | Drill-socket-specific (standard is 13mm) |
| Ridge position | 15.35mm | From opening; retains drill bit. Drill-socket-specific (standard is 7.35mm) — moved deeper so the ridge lies below the 13mm nose bore (which would otherwise erase it) and aligns with the drill bit's groove when the bit is fully seated. |

The female socket extends from the tip of the nose through the nose, angled teeth,
and into the body — a total depth of 21mm. See [CONNECTION_SPEC.md](CONNECTION_SPEC.md)
for the standard female socket cross-section and snap ridge details.

## Flange

| Dimension | Value | Notes |
|-----------|-------|-------|
| Thickness | 2mm | Consistent across both sketches |
| Outer diameter | 28.5mm | Maximum diameter of the entire piece |
| Inner diameter | 21.5mm | Hollow, matching body interior; flange is a ring, not a solid disc |

The flange acts as a mechanical stop — it rests against the drill press housing to
position the gear at the correct mesh depth. The flange is a hollow ring: the body's
interior (21.5mm) passes straight through it.

## Internal Bore

| Dimension | Value | Notes |
|-----------|-------|-------|
| Diameter | 4mm | Extends from bottom face up through shaft, collar, and 1.5mm above the flange base |
| Extent | From bottom face through square shaft, collar, and 1.5mm above the flange base (within the flange) | bore_d (4mm) < cyl_d (6mm), so 1mm of material remains around the bore in the cylindrical piece. Collar cylinder provides solid material through this extension. |

A 4mm diameter bore runs from the bottom face of the part up through the square
shaft and collar, extending 1.5mm above the flange base within the flange
(total bore depth: 21mm). The bore diameter (4mm) is smaller than the cylindrical piece diameter
(6mm), so 1mm of material remains around the bore in the bottom cylindrical piece.

## Male Connection (collar + shaft + cylindrical piece)

The bottom of the drill socket uses a male connection that is smaller than the
standard attachment connection. Both the cross-section dimensions and lengths
are drill-socket-specific.

| Section | Dimension | Value | Notes |
|---------|-----------|-------|-------|
| Collar | OD | 9.5mm | Drill-socket-specific (standard is 12.5mm) |
| Collar | Height | 12mm | Drill-socket-specific (standard is 8.3mm) |
| Square shaft | Side length | 6.5mm | Drill-socket-specific (standard is 8.2mm) |
| Square shaft | Length | 6.5mm | Drill-socket-specific (standard is 12.4mm) |
| Cylindrical piece | Length | 1mm | Not present in standard; small cylindrical section at the very bottom |
| Cylindrical piece | Diameter | 6mm | 1mm of material remains around the 4mm bore |

## Z-Axis Layout

Total length: 45.5mm. Individual section heights:

| # | Section | Height |
|---|---------|--------|
| 1 | Nose | 8mm |
| 2 | Angled teeth | 8mm |
| 3 | Body | 8mm |
| 4 | Flange | 2mm |
| 5 | Collar | 12mm |
| 6 | Square shaft | 6.5mm |
| 7 | Cylindrical piece | 1mm |
| | **Sum** | **45.5mm** |

## Diameter Summary

```
  Radial dimensions (not to scale):

  |<------------- 28.5mm ------------>|   flange OD (max diameter)
      |<-------- 25.5mm -------->|        body OD = tooth tips at base
        |<------ 21.5mm ------>|          body/flange inner diameter (hollow)
          |<---- 22.5mm ---->|            tooth valleys at base
            |<-- 16mm -->|               nose OD = tooth tips at top
              |<- 13mm ->|               nose ID (bore) = tooth valleys at top
               |<9.5mm>|                 collar OD (drill-socket-specific)
                |<6.5mm>|                shaft side (drill-socket-specific)
                 |<4mm>|                 cylindrical piece diameter
```

## Measurement Source

Dimensions provided by the part owner from direct measurement of the original
injection-molded part. Reference photographs (img-1, img-2, img-3) and
hand-drawn caliper sketches (img-4, img-5, img-6) are attached to issue #114.
Corrected dimensions (nose, male connection, hollow body, teeth, bore) from
issue #124.
