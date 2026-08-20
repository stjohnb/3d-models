"""Text-level invariant tests for the build workflow.

CI runs on the org's self-hosted NixOS runners, which deliberately provide
only nix/git/docker. Every tool build.yml shells out to comes from this
repo's own flake.nix devShell, entered via the job-level default shell
(`nix ... develop ...#default --command bash ...`). These tests guard
against edits that reintroduce runner-provided tooling:

* ``actions/setup-node`` / ``actions/setup-python`` never work here — their
  prebuilt tarballs hardcode FHS loader paths and the tool manifest matches
  against an Ubuntu release (issues #348, #356). node/python come from the
  flake.
* ``sudo``/``apt-get`` don't exist on the runners; the job is unprivileged
  by design.
* OpenSCAD PNG rendering must stay on the flake's EGL/llvmpipe headless
  wrapper. The old Xvfb + NVIDIA-EGL-pinning workarounds (issue #361;
  St-John-Software/nixos-config#110, #111) are gone and must not creep back.

ImageMagick from the flake ships no distro ``type.xml``, so every
text-capable invocation in ``build.yml`` — ``montage`` (which labels tiles
by default) and the ``convert``/``magick`` fallback — must name a font
explicitly or it fails with "unable to read font `(null)'" (issue #352).
The flake pins FONTCONFIG_FILE to a Liberation font set so the named font
always resolves.

Run with: python3 -m unittest test_build_workflow
"""

import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD_YML = REPO_ROOT / ".github" / "workflows" / "build.yml"
NOTIFY_YML = REPO_ROOT / ".github" / "workflows" / "notify-failures.yml"
FLAKE_NIX = REPO_ROOT / "flake.nix"
SCRIPTS_DIR = REPO_ROOT / "scripts"
OG_FONT = "Liberation-Sans"


def read(path):
    return path.read_text(encoding="utf-8")


def step_body(text, name):
    """Return the run-block text of the named step, up to the next step."""
    marker = f"      - name: {name}\n"
    if marker not in text:
        raise AssertionError(f"step {name!r} not found in build.yml")
    start = text.index(marker)
    next_step = text.index("\n      - name: ", start + len(marker))
    return text[start:next_step]


def code_lines(text):
    """Workflow text with comment-only lines removed."""
    return "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("#")
    )


class OgHeroFontTests(unittest.TestCase):
    def test_og_font_variable_defined(self):
        text = read(BUILD_YML)
        self.assertIn(
            f"OG_FONT='{OG_FONT}'",
            text,
            f"build.yml must define OG_FONT='{OG_FONT}'",
        )

    def test_imagemagick_invocations_name_a_font(self):
        lines = read(BUILD_YML).splitlines()
        # Invocations are wrapped in `if ... ; then` so the interesting
        # token may not be the first word on the line.
        invocation_re = re.compile(
            r'^(if\s+)?(montage\s|"?\$\{?IM_CONVERT|convert\s|magick\s)'
        )
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not invocation_re.match(stripped):
                continue
            window = lines[i : i + 13]
            self.assertTrue(
                any("-font" in w for w in window),
                f"build.yml:{i + 1} invokes ImageMagick without naming a "
                f"font within the following 12 lines: {stripped!r}",
            )

    def test_no_bare_default_font_reliance(self):
        lines = read(BUILD_YML).splitlines()
        for i, line in enumerate(lines):
            if "-annotate" not in line:
                continue
            window = lines[max(0, i - 6) : i + 1]
            self.assertTrue(
                any(f'-font "$OG_FONT"' in w for w in window),
                f"build.yml:{i + 1} uses -annotate without -font \"$OG_FONT\" "
                "in the preceding 6 lines",
            )

    def test_flake_pins_fontconfig_to_liberation(self):
        text = read(FLAKE_NIX)
        self.assertIn(
            "FONTCONFIG_FILE",
            text,
            "flake.nix must pin FONTCONFIG_FILE so ImageMagick can resolve "
            f"{OG_FONT} — see issue #352",
        )
        self.assertIn(
            "liberation_ttf",
            text,
            "flake.nix's font set must include liberation_ttf",
        )


