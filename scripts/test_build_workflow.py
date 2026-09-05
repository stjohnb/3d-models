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
* Temp files must live in per-job $RUNNER_TEMP, not world-writable /tmp, to
  prevent symlink-clobber attacks and untrusted content injection (#424).

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

from oembed_helpers import OG_HERO_TILE_COLUMNS, OG_HERO_TILE_ROWS

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD_YML = REPO_ROOT / ".github" / "workflows" / "build.yml"
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
            self.assertNotIn(
                forbidden,
                code_lines(read(BUILD_YML)),
                f"build.yml must not use {forbidden} — its prebuilt "
                "toolchains do not work on the NixOS runners (#348, "
                "#356). Add the tool to flake.nix instead.",
            )

    def test_no_privileged_install(self):
        for forbidden in ("sudo ", "apt-get", "dpkg "):
            self.assertNotIn(
                forbidden,
                code_lines(read(BUILD_YML)),
                f"build.yml must not use {forbidden!r} — the NixOS "
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

    def test_no_pip_installs(self):
        """Issue #423: no unpinned PyPI code on the credentialed runner."""
        for forbidden in ("pip install", "python3 -m venv", "-m virtualenv"):
            self.assertNotIn(
                forbidden,
                code_lines(read(BUILD_YML)),
                f"build.yml must not use {forbidden!r} — the build job "
                "holds the deploy AWS role and a write-scoped "
                "GITHUB_TOKEN. Python deps come from flake.nix's "
                "python3.withPackages, pinned by flake.lock (#423).",
            )

    def test_default_devshell_provides_python_deps(self):
        flake = read(FLAKE_NIX)
        self.assertIn("python3.withPackages", flake)
        default = flake[flake.index("default = pkgs.mkShell"):
                        flake.index("scripts = pkgs.mkShell")]
        for pkg in ("jsonschema", "trimesh", "manifold3d", "numpy"):
            self.assertIn(pkg, default,
                          f"the default devShell must provide {pkg} (#423)")


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


class ScratchPathTests(unittest.TestCase):
    """Temp files must live in the per-job $RUNNER_TEMP, not shared /tmp (#424).

    The runners are long-lived, self-hosted and shared between the org's
    repos, so a fixed /tmp path is both a symlink-clobber primitive and a
    way to forge the OpenSCAD log the render step's "library, no top-level
    geometry" branch trusts — which silently drops a model from the deploy.
    """

    def test_render_log_uses_runner_temp(self):
        body = step_body(read(BUILD_YML), "Render STL files")
        self.assertEqual(
            body.count('"$RUNNER_TEMP/scad.log"'),
            3,
            "the render step must redirect, cat and grep the OpenSCAD log "
            'via "$RUNNER_TEMP/scad.log"',
        )

    def test_no_fixed_tmp_paths_in_workflow(self):
        self.assertNotIn(
            "/tmp/",
            code_lines(read(BUILD_YML)),
            "build.yml must not name a fixed /tmp path — use $RUNNER_TEMP, "
            "which the runner creates per job (issue #424)",
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


class ParamManifestExternalAssetTests(unittest.TestCase):
    """The customizer check is per-renderable, not per-project (#448)."""

    def test_check_is_scoped_to_the_manifests_own_scad(self):
        body = code_lines(step_body(read(BUILD_YML), "Validate parameters manifests"))
        self.assertIn("external_assets_for(scad_path, project_dir)", body)
        self.assertNotIn("external_assets(project_dir)", body)
        self.assertIn("from external_assets import external_assets_for", body)

    def test_source_zip_step_stays_per_project(self):
        body = step_body(read(BUILD_YML), "Bundle project source zips")
        self.assertIn('python3 scripts/external_assets.py "$dir"', body)


class OgHeroTileSourceTests(unittest.TestCase):
    """Issue #458: OG hero tiles come from .scad-map, not a site/*.png glob."""

    def test_no_bare_png_glob(self):
        body = step_body(read(BUILD_YML), "Generate OG hero image")
        self.assertNotIn(
            "(site/*.png)",
            code_lines(body),
            "the glob swept the _top/_bottom/_front orthographic views "
            "written by the complex_interior step (issue #458)",
        )

    def test_tiles_chosen_by_tested_helper(self):
        body = step_body(read(BUILD_YML), "Generate OG hero image")
        self.assertIn(
            "og_hero_thumbnails",
            body,
            "tile selection must go through the tested Python helper, not "
            "be re-derived in Bash",
        )

    def test_tile_grid_matches_helper_cap(self):
        body = step_body(read(BUILD_YML), "Generate OG hero image")
        self.assertIn(f"-tile {OG_HERO_TILE_COLUMNS}x{OG_HERO_TILE_ROWS}", body)

    def test_montage_output_piped_to_second_stage(self):
        body = step_body(read(BUILD_YML), "Generate OG hero image")
        self.assertIn("miff:-", body)
        self.assertGreaterEqual(
            body.count("miff:-"),
            2,
            "montage output must be piped into a second ImageMagick stage "
            "for -extent to actually apply",
        )

    def test_extent_applied(self):
        body = step_body(read(BUILD_YML), "Generate OG hero image")
        self.assertIn("-extent 1200x630", body)

    def test_no_resize_chained_onto_montage(self):
        body = step_body(read(BUILD_YML), "Generate OG hero image")
        self.assertNotIn(
            "-resize",
            code_lines(body),
            "-resize chained onto montage is a silent no-op — the deployed "
            "og-hero.png measured 1224x14168 (issue #458)",
        )

    def test_tiles_read_with_mapfile(self):
        body = step_body(read(BUILD_YML), "Generate OG hero image")
        self.assertIn("mapfile -t THUMBS", body)


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


class OutputNameUniquenessTests(unittest.TestCase):
    """Issue #449: renderables share one flat output namespace.

    The gate is scripts/test_output_names.py, a source-tree invariant test.
    It only gates the build if the unit-test step still runs before the
    render step — reordering them would let a collision clobber an STL
    before the check fires.
    """

    def test_output_names_module_runs_in_ci(self):
        body = step_body(read(BUILD_YML), UNIT_TEST_STEP)
        self.assertIn("unittest discover", body)
        self.assertIn("-p 'test_*.py'", body)

    def test_unit_tests_run_before_the_render_step(self):
        text = read(BUILD_YML)
        self.assertLess(
            text.index(f"      - name: {UNIT_TEST_STEP}"),
            text.index("      - name: Render STL files"),
            "test_output_names gates duplicate basenames and slug "
            "collisions; if the unit-test step moves after the render "
            "step, the clobber happens before the gate fires",
        )


class StructuredDataTests(unittest.TestCase):
    """Issue #409: the @graph payload is built by the shared helper, not inline."""

    def test_structured_data_step_uses_helper(self):
        body = step_body(read(BUILD_YML), "Generate structured data")
        self.assertIn("build_structured_data", body)
        self.assertNotIn("'@type': 'Organization'", body)

    def test_sitemap_step_uses_helper(self):
        body = step_body(read(BUILD_YML), "Generate sitemap.xml")
        self.assertIn("build_sitemap", body)
        self.assertIn("stl_lastmods", body)
        self.assertNotIn("<urlset", body)
        self.assertNotIn("<loc>", body)
        self.assertNotIn(r"re.sub(r'\.stl$'", body)

    def test_injection_preserves_script_escapes(self):
        body = step_body(
            read(BUILD_YML),
            "Copy index.html and embed.html to site with cache-busting hash and injected data",
        )
        for escape in (r"\\u0026", r"\\u003c", r"\\u003e"):
            self.assertIn(escape, body)


UNIT_TEST_STEP = "Run Python unit tests for build scripts"
UNIT_TEST_DISCOVER = "python3 -m unittest discover -s scripts -p 'test_*.py'"

# Modules whose *third-party* deps are not all in the `default` devShell.
# They must be discovered and self-skip, never silently omitted.
ENV_GATED_TEST_MODULES = {
    "test_scan_masks":
        "MaskGeometryTests needs opencv4, which lives in the `scan` devShell",
}


class UnitTestStepCoverageTests(unittest.TestCase):
    """Issue #457: the step discovers every scripts/test_*.py rather than
    naming modules by hand, so a new test file cannot silently not run."""

    def test_step_uses_discovery_not_a_hand_list(self):
        body = step_body(read(BUILD_YML), UNIT_TEST_STEP)
        self.assertIn(UNIT_TEST_DISCOVER, body)

    def test_step_names_no_individual_modules(self):
        body = step_body(read(BUILD_YML), UNIT_TEST_STEP)
        named = sorted(set(re.findall(r"\btest_[a-z0-9_]{2,}\b", body))
                       - {"test_"})
        self.assertEqual(
            named, [],
            f"{named} named explicitly in the {UNIT_TEST_STEP!r} step; "
            f"discovery covers scripts/test_*.py — remove the hand list",
        )

    def test_env_gated_modules_self_skip(self):
        for mod, why in sorted(ENV_GATED_TEST_MODULES.items()):
            path = SCRIPTS_DIR / f"{mod}.py"
            self.assertTrue(path.is_file(), f"stale entry: {path} is gone")
            src = path.read_text()
            self.assertTrue(
                "skipUnless" in src or "skipIf" in src,
                f"{mod} ({why}) is discovered by CI but has no skip guard; "
                f"it will hard-error in the default devShell",
            )


class ActionPinTests(unittest.TestCase):
    """Issue #499: third-party actions must be pinned to full commit SHAs.

    The build job runs with `id-token: write` and mints an OIDC token for
    the AWS deploy role in the `Configure AWS credentials` step. A mutable
    major-version tag there means a force-moved upstream tag, or a
    compromised action repo, executes arbitrary code inside the credential
    step of every privileged main-branch deploy with no change in this
    repo. Tag pins are also invisible to Dependabot when a tag is rewritten
    in place.
    """

    USES_RE = re.compile(r"^\s*(?:-\s+)?uses:\s*(\S+)(.*)$", re.MULTILINE)
    SHA_RE = re.compile(r"^[0-9a-f]{40}$")

    def _external_uses(self):
        for ref, rest in self.USES_RE.findall(read(BUILD_YML)):
            if ref.startswith("./"):
                continue  # local composite action; already immutable
            yield ref, rest

    def test_every_external_action_is_sha_pinned(self):
        for ref, _rest in self._external_uses():
            self.assertIn("@", ref, f"{ref} has no version reference")
            _repo, _, version = ref.partition("@")
            self.assertRegex(
                version, self.SHA_RE,
                f"{ref} is pinned to a mutable tag. Pin it to a full "
                "40-character commit SHA (#499) — the build job holds "
                "id-token: write and the AWS deploy role.",
            )

    def test_sha_pins_carry_a_version_comment(self):
        for ref, rest in self._external_uses():
            self.assertRegex(
                rest.strip(), r"^#\s*v\d+\.\d+\.\d+$",
                f"{ref} must carry a trailing '# vX.Y.Z' comment so the "
                "human-readable version stays visible and Dependabot can "
                "update both the SHA and the comment",
            )

    def test_local_setup_nix_stays_a_path_reference(self):
        self.assertIn(
            "uses: ./.github/actions/setup-nix", read(BUILD_YML),
            "the repo's own composite action must stay a local path "
            "reference — it cannot and must not be SHA-pinned",
        )

    def test_aws_credentials_step_is_sha_pinned(self):
        self.assertRegex(
            read(BUILD_YML),
            r"uses: aws-actions/configure-aws-credentials@[0-9a-f]{40}"
            r" # v\d+\.\d+\.\d+",
            "the OIDC credential step must be SHA-pinned (#499)",
        )


if __name__ == "__main__":
    unittest.main()
