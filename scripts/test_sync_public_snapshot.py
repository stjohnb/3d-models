"""Tests for sync_public_snapshot.py.

Run with: python3 -m pytest scripts/test_sync_public_snapshot.py
"""

import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from sync_public_snapshot import (
    SECRET_SCAN_SKIP,
    SNAPSHOT_EXCLUDES,
    STAGING_MARKER,
    StagingDirError,
    build_snapshot,
    is_excluded,
    mirror_files,
    prepare_staging_dir,
    scan_for_secrets,
)


class TestIsExcluded(unittest.TestCase):

    def test_exact_file_match(self):
        self.assertTrue(is_excluded("docs/blog-post.md"))
        self.assertTrue(is_excluded("docs/website-checklist-audit.md"))
        self.assertTrue(is_excluded(".mcp-claws.json"))

    def test_directory_prefix_match(self):
        self.assertTrue(is_excluded("ideas/rejected.md"))
        self.assertTrue(is_excluded("ideas/some-deep/path.md"))
        self.assertTrue(is_excluded("ideas"))

    def test_not_excluded(self):
        self.assertFalse(is_excluded("docs/OVERVIEW.md"))
        self.assertFalse(is_excluded("power-workshop/drill_bit.scad"))
        self.assertFalse(is_excluded("README.md"))
        self.assertFalse(is_excluded("index.html"))

    def test_prefix_boundary_correctness(self):
        # "ideas-backlog.md" must NOT be excluded by the "ideas" entry
        self.assertFalse(is_excluded("ideas-backlog.md"))
        # "docs/blog-post.md.bak" must NOT match the exact "docs/blog-post.md" entry
        self.assertFalse(is_excluded("docs/blog-post.md.bak"))

    def test_custom_excludes(self):
        self.assertTrue(is_excluded("secret/dir/file.txt", excludes=["secret"]))
        self.assertFalse(is_excluded("public/file.txt", excludes=["secret"]))


class TestScanForSecrets(unittest.TestCase):

    def test_flags_planted_jwt(self):
        with tempfile.TemporaryDirectory() as tmp:
            fpath = os.path.join(tmp, "token.txt")
            with open(fpath, "w") as fh:
                fh.write("eyJabcdefghij.klmnopqrstuvwx.uvwxyz0123456789\n")
            hits = scan_for_secrets(tmp, ["token.txt"])
        self.assertTrue(any("token.txt" == h[0] for h in hits))

    def test_flags_claws_token_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            fpath = os.path.join(tmp, "config.env")
            with open(fpath, "w") as fh:
                fh.write("CLAWS_MCP_AUTH_TOKEN=abc123\n")
            hits = scan_for_secrets(tmp, ["config.env"])
        self.assertTrue(any("config.env" == h[0] for h in hits))

    def test_clean_scad_no_hits(self):
        with tempfile.TemporaryDirectory() as tmp:
            fpath = os.path.join(tmp, "part.scad")
            with open(fpath, "w") as fh:
                fh.write("$fn = 64;\ncylinder(h=10, r=5);\n")
            hits = scan_for_secrets(tmp, ["part.scad"])
        self.assertEqual(hits, [])

    def test_ignores_binary_no_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            fpath = os.path.join(tmp, "binary.bin")
            with open(fpath, "wb") as fh:
                fh.write(bytes(range(256)))
            hits = scan_for_secrets(tmp, ["binary.bin"])
        self.assertEqual(hits, [])

    def test_home_assistant_token_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            fpath = os.path.join(tmp, "settings.py")
            with open(fpath, "w") as fh:
                fh.write("HOME_ASSISTANT_TOKEN = os.getenv('HA_TOKEN')\n")
            hits = scan_for_secrets(tmp, ["settings.py"])
        self.assertTrue(any("settings.py" == h[0] for h in hits))

    def test_skips_scanner_own_files(self):
        # The scanner's own source/tests/docs legitimately contain the pattern
        # strings; they must not be flagged as secrets.
        skip_path = "scripts/sync_public_snapshot.py"
        self.assertIn(skip_path, SECRET_SCAN_SKIP)
        with tempfile.TemporaryDirectory() as tmp:
            fpath = os.path.join(tmp, "skipped.txt")
            with open(fpath, "w") as fh:
                fh.write("CLAWS_MCP_AUTH_TOKEN=abc123\n")
            hits = scan_for_secrets(tmp, ["skipped.txt"], skip={"skipped.txt"})
        self.assertEqual(hits, [])


