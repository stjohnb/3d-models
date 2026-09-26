"""Tests for fetch_terrain_heightmap — exercises the in-memory pipeline."""

import io
import os
import tempfile
import unittest
from unittest import mock

import numpy as np
from PIL import Image

import fetch_terrain_heightmap as fth


def _make_terrarium_png(arr_m: np.ndarray) -> bytes:
    """Encode an HxW float32 elevation array (metres) into a terrarium PNG."""
    enc = arr_m + 32768.0
    r = np.floor(enc / 256).astype(np.int32)
    rem = enc - r * 256.0
    g = np.floor(rem).astype(np.int32)
    b = np.clip(np.round((rem - g) * 256.0), 0, 255).astype(np.int32)
    rgb = np.stack([r, g, b], axis=-1).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(rgb, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class SlippyMathTests(unittest.TestCase):
    def test_lon_x_round_trip(self):
        n = 1 << 14
        for lon in (-179.99, -45.0, 0.0, 168.864580):
            x = fth.lon_to_x(lon, n)
            back = fth.x_to_lon(x, n)
            self.assertLess(abs(back - lon), 360 / n)

    def test_lat_y_round_trip(self):
        n = 1 << 14
        # int() truncates toward zero, so y_to_lat(lat_to_y(lat)) returns the
        # north edge of the tile containing lat. Tile size in latitude shrinks
        # away from the equator, but at zoom 14 it never exceeds ~0.022 deg.
        tolerance_deg = 360.0 / n
        for lat in (-60.0, -44.9957, 0.0, 50.0):
            y = fth.lat_to_y(lat, n)
            back = fth.y_to_lat(y, n)
            self.assertLess(abs(back - lat), tolerance_deg)


class DecodeTerrariumTests(unittest.TestCase):
    def test_known_pixel_decodes_to_expected_metres(self):
        # (R, G, B) = (128, 16, 64) -> 128*256 + 16 + 64/256 - 32768
        #                            = 32784.25 - 32768 = 16.25 m
        img = Image.new("RGB", (1, 1), (128, 16, 64))
        out = fth.decode_terrarium(img)
        self.assertEqual(out.shape, (1, 1))
        self.assertAlmostEqual(float(out[0, 0]), 16.25, places=4)

    def test_decode_round_trips_through_encoder(self):
        target = np.array([[100.0, 250.0], [-20.0, 1234.5]], dtype=np.float32)
        png = _make_terrarium_png(target)
        img = Image.open(io.BytesIO(png))
        out = fth.decode_terrarium(img)
        # Round-trip is exact-ish to ~1/256 m because of the B channel granularity.
        self.assertTrue(np.all(np.abs(out - target) < 1.0))


class FetchHeightmapTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._cwd = os.getcwd()
        os.chdir(self._tmp.name)
        self.addCleanup(lambda: os.chdir(self._cwd))

    def _single_tile_session(self, payload: bytes) -> mock.Mock:
        session = mock.Mock()
        resp = mock.Mock(status_code=200, content=payload)
        resp.raise_for_status = mock.Mock()
        session.get = mock.Mock(return_value=resp)
        session.headers = {}
        return session

    def test_end_to_end_pipeline_caches_and_records_extents(self):
        # Sentinel elevation written into the first and last *columns* of the
        # 256x256 tile.  The crop computed by fetch_heightmap for a 0.5 km bbox
        # at this lat/lon/zoom is well inside the tile horizontally (roughly
        # columns 18-92 of the 256-pixel wide tile grid), so these column-edge
        # sentinel pixels are always outside the crop region.  Asserting
        # elev_max_m < SENTINEL therefore confirms the crop actually trimmed them.
        SENTINEL = 9999.0
        elev = np.zeros((256, 256), dtype=np.float32)
        for i in range(256):
            elev[i, :] = i * 10.0  # 0 .. 2550 m row gradient
        # Overwrite first and last columns with the sentinel value.
        elev[:, 0] = SENTINEL
        elev[:, -1] = SENTINEL
        payload = _make_terrarium_png(elev)
        session = self._single_tile_session(payload)

        # At zoom 14 + lat=-45, one tile is ~2.4 km; a 0.5 km bbox may straddle
        # a tile boundary depending on where the centre falls. The test asserts
        # the *pipeline* — every requested tile is fetched, decoded, stitched,
        # and the cache is reused on the second call — not an exact tile count.
        kwargs = dict(
            lat=-44.9957,
            lon=168.8646,
            area_km=0.5,
            zoom=14,
            px=32,
            session=session,
        )
        img, meta = fth.fetch_heightmap(**kwargs)
        self.assertEqual(img.size, (32, 32))
        self.assertEqual(img.mode, "L")
        expected_calls = meta["tile_count_x"] * meta["tile_count_y"]
        self.assertEqual(session.get.call_count, expected_calls)

        # Sanity-check metadata.
        self.assertEqual(meta["px"], 32)
        self.assertEqual(meta["zoom"], 14)
        self.assertEqual(meta["missing_tiles"], [])
        self.assertGreater(meta["elev_max_m"], meta["elev_min_m"])
        self.assertEqual(meta["source"], fth.SOURCE_NAME)
        self.assertGreaterEqual(meta["elev_min_m"], 0.0)
        self.assertLessEqual(meta["elev_max_m"], 2550.0)
        # The crop must have trimmed the sentinel border: elev_max_m < 9999.
        self.assertLess(meta["elev_max_m"], SENTINEL)
        self.assertEqual(meta["elev_range_m"], round(meta["elev_max_m"] - meta["elev_min_m"]))
        # A second call should reuse the cache (no extra GET).
        session.get.reset_mock()
        fth.fetch_heightmap(**kwargs)
        session.get.assert_not_called()

    def test_missing_tile_is_recorded_and_filled_with_zero(self):
        session = mock.Mock()
        resp = mock.Mock(status_code=404, content=b"")
        resp.raise_for_status = mock.Mock()
        session.get = mock.Mock(return_value=resp)
        session.headers = {}
        img, meta = fth.fetch_heightmap(
            lat=-44.9957,
            lon=168.8646,
            area_km=0.5,
            zoom=14,
            px=16,
            session=session,
        )
        self.assertEqual(img.size, (16, 16))
        # Every requested tile 404s, so all of them are recorded.
        self.assertEqual(
            len(meta["missing_tiles"]),
            meta["tile_count_x"] * meta["tile_count_y"],
        )
        # Verify entry structure: each missing-tile record must carry z, x, y
        # keys and the z value must match the zoom level used in the call.
        first = meta["missing_tiles"][0]
        self.assertEqual(first["z"], 14)
        self.assertIn("x", first)
        self.assertIn("y", first)
        # All sea-level -> elev_min and elev_max collapse to 0; we still get a
        # valid PNG (normalisation uses range || 1.0).
        self.assertEqual(meta["elev_min_m"], 0.0)
        self.assertEqual(meta["elev_max_m"], 0.0)
        import math as _math
        _n = 1 << 14
        _km_per_deg_lon = 111.32 * _math.cos(_math.radians(-44.9957))
        _dlat = 0.25 / 111.32
        _dlon = 0.25 / _km_per_deg_lon
        expected_tx = fth.lon_to_x(168.8646 - _dlon, _n)
        expected_ty = fth.lat_to_y(-44.9957 + _dlat, _n)
        self.assertEqual(first["x"], expected_tx)
        self.assertEqual(first["y"], expected_ty)
        self.assertEqual(meta["elev_range_m"], 0)


    def test_empty_crop_raises_value_error(self):
        # Patch slippy-tile helpers so the bbox lands entirely outside the tile
        # grid, collapsing crop_l == crop_r == 0 and triggering ValueError.
        #
        # lon_to_x / lat_to_y always return 0  →  single 1×1 tile (256×256 px).
        # x_to_lon returns grid_w=170.0, grid_e=171.0 so the actual bbox
        # (~168.857..168.863) is west of the grid; both fractions are negative
        # and clamped to 0, making crop_l == crop_r == 0 → empty crop.
        # y_to_lat returns grid_n=-40.0, grid_s=-41.0 so the bbox (~-45) is
        # south of the grid; both fractions are > 1 and clamped to full_h,
        # making crop_t == crop_b == full_h → empty crop (belt-and-suspenders).
        elev = np.zeros((256, 256), dtype=np.float32)
        payload = _make_terrarium_png(elev)
        session = self._single_tile_session(payload)

        with mock.patch.object(fth, "lon_to_x", return_value=0), \
             mock.patch.object(fth, "lat_to_y", return_value=0), \
             mock.patch.object(fth, "x_to_lon", side_effect=[170.0, 171.0]), \
             mock.patch.object(fth, "y_to_lat", side_effect=[-40.0, -41.0]):
            with self.assertRaises(ValueError):
                fth.fetch_heightmap(
                    lat=-44.9957,
                    lon=168.8646,
                    area_km=0.5,
                    zoom=14,
                    px=32,
                    session=session,
                )

    def test_non_404_http_error_propagates(self):
        # A 500 response must propagate as requests.HTTPError, not be swallowed.
        import requests as req_mod

        session = mock.Mock()
        resp = mock.Mock(status_code=500, content=b"Internal Server Error")
        resp.raise_for_status = mock.Mock(side_effect=req_mod.HTTPError("500"))
        session.get = mock.Mock(return_value=resp)
        session.headers = {}

        with self.assertRaises(req_mod.HTTPError):
            fth.fetch_heightmap(
                lat=-44.9957,
                lon=168.8646,
                area_km=0.5,
                zoom=14,
                px=32,
                session=session,
            )

    def test_main_writes_output_files(self):
        # main() must save the PNG and JSON sidecar to the paths provided on the
        # command line.  fetch_heightmap is replaced with a stub that returns a
        # known small image and a minimal metadata dict.
        import json as json_mod

        stub_img = Image.new("L", (4, 4), color=128)
        stub_meta = {
            "elev_min_m": 10.0,
            "elev_max_m": 200.0,
            "elev_range_m": 190,
            "area_km": 0.5,
            "lat": -44.9957,
            "lon": 168.8646,
            "px": 4,
            "zoom": 14,
            "tile_count_x": 1,
            "tile_count_y": 1,
            "missing_tiles": [],
            "source": fth.SOURCE_NAME,
        }

        png_path = os.path.join(self._tmp.name, "out.png")
        json_path = os.path.join(self._tmp.name, "out.json")

        with mock.patch.object(
            fth, "fetch_heightmap", return_value=(stub_img, stub_meta)
        ):
            rc = fth.main([
                "--lat", "-44.9957",
                "--lon", "168.8646",
                "--area-km", "0.5",
                "--output", png_path,
                "--metadata-output", json_path,
            ])

        self.assertEqual(rc, 0)
        self.assertTrue(os.path.isfile(png_path), "PNG output not written")
        self.assertTrue(os.path.isfile(json_path), "JSON sidecar not written")

        written = Image.open(png_path)
        self.assertEqual(written.mode, "L")

        with open(json_path) as fh:
            loaded = json_mod.load(fh)
        self.assertEqual(loaded["elev_min_m"], 10.0)
        self.assertEqual(loaded["elev_max_m"], 200.0)


if __name__ == "__main__":
    unittest.main()
