"""Text-level invariant tests for the spec pages workflow (pages.yml).

pages.yml publishes pages/ to the private Garage pages host and deletes
sibling SHAs under the same prefix, so these tests pin the guardrails: the
PR number is validated as numeric before any `aws s3` call, the PAGES_S3_*
secrets reach the shell only through `env:`, the supersession delete runs
before the stable entry page is written, nothing writes the host-root
index, and the job stays on `[container, linux]` with tools from the
flake. They also pin the PR-close step in pr-preview-cleanup.yml and
build.yml's `pages/**` path filter.

Run with: python3 -m unittest test_pages_workflow
"""

import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOWS = REPO_ROOT / ".forgejo" / "workflows"
PAGES_YML = WORKFLOWS / "pages.yml"
CLEANUP_YML = WORKFLOWS / "pr-preview-cleanup.yml"
BUILD_YML = WORKFLOWS / "build.yml"


def read(path):
    return path.read_text(encoding="utf-8")


def step(text, name):
    """The text of the step called ``name``, up to the next step."""
    start = text.index(f"      - name: {name}\n")
    end = text.find("\n      - ", start + 1)
    return text[start:] if end == -1 else text[start:end]


def run_block(step_text):
    return step_text[step_text.index("        run: |\n"):]


class WorkflowShapeTests(unittest.TestCase):
    def test_workflow_exists(self):
        self.assertTrue(PAGES_YML.is_file())

    def test_runner_is_self_hosted_linux_only(self):
        text = read(PAGES_YML)
        self.assertEqual(re.findall(r"runs-on:.*", text), ["runs-on: [container, linux]"])
        for forbidden in ("self-hosted", "beefy", "ram-", "disk-", "ubuntu-", "windows-", "macos-"):
            self.assertNotIn(forbidden, text)

    def test_runs_inside_default_devshell(self):
        text = read(PAGES_YML)
        self.assertIn(
            "shell: nix --extra-experimental-features nix-command "
            "--extra-experimental-features flakes develop "
            "${{ github.workspace }}#default --command bash -euo pipefail {0}",
            text,
        )
        self.assertIn("uses: ./.github/actions/setup-nix", text)

    def test_no_toolchain_installs_or_render(self):
        text = read(PAGES_YML)
        for forbidden in ("openscad", "setup-node", "setup-python", "sudo",
                          "apt-get", "nix-env -i", "pip install"):
            self.assertNotIn(forbidden, text)

    def test_no_oidc(self):
        text = read(PAGES_YML)
        self.assertNotIn("enable-openid-connect", text)
        self.assertNotIn("configure-aws-credentials", text)

    def test_fork_prs_are_skipped(self):
        self.assertIn(
            "github.event.pull_request.head.repo.full_name == github.repository",
            read(PAGES_YML),
        )

    def test_triggers_on_main_push_and_pr_without_close(self):
        text = read(PAGES_YML)
        self.assertRegex(text, r"push:\n    branches: \[main\]")
        self.assertIn("types: [opened, synchronize, reopened]", text)
        self.assertNotIn("closed", text)

    def test_concurrency_does_not_join_build_groups(self):
        text = read(PAGES_YML)
        self.assertIn("group: spec-pages-", text)
        self.assertNotRegex(text, r"group: pages-")

    def test_external_actions_are_sha_pinned_full_urls(self):
        uses = re.findall(r"uses:\s*(\S+)(.*)", read(PAGES_YML))
        self.assertTrue(uses)
        for ref, rest in uses:
            if ref.startswith("./"):
                continue
            self.assertTrue(ref.startswith("https://"), ref)
            self.assertRegex(ref.partition("@")[2], r"^[0-9a-f]{40}$")
            self.assertRegex(rest.strip(), r"^#\s*v\d+\.\d+\.\d+$")

    def test_checks_figures_before_publishing(self):
        text = read(PAGES_YML)
        check = text.index("test_spec_pages.py")
        self.assertLess(check, text.index("aws s3 sync"))


