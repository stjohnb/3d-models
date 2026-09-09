"""Text-level invariant tests for the PR preview cleanup workflow.

pr-preview-cleanup.yml deletes a whole S3 prefix
(pr-preview/pr-{N}/) when a PR closes. That is destructive by design, so
these tests pin the guardrails that keep the blast radius to exactly one
PR's prefix: the PR number must be validated as numeric before it reaches
`aws s3 rm --recursive`, and it must never be interpolated directly into
the `run:` command line (it must arrive only via `env:`), since an empty
or malformed value there would widen the delete target to every pr-*
prefix in the bucket.

These tests also pin that build.yml's `pull_request` trigger stays
`[opened, synchronize, reopened]` — adding `closed` there would make the
full render pipeline (the `build` job, pinned to the `ryzen` runner) run
on PR close and re-upload the very preview this workflow just deleted,
since "Deploy PR preview" is gated only on `github.event_name ==
'pull_request'`.

Run with: python3 -m unittest test_pr_preview_cleanup
"""

import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CLEANUP_YML = REPO_ROOT / ".github" / "workflows" / "pr-preview-cleanup.yml"
BUILD_YML = REPO_ROOT / ".github" / "workflows" / "build.yml"


def read(path):
    return path.read_text(encoding="utf-8")


class WorkflowShapeTests(unittest.TestCase):
    def test_workflow_exists(self):
        self.assertTrue(CLEANUP_YML.is_file())

    def test_triggers_on_pull_request_closed(self):
        text = read(CLEANUP_YML)
        self.assertIn("pull_request:", text)
        self.assertIn("types: [closed]", text)

    def test_runner_is_self_hosted_linux(self):
        text = read(CLEANUP_YML)
        self.assertIn("runs-on: [self-hosted, linux]", text)
        for forbidden in (
            "ubuntu-latest",
            "ubuntu-22.04",
            "windows-latest",
            "macos-latest",
        ):
            self.assertNotIn(forbidden, text)
        for line in text.splitlines():
            self.assertNotRegex(
                line.strip(), r"^runs-on:\s*self-hosted\s*$",
                "bare 'runs-on: self-hosted' is missing an OS label",
            )

    def test_no_privileged_install(self):
        text = read(CLEANUP_YML)
        for forbidden in ("sudo", "apt-get", "nix-env -i"):
            self.assertNotIn(forbidden, text)

    def test_setup_nix_is_local_path(self):
        self.assertIn("uses: ./.github/actions/setup-nix", read(CLEANUP_YML))


class ActionPinTests(unittest.TestCase):
    """Same guard as build.yml's ActionPinTests (#499): this workflow also
    mints an OIDC session for the AWS deploy role, so its external actions
    must be pinned to full commit SHAs, not mutable tags.
    """

    USES_RE = re.compile(r"^\s*(?:-\s+)?uses:\s*(\S+)(.*)$", re.MULTILINE)
    SHA_RE = re.compile(r"^[0-9a-f]{40}$")

    def _external_uses(self):
        for ref, rest in self.USES_RE.findall(read(CLEANUP_YML)):
            if ref.startswith("./"):
                continue
            yield ref, rest

    def test_external_actions_are_sha_pinned(self):
        for ref, _rest in self._external_uses():
            self.assertIn("@", ref, f"{ref} has no version reference")
            _repo, _, version = ref.partition("@")
            self.assertRegex(
                version, self.SHA_RE,
                f"{ref} is pinned to a mutable tag, not a full 40-character "
                "commit SHA (#499)",
            )

    def test_sha_pins_carry_a_version_comment(self):
        for ref, rest in self._external_uses():
            self.assertRegex(
                rest.strip(), r"^#\s*v\d+\.\d+\.\d+$",
                f"{ref} must carry a trailing '# vX.Y.Z' comment",
            )


class DeleteSafetyTests(unittest.TestCase):
    def test_pr_number_is_validated_before_delete(self):
        text = read(CLEANUP_YML)
        self.assertIn("*[!0-9]*", text)
        self.assertIn("Refusing to delete", text)

    def test_delete_target_is_scoped_to_one_pr(self):
        text = read(CLEANUP_YML)
        self.assertEqual(text.count("aws s3 rm"), 1)
        self.assertNotIn('pr-preview/" --recursive', text)
        self.assertNotIn('pr-preview" --recursive', text)
        self.assertIn('target="${BUCKET_PREFIX}/pr-${pr}/"', text)

    def test_pr_number_not_interpolated_into_run_command(self):
        text = read(CLEANUP_YML)
        run_marker = "        run: |\n"
        start = text.index(run_marker) + len(run_marker)
        run_block = text[start:]
        self.assertNotIn("${{", run_block)


class BuildWorkflowInteractionTests(unittest.TestCase):
    def test_build_workflow_does_not_run_on_pr_close(self):
        """Adding `closed` to build.yml's pull_request types would re-run
        the full render pipeline on PR close and re-upload the preview
        this workflow just deleted (see module docstring).
        """
        text = read(BUILD_YML)
        self.assertIn("types: [opened, synchronize, reopened]", text)

    def test_concurrency_group_matches_build_pr_group(self):
        """build.yml's PR concurrency group evaluates to 'pages-pr-{N}'
        (literal 'pages-' prefix + format('pr-{0}', ...)). The cleanup
        workflow's group must evaluate to the same string so that closing
        a PR cancels any in-flight build for it before the delete runs.
        """
        build_text = read(BUILD_YML)
        self.assertIn("group: pages-${{", build_text)
        self.assertIn("format('pr-{0}', github.event.number)", build_text)
        self.assertIn(
            "format('pages-pr-{0}', github.event.number)", read(CLEANUP_YML)
        )


if __name__ == "__main__":
    unittest.main()
