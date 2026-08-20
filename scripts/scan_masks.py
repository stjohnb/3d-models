"""Per-frame masking for the photogrammetry pipeline.

Operator tool — not used by CI.

The camera is stationary and the object sits on a rotating platter, so the
platter's image position is fixed and gets specified once as an ellipse. The
platter itself is always kept: it rotates rigidly with the object and carries
trackable texture (and its known 150 mm diameter is what sets scale later).
Only the column of pixels above it varies per frame, so that is the only part
a per-frame salient-object segmentation has to decide.

Deliberately NOT temporal-median background subtraction: the object and the
platter occupy the same pixels in every frame, so their median is themselves
and differencing erases exactly what we want to keep.

Every function lazy-imports its third-party dependencies so the pure helpers
(`parse_ellipse`, `mask_filename`) stay importable outside `nix develop .#scan`.
"""

_SESSION = None


def parse_ellipse(text):
    """Parse a "cx,cy,rx,ry" pixel ellipse spec into four floats. Pure stdlib."""
    error = ValueError("--platter must be cx,cy,rx,ry in pixels")
    parts = text.split(",")
    if len(parts) != 4:
        raise error
    try:
        cx, cy, rx, ry = (float(p) for p in parts)
    except ValueError:
        raise error from None
    if rx <= 0 or ry <= 0:
        raise error
    return (cx, cy, rx, ry)


def mask_filename(image_name):
    """COLMAP's --ImageReader.mask_path convention: image filename plus .png."""
    return f"{image_name}.png"


def _read_frame(frame_path):
    import cv2

    frame = cv2.imread(str(frame_path), cv2.IMREAD_COLOR)
    if frame is None:
        raise RuntimeError(f"could not read frame {frame_path}")
    return frame


def platter_mask(shape, ellipse):
    """Filled ellipse over the platter. uint8, 0 or 255."""
    import cv2
    import numpy

    cx, cy, rx, ry = ellipse
    mask = numpy.zeros((shape[0], shape[1]), dtype=numpy.uint8)
    cv2.ellipse(
        mask,
        (int(round(cx)), int(round(cy))),
        (int(round(rx)), int(round(ry))),
        0, 0, 360, 255, -1,
    )
    return mask


def column_mask(shape, ellipse, height_px):
    """The convex column swept by the platter ellipse `height_px` pixels upward.

    Draws the ellipse at the platter and again translated up, then fills each
    image column between its topmost and bottommost set row. The result
    contains the platter and everything vertically above it, and nothing else.
    """
    import cv2
    import numpy

    cx, cy, rx, ry = ellipse
    mask = numpy.zeros((shape[0], shape[1]), dtype=numpy.uint8)
    axes = (int(round(rx)), int(round(ry)))
    cv2.ellipse(mask, (int(round(cx)), int(round(cy))), axes, 0, 0, 360, 255, -1)
    cv2.ellipse(
        mask,
        (int(round(cx)), int(round(cy - height_px))),
        axes, 0, 0, 360, 255, -1,
    )

    filled = mask > 0
    from_top = numpy.maximum.accumulate(filled, axis=0)
    from_bottom = numpy.maximum.accumulate(filled[::-1], axis=0)[::-1]
    return ((from_top & from_bottom) * 255).astype(numpy.uint8)


def salient_mask(frame_path):
    """Segment the salient foreground object in a frame. uint8, 0 or 255."""
    import cv2
    import numpy

    global _SESSION
    if _SESSION is None:
        from rembg import new_session

        try:
            _SESSION = new_session("u2net")
        except Exception as exc:
            raise RuntimeError(
                "rembg model download failed (needs network on first run; "
                "caches to ~/.u2net) — rerun, or use --mask-mode roi"
            ) from exc

    from rembg import remove

    frame = _read_frame(frame_path)
    alpha = remove(
        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
        session=_SESSION,
        only_mask=True,
    )
    return numpy.where(numpy.asarray(alpha) >= 128, 255, 0).astype(numpy.uint8)


def suggest_ellipse(frame_path):
    """Suggest a platter ellipse from one frame's largest salient component.

    A suggestion only — printed for the operator to check against
    roi-preview.jpg and pass back explicitly. Never applied unattended.
    """
    import cv2
    import numpy

    mask = salient_mask(frame_path)
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if count < 2:
        raise RuntimeError(
            f"no salient object found in {frame_path} — pass --platter explicitly"
        )
    largest = 1 + int(numpy.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x = float(stats[largest, cv2.CC_STAT_LEFT])
    y = float(stats[largest, cv2.CC_STAT_TOP])
    w = float(stats[largest, cv2.CC_STAT_WIDTH])
    h = float(stats[largest, cv2.CC_STAT_HEIGHT])
    return (x + w / 2, y + h / 2, w / 2, h / 2)


def frame_mask(frame_path, shape, ellipse, height_px, mode, on_empty=None):
    """Build one frame's mask: platter union (salient object within the column).

    `mode="roi"` skips segmentation entirely and keeps the whole column — the
    no-ML fallback. `on_empty` is called with `frame_path` when segmentation
    finds nothing above the platter; the frame is still usable (the platter
    union is non-empty), so it is never skipped.
    """
    import cv2
    import numpy

    column = column_mask(shape, ellipse, height_px)
    if mode == "roi":
        mask = column
    elif mode == "salient":
        salient = cv2.bitwise_and(salient_mask(frame_path), column)
        if on_empty is not None and not salient.any():
            on_empty(frame_path)
        mask = cv2.bitwise_or(platter_mask(shape, ellipse), salient)
    else:
        raise ValueError(f"unknown mask mode {mode!r}")

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return numpy.where(closed > 0, 255, 0).astype(numpy.uint8)


def write_masked_pair(frame, mask, image_path, mask_path):
    """Write the blacked-out frame and its mask PNG."""
    import cv2

    if not cv2.imwrite(str(image_path), cv2.bitwise_and(frame, frame, mask=mask)):
        raise RuntimeError(f"could not write {image_path}")
    if not cv2.imwrite(str(mask_path), mask):
        raise RuntimeError(f"could not write {mask_path}")