class SecretHandlingTests(unittest.TestCase):
    def test_pages_secrets_only_on_env_lines(self):
        for path in (PAGES_YML, CLEANUP_YML):
            for line in read(path).splitlines():
                if "secrets.PAGES_S3_" in line:
                    with self.subTest(path=path.name, line=line.strip()):
                        self.assertRegex(
                            line.strip(),
                            r"^AWS_(ACCESS_KEY_ID|SECRET_ACCESS_KEY): "
                            r"\$\{\{ secrets\.PAGES_S3_\w+ \}\}$",
                        )

    def test_no_expressions_in_run_blocks(self):
        text = read(PAGES_YML)
        for name in ("Check spec pages", "Publish PR spec pages",
                     "Publish main spec pages", "Link spec pages from the PR"):
            with self.subTest(step=name):
                self.assertNotIn("${{", run_block(step(text, name)))

    def test_garage_endpoint_region_and_path_style(self):
        for name in ("Publish PR spec pages", "Publish main spec pages"):
            body = step(read(PAGES_YML), name)
            with self.subTest(step=name):
                self.assertIn("AWS_ENDPOINT_URL: https://s3.home.bstjohn.net", body)
                self.assertIn("AWS_DEFAULT_REGION: garage", body)
                self.assertIn("AWS_CONFIG_FILE: ${{ runner.temp }}/aws-config", body)
                self.assertIn("addressing_style = path", body)
                self.assertIn("PAGES_S3_* secrets are empty", body)


class PublishTests(unittest.TestCase):
    def test_pr_number_validated_before_any_aws_call(self):
        body = step(read(PAGES_YML), "Publish PR spec pages")
        guard = body.index('case "$PR_NUMBER" in \'\'|*[!0-9]*)')
        self.assertLess(guard, body.index("aws s3"))
        self.assertIn('PREFIX="3d-models/pr/pr-${PR_NUMBER}"', body)

    def test_pr_supersedes_earlier_shas_and_outputs_url(self):
        body = step(read(PAGES_YML), "Publish PR spec pages")
        sync = body.index('aws s3 sync ./pages "s3://pages/${PREFIX}/${SHA8}/" --delete')
        rm = body.index('aws s3 rm "s3://pages/${PREFIX}/" --recursive --exclude "${SHA8}/*"')
        self.assertLess(sync, rm)
        self.assertIn('echo "url=$URL" >> "$GITHUB_OUTPUT"', body)

    def test_main_entry_page_written_after_supersession(self):
        body = step(read(PAGES_YML), "Publish main spec pages")
        self.assertIn('PREFIX="3d-models/docs/main"', body)
        sync = body.index('aws s3 sync ./pages "s3://pages/${PREFIX}/${SHA8}/" --delete')
        rm = body.index('aws s3 rm "s3://pages/${PREFIX}/" --recursive --exclude "${SHA8}/*"')
        cp = body.index('aws s3 cp "$RUNNER_TEMP/index.html" "s3://pages/${PREFIX}/index.html"')
        self.assertLess(sync, rm)
        self.assertLess(rm, cp)
        self.assertIn("--content-type text/html --cache-control no-cache", body[cp:])
        self.assertIn('http-equiv="refresh" content="0; url=./%s/"', body)

    def test_main_publish_gated_to_main_push(self):
        self.assertIn(
            "if: github.event_name == 'push' && github.ref == 'refs/heads/main'",
            step(read(PAGES_YML), "Publish main spec pages"),
        )

    def test_repo_only_sources_are_not_published(self):
        text = read(PAGES_YML)
        self.assertEqual(text.count('--exclude "*/src/*" --exclude "*.md"'), 2)

    def test_never_writes_host_root_index(self):
        text = read(PAGES_YML)
        self.assertNotIn("s3://pages/index.html", text)
        self.assertNotRegex(text, r'"s3://pages/"')

    def test_pr_comment_is_best_effort_and_pr_only(self):
        body = step(read(PAGES_YML), "Link spec pages from the PR")
        self.assertIn("if: github.event_name == 'pull_request'", body)
        self.assertIn("continue-on-error: true", body)
        self.assertIn("python3 scripts/pages_pr_comment.py", body)


class CleanupTests(unittest.TestCase):
    def test_spec_pages_step_deletes_one_pr_prefix(self):
        body = step(read(CLEANUP_YML), "Delete spec pages prefix")
        guard = body.index("''|*[!0-9]*)")
        self.assertLess(guard, body.index("aws s3 rm"))
        self.assertIn('target="s3://pages/3d-models/pr/pr-${pr}/"', body)
        self.assertIn('aws s3 rm "$target" --recursive', body)
        self.assertIn("addressing_style = path", body)
        self.assertIn("AWS_ENDPOINT_URL: https://s3.home.bstjohn.net", body)

    def test_spec_pages_step_runs_before_oidc_credentials(self):
        text = read(CLEANUP_YML)
        self.assertLess(text.index("      - name: Delete spec pages prefix"),
                        text.index("      - name: Configure AWS credentials"))


class BuildInteractionTests(unittest.TestCase):
    def test_build_ignores_pages_only_changes(self):
        text = read(BUILD_YML)
        self.assertEqual(text.count("      - 'pages/**'"), 2)


if __name__ == "__main__":
    unittest.main()
