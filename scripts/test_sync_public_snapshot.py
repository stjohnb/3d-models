"""Tests for sync_public_snapshot.py.

Run with: python3 -m pytest scripts/test_sync_public_snapshot.py
"""

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from sync_public_snapshot import (
    SECRET_SCAN_SKIP,
    SNAPSHOT_RENAMES,
    STAGING_MARKER,
    MirrorRefsError,
    StagingDirError,
    build_snapshot,
    check_mirror_refs,
    enumerate_tracked_files,
    included_files,
    is_excluded,
    is_included,
    main as sync_main,
    mirror_default_branch,
    mirror_files,
    prepare_staging_dir,
    publish_orphan_commit,
    push_snapshot,
    scan_for_image_metadata,
    scan_for_secrets,
    staged_path,
    staged_paths,
    superseded_targets,
)


PRIVATE_PLAYBOOK_FIXTURE = "playbooks/private-maintainer-flow.md"


class TestIsIncluded(unittest.TestCase):

    def test_exact_file_match(self):
        self.assertTrue(is_included("docs/OVERVIEW.md"))
        self.assertTrue(is_included("playbooks/scan_a_capture.md"))
        self.assertTrue(is_included("README.public.md"))

    def test_directory_prefix_match(self):
        self.assertTrue(is_included("scripts/sync_public_snapshot.py"))
        self.assertTrue(is_included("adjustable-bracket/piece_a.scad"))

    def test_not_included_by_default(self):
        self.assertFalse(is_included("docs/new-internal-note.md"))
        self.assertFalse(is_included("playbooks/new-private-flow.md"))
        self.assertFalse(is_included(PRIVATE_PLAYBOOK_FIXTURE))

    def test_prefix_boundary_correctness(self):
        self.assertFalse(is_included("scripts-private/tool.py"))
        self.assertFalse(is_included("docs/OVERVIEW.md.bak"))


class TestIsExcluded(unittest.TestCase):

    def test_exact_file_match(self):
        self.assertTrue(is_excluded("docs/blog-post.md"))
        self.assertTrue(is_excluded("docs/agent-notes.md"))
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


class TestScanForImageMetadata(unittest.TestCase):

    def test_flags_jpeg_with_exif_gps(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "photo.jpg")
            im = Image.new("RGB", (10, 10), (1, 2, 3))
            exif = Image.Exif()
            exif[0x0112] = 6
            gps_ifd = exif.get_ifd(0x8825)
            gps_ifd[1] = "N"
            exif[0x8825] = gps_ifd
            im.save(path, format="JPEG", exif=exif)

            hits = scan_for_image_metadata(tmp, ["photo.jpg"])

        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][0], "photo.jpg")
        self.assertTrue(any("GPS" in r for r in hits[0][1]))

    def test_clean_image_no_hits(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "clean.png")
            Image.new("RGB", (10, 10), (1, 2, 3)).save(path, format="PNG")

            hits = scan_for_image_metadata(tmp, ["clean.png"])

        self.assertEqual(hits, [])

    def test_ignores_non_image_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "notes.txt")
            with open(path, "w") as fh:
                fh.write("no exif here")

            hits = scan_for_image_metadata(tmp, ["notes.txt"])

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
                with open(os.path.join(stale_dir, "stale.md"), "w") as fh:
                    fh.write("should not survive")

                build_snapshot(src, dst, ["keep/a.scad"])

                self.assertTrue(os.path.isfile(os.path.join(dst, "keep", "a.scad")))
                self.assertFalse(os.path.exists(os.path.join(dst, "secret", "stale.md")))

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


class TestSnapshotRenames(unittest.TestCase):

    def test_staged_paths_maps_public_readme(self):
        self.assertEqual(
            staged_paths(["a.scad", "README.public.md"]),
            ["a.scad", "README.md"],
        )
        self.assertEqual(staged_path("index.html"), "index.html")

    def test_superseded_targets_requires_source_present(self):
        self.assertEqual(
            superseded_targets(["README.md", "README.public.md"]),
            {"README.md"},
        )
        self.assertEqual(superseded_targets(["README.md"]), set())

    def test_build_snapshot_writes_public_text_as_readme(self):
        with tempfile.TemporaryDirectory() as src:
            with tempfile.TemporaryDirectory() as dst:
                with open(os.path.join(src, "README.md"), "w") as fh:
                    fh.write("gallery")
                with open(os.path.join(src, "README.public.md"), "w") as fh:
                    fh.write("public intro")

                build_snapshot(src, dst, ["README.public.md"])

                with open(os.path.join(dst, "README.md")) as fh:
                    self.assertEqual(fh.read(), "public intro")
                self.assertFalse(os.path.exists(os.path.join(dst, "README.public.md")))

    def test_secret_scan_reads_source_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            fpath = os.path.join(tmp, "README.public.md")
            with open(fpath, "w") as fh:
                fh.write(
                    "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghijk\n"
                )
            hits = scan_for_secrets(tmp, ["README.public.md"])
        self.assertTrue(any(h[0] == "README.public.md" for h in hits))


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


