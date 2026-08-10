"""Text-level invariant tests for the web viewers.

These guard the contracts CI and the docs depend on but which nothing else
can check statically:

* the build-time placeholder markers CI string-replaces in ``index.html``
* the ``__HASH_ROUTING_*`` markers ``test_hash_routing.mjs`` slices between
* the ``slugify()`` / ``PUBLIC_REPO`` copies that must stay textually
  identical across viewers (see CLAUDE.md)
* the "no ``innerHTML`` for user data" XSS convention

Run with: python3 -m unittest test_viewer_invariants
"""

import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEX_HTML = REPO_ROOT / "index.html"
EMBED_HTML = REPO_ROOT / "embed.html"
STANDALONE_PY = REPO_ROOT / "scripts" / "generate-standalone.py"

VIEWERS = (INDEX_HTML, EMBED_HTML)
# Every place a WebGL render loop is written — the two viewers plus the
# standalone generator's HTML_TEMPLATE.
RENDER_SOURCES = (INDEX_HTML, EMBED_HTML, STANDALONE_PY)


def read(path):
    return path.read_text(encoding="utf-8")


class BuildMarkerTests(unittest.TestCase):
    """CI does a literal string replacement for each of these exactly once."""

    def test_build_markers(self):
        html = read(INDEX_HTML)
        for marker in (
            "__BUILD_HASH__",
            "<!-- __STRUCTURED_DATA__ -->",
            "<!-- __OEMBED_LINKS__ -->",
        ):
            self.assertEqual(
                html.count(marker),
                1,
                f"index.html must contain exactly one {marker!r}",
            )

    def test_hash_routing_markers(self):
        html = read(INDEX_HTML)
        for marker in ("__HASH_ROUTING_START__", "__HASH_ROUTING_END__"):
            self.assertEqual(
                html.count(marker),
                1,
                f"index.html must contain exactly one {marker!r} "
                "(scripts/test_hash_routing.mjs slices between them)",
            )
        self.assertLess(
            html.index("__HASH_ROUTING_START__"),
            html.index("__HASH_ROUTING_END__"),
            "__HASH_ROUTING_START__ must precede __HASH_ROUTING_END__",
        )


class LandingPageTests(unittest.TestCase):
    """Issue #345: index.html opens on a gallery of every project."""

    def test_landing_order_markers(self):
        html = read(INDEX_HTML)
        for marker in ("__LANDING_ORDER_START__", "__LANDING_ORDER_END__"):
            self.assertEqual(
                html.count(marker),
                1,
                f"index.html must contain exactly one {marker!r} "
                "(scripts/test_landing_order.mjs slices between them)",
            )
        self.assertLess(
            html.index("__LANDING_ORDER_START__"),
            html.index("__LANDING_ORDER_END__"),
            "__LANDING_ORDER_START__ must precede __LANDING_ORDER_END__",
        )

    def test_landing_markup_and_builder(self):
        html = read(INDEX_HTML)
        for token in (
            'id="landing"',
            'id="home-btn"',
            "function buildLanding(",
            "landing-desc-toggle",
            "is-collapsed",
            "function syncDescToggles(",
            "project.hero",
        ):
            self.assertIn(
                token,
                html,
                f"index.html must contain {token!r} for the landing gallery",
            )


class CopiedInvariantTests(unittest.TestCase):
    """Functions duplicated across viewers must stay textually identical."""

    SLUGIFY_BODY = (
        r"return str.replace(/\.stl$/i, '')"
        r".replace(/[_\s]+/g, '-').toLowerCase();"
    )
    PUBLIC_REPO_LINE = (
        "const PUBLIC_REPO = 'https://github.com/stjohnb/3d-models';"
    )

    def test_slugify_parity(self):
        for path in VIEWERS:
            self.assertIn(
                self.SLUGIFY_BODY,
                read(path),
                f"{path.name} must contain the canonical slugify() body",
            )

    def test_public_repo_parity(self):
        for path in VIEWERS:
            self.assertIn(
                self.PUBLIC_REPO_LINE,
                read(path),
                f"{path.name} must declare PUBLIC_REPO identically",
            )