class TestBuildSnapshot(unittest.TestCase):

    def test_copies_included_files(self):
        with tempfile.TemporaryDirectory() as src:
            with tempfile.TemporaryDirectory() as dst:
                # Create files: one included, one in ideas/
                keep_dir = os.path.join(src, "keep")
                os.makedirs(keep_dir)
                with open(os.path.join(keep_dir, "a.scad"), "w") as fh:
                    fh.write("sphere(10);")
                ideas_dir = os.path.join(src, "ideas")
                os.makedirs(ideas_dir)
                with open(os.path.join(ideas_dir, "x.md"), "w") as fh:
                    fh.write("idea")

                included = ["keep/a.scad"]
                build_snapshot(src, dst, included)

                self.assertTrue(os.path.isfile(os.path.join(dst, "keep", "a.scad")))
                self.assertFalse(os.path.exists(os.path.join(dst, "ideas", "x.md")))

    def test_creates_staging_dir_if_missing(self):
        with tempfile.TemporaryDirectory() as src:
            with tempfile.TemporaryDirectory() as parent:
                staging = os.path.join(parent, "new_staging")
                with open(os.path.join(src, "file.txt"), "w") as fh:
                    fh.write("hello")
                build_snapshot(src, staging, ["file.txt"])
                self.assertTrue(os.path.isfile(os.path.join(staging, "file.txt")))

    def test_preserves_file_contents(self):
        with tempfile.TemporaryDirectory() as src:
            with tempfile.TemporaryDirectory() as dst:
                content = "module test() { cube(10); }\n"
                with open(os.path.join(src, "part.scad"), "w") as fh:
                    fh.write(content)
                build_snapshot(src, dst, ["part.scad"])
                with open(os.path.join(dst, "part.scad")) as fh:
                    self.assertEqual(fh.read(), content)

    def test_removes_stale_file_from_staging(self):
        with tempfile.TemporaryDirectory() as src:
            with tempfile.TemporaryDirectory() as dst:
                keep_dir = os.path.join(src, "keep")
                os.makedirs(keep_dir)
                with open(os.path.join(keep_dir, "a.scad"), "w") as fh:
                    fh.write("sphere(10);")

                with open(os.path.join(dst, STAGING_MARKER), "w") as fh:
                    fh.write("marker")
                stale_dir = os.path.join(dst, "secret")
                os.makedirs(stale_dir)
                with open(os.path.join(stale_dir, "leak.md"), "w") as fh:
                    fh.write("should not survive")

                build_snapshot(src, dst, ["keep/a.scad"])

                self.assertTrue(os.path.isfile(os.path.join(dst, "keep", "a.scad")))
                self.assertFalse(os.path.exists(os.path.join(dst, "secret", "leak.md")))

    def test_removes_stale_file_deleted_from_repo(self):
        with tempfile.TemporaryDirectory() as src:
            with tempfile.TemporaryDirectory() as dst:
                with open(os.path.join(dst, STAGING_MARKER), "w") as fh:
                    fh.write("marker")
                with open(os.path.join(dst, "gone.md"), "w") as fh:
                    fh.write("should not survive")

                build_snapshot(src, dst, [])

                self.assertFalse(os.path.exists(os.path.join(dst, "gone.md")))

    def test_marker_written(self):
        with tempfile.TemporaryDirectory() as src:
            with tempfile.TemporaryDirectory() as dst:
                build_snapshot(src, dst, [])
                self.assertTrue(os.path.isfile(os.path.join(dst, STAGING_MARKER)))