@unittest.skipUnless(_git_available(), "git not available")
class TestIncludedFilesRename(unittest.TestCase):

    def _init_repo(self, tmp, filenames_and_contents):
        subprocess.run(["git", "init", tmp], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", tmp, "config", "user.email", "test@test.com"],
            capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "-C", tmp, "config", "user.name", "Test"],
            capture_output=True, check=True,
        )
        for name, content in filenames_and_contents.items():
            path = os.path.join(tmp, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as fh:
                fh.write(content)
        subprocess.run(
            ["git", "-C", tmp, "add"] + list(filenames_and_contents.keys()),
            check=True,
        )
        subprocess.run(
            ["git", "-C", tmp, "commit", "-m", "init"],
            capture_output=True, check=True,
        )

    def test_drops_gallery_readme_when_public_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._init_repo(tmp, {
                "README.md": "gallery",
                "README.public.md": "public intro",
                "index.html": "<html></html>",
                "docs/private-note.md": "private",
            })
            files = included_files(tmp)
        self.assertIn("README.public.md", files)
        self.assertIn("index.html", files)
        self.assertNotIn("README.md", files)
        self.assertNotIn("docs/private-note.md", files)

    def test_keeps_readme_when_public_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._init_repo(tmp, {
                "README.md": "gallery",
                "index.html": "<html></html>",
            })
            files = included_files(tmp)
        self.assertIn("README.md", files)

    def test_new_playbooks_are_private_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._init_repo(tmp, {
                "playbooks/scan_a_capture.md": "public",
                "playbooks/new-private-flow.md": "private",
                PRIVATE_PLAYBOOK_FIXTURE: "private",
            })
            files = included_files(tmp)
        self.assertIn("playbooks/scan_a_capture.md", files)
        self.assertNotIn("playbooks/new-private-flow.md", files)
        self.assertNotIn(PRIVATE_PLAYBOOK_FIXTURE, files)

    def test_mirror_contains_exactly_one_readme(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._init_repo(tmp, {
                "README.md": "gallery",
                "README.public.md": "public intro",
                "index.html": "<html></html>",
            })
            files = included_files(tmp)
            with tempfile.TemporaryDirectory() as staging:
                with tempfile.TemporaryDirectory() as dest:
                    build_snapshot(tmp, staging, files)
                    mirror_files(staging, dest, staged_paths(files))
                    readmes = sorted(p for p in os.listdir(dest) if "README" in p)
                    self.assertEqual(readmes, ["README.md"])
                    with open(os.path.join(dest, "README.md")) as fh:
                        self.assertEqual(fh.read(), "public intro")


@unittest.skipUnless(_git_available(), "git not available")
class TestPublicSnapshotContent(unittest.TestCase):

    def test_included_files_do_not_reference_private_playbooks(self):
        root = pathlib.Path(__file__).resolve().parent.parent
        files = included_files(str(root))
        public_files = set(files)
        private_playbooks = [
            rel_path for rel_path in enumerate_tracked_files(str(root))
            if rel_path.startswith("playbooks/") and rel_path not in public_files
        ]

        self.assertTrue(private_playbooks)
        for rel_path in files:
            path = root / rel_path
            try:
                content = path.read_bytes().decode("utf-8", "ignore")
            except OSError:
                continue
            for private_path in private_playbooks:
                self.assertNotIn(private_path, content, rel_path)


@unittest.skipUnless(_git_available(), "git not available")
class TestMainAbortsOnImageMetadata(unittest.TestCase):
    """End-to-end: main() must abort before staging/push if an image has metadata."""

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

    def _commit(self, tmp, filenames):
        subprocess.run(["git", "-C", tmp, "add"] + filenames, check=True)
        subprocess.run(
            ["git", "-C", tmp, "commit", "-m", "init"],
            capture_output=True, check=True,
        )

    def _run_sync(self, tmp, staging):
        script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "sync_public_snapshot.py"
        )
        return subprocess.run(
            [sys.executable, script, "--staging-dir", staging],
            cwd=tmp, capture_output=True, text=True,
        )

    def test_aborts_on_image_with_exif(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._init_repo(tmp)
            path = os.path.join(tmp, "photo.jpg")
            exif = Image.Exif()
            gps_ifd = exif.get_ifd(0x8825)
            gps_ifd[1] = "N"
            exif[0x8825] = gps_ifd
            Image.new("RGB", (10, 10), (1, 2, 3)).save(path, format="JPEG", exif=exif)
            self._commit(tmp, ["photo.jpg"])

            with tempfile.TemporaryDirectory() as staging:
                result = self._run_sync(tmp, staging)
                self.assertFalse(os.path.exists(os.path.join(staging, "photo.jpg")))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("image metadata", result.stderr)

    def test_passes_on_clean_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._init_repo(tmp)
            path = os.path.join(tmp, "clean.png")
            Image.new("RGB", (10, 10), (1, 2, 3)).save(path, format="PNG")
            self._commit(tmp, ["clean.png"])

            with tempfile.TemporaryDirectory() as staging:
                result = self._run_sync(tmp, staging)

        self.assertEqual(result.returncode, 0, result.stderr)


@unittest.skipUnless(_git_available(), "git not available")
class TestMainAbortsWhenPillowMissing(unittest.TestCase):
    """main() must abort (return 1) rather than skip the image-metadata check
    when Pillow can't be imported — not just when it flags a hit."""

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

    def _commit(self, tmp, filenames):
        subprocess.run(["git", "-C", tmp, "add"] + filenames, check=True)
        subprocess.run(
            ["git", "-C", tmp, "commit", "-m", "init"],
            capture_output=True, check=True,
        )

    def test_missing_pillow_aborts_before_staging(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._init_repo(tmp)
            path = os.path.join(tmp, "clean.png")
            Image.new("RGB", (10, 10), (1, 2, 3)).save(path, format="PNG")
            self._commit(tmp, ["clean.png"])

            with tempfile.TemporaryDirectory() as staging:
                cwd = os.getcwd()
                os.chdir(tmp)
                try:
                    # Force the dynamic `from image_metadata import ...` inside
                    # scan_for_image_metadata() to re-import against a PIL-less
                    # world, rather than reusing an already-cached module.
                    with mock.patch.dict(
                        sys.modules, {"PIL": None, "image_metadata": None}
                    ):
                        rc = sync_main(["--staging-dir", staging])
                finally:
                    os.chdir(cwd)

                self.assertEqual(rc, 1)
                self.assertFalse(os.path.exists(os.path.join(staging, "clean.png")))


def _git(clone_dir, *args, **kwargs):
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    kwargs.setdefault("check", True)
    return subprocess.run(["git", "-C", clone_dir, *args], **kwargs)


@unittest.skipUnless(_git_available(), "git not available")
class TestPublishOrphanCommit(unittest.TestCase):

    def _make_source_repo(self, tmp, default_branch="main"):
        subprocess.run(["git", "init", "-q", "-b", default_branch, tmp], capture_output=True, check=True)
        _git(tmp, "config", "user.email", "test@test.com")
        _git(tmp, "config", "user.name", "Test")
        with open(os.path.join(tmp, "keep.txt"), "w") as fh:
            fh.write("first commit\n")
        _git(tmp, "add", "keep.txt")
        _git(tmp, "commit", "-q", "-m", "first")
        with open(os.path.join(tmp, "old-photo.jpg"), "wb") as fh:
            fh.write(b"old bytes")
        _git(tmp, "add", "old-photo.jpg")
        _git(tmp, "commit", "-q", "-m", "adds old photo")

    def _make_staging_dir(self, files_and_contents):
        staging = tempfile.mkdtemp()
        for name, content in files_and_contents.items():
            path = os.path.join(staging, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as fh:
                fh.write(content)
        return staging

    def test_produces_single_commit_without_old_history_file(self):
        with tempfile.TemporaryDirectory() as source:
            self._make_source_repo(source)
            with tempfile.TemporaryDirectory() as parent:
                clone_dir = os.path.join(parent, "clone")
                subprocess.run(["git", "clone", "-q", source, clone_dir], check=True)
                _git(clone_dir, "config", "user.email", "test@test.com")
                _git(clone_dir, "config", "user.name", "Test")
                staging = self._make_staging_dir({"keep.txt": "sanitized\n"})
                try:
                    branch = publish_orphan_commit(clone_dir, staging, ["keep.txt"], "Public snapshot")
                finally:
                    shutil.rmtree(staging)

                self.assertEqual(branch, "main")
                count = _git(clone_dir, "rev-list", "--count", "HEAD").stdout.strip()
                self.assertEqual(count, "1")

                tree_files = sorted(
                    p for p in os.listdir(clone_dir) if p != ".git"
                )
                self.assertEqual(tree_files, ["keep.txt"])

                objects = _git(clone_dir, "rev-list", "--objects", "--all").stdout
                self.assertNotIn("old-photo.jpg", objects)

    def test_uses_clone_default_branch_trunk(self):
        with tempfile.TemporaryDirectory() as source:
            self._make_source_repo(source, default_branch="trunk")
            with tempfile.TemporaryDirectory() as parent:
                clone_dir = os.path.join(parent, "clone")
                subprocess.run(["git", "clone", "-q", source, clone_dir], check=True)
                _git(clone_dir, "config", "user.email", "test@test.com")
                _git(clone_dir, "config", "user.name", "Test")
                staging = self._make_staging_dir({"keep.txt": "sanitized\n"})
                try:
                    branch = publish_orphan_commit(clone_dir, staging, ["keep.txt"], "Public snapshot")
                finally:
                    shutil.rmtree(staging)

                self.assertEqual(branch, "trunk")
                self.assertEqual(mirror_default_branch(clone_dir), "trunk")

    def test_file_absent_from_staged_list_is_dropped(self):
        with tempfile.TemporaryDirectory() as source:
            self._make_source_repo(source)
            with tempfile.TemporaryDirectory() as parent:
                clone_dir = os.path.join(parent, "clone")
                subprocess.run(["git", "clone", "-q", source, clone_dir], check=True)
                _git(clone_dir, "config", "user.email", "test@test.com")
                _git(clone_dir, "config", "user.name", "Test")
                # keep.txt existed in the old history but is not in the staged list.
                staging = self._make_staging_dir({"new.txt": "only this ships\n"})
                try:
                    publish_orphan_commit(clone_dir, staging, ["new.txt"], "Public snapshot")
                finally:
                    shutil.rmtree(staging)

                tree_files = sorted(
                    p for p in os.listdir(clone_dir) if p != ".git"
                )
                self.assertEqual(tree_files, ["new.txt"])
                objects = _git(clone_dir, "rev-list", "--objects", "--all").stdout
                self.assertNotIn("keep.txt", objects)

    def test_staged_gitignore_does_not_filter_staged_files(self):
        # The orphan checkout clears the index (git rm -rf), so every staged
        # file is untracked when `git add` runs — a plain `add -A` would
        # silently filter untracked files through a staged .gitignore.
        with tempfile.TemporaryDirectory() as source:
            self._make_source_repo(source)
            with tempfile.TemporaryDirectory() as parent:
                clone_dir = os.path.join(parent, "clone")
                subprocess.run(["git", "clone", "-q", source, clone_dir], check=True)
                _git(clone_dir, "config", "user.email", "test@test.com")
                _git(clone_dir, "config", "user.name", "Test")
                files_and_contents = {
                    ".gitignore": "*.stl\n!scans/**/*.stl\n",
                    "scans/x.stl": "scan data\n",
                    "keep.txt": "sanitized\n",
                }
                staging = self._make_staging_dir(files_and_contents)
                staged_list = sorted(files_and_contents.keys())
                try:
                    publish_orphan_commit(clone_dir, staging, staged_list, "Public snapshot")
                finally:
                    shutil.rmtree(staging)

                tracked = sorted(
                    p for p in _git(clone_dir, "ls-files").stdout.splitlines() if p
                )
                self.assertEqual(tracked, staged_list)

    def test_empty_tree_default_branch_is_replaced(self):
        with tempfile.TemporaryDirectory() as source:
            subprocess.run(["git", "init", "-q", "-b", "main", source], capture_output=True, check=True)
            _git(source, "config", "user.email", "test@test.com")
            _git(source, "config", "user.name", "Test")
            _git(source, "commit", "--allow-empty", "-q", "-m", "empty")
            with tempfile.TemporaryDirectory() as parent:
                clone_dir = os.path.join(parent, "clone")
                subprocess.run(["git", "clone", "-q", source, clone_dir], check=True)
                _git(clone_dir, "config", "user.email", "test@test.com")
                _git(clone_dir, "config", "user.name", "Test")
                staging = self._make_staging_dir({"README.md": "public\n"})
                try:
                    publish_orphan_commit(clone_dir, staging, ["README.md"], "Public snapshot")
                finally:
                    shutil.rmtree(staging)

                tracked = _git(clone_dir, "ls-files").stdout.splitlines()
                self.assertEqual(tracked, ["README.md"])


@unittest.skipUnless(_git_available(), "git not available")
class TestCheckMirrorRefs(unittest.TestCase):

    def _init_repo(self, tmp):
        subprocess.run(["git", "init", "-q", "-b", "main", tmp], capture_output=True, check=True)
        _git(tmp, "config", "user.email", "test@test.com")
        _git(tmp, "config", "user.name", "Test")
        with open(os.path.join(tmp, "a.txt"), "w") as fh:
            fh.write("a\n")
        _git(tmp, "add", "a.txt")
        _git(tmp, "commit", "-q", "-m", "init")

    def test_no_extra_refs_on_single_branch_mirror(self):
        with tempfile.TemporaryDirectory() as source:
            self._init_repo(source)
            with tempfile.TemporaryDirectory() as parent:
                clone_dir = os.path.join(parent, "clone")
                subprocess.run(["git", "clone", "-q", source, clone_dir], check=True)
                self.assertEqual(check_mirror_refs(clone_dir), [])

    def test_reports_extra_branch_and_tag(self):
        with tempfile.TemporaryDirectory() as source:
            self._init_repo(source)
            _git(source, "branch", "stale-branch")
            _git(source, "tag", "v0-old")
            with tempfile.TemporaryDirectory() as parent:
                clone_dir = os.path.join(parent, "clone")
                subprocess.run(["git", "clone", "-q", source, clone_dir], check=True)
                extra = check_mirror_refs(clone_dir)
                self.assertEqual(extra, sorted(["origin/stale-branch", "v0-old"]))

    def test_origin_head_mismatch_raises(self):
        with tempfile.TemporaryDirectory() as source:
            self._init_repo(source)
            _git(source, "branch", "stale-branch")
            with tempfile.TemporaryDirectory() as parent:
                clone_dir = os.path.join(parent, "clone")
                subprocess.run(["git", "clone", "-q", source, clone_dir], check=True)
                _git(clone_dir, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/stale-branch")

                with self.assertRaises(MirrorRefsError):
                    check_mirror_refs(clone_dir)


@unittest.skipUnless(_git_available(), "git not available")
class TestPushSnapshot(unittest.TestCase):

    def _init_work_repo(self, tmp, default_branch="main"):
        subprocess.run(["git", "init", "-q", "-b", default_branch, tmp], capture_output=True, check=True)
        _git(tmp, "config", "user.email", "test@test.com")
        _git(tmp, "config", "user.name", "Test")

    def _commit_file(self, repo, name, content, message):
        path = os.path.join(repo, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(content)
        _git(repo, "add", name)
        _git(repo, "commit", "-q", "-m", message)

    def _make_bare_mirror(self, tmp, extra_branch=False):
        work = os.path.join(tmp, "work")
        bare = os.path.join(tmp, "mirror.git")
        self._init_work_repo(work)
        self._commit_file(work, "old.txt", "old public data\n", "old snapshot")
        self._commit_file(work, "old-photo.jpg", "old public data\n", "old photo")
        if extra_branch:
            _git(work, "branch", "stale-branch")
        subprocess.run(["git", "clone", "-q", "--bare", work, bare], check=True)
        return bare

    def _make_staging_dir(self, files_and_contents):
        staging = tempfile.mkdtemp()
        for name, content in files_and_contents.items():
            path = os.path.join(staging, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as fh:
                fh.write(content)
        return staging

    def _clone_with_identity(self, source_bare):
        def clone(_target_repo, clone_dir):
            subprocess.run(["git", "clone", "-q", source_bare, clone_dir], check=True)
            _git(clone_dir, "config", "user.email", "test@test.com")
            _git(clone_dir, "config", "user.name", "Test")
        return clone

    def test_extra_ref_aborts_before_history_rewrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            bare = self._make_bare_mirror(tmp, extra_branch=True)
            before_count = _git(bare, "rev-list", "--count", "HEAD").stdout.strip()
            staging = self._make_staging_dir({"README.md": "new snapshot\n"})
            try:
                with mock.patch(
                    "sync_public_snapshot.clone_mirror",
                    side_effect=self._clone_with_identity(bare),
                ):
                    with self.assertRaises(MirrorRefsError):
                        push_snapshot(staging, "ignored/repo", ["README.md"])
            finally:
                shutil.rmtree(staging)

            after_count = _git(bare, "rev-list", "--count", "HEAD").stdout.strip()
            self.assertEqual(after_count, before_count)
            self.assertIn("old-photo.jpg", _git(bare, "rev-list", "--objects", "--all").stdout)

    def test_clean_mirror_is_force_pushed_to_single_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            bare = self._make_bare_mirror(tmp)
            staging = self._make_staging_dir({
                "README.md": "new snapshot\n",
                "models/example.scad": "cube(1);\n",
            })
            staged_files = sorted(["README.md", "models/example.scad"])
            try:
                with mock.patch(
                    "sync_public_snapshot.clone_mirror",
                    side_effect=self._clone_with_identity(bare),
                ) as mock_clone:
                    push_snapshot(staging, "ignored/repo", staged_files)
            finally:
                shutil.rmtree(staging)

            mock_clone.assert_called_once()
            self.assertEqual(_git(bare, "rev-list", "--count", "HEAD").stdout.strip(), "1")
            tree_files = sorted(_git(bare, "ls-tree", "-r", "--name-only", "HEAD").stdout.splitlines())
            self.assertEqual(tree_files, staged_files)
            objects = _git(bare, "rev-list", "--objects", "--all").stdout
            self.assertNotIn("old-photo.jpg", objects)


@unittest.skipUnless(_git_available(), "git not available")
class TestMainDoesNotPushWithoutFlag(unittest.TestCase):

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

    def _commit(self, tmp, filenames):
        subprocess.run(["git", "-C", tmp, "add"] + filenames, check=True)
        subprocess.run(
            ["git", "-C", tmp, "commit", "-m", "init"],
            capture_output=True, check=True,
        )

    def test_push_snapshot_not_called_without_push_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._init_repo(tmp)
            with open(os.path.join(tmp, "clean.png"), "wb") as fh:
                Image.new("RGB", (10, 10), (1, 2, 3)).save(fh, format="PNG")
            self._commit(tmp, ["clean.png"])

            with tempfile.TemporaryDirectory() as staging:
                cwd = os.getcwd()
                os.chdir(tmp)
                try:
                    with mock.patch("sync_public_snapshot.push_snapshot") as mock_push:
                        rc = sync_main(["--staging-dir", staging])
                finally:
                    os.chdir(cwd)

                self.assertEqual(rc, 0)
                mock_push.assert_not_called()


@unittest.skipUnless(_git_available(), "git not available")
class TestMainPushErrorHandling(unittest.TestCase):

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

    def _commit(self, tmp, filenames):
        subprocess.run(["git", "-C", tmp, "add"] + filenames, check=True)
        subprocess.run(
            ["git", "-C", tmp, "commit", "-m", "init"],
            capture_output=True, check=True,
        )

    def _run_push_with(self, side_effect):
        with tempfile.TemporaryDirectory() as tmp:
            self._init_repo(tmp)
            with open(os.path.join(tmp, "clean.png"), "wb") as fh:
                Image.new("RGB", (10, 10), (1, 2, 3)).save(fh, format="PNG")
            self._commit(tmp, ["clean.png"])

            with tempfile.TemporaryDirectory() as staging:
                cwd = os.getcwd()
                os.chdir(tmp)
                try:
                    with mock.patch(
                        "sync_public_snapshot.push_snapshot",
                        side_effect=side_effect,
                    ):
                        return sync_main(["--staging-dir", staging, "--push"])
                finally:
                    os.chdir(cwd)

    def test_main_returns_1_on_mirror_refs_error(self):
        rc = self._run_push_with(MirrorRefsError("origin/stale-branch"))
        self.assertEqual(rc, 1)

    def test_main_returns_1_on_staging_dir_error(self):
        rc = self._run_push_with(StagingDirError("orphan commit staging does not match"))
        self.assertEqual(rc, 1)

    def test_main_returns_1_on_called_process_error(self):
        rc = self._run_push_with(
            subprocess.CalledProcessError(1, ["git", "push", "--force", "origin", "main"])
        )
        self.assertEqual(rc, 1)

    def test_main_returns_1_on_missing_command(self):
        rc = self._run_push_with(FileNotFoundError("gh"))
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
