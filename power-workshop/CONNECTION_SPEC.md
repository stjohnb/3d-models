# Power Workshop Attachment Connection Specification

All attachments (drill bit, flathead screwdriver, buffing wheel, etc.) share a common
square-peg connection that plugs into either the power handle or the manual screwdriver
handle.

## Sections

The sections of the male connection, starting from the tip are:

- A square section of side 8.2mm that runs for 3.5mm
- A square section of side 6.3mm that runs for 3.1mm
- A square section of side 8.2mm that runs for 5.8mm
- A circular section of diameter 12.5mm that runs for 8.3mm 

## Square Shaft (Male - on attachments)

```
        <- 8.2mm ->
        ___________
       |           |  ^
       |           |  | 3.5mm (tip)
       |           |  v
       |___     ___|  ^
           |   |      | 3.1mm (groove)
        ___|   |___   v
       |           |  ^
       |           |  |
       |           |  | 5.8mm (main shaft)
       |           |  |
       |___________|  v

       Total length: 12.4mm
```

| Dimension | Value | Notes |
|-----------|-------|-------|
| Side length | 8.2mm | Measured 8.19mm across one face, 8.18mm across other |
| Corner radius | 1.0mm | Corners rounded to match injection-molded originals (`corner_r`) |
| Total length | 12.4mm | 3.5 + 3.1 + 5.8, end of tip to start of collar |
| Groove width | 3.1mm | Narrowed section |
| Groove depth per side | 0.95mm | Shaft narrows from 8.2mm to 6.3mm at groove |
| Tip length | 3.5mm | From end of shaft to start of groove |
| Groove position (center from tip) | 5.05mm | Calculated: 3.5 + 3.1/2 |

## Collar (Transition between shaft and tool body)

| Dimension | Value |
|-----------|-------|
| Diameter | 12.5mm |
| Length | 8.3mm |

The collar sits between the square shaft and the round tool body (drill shaft, screwdriver
shaft, etc.). It is cylindrical.

## Square Socket (Female - in handles)

The socket accepts the square shaft. Dimensions include clearance for a press-fit.

| Dimension | Value | Notes |
|-----------|-------|-------|
| Side length | 8.6mm | +0.4mm clearance over shaft |
| Depth | 13mm | Deep enough to accept full 12.4mm shaft length |
| Ridge width | 3.1mm | Matches groove width |
| Ridge depth | 0.95mm | Matches groove depth |
| Ridge position | 7.35mm | From opening; aligns with groove when shaft fully inserted |

The socket has an internal snap ridge that retains attachments by engaging with the
shaft groove. The ridge uses a **corner-only octagonal profile** rather than
protruding on all four sides — created by intersecting the socket square with a
45-degree-rotated square. This allows the shaft's flat sides to pass freely while
the four corners provide enough interference to require moderate force for
insertion/removal, snapping into the groove for retention. The `ridge_depth`
parameter controls how far the corners protrude.

## Cross Section (side view)

```
  Shaft side view (not to scale):

  |<---------- 12.4mm --------->|<- 8.3mm ->|
  |                              |            |
  +---+    +--------------------+----+       |
  |   |    |                    |    | collar |
  |   +--+-+                    |    +-------+----
  |   |  | |                    |    | 12.5mm dia
  |   +--+-+                    |    +-------+----
  |   |    |                    |    |       |
  +---+    +--------------------+----+       |
  |   |    |                    |            |
  tip groove    main shaft         collar

  8.2  6.3  8.2mm
```

## Measurement Source

All dimensions measured with digital calipers from existing Power Workshop attachments
(grey buffing attachment and yellow screwdriver bit). Reference photos in this directory
(IMG_2832 through IMG_2839).
