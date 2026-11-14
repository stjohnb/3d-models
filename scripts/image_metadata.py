#!/usr/bin/env python3
"""Find and strip embedded metadata (EXIF/XMP/IPTC/comments) from tracked images.

Tracked images reach the public mirror (stjohnb/3d-models); phone photos and
marketplace exports can carry GPS coordinates, capture timestamps, device
info, or other metadata that should never be committed. ICC colour profiles
are the one thing this module treats as safe to keep.

Usage:
    python3 scripts/image_metadata.py [--fix] [paths...]

With no paths, checks every tracked image (git ls-files, filtered by
extension). Prints "path: reason" for each hit and exits 1 if any are found.
With --fix, strips each offending file in place and re-checks it, exiting 0
only if everything ends up clean.
"""

import argparse
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageOps, JpegImagePlugin

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")

# im.info keys that carry metadata worth flagging, beyond what getexif() sees.
_METADATA_INFO_KEYS = ("xmp", "XML:com.adobe.xmp", "photoshop", "comment")

# JPEG APP1 payload prefixes, used when scanning MPO secondary frames directly.
_JPEG_EXIF_PREFIX = b"Exif\x00"
_JPEG_XMP_PREFIXES = (
    b"http://ns.adobe.com/xap/1.0/\x00",
    b"http://ns.adobe.com/xmp/extension/\x00",
)

_GPS_IFD = 0x8825
_ORIENTATION_TAG = 0x0112


