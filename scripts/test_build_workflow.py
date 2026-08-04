"""Text-level invariant tests for the build workflow.

ImageMagick on the NixOS runner ships no default font (no distro
``type.xml``), so every text-capable invocation in ``build.yml`` — ``montage``
(which labels tiles by default) and the ``convert``/``magick`` fallback — must
name a font explicitly or it fails with "unable to read font `(null)'"
(issue #352). These tests guard against a future edit reintroducing a
fontless ImageMagick call.

The ryzen runner also has no system ``nodejs``, so ``actions/setup-node`` is
the only source of a ``node`` binary. When the runner's tool cache was
relocated off the ``/run`` tmpfs (St-John-Software/nixos-config issue #85),
the new path became writable but not executable by the runner's systemd
``DynamicUser`` unit, producing "Permission denied" / exit 126 (issue #356).
Overriding ``RUNNER_TOOL_CACHE`` via step ``env:`` does not work around this
— the runner re-injects its own value into every step's process environment
regardless of what the workflow declares. The workaround instead copies the
extracted toolchain into ``$RUNNER_TEMP`` (guaranteed exec-enabled, since the
runner executes step scripts from there) and adds a fail-fast verification
step; these tests guard against a future edit dropping that relocation or
reordering the steps.

Run with: python3 -m unittest test_build_workflow
"""

import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD_YML = REPO_ROOT / ".github" / "workflows" / "build.yml"
OG_FONT = "Liberation-Sans"


def read(path):
    return path.read_text(encoding="utf-8")


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


class NodeToolCacheTests(unittest.TestCase):
    """setup-node's output must be relocated to an executable path (#356)."""

    def test_no_runner_tool_cache_override(self):
        # A step-level `env: RUNNER_TOOL_CACHE: ...` override looks like a
        # fix but the runner silently discards it (confirmed in the #356
        # failure logs) — don't let it creep back in.
        text = read(BUILD_YML)
        self.assertNotIn(
            "RUNNER_TOOL_CACHE:",
            text,
            "RUNNER_TOOL_CACHE overrides via step env: are silently ignored "
            "by the runner — see issue #356. Relocate the toolchain to "
            "$RUNNER_TEMP instead.",
        )

    def test_step_order(self):
        text = read(BUILD_YML)
        setup_name = "- name: Set up Node.js for WASM smoke test"
        relocate_name = "- name: Relocate Node.js to an executable path"
        verify_name = "- name: Verify Node.js is executable"
        smoke_name = "- name: Smoke-test WASM customizer rendering"
        for name in (setup_name, relocate_name, verify_name, smoke_name):
            self.assertIn(name, text)
        self.assertLess(text.index(setup_name), text.index(relocate_name))
        self.assertLess(text.index(relocate_name), text.index(verify_name))
        self.assertLess(text.index(verify_name), text.index(smoke_name))

    def test_relocate_step_targets_runner_temp(self):
        lines = read(BUILD_YML).splitlines()
        for i, line in enumerate(lines):
            if "- name: Relocate Node.js to an executable path" not in line:
                continue
            window = lines[i : i + 14]
            self.assertTrue(
                any("$RUNNER_TEMP" in w for w in window),
                "Relocate step must copy the toolchain into $RUNNER_TEMP — "
                "see issue #356",
            )
            self.assertTrue(
                any("$GITHUB_PATH" in w for w in window),
                "Relocate step must add the copy to PATH via $GITHUB_PATH — "
                "see issue #356",
            )
            return
        self.fail("Relocate Node.js to an executable path step not found")


if __name__ == "__main__":
    unittest.main()
