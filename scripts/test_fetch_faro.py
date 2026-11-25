"""Tests for fetch_faro / faro_assets — staging and hash pinning, no network."""

import hashlib
import os
import tempfile
import unittest
from unittest import mock

import faro_assets
import fetch_faro
import threejs_assets
from faro_assets import FARO_ASSET, FARO_VERSION


class StageAssetTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._cwd = os.getcwd()
        os.chdir(self._tmp.name)
        self.addCleanup(lambda: os.chdir(self._cwd))

    def test_stage_writes_bundle_with_pinned_hash(self):
        stub = b"// stub faro"
        fetch_mock = mock.Mock(return_value=stub)
        with mock.patch.object(fetch_faro, "fetch_url", fetch_mock):
            out = fetch_faro.stage_asset("out")

        self.assertEqual(out, os.path.join("out", "faro-web-sdk.iife.js"))
        with open(out, "rb") as f:
            self.assertEqual(f.read(), stub)
        fetch_mock.assert_called_once_with(
            FARO_ASSET["url"], expected_sha256=FARO_ASSET["sha256"], cache_subdir="faro"
        )

    def test_hash_mismatch_propagates_and_writes_nothing(self):
        boom = mock.Mock(side_effect=ValueError("SHA-256 mismatch"))
        with mock.patch.object(fetch_faro, "fetch_url", boom):
            with self.assertRaises(ValueError):
                fetch_faro.stage_asset("out")
        self.assertFalse(os.path.exists("out"))

    def test_tampered_download_is_rejected(self):
        env = mock.patch.dict(os.environ, {"ASSET_CACHE_DIR": self._tmp.name})
        with env, mock.patch.object(
            threejs_assets.urllib.request,
            "urlopen",
            mock.Mock(side_effect=OSError("no network")),
        ):
            # Seed a tampered cache entry under the faro subdir.
            cache_file = threejs_assets._cache_path(FARO_ASSET["url"], "faro")
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, "wb") as f:
                f.write(b"tampered")
            with self.assertRaises(ValueError):
                fetch_faro.stage_asset("out")
        self.assertFalse(os.path.exists("out"))


class PinTests(unittest.TestCase):
    def test_hash_is_well_formed(self):
        self.assertRegex(FARO_ASSET["sha256"], r"^[0-9a-f]{64}$")

    def test_url_and_paths_carry_the_pinned_version(self):
        self.assertIn(f"@grafana/faro-web-sdk@{FARO_VERSION}/", FARO_ASSET["url"])
        self.assertTrue(FARO_ASSET["url"].startswith("https://"))
        self.assertEqual(
            faro_assets.VENDOR_DIR, os.path.join("site", "vendor", "faro", FARO_VERSION)
        )
        self.assertEqual(
            faro_assets.SCRIPT_SRC,
            f"./vendor/faro/{FARO_VERSION}/{FARO_ASSET['path']}",
        )
        self.assertNotIn("..", FARO_ASSET["path"])
        self.assertFalse(FARO_ASSET["path"].startswith("/"))

    def test_faro_cache_is_separate_from_threejs(self):
        url = FARO_ASSET["url"]
        self.assertNotEqual(
            os.path.dirname(threejs_assets._cache_path(url, "faro")),
            os.path.dirname(threejs_assets._cache_path(url)),
        )

    def test_cached_copy_with_matching_hash_is_used(self):
        payload = b"// cached faro"
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(
            os.environ, {"ASSET_CACHE_DIR": tmp}
        ):
            url = "https://example.invalid/faro.js"
            cache_file = threejs_assets._cache_path(url, "faro")
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, "wb") as f:
                f.write(payload)
            never = mock.Mock(side_effect=AssertionError("network"))
            with mock.patch.object(threejs_assets.urllib.request, "urlopen", never):
                data = threejs_assets.fetch_url(
                    url,
                    expected_sha256=hashlib.sha256(payload).hexdigest(),
                    cache_subdir="faro",
                )
        self.assertEqual(data, payload)


if __name__ == "__main__":
    unittest.main()