class TestPrepareStagingDir(unittest.TestCase):

    def test_refuses_unmarked_non_empty_dir(self):
        with tempfile.TemporaryDirectory() as dst:
            important = os.path.join(dst, "important.txt")
            with open(important, "w") as fh:
                fh.write("do not delete")

            with self.assertRaises(StagingDirError):
                prepare_staging_dir(dst)

            self.assertTrue(os.path.isfile(important))

    def test_build_snapshot_refuses_unmarked_dir(self):
        with tempfile.TemporaryDirectory() as src:
            with tempfile.TemporaryDirectory() as dst:
                important = os.path.join(dst, "important.txt")
                with open(important, "w") as fh:
                    fh.write("do not delete")

                with self.assertRaises(StagingDirError):
                    build_snapshot(src, dst, [])

                self.assertTrue(os.path.isfile(important))

    def test_accepts_empty_existing_dir(self):
        with tempfile.TemporaryDirectory() as dst:
            prepare_staging_dir(dst)
            self.assertTrue(os.path.isfile(os.path.join(dst, STAGING_MARKER)))

    def test_creates_missing_dir(self):
        with tempfile.TemporaryDirectory() as parent:
            staging = os.path.join(parent, "new_staging")
            prepare_staging_dir(staging)
            self.assertTrue(os.path.isfile(os.path.join(staging, STAGING_MARKER)))

    def test_rejects_file_path(self):
        with tempfile.TemporaryDirectory() as parent:
            file_path = os.path.join(parent, "a_file.txt")
            with open(file_path, "w") as fh:
                fh.write("not a directory")
            with self.assertRaises(StagingDirError):
                prepare_staging_dir(file_path)

    def test_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as parent:
            real_dir = os.path.join(parent, "real")
            os.makedirs(real_dir)
            with open(os.path.join(real_dir, "keep.txt"), "w") as fh:
                fh.write("keep me")
            link_path = os.path.join(parent, "link")
            os.symlink(real_dir, link_path)

            with self.assertRaises(StagingDirError):
                prepare_staging_dir(link_path)

            self.assertTrue(os.path.isfile(os.path.join(real_dir, "keep.txt")))


class TestMirrorFiles(unittest.TestCase):

    def test_copies_only_listed_files(self):
        with tempfile.TemporaryDirectory() as staging:
            with tempfile.TemporaryDirectory() as dest:
                with open(os.path.join(staging, "a.scad"), "w") as fh:
                    fh.write("cube(1);")
                with open(os.path.join(staging, STAGING_MARKER), "w") as fh:
                    fh.write("marker")
                with open(os.path.join(staging, "stale.md"), "w") as fh:
                    fh.write("stale")

                mirror_files(staging, dest, ["a.scad"])

                self.assertTrue(os.path.isfile(os.path.join(dest, "a.scad")))
                self.assertFalse(os.path.exists(os.path.join(dest, "stale.md")))
                self.assertFalse(os.path.exists(os.path.join(dest, STAGING_MARKER)))

    def test_creates_nested_parents(self):
        with tempfile.TemporaryDirectory() as staging:
            with tempfile.TemporaryDirectory() as dest:
                nested_dir = os.path.join(staging, "deep", "nested")
                os.makedirs(nested_dir)
                with open(os.path.join(nested_dir, "b.scad"), "w") as fh:
                    fh.write("sphere(1);")

                mirror_files(staging, dest, ["deep/nested/b.scad"])

                self.assertTrue(os.path.isfile(os.path.join(dest, "deep", "nested", "b.scad")))

    def test_missing_source_raises(self):
        with tempfile.TemporaryDirectory() as staging:
            with tempfile.TemporaryDirectory() as dest:
                with self.assertRaises(StagingDirError):
                    mirror_files(staging, dest, ["absent.scad"])


def _git_available():
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


@unittest.skipUnless(_git_available(), "git not available")
class TestEnumerateTrackedFiles(unittest.TestCase):

    def test_excludes_untracked_files(self):
        from sync_public_snapshot import enumerate_tracked_files
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", tmp], capture_output=True, check=True)
            subprocess.run(
                ["git", "-C", tmp, "config", "user.email", "test@test.com"],
                capture_output=True, check=True,
            )
            subprocess.run(
                ["git", "-C", tmp, "config", "user.name", "Test"],
                capture_output=True, check=True,
            )
            committed = os.path.join(tmp, "committed.scad")
            with open(committed, "w") as fh:
                fh.write("sphere(5);")
            subprocess.run(["git", "-C", tmp, "add", "committed.scad"], check=True)
            subprocess.run(
                ["git", "-C", tmp, "commit", "-m", "init"],
                capture_output=True, check=True,
            )
            untracked = os.path.join(tmp, "untracked.txt")
            with open(untracked, "w") as fh:
                fh.write("secret")

            tracked = enumerate_tracked_files(tmp)

        self.assertIn("committed.scad", tracked)
        self.assertNotIn("untracked.txt", tracked)


if __name__ == "__main__":
    unittest.main()
