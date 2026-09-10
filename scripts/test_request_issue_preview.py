"""Tests for request-issue-preview.sh (issue #518).

The script runs on the planner host (openclaw) and must never render
locally — it only stages candidate .scad files onto a claws/preview-issue-<N>
branch and opens a draft, "Claws Ignore"-labelled PR so build.yml's existing
pull_request path renders them on the ryzen runner. All tests here are
hermetic: no network, no real openscad, no real gh. `gh` is replaced with a
logging stub on PATH; git operations run against a local bare "origin" so
`git fetch`/`git push` work without a network.

Run with: python3 -m unittest test_request_issue_preview
"""

import glob
import os
import pathlib
import re
import shutil
import stat
import subprocess
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "request-issue-preview.sh"
BASH = shutil.which("bash")
GIT = shutil.which("git")

USAGE_ARGS = ["518", "candidate.scad"]

GH_STUB = """#!/usr/bin/env bash
mkdir -p "$GH_STUB_LOG_DIR"
outfile="$(mktemp "$GH_STUB_LOG_DIR/call-XXXXXX")"
printf '%s\\n' "$@" > "$outfile"
case "$1 $2" in
  "pr list")
    if [ -n "${GH_STUB_PR_NUMBER:-}" ]; then
      echo "$GH_STUB_PR_NUMBER"
    fi
    ;;
  "pr view")
    echo "$GH_STUB_PR_URL"
    ;;
  "pr create")
    echo "$GH_STUB_PR_URL"
    ;;
esac
"""


def _write_executable(path, content):
    path.write_text(content, encoding="utf-8")
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _git(*args, cwd, check=True, env=None):
    return subprocess.run(
        [GIT, *args], cwd=cwd, check=check, capture_output=True, text=True, env=env
    )


class ArgValidationTests(unittest.TestCase):
    """Argument validation must fail before any git network call."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo_dir = os.path.join(self._tmp.name, "repo")
        os.makedirs(self.repo_dir)
        _git("init", "-q", "-b", "main", cwd=self.repo_dir)
        _git("config", "user.email", "test@example.com", cwd=self.repo_dir)
        _git("config", "user.name", "Test", cwd=self.repo_dir)

        self.bindir = os.path.join(self._tmp.name, "bin")
        os.makedirs(self.bindir)
        _write_executable(pathlib.Path(self.bindir, "gh"), "#!/usr/bin/env bash\nexit 99\n")

        self.env = dict(os.environ)
        self.env["PATH"] = self.bindir + os.pathsep + self.env["PATH"]

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, args):
        return subprocess.run(
            [BASH, str(SCRIPT), *args],
            cwd=self.repo_dir,
            env=self.env,
            capture_output=True,
            text=True,
        )

    def test_missing_issue_number(self):
        result = self._run([])
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_non_numeric_issue_number(self):
        result = self._run(["abc", "candidate.scad"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_numeric_issue_but_no_files(self):
        result = self._run(["518"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_file_not_scad(self):
        path = pathlib.Path(self.repo_dir, "candidate.txt")
        path.write_text("not scad\n")
        result = self._run(["518", "candidate.txt"])
        self.assertEqual(result.returncode, 2)

    def test_path_outside_repo(self):
        outside_dir = pathlib.Path(self._tmp.name, "outside")
        outside_dir.mkdir()
        (outside_dir / "evil.scad").write_text("cube(1);\n")
        result = self._run(["518", "../outside/evil.scad"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("escapes the repo", result.stderr)

    def test_bad_charset_basename(self):
        path = pathlib.Path(self.repo_dir, "bad$name.scad")
        path.write_text("cube(1);\n")
        result = self._run(["518", "bad$name.scad"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("charset", result.stderr)


class ScriptShapeTests(unittest.TestCase):
    def test_is_executable(self):
        self.assertTrue(os.access(SCRIPT, os.X_OK))

    def test_has_strict_mode(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", text)

    def test_never_invokes_openscad(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("openscad", text)

    def test_no_privileged_install(self):
        text = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("sudo", "apt-get"):
            self.assertNotIn(forbidden, text)


class _RepoHarness(unittest.TestCase):
    """Shared setup: a caller repo with a local bare 'origin', plus a
    logging gh stub on PATH."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = self._tmp.name

        self.origin_dir = os.path.join(root, "origin.git")
        os.makedirs(self.origin_dir)
        _git("init", "-q", "--bare", "-b", "main", cwd=self.origin_dir)

        self.repo_dir = os.path.join(root, "repo")
        os.makedirs(self.repo_dir)
        _git("init", "-q", "-b", "main", cwd=self.repo_dir)
        _git("config", "user.email", "test@example.com", cwd=self.repo_dir)
        _git("config", "user.name", "Test", cwd=self.repo_dir)

        pathlib.Path(self.repo_dir, "flake.nix").write_text("{ }\n")
        os.makedirs(os.path.join(self.repo_dir, "scripts"))
        pathlib.Path(self.repo_dir, "scripts", "placeholder.txt").write_text("x\n")
        _git("add", "flake.nix", "scripts/placeholder.txt", cwd=self.repo_dir)
        _git("commit", "-q", "-m", "initial", cwd=self.repo_dir)

        _git("remote", "add", "origin", self.origin_dir, cwd=self.repo_dir)
        _git("push", "-q", "origin", "main", cwd=self.repo_dir)

        pathlib.Path(self.repo_dir, "candidate.scad").write_text("cube(1);\n")

        self.bindir = os.path.join(root, "bin")
        os.makedirs(self.bindir)
        _write_executable(pathlib.Path(self.bindir, "gh"), GH_STUB)

        self.gh_log_dir = os.path.join(root, "gh-log")
        os.makedirs(self.gh_log_dir)

        self.tmp_home = os.path.join(root, "tmp")
        os.makedirs(self.tmp_home)

        self.env = dict(os.environ)
        self.env["PATH"] = self.bindir + os.pathsep + self.env["PATH"]
        self.env["GH_STUB_LOG_DIR"] = self.gh_log_dir
        self.env["GH_STUB_PR_URL"] = "https://github.com/example/repo/pull/999"
        self.env["GH_STUB_PR_NUMBER"] = ""
        self.env["TMPDIR"] = self.tmp_home

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, args):
        return subprocess.run(
            [BASH, str(SCRIPT), *args],
            cwd=self.repo_dir,
            env=self.env,
            capture_output=True,
            text=True,
        )

    def _gh_calls(self):
        calls = []
        for path in sorted(glob.glob(os.path.join(self.gh_log_dir, "call-*"))):
            calls.append(pathlib.Path(path).read_text(encoding="utf-8"))
        return calls