class NixDevShellTests(unittest.TestCase):
    """Every CI tool must come from flake.nix, not the runner."""

    def test_no_toolchain_setup_actions(self):
        for forbidden in ("actions/setup-node", "actions/setup-python"):
            for path in (BUILD_YML, NOTIFY_YML):
                self.assertNotIn(
                    forbidden,
                    code_lines(read(path)),
                    f"{path.name} must not use {forbidden} — its prebuilt "
                    "toolchains do not work on the NixOS runners (#348, "
                    "#356). Add the tool to flake.nix instead.",
                )

    def test_no_privileged_install(self):
        for forbidden in ("sudo ", "apt-get", "dpkg "):
            for path in (BUILD_YML, NOTIFY_YML):
                self.assertNotIn(
                    forbidden,
                    code_lines(read(path)),
                    f"{path.name} must not use {forbidden!r} — the NixOS "
                    "runners have no apt or sudo, and CI tools belong in "
                    "flake.nix.",
                )

    def test_build_job_runs_inside_default_devshell(self):
        text = read(BUILD_YML)
        self.assertRegex(
            text,
            r"shell: nix .*develop \$\{\{ github\.workspace \}\}#default"
            r" --command bash -euo pipefail \{0\}",
            "build.yml must run every step inside the flake's default "
            "devShell via a job-level defaults.run.shell",
        )
        self.assertIn(
            "--extra-experimental-features nix-command",
            text,
            "the nix develop shell must enable nix-command/flakes explicitly "
            "— don't rely on the runner's nix.conf",
        )

    def test_setup_nix_runs_before_shell_is_needed(self):
        text = read(BUILD_YML)
        setup_nix = "uses: ./.github/actions/setup-nix"
        self.assertIn(setup_nix, text, "build.yml must use the setup-nix action")
        first_run = text.index("\n        run: |")
        self.assertLess(
            text.index(setup_nix),
            first_run,
            "setup-nix must run before the first run: step — the default "
            "shell needs nix on PATH",
        )

    def test_runner_labels_unchanged(self):
        self.assertIn(
            "runs-on: [self-hosted, linux, ryzen]",
            read(BUILD_YML),
            "the build job must stay pinned to the ryzen runner — "
            "RENDER_MEM_MAX is calibrated against that host's RAM",
        )


class HeadlessRenderTests(unittest.TestCase):
    """Rendering must stay on the flake's EGL-offscreen openscad wrapper."""

    def test_no_xvfb(self):
        self.assertNotIn(
            "xvfb",
            code_lines(read(BUILD_YML)).lower(),
            "build.yml must not use Xvfb — the flake's openscad wrapper "
            "renders offscreen via EGL/llvmpipe (issue #361 is solved in "
            "flake.nix, not in the workflow)",
        )

    def test_gl_smoke_step_is_non_fatal(self):
        body = step_body(read(BUILD_YML), "Verify headless OpenSCAD rendering")
        self.assertIn("continue-on-error: true", body)
        self.assertIn("89504e470d0a1a0a", body)
        self.assertIn("::warning::", body)
        self.assertNotIn("::error::", body)
        self.assertNotIn("exit 1", body)

    def test_stl_export_pins_cgal_backend(self):
        body = step_body(read(BUILD_YML), "Render STL files")
        self.assertIn(
            "--backend=CGAL --export-format binstl",
            body,
            "STL export must pin --backend=CGAL — openscad-unstable's "
            "default Manifold backend emits degenerate facets for the "
            "drawer baseplate grids, which fails admesh validation",
        )

    def test_flake_wrapper_forces_software_gl(self):
        text = read(FLAKE_NIX)
        for needle in (
            "LIBGL_ALWAYS_SOFTWARE",
            "__EGL_VENDOR_LIBRARY_FILENAMES",
            "QT_QPA_PLATFORM offscreen",
            "--unset DISPLAY",
        ):
            self.assertIn(
                needle,
                text,
                f"flake.nix's openscad wrapper must set {needle!r} so PNG "
                "export works with no X server (issue #361)",
            )


