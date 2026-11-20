#!/usr/bin/env python3
"""Stage the pinned Three.js runtime under site/vendor/three/<version>/.

The deployed viewers (index.html, embed.html) load Three.js same-origin via
an import map rather than from a CDN, so a compromised CDN response can't
execute as first-party script on the site (issue #403). Every file is
verified against the SHA-256 pinned in threejs_assets.py before it is
written; a mismatch is a hard failure — a tampered runtime must never reach
S3, so this deliberately does not join the deferred-enforcement pattern.
"""

import hashlib
import os
import sys
import urllib.request

from threejs_assets import THREEJS_ASSETS, THREEJS_VERSION, VENDOR_DIR, fetch_url


def stage_assets(vendor_dir: str = VENDOR_DIR) -> list[str]:
    """Download, verify and write every Three.js asset under vendor_dir.

    Returns the list of written paths.
    """
    written = []
    for key, asset in THREEJS_ASSETS.items():
        data = fetch_url(asset["url"], expected_sha256=asset["sha256"])
        out = os.path.join(vendor_dir, *asset["path"].split("/"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as f:
            f.write(data)
        print(f"  {key}: {len(data):,} bytes -> {out}")
        written.append(out)
    return written


def print_hashes() -> int:
    """Download each asset and print its SHA-256 without staging or caching."""
    for key, asset in THREEJS_ASSETS.items():
        req = urllib.request.Request(
            asset["url"], headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        print(f'  {key}: "sha256": "{hashlib.sha256(data).hexdigest()}",')
    return 0


def main() -> int:
    if "--print-hashes" in sys.argv[1:]:
        return print_hashes()
    print(f"Vendoring Three.js {THREEJS_VERSION} to {VENDOR_DIR}")
    stage_assets()
    # Record the pinned version for diagnostics.
    with open(os.path.join(VENDOR_DIR, "VERSION"), "w") as f:
        f.write(THREEJS_VERSION + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