class CommitBuildTests(_RepoHarness):
    def test_pushed_branch_carries_full_tree_and_candidate(self):
        result = self._run(["518", "candidate.scad"])
        self.assertEqual(result.returncode, 0, result.stderr)

        ls = subprocess.run(
            [GIT, "ls-tree", "-r", "--name-only", "refs/heads/claws/preview-issue-518"],
            cwd=self.origin_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        names = ls.stdout.splitlines()
        self.assertIn("flake.nix", names)
        self.assertIn("candidate.scad", names)

    def test_caller_worktree_and_head_untouched(self):
        head_before = _git("rev-parse", "HEAD", cwd=self.repo_dir).stdout
        status_before = _git("status", "--porcelain", cwd=self.repo_dir).stdout

        result = self._run(["518", "candidate.scad"])
        self.assertEqual(result.returncode, 0, result.stderr)

        head_after = _git("rev-parse", "HEAD", cwd=self.repo_dir).stdout
        status_after = _git("status", "--porcelain", cwd=self.repo_dir).stdout
        self.assertEqual(head_before, head_after)
        self.assertEqual(status_before, status_after)

    def test_no_temp_index_file_survives(self):
        result = self._run(["518", "candidate.scad"])
        self.assertEqual(result.returncode, 0, result.stderr)
        leftovers = glob.glob(os.path.join(self.tmp_home, "issue-preview-index.*"))
        self.assertEqual(leftovers, [])


class GhInvocationTests(_RepoHarness):
    def test_pr_create_uses_draft_label_and_no_issue_reference(self):
        result = self._run(["518", "candidate.scad"])
        self.assertEqual(result.returncode, 0, result.stderr)

        calls = self._gh_calls()
        create_calls = [c for c in calls if c.startswith("pr\ncreate\n")]
        self.assertEqual(len(create_calls), 1)
        body = create_calls[0]
        self.assertIn("--draft\n", body)
        self.assertIn("--base\nmain\n", body)
        self.assertIn("--label\nClaws Ignore\n", body)
        self.assertNotRegex(body, r"#\d")

    def test_existing_open_pr_skips_create(self):
        self.env["GH_STUB_PR_NUMBER"] = "999"
        result = self._run(["518", "candidate.scad"])
        self.assertEqual(result.returncode, 0, result.stderr)

        calls = self._gh_calls()
        create_calls = [c for c in calls if c.startswith("pr\ncreate\n")]
        self.assertEqual(create_calls, [])
        view_calls = [c for c in calls if c.startswith("pr\nview\n")]
        self.assertEqual(len(view_calls), 1)


if __name__ == "__main__":
    unittest.main()