class XssConventionTests(unittest.TestCase):
    """`innerHTML` may only carry static markup, never model-derived data."""

    # Matches `innerHTML = `...`` (a template literal, possibly multi-line).
    TEMPLATE_ASSIGNMENT = re.compile(r"innerHTML\s*=\s*`([^`]*)`", re.DOTALL)
    # Matches an interpolation like ${TOUCH_ICON_ROTATE}
    INTERPOLATION = re.compile(r"\$\{([^}]*)\}")
    # Only SCREAMING_SNAKE_CASE constants (static SVG icon literals) allowed.
    STATIC_CONST = re.compile(r"^[A-Z][A-Z0-9_]*$")

    def test_no_interpolated_innerhtml(self):
        for path in VIEWERS:
            html = read(path)
            for template in self.TEMPLATE_ASSIGNMENT.findall(html):
                for expr in self.INTERPOLATION.findall(template):
                    self.assertRegex(
                        expr.strip(),
                        self.STATIC_CONST,
                        f"{path.name}: innerHTML interpolates {expr!r}; use "
                        "createElement/textContent for anything but a static "
                        "icon constant",
                    )


class ViewerChromeTests(unittest.TestCase):
    """Issue #337: one controls row, Orbit-only, collapsed disclosures."""

    def test_no_control_mode_switcher(self):
        for path in VIEWERS:
            html = read(path)
            for token in ("TrackballControls", "ArcballControls",
                          'id="mode-orbit"', "mode-btn"):
                self.assertNotIn(token, html, f"{path.name} still references {token}")

    def test_index_has_single_controls_row(self):
        html = read(INDEX_HTML)
        self.assertIn("pane-controls-row", html)
        self.assertNotIn("cross-section-row", html)
        self.assertNotIn("view-controls-row", html)

    def test_index_disclosures_start_closed(self):
        html = read(INDEX_HTML)
        self.assertNotIn("det.open = true", html)


class RenderBudgetTests(unittest.TestCase):
    """Issue #341 — the viewers must render on demand, not every frame."""

    def test_pixel_ratio_capped(self):
        for path in RENDER_SOURCES:
            text = read(path)
            self.assertNotIn(
                "setPixelRatio(window.devicePixelRatio)",
                text,
                f"{path.name} uses the raw device pixel ratio; cap it with "
                "MAX_PIXEL_RATIO so Retina displays don't pay 4x fragment cost",
            )
            self.assertIn(
                "MAX_PIXEL_RATIO",
                text,
                f"{path.name} must declare and apply MAX_PIXEL_RATIO",
            )

    def test_low_power_gpu_hint(self):
        for path in RENDER_SOURCES:
            self.assertIn(
                "powerPreference: 'low-power'",
                read(path),
                f"{path.name} must hint the integrated GPU — a discrete GPU is "
                "the biggest thermal lever on a dual-GPU laptop",
            )

    def test_on_demand_render_loop(self):
        for path in RENDER_SOURCES:
            text = read(path)
            for token in ("needsRender", "function invalidate("):
                self.assertIn(
                    token,
                    text,
                    f"{path.name} must render on demand via {token!r}",
                )

    def test_resize_observer(self):
        for path in RENDER_SOURCES:
            text = read(path)
            self.assertIn(
                "new ResizeObserver(",
                text,
                f"{path.name} must observe canvas size instead of polling "
                "clientWidth every frame",
            )
            self.assertIsNone(
                re.search(r"requestAnimationFrame\(animate\);\s*\n\s*resize\(\);", text),
                f"{path.name} still calls resize() from the animation loop, "
                "which forces a layout flush every frame",
            )


if __name__ == "__main__":
    unittest.main()
