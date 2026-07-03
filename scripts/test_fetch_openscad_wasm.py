"""Tests for fetch_openscad_wasm — exercises the in-memory parsing path."""

import hashlib
import os
import tempfile
import unittest
from unittest import mock

import fetch_openscad_wasm as foa


class FakeResponse:
    def __init__(self, data: bytes):
        self._data = data

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FetchAssetTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._cwd = os.getcwd()
        os.chdir(self._tmp.name)
        self.addCleanup(lambda: os.chdir(self._cwd))

    def test_fetch_asset_validates_hash_and_caches(self):
        payload = b"// not-really-openscad.js content"
        digest = hashlib.sha256(payload).hexdigest()
        opener = mock.Mock(return_value=FakeResponse(payload))

        with mock.patch.dict(foa.EXPECTED_HASHES, {"openscad.js": digest}, clear=False):
            data = foa.fetch_asset("openscad.js", opener=opener)
        self.assertEqual(data, payload)
        # Cache populated for subsequent calls.
        cache_path = os.path.join(foa.CACHE_DIR, "openscad.js")
        self.assertTrue(os.path.isfile(cache_path))
        with open(cache_path, "rb") as f:
            self.assertEqual(f.read(), payload)

    def test_fetch_asset_rejects_mismatched_hash(self):
        payload = b"tampered"
        opener = mock.Mock(return_value=FakeResponse(payload))
        with mock.patch.dict(foa.EXPECTED_HASHES, {"openscad.js": "0" * 64}, clear=False):
            with self.assertRaises(ValueError):
                foa.fetch_asset("openscad.js", opener=opener)

    def test_fetch_asset_reuses_cache_when_hash_matches(self):
        payload = b"cached-bytes"
        digest = hashlib.sha256(payload).hexdigest()
        os.makedirs(foa.CACHE_DIR, exist_ok=True)
        with open(os.path.join(foa.CACHE_DIR, "openscad.wasm"), "wb") as f:
            f.write(payload)
        opener = mock.Mock(side_effect=AssertionError("should not call network"))
        with mock.patch.dict(foa.EXPECTED_HASHES, {"openscad.wasm": digest}, clear=False):
            data = foa.fetch_asset("openscad.wasm", opener=opener)
        self.assertEqual(data, payload)
        opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
