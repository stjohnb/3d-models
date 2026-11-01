"""Tests for project_dates.project_updated.

Run with: python3 -m unittest test_project_dates
"""

import os
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

import project_dates
from project_dates import project_updated


def run(cmd, cwd, env=None):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, env=env)


def commit(repo, relpath, date):
    path = pathlib.Path(repo) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("cube(1);\n", encoding="utf-8")
    run(["git", "add", "--all"], cwd=repo)
    env = dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    run(
        [
            "git",
            "-c", "user.email=t@t",
            "-c", "user.name=T",
            "commit", "-q", "-m", f"add {relpath}",
        ],
        cwd=repo,
        env=env,
    )


class ProjectUpdatedTests(unittest.TestCase):
    def test_reports_last_commit_date_per_dir(self):
        with tempfile.TemporaryDirectory() as repo:
            run(["git", "init", "-q", "-b", "main"], cwd=repo)
            commit(repo, "a/x.scad", "2020-01-01T12:00:00+00:00")
            commit(repo, "b/y.scad", "2021-06-05T12:00:00+00:00")

            updated = project_updated(["a", "b"], repo_root=repo)

            self.assertEqual(set(updated), {"a", "b"})
            # Compare the date prefix only — git normalises the timezone
            # suffix of %cI to the committer's configured offset.
            self.assertTrue(updated["a"].startswith("2020-01-01"), updated["a"])
            self.assertTrue(updated["b"].startswith("2021-06-05"), updated["b"])

    def test_unknown_dir_is_omitted(self):
        with tempfile.TemporaryDirectory() as repo:
            run(["git", "init", "-q", "-b", "main"], cwd=repo)
            commit(repo, "a/x.scad", "2020-01-01T12:00:00+00:00")

            updated = project_updated(["a", "nope"], repo_root=repo)

            self.assertIn("a", updated)
            self.assertNotIn("nope", updated)

    def test_no_dirs(self):
        with tempfile.TemporaryDirectory() as repo:
            run(["git", "init", "-q", "-b", "main"], cwd=repo)
            self.assertEqual(project_updated([], repo_root=repo), {})

    def test_non_git_root_degrades_to_empty(self):
        with tempfile.TemporaryDirectory() as plain:
            (pathlib.Path(plain) / "a").mkdir()
            self.assertEqual(project_updated(["a"], repo_root=plain), {})

    def test_missing_git_binary_degrades_to_empty(self):
        with mock.patch.object(
            project_dates.subprocess,
            "run",
            side_effect=FileNotFoundError("git"),
        ):
            self.assertEqual(project_updated(["a"], repo_root="."), {})


if __name__ == "__main__":
    unittest.main()
