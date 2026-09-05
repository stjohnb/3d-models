"""Tests for asset_cache — cache root resolution and atomic writes, no network."""

import os
import tempfile
import unittest
from unittest import mock

import asset_cache


class CacheRootTests(unittest.TestCase):
    def test_default_root_is_under_home(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(asset_cache.ENV_VAR, None)
            root = asset_cache.cache_root()
        self.assertEqual(
            root, os.path.join(os.path.expanduser("~"), ".cache", "3d-models")
        )
        self.assertTrue(os.path.isabs(root))

    def test_default_root_is_outside_the_checkout(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(asset_cache.ENV_VAR, None)
            root = asset_cache.cache_root()
        self.assertFalse(root.startswith(os.getcwd()))

    def test_env_override_wins(self):
        with mock.patch.dict(os.environ, {asset_cache.ENV_VAR: "/tmp/somewhere"}):
            self.assertEqual(asset_cache.cache_root(), "/tmp/somewhere")

    def test_env_override_expands_tilde(self):
        with mock.patch.dict(os.environ, {asset_cache.ENV_VAR: "~/somewhere"}):
            self.assertEqual(
                asset_cache.cache_root(),
                os.path.join(os.path.expanduser("~"), "somewhere"),
            )

    def test_empty_env_override_falls_back_to_default(self):
        with mock.patch.dict(os.environ, {asset_cache.ENV_VAR: ""}):
            self.assertEqual(
                asset_cache.cache_root(),
                os.path.join(os.path.expanduser("~"), ".cache", "3d-models"),
            )

    def test_cache_dir_joins_parts(self):
        with mock.patch.dict(os.environ, {asset_cache.ENV_VAR: "/tmp/somewhere"}):
            self.assertEqual(
                asset_cache.cache_dir("openscad-wasm", "2022.03.20"),
                os.path.join("/tmp/somewhere", "openscad-wasm", "2022.03.20"),
            )


class WriteAtomicTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_write_atomic_creates_dirs_and_leaves_no_temp_file(self):
        path = os.path.join(self._tmp.name, "nested", "deep", "file.bin")
        asset_cache.write_atomic(path, b"hello")

        with open(path, "rb") as f:
            self.assertEqual(f.read(), b"hello")

        parent = os.path.dirname(path)
        self.assertEqual(os.listdir(parent), ["file.bin"])

    def test_write_atomic_overwrites_existing(self):
        path = os.path.join(self._tmp.name, "file.bin")
        asset_cache.write_atomic(path, b"first")
        asset_cache.write_atomic(path, b"second")

        with open(path, "rb") as f:
            self.assertEqual(f.read(), b"second")


class RequireSha256Tests(unittest.TestCase):
    def test_valid_lowercase_digest_returned_unchanged(self):
        digest = "a" * 64
        self.assertEqual(asset_cache.require_sha256(digest, "thing"), digest)

    def test_uppercase_digest_is_lowercased(self):
        digest = "A" * 64
        self.assertEqual(asset_cache.require_sha256(digest, "thing"), "a" * 64)

    def test_surrounding_whitespace_is_stripped(self):
        digest = "b" * 64
        self.assertEqual(
            asset_cache.require_sha256(f"  {digest}\n", "thing"), digest
        )

    def test_none_raises(self):
        with self.assertRaisesRegex(ValueError, "thing"):
            asset_cache.require_sha256(None, "thing")

    def test_empty_string_raises(self):
        with self.assertRaisesRegex(ValueError, "thing"):
            asset_cache.require_sha256("", "thing")

    def test_non_string_zero_raises(self):
        with self.assertRaisesRegex(ValueError, "thing"):
            asset_cache.require_sha256(0, "thing")

    def test_non_string_bytes_raises(self):
        with self.assertRaisesRegex(ValueError, "thing"):
            asset_cache.require_sha256(b"a" * 64, "thing")

    def test_too_short_raises(self):
        with self.assertRaisesRegex(ValueError, "thing"):
            asset_cache.require_sha256("abc", "thing")

    def test_non_hex_raises(self):
        with self.assertRaisesRegex(ValueError, "thing"):
            asset_cache.require_sha256("z" * 64, "thing")


if __name__ == "__main__":
    unittest.main()