class ThumbnailRenderTests(unittest.TestCase):
    """Thumbnail rendering must fail loudly, not ship 0-byte PNGs (#359).

    OpenSCAD exits 0 after "Cannot create OpenGL OffscreenView" but leaves an
    empty file behind. Without an output check those empties synced to S3 and
    the landing gallery hid every image, showing bare text.
    """

    def test_thumbnail_step_validates_png_magic(self):
        body = step_body(read(BUILD_YML), "Render PNG thumbnails")
        self.assertIn(
            "89504e470d0a1a0a",
            body,
            "the thumbnail step must check the 8-byte PNG signature — a "
            "non-empty file is not enough, and `file`/`identify` are not "
            "guaranteed in the devShell",
        )

    def test_thumbnail_step_records_failures(self):
        text = read(BUILD_YML)
        self.assertGreaterEqual(
            text.count(".thumb-failures"),
            2,
            "the thumbnail step must write .thumb-failures and the "
            "enforcement step must cat it",
        )

    def test_thumbnail_step_has_id(self):
        self.assertIn(
            "id: thumbnails",
            read(BUILD_YML),
            "the enforcement step keys off steps.thumbnails.outputs.failed",
        )

    def test_thumbnail_enforcement_step_exists(self):
        text = read(BUILD_YML)
        self.assertIn("steps.thumbnails.outputs.failed == 'true'", text)
        enforce = "- name: Enforce thumbnail rendering"
        deploy = "- name: Deploy to S3"
        self.assertIn(enforce, text)
        self.assertIn(deploy, text)
        self.assertLess(
            text.index(deploy),
            text.index(enforce),
            "deferred enforcement: the pipeline must reach the deploy step "
            "(and produce PR comment / validation.json) before the thumbnail "
            "failure exits non-zero",
        )

    def test_invalid_thumbnails_are_deleted(self):
        body = step_body(read(BUILD_YML), "Render PNG thumbnails")
        self.assertIn(
            'rm -f "site/$name.png"',
            body,
            "an invalid PNG must be deleted so the S3 sync cannot ship it",
        )

    def test_deploy_is_gated_on_thumbnail_success(self):
        """A thumbnail regression must not reach production (#406).

        Invalid PNGs are deleted above and the main deploy runs
        `aws s3 sync --delete`, so deploying after a thumbnail failure
        strips the last good thumbnails off the live site — the exact
        #359 symptom.
        """
        body = step_body(read(BUILD_YML), "Deploy to S3 (main)")
        for output in (
            "validate",
            "metadata",
            "interference",
            "param_meta",
            "thumbnails",
        ):
            self.assertIn(
                f"steps.{output}.outputs.failed != 'true'",
                body,
                f"the main S3 deploy must be gated on steps.{output}",
            )
        self.assertIn("--delete", body)


class ProjectDisplayNameTests(unittest.TestCase):
    """One dir→display-name implementation, consumed everywhere (issue #399)."""

    def test_no_inline_python_copies(self):
        self.assertNotIn(
            ".replace('-', ' ').replace('_', ' ').title()",
            code_lines(read(BUILD_YML)),
            "build.yml must call scripts.oembed_helpers.project_display_name "
            "instead of re-implementing the transform inline",
        )

    def test_manifest_step_uses_helper(self):
        body = step_body(read(BUILD_YML), "Generate models manifest")
        self.assertIn("project_name = project_display_name(project_dir)", body)

    def test_changed_projects_step_uses_helper(self):
        body = step_body(read(BUILD_YML), "Generate changed projects list (PR only)")
        self.assertIn("from scripts.oembed_helpers import project_display_name", body)
        self.assertIn("project_display_name(d)", body)

    def test_pr_comment_reads_canonical_names(self):
        body = step_body(read(BUILD_YML), "Comment on PR with thumbnails")
        self.assertIn("site/models.json", body)
        self.assertIn("dirToProject", body)
        self.assertNotIn(
            "toUpperCase",
            body,
            "the PR-comment step must read display names from models.json, "
            "not re-derive them in JS",
        )


