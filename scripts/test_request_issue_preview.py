"""Tests for request-issue-preview.sh (issue #518, PR-less since
clw_01M39H53GDR0QVMAF3WVMWQKTM).

The script runs on the planner host (openclaw) and must never render
locally — it only stages candidate .scad files, plus a project's meta.json
or dependency-graph.md, onto a claws/preview-issue-<id> branch, whose push
build.yml renders on a self-hosted Linux runner into
issue-preview/<id>/<sha8>/. It opens no PR; `--cleanup` closes any legacy
preview PR and deletes the branch. All tests here are hermetic: no network,
no real openscad, no real gh. `gh` is replaced with a logging stub on PATH;
git operations run against a local bare "origin" so `git fetch`/`git push`
work without a network.

Run with: python3 -m unittest test_request_issue_preview
"""

import glob
import os
import pathlib
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
  "pr close")
    ;;
  *)
    exit 99
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

    def test_clw_prefix_with_empty_tail(self):
        result = self._run(["clw_", "candidate.scad"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_clw_id_with_bad_characters(self):
        result = self._run(["clw_../x", "candidate.scad"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_cleanup_requires_valid_id(self):
        for args in (["--cleanup"], ["--cleanup", "abc"], ["--cleanup", "518", "x.scad"]):
            result = self._run(args)
            self.assertEqual(result.returncode, 2, args)
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

    def test_other_json_rejected(self):
        path = pathlib.Path(self.repo_dir, "parameters.json")
        path.write_text("{}\n")
        result = self._run(["518", "parameters.json"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a .scad", result.stderr)

    def test_meta_json_passes_validation_stage(self):
        newproj = pathlib.Path(self.repo_dir, "newproj")
        newproj.mkdir()
        (newproj / "meta.json").write_text('{"description": "x"}\n')
        result = self._run(["518", "newproj/meta.json"])
        self.assertNotEqual(result.returncode, 2)
        self.assertNotIn("not a .scad", result.stderr)

    def test_dependency_graph_md_passes_validation_stage(self):
        newproj = pathlib.Path(self.repo_dir, "newproj")
        newproj.mkdir()
        (newproj / "dependency-graph.md").write_text("# deps\n")
        result = self._run(["518", "newproj/dependency-graph.md"])
        self.assertNotEqual(result.returncode, 2)
        self.assertNotIn("not a .scad", result.stderr)

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

    def test_pushed_branch_carries_meta_json_and_dependency_graph(self):
        newproj = pathlib.Path(self.repo_dir, "newproj")
        newproj.mkdir()
        (newproj / "candidate.scad").write_text("cube(1);\n")
        (newproj / "meta.json").write_text('{"description": "Preview project"}\n')
        (newproj / "dependency-graph.md").write_text("# deps\n")

        result = self._run([
            "518",
            "newproj/candidate.scad",
            "newproj/meta.json",
            "newproj/dependency-graph.md",
        ])
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
        self.assertIn("newproj/candidate.scad", names)
        self.assertIn("newproj/meta.json", names)
        self.assertIn("newproj/dependency-graph.md", names)


CLW_ID = "clw_01M39H53GDR0QVMAF3WVMWQKTM"


class PrLessPreviewTests(_RepoHarness):
    def _branch_sha(self, branch):
        return _git("rev-parse", f"refs/heads/{branch}", cwd=self.origin_dir).stdout.strip()

    def test_default_mode_makes_no_pr_calls(self):
        result = self._run(["518", "candidate.scad"])
        self.assertEqual(result.returncode, 0, result.stderr)
        for call in self._gh_calls():
            self.assertFalse(call.startswith("pr\n"), call)

    def test_output_names_issue_preview_and_summary_urls(self):
        result = self._run(["518", "candidate.scad"])
        self.assertEqual(result.returncode, 0, result.stderr)
        sha8 = self._branch_sha("claws/preview-issue-518")[:8]
        viewer = f"https://www.bstjohn.net/3d-models/issue-preview/518/{sha8}/"
        lines = result.stdout.splitlines()
        self.assertIn("claws/preview-issue-518", lines)
        self.assertIn(viewer, lines)
        self.assertIn(viewer + "preview-summary.json", lines)

    def test_clw_id_is_accepted(self):
        result = self._run([CLW_ID, "candidate.scad"])
        self.assertEqual(result.returncode, 0, result.stderr)
        sha = self._branch_sha(f"claws/preview-issue-{CLW_ID}")
        self.assertRegex(sha, r"^[0-9a-f]{40}$")
        self.assertIn(f"/issue-preview/{CLW_ID}/{sha[:8]}/", result.stdout)

    def test_script_never_opens_a_pr(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("gh pr create", text)


class CleanupTests(_RepoHarness):
    def _remote_has(self, branch):
        return _git(
            "show-ref", "--verify", "--quiet", f"refs/heads/{branch}",
            cwd=self.origin_dir, check=False,
        ).returncode == 0

    def test_cleanup_deletes_branch(self):
        self.assertEqual(self._run([CLW_ID, "candidate.scad"]).returncode, 0)
        branch = f"claws/preview-issue-{CLW_ID}"
        self.assertTrue(self._remote_has(branch))

        result = self._run(["--cleanup", CLW_ID])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self._remote_has(branch))
        self.assertIn("pr-preview-cleanup.yml", result.stdout)
        close_calls = [c for c in self._gh_calls() if c.startswith("pr\nclose\n")]
        self.assertEqual(close_calls, [])

    def test_cleanup_closes_legacy_open_pr(self):
        self.assertEqual(self._run(["518", "candidate.scad"]).returncode, 0)
        self.env["GH_STUB_PR_NUMBER"] = "546"
        result = self._run(["--cleanup", "518"])
        self.assertEqual(result.returncode, 0, result.stderr)
        close_calls = [c for c in self._gh_calls() if c.startswith("pr\nclose\n")]
        self.assertEqual(len(close_calls), 1)
        self.assertTrue(close_calls[0].startswith("pr\nclose\n546\n"))
        list_calls = [c for c in self._gh_calls() if c.startswith("pr\nlist\n")]
        self.assertIn("--head\nclaws/preview-issue-518\n", list_calls[0])

    def test_cleanup_when_branch_already_gone(self):
        result = self._run(["--cleanup", "518"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("does not exist", result.stdout)


if __name__ == "__main__":
    unittest.main()