def repo_root():
    """Return the absolute path to the git repo root."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def tracked_images(root):
    """Return tracked file paths (relative to root) with an image extension."""
    result = subprocess.run(
        ["git", "-C", root, "ls-files", "-z"],
        capture_output=True, check=True,
    )
    parts = [p.decode() for p in result.stdout.split(b"\x00") if p]
    return [p for p in parts if p.lower().endswith(IMAGE_EXTENSIONS)]


def _jpeg_segment_metadata(fh, offset):
    """Return metadata reasons found in the JPEG header segments at ``offset``.

    Walks the marker segments of one embedded JPEG stream (from SOI up to
    SOS/EOI) and flags EXIF/XMP APP1, APP13 (Photoshop/IPTC), and COM
    segments. Used for MPO secondary frames, where Pillow only refreshes
    EXIF on seek() — and only when APP1 is the very first segment — while
    im.info's comment/xmp/photoshop keys always reflect frame 0.
    """
    reasons = []
    fh.seek(offset)
    if fh.read(2) != b"\xff\xd8":
        return ["unreadable MPO frame"]
    while True:
        byte = fh.read(1)
        if byte != b"\xff":
            return reasons
        marker = fh.read(1)
        while marker == b"\xff":
            marker = fh.read(1)
        if not marker or marker in (b"\xd9", b"\xda"):
            return reasons
        if marker == b"\x01" or b"\xd0" <= marker <= b"\xd7":
            continue
        length_bytes = fh.read(2)
        if len(length_bytes) < 2:
            return reasons
        length = int.from_bytes(length_bytes, "big") - 2
        if length < 0:
            return reasons
        if marker == b"\xfe":
            reasons.append("'comment' metadata")
            fh.seek(length, os.SEEK_CUR)
        elif marker == b"\xed":
            reasons.append("'photoshop' metadata")
            fh.seek(length, os.SEEK_CUR)
        elif marker == b"\xe1":
            payload = fh.read(length)
            if payload.startswith(_JPEG_EXIF_PREFIX):
                reasons.append("EXIF metadata")
            elif payload.startswith(_JPEG_XMP_PREFIXES):
                reasons.append("'xmp' metadata")
        else:
            fh.seek(length, os.SEEK_CUR)


def find_metadata(path):
    """Return a list of human-readable reasons ``path`` carries metadata.

    Empty list means the image is clean. Checks getexif() (and, within it,
    the GPS IFD specifically, so location exposure is obvious), then a fixed
    set of im.info keys (xmp/photoshop/comment), then PNG text
    chunks. Ignores icc_profile, dpi, jfif*, progressive/progression, and the
    WebP loop/background keys.

    MPO files (multi-picture JPEGs, e.g. iPhone gain-map/depth photos) can
    carry metadata in frames after the first. Pillow's im.info only reflects
    frame 0 for everything but EXIF, so each secondary frame's JPEG segments
    are also scanned directly for EXIF/XMP/Photoshop/comment markers.

    Caveat: if frame 0's own EXIF block is malformed enough that
    im.getexif() raises, GPS presence can't be checked (the raw segment
    scan flags EXIF/XMP/Photoshop/comment generically but doesn't parse the
    GPS IFD), so a corrupted-but-GPS-bearing primary frame may be reported
    as carrying "EXIF metadata" without "GPS location".
    """
    reasons = []
    frame_reasons = []
    has_exif = False
    has_gps = False
    with Image.open(path) as im:
        fmt = (im.format or "").upper()
        n_frames = getattr(im, "n_frames", 1) if fmt == "MPO" else 1
        if im.info.get("exif"):
            has_exif = True
        # Opened once up front (rather than per secondary frame) since real
        # MPOs only ever have 2 frames, but there's no reason to reopen.
        frame_fh = open(path, "rb") if n_frames > 1 else None
        try:
            for frame in range(n_frames):
                try:
                    if frame:
                        im.seek(frame)
                    exif = im.getexif()
                except (SyntaxError, IndexError):
                    # A secondary frame whose first segment is a non-EXIF
                    # APP1 (e.g. XMP): Pillow's seek() tries to parse it as
                    # EXIF. A malformed Photoshop/IPTC (APP13) resource
                    # block can also send Pillow's own APP-segment parser
                    # past the end of the segment (IndexError). Either way
                    # the raw segment scan below still reports it.
                    exif = None
                if frame:
                    # seek() sets im.offset before parsing the frame's
                    # segments, so it is valid even when the parse above
                    # failed.
                    frame_reasons.extend(_jpeg_segment_metadata(frame_fh, im.offset))
                if exif is None:
                    continue
                if len(exif) > 0:
                    has_exif = True
                gps = exif.get_ifd(_GPS_IFD) if exif else {}
                if gps:
                    has_gps = True
        finally:
            if frame_fh is not None:
                frame_fh.close()

        if has_exif:
            reasons.append("EXIF metadata")
        if has_gps:
            reasons.append("GPS location")

        for key in _METADATA_INFO_KEYS:
            if im.info.get(key):
                reasons.append(f"'{key}' metadata")
        for reason in frame_reasons:
            if reason not in reasons:
                reasons.append(reason)

        text = getattr(im, "text", None)
        if text:
            for key in text:
                reasons.append(f"PNG text chunk '{key}'")

    return reasons


def _webp_is_lossless(path):
    """Check whether a WebP file's image data chunk is VP8L (lossless).

    Walks the RIFF chunk list rather than sniffing a fixed-size header slice:
    in an extended (VP8X) WebP, ICCP/ANIM chunks can push the image data
    chunk past any fixed offset. For an animated WebP the image data sits
    inside ANMF chunks, so the first frame's sub-chunks are walked instead.
    """
    try:
        with open(path, "rb") as fh:
            header = fh.read(12)
            if len(header) < 12 or header[0:4] != b"RIFF" or header[8:12] != b"WEBP":
                return False
            while True:
                chunk_header = fh.read(8)
                if len(chunk_header) < 8:
                    return False
                fourcc = chunk_header[0:4]
                size = int.from_bytes(chunk_header[4:8], "little")
                if fourcc == b"VP8L":
                    return True
                if fourcc == b"VP8 ":
                    return False
                if fourcc == b"ANMF":
                    # 16-byte frame header (offsets, size, duration, flags),
                    # then the frame's own ALPH/VP8/VP8L sub-chunks.
                    fh.seek(16, os.SEEK_CUR)
                    continue
                fh.seek(size + (size & 1), os.SEEK_CUR)
    except OSError:
        return False


def strip_metadata(path):
    """Re-encode ``path`` in place with no EXIF/XMP/IPTC/comment metadata.

    Applies EXIF orientation to the pixels first (ImageOps.exif_transpose),
    since the saved file carries no orientation tag afterwards. An ICC
    profile, if present, is passed through untouched. Writes to a temp file
    in the same directory and os.replace()s over the original, so a failure
    can't truncate it.
    """
    directory = os.path.dirname(path) or "."
    with Image.open(path) as im:
        fmt = (im.format or "").upper()
        n_frames = getattr(im, "n_frames", 1)
        orientation = im.getexif().get(_ORIENTATION_TAG, 1)
        icc_profile = im.info.get("icc_profile")
        subsampling = (
            JpegImagePlugin.get_sampling(im) if fmt in ("JPEG", "MPO") else -1
        )

        animated = fmt == "WEBP" and n_frames > 1
        if animated and orientation not in (1, None):
            # ImageOps.exif_transpose only handles a single frame, and the
            # EXIF block (orientation tag included) is dropped on save either
            # way, so an animated WebP with a non-default orientation would
            # silently lose it rather than being safely reapplied per-frame.
            raise NotImplementedError(
                f"{path}: animated WebP with EXIF orientation {orientation} "
                "is not supported by strip_metadata() — per-frame transpose "
                "isn't implemented, so stripping would silently drop the "
                "correct orientation"
            )
        if orientation not in (1, None) and not animated:
            out = ImageOps.exif_transpose(im)
            quality = 92
        elif fmt == "MPO":
            # Pillow's quality="keep" re-encode requires im.format == "JPEG";
            # MPO is re-saved as JPEG below, so it can't take that path.
            out = im
            quality = 92
        else:
            out = im
            quality = "keep"
        out.load()

        save_kwargs = {}
        if icc_profile:
            save_kwargs["icc_profile"] = icc_profile

        if fmt in ("JPEG", "MPO"):
            # MPO (multi-picture JPEG, e.g. iPhone gain-map/depth photos) is
            # saved back as a plain single-frame JPEG: only the primary frame
            # carries the image people expect, and MPO's secondary frames are
            # where residual EXIF/GPS most often survives.
            save_fmt = "JPEG"
            save_kwargs["quality"] = quality
            # Pillow's quality="keep" re-encode otherwise carries the
            # original COM segment through verbatim even without a comment=
            # kwarg passed in.
            save_kwargs["comment"] = b""
            if subsampling >= 0:
                save_kwargs["subsampling"] = subsampling
        elif fmt == "WEBP":
            save_fmt = fmt
            if _webp_is_lossless(path):
                save_kwargs["lossless"] = True
            else:
                save_kwargs["quality"] = 90
            if animated:
                save_kwargs["save_all"] = True
                if "duration" in im.info:
                    save_kwargs["duration"] = im.info["duration"]
                if "loop" in im.info:
                    save_kwargs["loop"] = im.info["loop"]
        else:
            save_fmt = fmt

        fd, tmp_path = tempfile.mkstemp(
            dir=directory, prefix=".image-metadata-", suffix=os.path.splitext(path)[1]
        )
        os.close(fd)
        try:
            out.save(tmp_path, format=save_fmt, **save_kwargs)
        except Exception:
            os.remove(tmp_path)
            raise

    os.replace(tmp_path, path)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Find (and optionally strip) metadata from tracked images.",
    )
    parser.add_argument(
        "paths", nargs="*",
        help="Image paths to check (default: every tracked image)",
    )
    parser.add_argument(
        "--fix", action="store_true", default=False,
        help="Strip metadata from offending files in place",
    )
    args = parser.parse_args(argv)

    if args.paths:
        paths = args.paths
    else:
        root = repo_root()
        paths = [os.path.join(root, p) for p in tracked_images(root)]

    hits = {}
    for path in paths:
        reasons = find_metadata(path)
        if reasons:
            hits[path] = reasons

    if not hits:
        return 0

    if args.fix:
        still_bad = {}
        for path in hits:
            try:
                strip_metadata(path)
            except NotImplementedError as exc:
                still_bad[path] = [str(exc)]
                continue
            reasons = find_metadata(path)
            if reasons:
                still_bad[path] = reasons
        if still_bad:
            for path, reasons in sorted(still_bad.items()):
                print(f"{path}: {', '.join(reasons)}", file=sys.stderr)
            return 1
        return 0

    for path, reasons in sorted(hits.items()):
        print(f"{path}: {', '.join(reasons)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
