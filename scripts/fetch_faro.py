#!/usr/bin/env python3
"""Stage the pinned Grafana Faro IIFE bundle under site/vendor/faro/<version>/.

``index.html`` and ``embed.html`` load it same-origin for browser RUM (Web
Vitals and JS errors, app ``3d-models``). The bytes are verified against the
SHA-256 pinned in faro_assets.py before they are written; a mismatch is a hard
failure — tampered first-party script must never reach S3, so like
fetch_threejs.py this deliberately does not join the deferred-enforcement
pattern.
"""

import hashlib
import os
import sys
import urllib.request

from faro_assets import FARO_ASSET, FARO_VERSION, VENDOR_DIR
from threejs_assets import fetch_url


def stage_asset(vendor_dir: str = VENDOR_DIR) -> str:
    """Download, verify and write the Faro bundle under vendor_dir; return its path."""
    data = fetch_url(
        FARO_ASSET["url"], expected_sha256=FARO_ASSET["sha256"], cache_subdir="faro"
    )
    out = os.path.join(vendor_dir, *FARO_ASSET["path"].split("/"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(data)
    print(f"  faro-web-sdk: {len(data):,} bytes -> {out}")
    return out


def print_hash() -> int:
    """Download the bundle and print its SHA-256 without staging or caching."""
    req = urllib.request.Request(FARO_ASSET["url"], headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    print(f'  faro-web-sdk: "sha256": "{hashlib.sha256(data).hexdigest()}",')
    return 0


def main() -> int:
    if "--print-hashes" in sys.argv[1:]:
        return print_hash()
    print(f"Vendoring Grafana Faro {FARO_VERSION} to {VENDOR_DIR}")
    stage_asset()
    return 0


if __name__ == "__main__":
    sys.exit(main())
