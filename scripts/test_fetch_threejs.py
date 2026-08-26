"""Tests for fetch_threejs — staging and hash verification, no network."""

import hashlib
import os
import tempfile
import unittest
from unittest import mock

import fetch_threejs
import threejs_assets
from threejs_assets import THREEJS_ASSETS


class FakeResponse:
    def __init__(self, data: bytes):
        self._data = data

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class StageAssetsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._cwd = os.getcwd()
        os.chdir(self._tmp.name)
        self.addCleanup(lambda: os.chdir(self._cwd))

    def test_stage_assets_writes_nested_paths(self):
        stub = b"// stub"
        with mock.patch.object(fetch_threejs, "fetch_url", mock.Mock(return_value=stub)):
            written = fetch_threejs.stage_assets("out")

        expected = (
            os.path.join("out", "three.module.min.js"),
            os.path.join("out", "addons", "loaders", "STLLoader.js"),
            os.path.join("out", "addons", "controls", "OrbitControls.js"),
        )
        self.assertCountEqual(written, expected)
        for path in expected:
            self.assertTrue(os.path.isfile(path), f"{path} not written")
            with open(path, "rb") as f:
                self.assertEqual(f.read(), stub)

    def test_hash_mismatch_propagates(self):
        boom = mock.Mock(side_effect=ValueError("SHA-256 mismatch"))
        with mock.patch.object(fetch_threejs, "fetch_url", boom):
            with self.assertRaises(ValueError):
                fetch_threejs.stage_assets("out")


class AssetPathTests(unittest.TestCase):
    def test_asset_paths_match_importmap_prefix(self):
        for key, asset in THREEJS_ASSETS.items():
            path = asset["path"]
            self.assertFalse(path.startswith("/"), f"{key} path must be relative")
            self.assertNotIn("..", path, f"{key} path must not escape the vendor dir")
        for key in ("STLLoader", "OrbitControls"):
            self.assertTrue(
                THREEJS_ASSETS[key]["path"].startswith("addons/"),
                f"{key} must resolve under the three/addons/ import-map prefix",
            )


class FetchUrlTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._cwd = os.getcwd()
        os.chdir(self._tmp.name)
        self.addCleanup(lambda: os.chdir(self._cwd))
        patcher = mock.patch.dict(os.environ, {"ASSET_CACHE_DIR": self._tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _seed_cache(self, url: str, payload: bytes) -> None:
        cache_file = threejs_assets._cache_path(url)
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "wb") as f:
            f.write(payload)

    def test_fetch_url_verifies_sha256(self):
        url = "https://example.invalid/three.module.min.js"
        payload = b"// cached three"
        self._seed_cache(url, payload)
        offline = mock.Mock(side_effect=OSError("no network"))

        with mock.patch.object(threejs_assets.urllib.request, "urlopen", offline):
            data = threejs_assets.fetch_url(
                url, expected_sha256=hashlib.sha256(payload).hexdigest()
            )
        self.assertEqual(data, payload)

    def test_fetch_url_rejects_bad_cached_digest(self):
        url = "https://example.invalid/tampered.js"
        self._seed_cache(url, b"tampered")
        offline = mock.Mock(side_effect=OSError("no network"))

        with mock.patch.object(threejs_assets.urllib.request, "urlopen", offline):
            with self.assertRaises(ValueError):
                threejs_assets.fetch_url(url, expected_sha256="0" * 64)

    def test_fetch_url_prefers_cache_over_network(self):
        url = "https://example.invalid/three.module.min.js"
        payload = b"// cached three"
        self._seed_cache(url, payload)
        never_call = mock.Mock(side_effect=AssertionError("should not call network"))

        with mock.patch.object(threejs_assets.urllib.request, "urlopen", never_call):
            data = threejs_assets.fetch_url(
                url, expected_sha256=hashlib.sha256(payload).hexdigest()
            )
        self.assertEqual(data, payload)
        never_call.assert_not_called()

    def test_offline_fallback_returns_unpinned_cache(self):
        url = "https://example.invalid/unpinned.js"
        payload = b"// unpinned cached copy"
        self._seed_cache(url, payload)
        offline = mock.Mock(side_effect=OSError("no network"))

        with mock.patch.object(threejs_assets.urllib.request, "urlopen", offline):
            data = threejs_assets.fetch_url(url, expected_sha256=None)
        self.assertEqual(data, payload)

    def test_stale_cache_falls_through_to_network(self):
        url = "https://example.invalid/fresh.js"
        payload = b"// freshly downloaded"
        self._seed_cache(url, b"stale")

        fresh_response = FakeResponse(payload)
        online = mock.Mock(return_value=fresh_response)

        with mock.patch.object(threejs_assets.urllib.request, "urlopen", online):
            data = threejs_assets.fetch_url(
                url, expected_sha256=hashlib.sha256(payload).hexdigest()
            )
        self.assertEqual(data, payload)

        cache_file = threejs_assets._cache_path(url)
        with open(cache_file, "rb") as f:
            self.assertEqual(f.read(), payload)


if __name__ == "__main__":
    unittest.main()