class QrSlugifyTests(unittest.TestCase):
    """Issue #398: the QR step imports slugify(); it never re-derives it.

    A Bash re-implementation is invisible to test_viewer_invariants.py's
    slugify-parity check, so it can drift and emit stale deep links.
    """

    def test_qr_step_imports_canonical_slugify(self):
        body = step_body(read(BUILD_YML), "Generate QR codes")
        self.assertIn("from scripts.oembed_helpers import", body)
        self.assertIn("slugify", body)

    def test_qr_step_has_no_shell_slug_pipeline(self):
        body = code_lines(step_body(read(BUILD_YML), "Generate QR codes"))
        for token in ("[:upper:]", "[:lower:]", "sed 's/[_ ]"):
            self.assertNotIn(
                token, body,
                f"QR step re-implements slugify in shell ({token!r}); "
                "import it from scripts.oembed_helpers instead",
            )

    def test_no_shell_slug_pipeline_anywhere(self):
        self.assertNotIn(
            "tr '[:upper:]' '[:lower:]'", code_lines(read(BUILD_YML)),
            "build.yml must not lowercase-slug in shell; use slugify()",
        )


class StructuredDataTests(unittest.TestCase):
    """Issue #409: the @graph payload is built by the shared helper, not inline."""

    def test_structured_data_step_uses_helper(self):
        body = step_body(read(BUILD_YML), "Generate structured data")
        self.assertIn("build_structured_data", body)
        self.assertNotIn("'@type': 'Organization'", body)

    def test_sitemap_step_uses_helper(self):
        body = step_body(read(BUILD_YML), "Generate sitemap.xml")
        self.assertIn("standalone_url", body)
        self.assertNotIn(r"re.sub(r'\.stl$'", body)

    def test_injection_preserves_script_escapes(self):
        body = step_body(
            read(BUILD_YML),
            "Copy index.html and embed.html to site with cache-busting hash and injected data",
        )
        for escape in (r"\\u0026", r"\\u003c", r"\\u003e"):
            self.assertIn(escape, body)


UNIT_TEST_STEP = "Run Python unit tests for build scripts"

# test_*.py modules deliberately NOT in the fast unit-test step, with why.
EXCLUDED_TEST_MODULES = {
    "test_check_interference":
        "runs in its own venv (trimesh/manifold3d) in the "
        "'Check mating part interference' step",
    "test_fetch_terrain_heightmap":
        "needs numpy/PIL/requests, which are not in the flake devShell",
    "test_sync_public_snapshot":
        "integration-style: drives real git subprocesses in temp repos",
    "test_scan_masks":
        "needs numpy/opencv4/rembg, which live in the scan devShell, not default",
    "test_scan_mesh":
        "needs numpy/trimesh, which live in the scan devShell, not default",
}


class UnitTestStepCoverageTests(unittest.TestCase):
    """Issue #407: every scripts/test_*.py must run somewhere, or be
    explicitly excluded with a reason. Three modules silently never ran."""

    def _listed_modules(self):
        body = step_body(read(BUILD_YML), UNIT_TEST_STEP)
        return set(re.findall(r"\btest_[a-z0-9_]+\b", body))

    def test_every_test_module_is_listed_or_excluded(self):
        on_disk = {p.stem for p in SCRIPTS_DIR.glob("test_*.py")}
        missing = sorted(on_disk - self._listed_modules()
                         - set(EXCLUDED_TEST_MODULES))
        self.assertEqual(
            missing, [],
            f"{missing} exist in scripts/ but run nowhere in CI; add them "
            f"to the {UNIT_TEST_STEP!r} step or to EXCLUDED_TEST_MODULES",
        )

    def test_listed_modules_all_exist(self):
        for mod in sorted(self._listed_modules()):
            self.assertTrue(
                (SCRIPTS_DIR / f"{mod}.py").is_file(),
                f"build.yml runs {mod}, but scripts/{mod}.py does not exist",
            )

    def test_exclusions_are_not_stale(self):
        for mod in sorted(EXCLUDED_TEST_MODULES):
            self.assertTrue(
                (SCRIPTS_DIR / f"{mod}.py").is_file(),
                f"stale exclusion: scripts/{mod}.py no longer exists",
            )

    def test_newly_added_modules_are_listed(self):
        for mod in ("test_generate_standalone", "test_scad_orientation",
                    "test_generate_gallery"):
            self.assertIn(mod, self._listed_modules())


if __name__ == "__main__":
    unittest.main()
