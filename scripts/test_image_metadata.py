"""Tests for image_metadata.py.

Run with: python3 -m pytest scripts/test_image_metadata.py
"""

import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

from PIL import Image
from PIL.PngImagePlugin import PngInfo

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from image_metadata import (
    find_metadata,
    strip_metadata,
    tracked_images,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestRepoImagesAreClean(unittest.TestCase):
    """Every tracked image in this repo must carry no metadata."""

    def test_all_tracked_images_clean(self):
        offenders = {}
        for path in tracked_images(REPO_ROOT):
            reasons = find_metadata(os.path.join(REPO_ROOT, path))
            if reasons:
                offenders[path] = reasons
        if offenders:
            lines = [f"  {p}: {', '.join(r)}" for p, r in sorted(offenders.items())]
            self.fail(
                "Tracked images carry metadata:\n"
                + "\n".join(lines)
                + "\nRun: python3 scripts/image_metadata.py --fix"
            )


class TestFindAndStripMetadata(unittest.TestCase):

    def _write(self, tmp, name, im, **save_kwargs):
        path = os.path.join(tmp, name)
        im.save(path, **save_kwargs)
        return path

    def test_gps_exif_orientation_flagged_and_stripped(self):
        with tempfile.TemporaryDirectory() as tmp:
            im = Image.new("RGB", (40, 20), (10, 20, 30))
            exif = Image.Exif()
            exif[0x0112] = 6  # orientation
            gps_ifd = exif.get_ifd(0x8825)
            gps_ifd[1] = "N"
            gps_ifd[2] = (54.0, 34.0, 22.5)
            exif[0x8825] = gps_ifd
            path = self._write(tmp, "gps.jpg", im, format="JPEG", exif=exif)

            reasons = find_metadata(path)
            self.assertTrue(any("GPS" in r for r in reasons))

            strip_metadata(path)

            self.assertEqual(find_metadata(path), [])
            with Image.open(path) as out:
                self.assertEqual(out.size, (20, 40))

    def test_jpeg_comment_flagged_and_stripped(self):
        with tempfile.TemporaryDirectory() as tmp:
            im = Image.new("RGB", (10, 10), (1, 2, 3))
            path = self._write(
                tmp, "comment.jpg", im, format="JPEG", comment=b"hello world"
            )

            self.assertTrue(find_metadata(path))

            strip_metadata(path)

            self.assertEqual(find_metadata(path), [])

    def test_png_text_chunk_flagged_and_stripped(self):
        with tempfile.TemporaryDirectory() as tmp:
            im = Image.new("RGB", (10, 10), (4, 5, 6))
            info = PngInfo()
            info.add_text("Comment", "hello")
            path = self._write(tmp, "text.png", im, format="PNG", pnginfo=info)

            self.assertTrue(find_metadata(path))

            strip_metadata(path)

            self.assertEqual(find_metadata(path), [])

    def test_webp_exif_flagged_and_stripped(self):
        with tempfile.TemporaryDirectory() as tmp:
            im = Image.new("RGB", (10, 10), (7, 8, 9))
            exif = Image.Exif()
            exif[0x0110] = "TestCamera"
            path = self._write(tmp, "photo.webp", im, format="WEBP", exif=exif)

            self.assertTrue(find_metadata(path))

            strip_metadata(path)

            self.assertEqual(find_metadata(path), [])

    def test_icc_only_not_flagged_and_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            im = Image.new("RGB", (10, 10), (1, 2, 3))
            icc_bytes = b"fake-icc-profile-bytes-for-testing"
            path = self._write(tmp, "icc.jpg", im, format="JPEG", icc_profile=icc_bytes)

            self.assertEqual(find_metadata(path), [])

            strip_metadata(path)

            self.assertEqual(find_metadata(path), [])
            with Image.open(path) as out:
                self.assertEqual(out.info.get("icc_profile"), icc_bytes)

    def test_clean_image_reported_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            im = Image.new("RGB", (10, 10), (1, 2, 3))
            path = self._write(tmp, "clean.png", im, format="PNG")

            self.assertEqual(find_metadata(path), [])

    def test_mpo_comment_flagged_and_stripped(self):
        # iPhone-style multi-picture JPEG (gain-map/depth frame). Pillow opens
        # this as format "MPO", not "JPEG".
        with tempfile.TemporaryDirectory() as tmp:
            primary = Image.new("RGB", (10, 10), (1, 2, 3))
            secondary = Image.new("RGB", (10, 10), (4, 5, 6))
            path = os.path.join(tmp, "photo.mpo")
            primary.save(
                path, format="MPO", append_images=[secondary], save_all=True,
                comment=b"secret",
            )

            self.assertTrue(find_metadata(path))

            strip_metadata(path)

            self.assertEqual(find_metadata(path), [])
            with Image.open(path) as out:
                self.assertEqual(out.format, "JPEG")

    def _mpo_with_secondary_segment(self, tmp, segment):
        """Write a clean 2-frame MPO, then splice ``segment`` into frame 1.

        The segment goes right after frame 1's APP0, so Pillow's own
        seek()-time check (which only looks at the first segment) can't see
        it. Frame 1 is the last frame, so inserting bytes there shifts no
        MPF offsets.
        """
        path = os.path.join(tmp, "photo.mpo")
        Image.new("RGB", (10, 10), (1, 2, 3)).save(
            path, format="MPO", save_all=True,
            append_images=[Image.new("RGB", (10, 10), (4, 5, 6))],
        )
        self.assertEqual(find_metadata(path), [])
        with Image.open(path) as im:
            im.seek(1)
            offset = im.offset
        with open(path, "rb") as fh:
            data = fh.read()
        self.assertEqual(data[offset + 2:offset + 4], b"\xff\xe0")
        insert_at = offset + 4 + int.from_bytes(data[offset + 4:offset + 6], "big")
        with open(path, "wb") as fh:
            fh.write(data[:insert_at] + segment + data[insert_at:])
        return path

    @staticmethod
    def _jpeg_segment(marker, payload):
        return b"\xff" + marker + (len(payload) + 2).to_bytes(2, "big") + payload

    def test_mpo_secondary_frame_metadata_flagged_and_stripped(self):
        cases = {
            "comment": (b"\xfe", b"secret", "'comment' metadata"),
            "xmp": (
                b"\xe1",
                b"http://ns.adobe.com/xap/1.0/\x00<x:xmpmeta/>",
                "'xmp' metadata",
            ),
            "photoshop": (
                b"\xed", b"Photoshop 3.0\x008BIM\x04\x04", "'photoshop' metadata",
            ),
            "exif": (
                b"\xe1", b"Exif\x00\x00" + Image.Exif().tobytes(), "EXIF metadata",
            ),
        }
        for name, (marker, payload, reason) in cases.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                path = self._mpo_with_secondary_segment(
                    tmp, self._jpeg_segment(marker, payload),
                )

                self.assertIn(reason, find_metadata(path))

                strip_metadata(path)

                self.assertEqual(find_metadata(path), [])

    def test_mpo_secondary_frame_leading_xmp_flagged(self):
        # An APP1 XMP segment as a frame's first segment makes Pillow's seek()
        # treat it as EXIF; getexif() then fails to parse it.
        with tempfile.TemporaryDirectory() as tmp:
            path = self._mpo_with_secondary_segment(tmp, b"")
            with Image.open(path) as im:
                im.seek(1)
                offset = im.offset
            with open(path, "rb") as fh:
                data = fh.read()
            segment = self._jpeg_segment(
                b"\xe1", b"http://ns.adobe.com/xap/1.0/\x00<x:xmpmeta/>",
            )
            with open(path, "wb") as fh:
                fh.write(data[:offset + 2] + segment + data[offset + 2:])

            self.assertIn("'xmp' metadata", find_metadata(path))

    def test_exif_reported_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            exif = Image.Exif()
            exif[0x0110] = "TestCamera"
            path = self._write(
                tmp, "exif.jpg", Image.new("RGB", (10, 10)), format="JPEG",
                exif=exif,
            )

            self.assertEqual(find_metadata(path), ["EXIF metadata"])

    def test_lossless_webp_with_icc_and_exif_flagged_and_stripped(self):
        # Padding pushes the VP8L chunk well past a fixed 64-byte header scan.
        with tempfile.TemporaryDirectory() as tmp:
            im = Image.new("RGB", (10, 10), (7, 8, 9))
            icc_bytes = b"\x00" * 200
            exif = Image.Exif()
            exif[0x0110] = "TestCamera"
            path = self._write(
                tmp, "lossless.webp", im, format="WEBP", lossless=True,
                icc_profile=icc_bytes, exif=exif,
            )

            self.assertTrue(find_metadata(path))

            strip_metadata(path)

            self.assertEqual(find_metadata(path), [])
            with Image.open(path) as out:
                self.assertEqual(out.info.get("icc_profile"), icc_bytes)
                # Still lossless — not silently re-encoded lossy.
                with open(path, "rb") as fh:
                    self.assertIn(b"VP8L", fh.read())

    def test_animated_webp_keeps_all_frames_after_strip(self):
        with tempfile.TemporaryDirectory() as tmp:
            frames = [Image.new("RGB", (10, 10), (i * 10, 0, 0)) for i in range(3)]
            exif = Image.Exif()
            exif[0x0110] = "TestCamera"
            path = os.path.join(tmp, "anim.webp")
            frames[0].save(
                path, format="WEBP", save_all=True, append_images=frames[1:],
                duration=100, loop=0, exif=exif,
            )

            self.assertTrue(find_metadata(path))

            strip_metadata(path)

            self.assertEqual(find_metadata(path), [])
            with Image.open(path) as out:
                self.assertEqual(getattr(out, "n_frames", 1), 3)

    def test_lossless_animated_webp_stays_lossless_after_strip(self):
        with tempfile.TemporaryDirectory() as tmp:
            frames = [Image.new("RGB", (10, 10), (i * 10, 0, 0)) for i in range(3)]
            exif = Image.Exif()
            exif[0x0110] = "TestCamera"
            path = os.path.join(tmp, "anim-lossless.webp")
            frames[0].save(
                path, format="WEBP", save_all=True, append_images=frames[1:],
                duration=100, loop=0, lossless=True, exif=exif,
            )

            strip_metadata(path)

            self.assertEqual(find_metadata(path), [])
            with open(path, "rb") as fh:
                data = fh.read()
            self.assertIn(b"VP8L", data)
            self.assertNotIn(b"VP8 ", data)

    def test_animated_webp_with_orientation_raises_instead_of_mis_stripping(self):
        with tempfile.TemporaryDirectory() as tmp:
            frames = [Image.new("RGB", (10, 10), (i * 10, 0, 0)) for i in range(3)]
            exif = Image.Exif()
            exif[0x0112] = 6  # orientation
            path = os.path.join(tmp, "anim-rotated.webp")
            frames[0].save(
                path, format="WEBP", save_all=True, append_images=frames[1:],
                duration=100, loop=0, exif=exif,
            )

            with self.assertRaises(NotImplementedError):
                strip_metadata(path)


def _git_available():
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


@unittest.skipUnless(_git_available(), "git not available")
class TestTrackedImages(unittest.TestCase):

    def _init_repo(self, tmp):
        subprocess.run(["git", "init", tmp], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", tmp, "config", "user.email", "test@test.com"],
            capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "-C", tmp, "config", "user.name", "Test"],
            capture_output=True, check=True,
        )

    def test_filters_by_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._init_repo(tmp)
            for name in ("a.JPG", "b.webp", "c.txt"):
                with open(os.path.join(tmp, name), "w") as fh:
                    fh.write("x")
            subprocess.run(
                ["git", "-C", tmp, "add", "a.JPG", "b.webp", "c.txt"], check=True,
            )
            subprocess.run(
                ["git", "-C", tmp, "commit", "-m", "init"],
                capture_output=True, check=True,
            )

            self.assertEqual(sorted(tracked_images(tmp)), ["a.JPG", "b.webp"])


if __name__ == "__main__":
    unittest.main()
