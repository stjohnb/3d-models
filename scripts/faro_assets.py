"""Single source of truth for the pinned Grafana Faro RUM runtime.

The deployed viewers (``index.html``, ``embed.html``) load Faro's IIFE
bundle same-origin from ``site/vendor/faro/<version>/`` — never from a CDN —
for the same reason as Three.js (issue #403). ``scripts/fetch_faro.py``
stages it, verified against the SHA-256 below, and
``scripts/check_browser_asset_vulns.py`` scans this version against OSV.
Standalone viewers never load it.

Bumping the version means: change ``FARO_VERSION``, run
``python3 scripts/fetch_faro.py --print-hashes`` and paste the printed digest
into ``FARO_ASSET``, then update ``FARO_BUNDLED`` from the new release's
``package.json`` (the bundle inlines ``@grafana/faro-core`` and
``ua-parser-js``). The viewers read the path from the ``data-faro-src``
attribute, which ``test_viewer_invariants.py`` checks against ``SCRIPT_SRC``.
"""

import os

FARO_VERSION = "2.14.0"

# url: where the bytes come from (the npm tarball's dist/bundle file, served
# verbatim by jsDelivr); sha256: the only bytes we accept; path: destination
# relative to the vendor dir.
FARO_ASSET = {
    "url": (
        f"https://cdn.jsdelivr.net/npm/@grafana/faro-web-sdk@{FARO_VERSION}"
        "/dist/bundle/faro-web-sdk.iife.js"
    ),
    "sha256": "10fce4fab3ea4b2d65046e594f41c0ec47f85b301a3e4e7850b8cd22e9d2de2a",
    "path": "faro-web-sdk.iife.js",
}

# Packages the IIFE bundle inlines at exact versions, scanned alongside the
# SDK itself. web-vitals is a caret range upstream and is not version-pinned.
FARO_BUNDLED = {
    "@grafana/faro-core": FARO_VERSION,
    "ua-parser-js": "1.0.41",
}

VENDOR_DIR = os.path.join("site", "vendor", "faro", FARO_VERSION)
SCRIPT_SRC = f"./vendor/faro/{FARO_VERSION}/{FARO_ASSET['path']}"
