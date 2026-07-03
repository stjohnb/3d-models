#!/usr/bin/env python3
"""Fetch openscad-wasm release assets and stage them under site/openscad/.

The non-threaded openscad-wasm build (no SharedArrayBuffer requirement)
is used so the customizer works on plain S3 hosting without COOP/COEP
headers. Files are cached locally under .cache/openscad-wasm/ so repeat
runs (and local dev) don't re-download. SHA-256 hashes are pinned per
file; first-run / version-bump procedure is the same as
scripts/generate-standalone.py — compute, hard-code, commit.

Pinned release: 2022.03.20
  - openscad.js       (ES module wrapper; default export is async OpenSCAD())
  - openscad.wasm.js  (Emscripten JS module loaded by the wrapper)
  - openscad.wasm     (the WASM binary itself)

Bumping the version: change OPENSCAD_WASM_VERSION, run this script
locally, copy the printed SHA-256 values into EXPECTED_HASHES, commit.
"""

import hashlib
import os
import sys
import urllib.request

OPENSCAD_WASM_VERSION = "2022.03.20"

# Files we copy into site/openscad/. Fonts and the MCAD library are
# intentionally omitted — no model in this repo uses text() or MCAD.
ASSET_FILES = ("openscad.js", "openscad.wasm.js", "openscad.wasm")

# SHA-256 of each asset at the pinned version. Verified offline against
# https://github.com/openscad/openscad-wasm/releases/download/2022.03.20/<file>.
EXPECTED_HASHES = {
    "openscad.js":      "2809954ab46b618134068464ef5c5c568191ce34b131ad6e8639a3bb9fbf17ff",
    "openscad.wasm.js": "1519f21f9f2806a6bd14279fa0aadfb8b45304b79d89d3d7726b133ee1f2d6f7",
    "openscad.wasm":    "2dbec831e81e963dd7011606e3ddd87e9984bc04e9a4076255641d30ebe2fbf0",
}

CACHE_DIR = os.path.join(".cache", "openscad-wasm", OPENSCAD_WASM_VERSION)
OUTPUT_DIR = os.path.join("site", "openscad")
BASE_URL = (
    f"https://github.com/openscad/openscad-wasm/releases/download/"
    f"{OPENSCAD_WASM_VERSION}"
)


def fetch_asset(name: str, *, opener=urllib.request.urlopen) -> bytes:
    """Return the bytes for an asset, using the local cache when present.

    The opener kwarg is overridable for tests so the disk + network path
    doesn't have to be exercised live.
    """
    cache_path = os.path.join(CACHE_DIR, name)
    expected = EXPECTED_HASHES.get(name)

    if os.path.isfile(cache_path):
        with open(cache_path, "rb") as f:
            data = f.read()
        if expected and hashlib.sha256(data).hexdigest() == expected:
            return data
        # Stale cache — fall through and re-download.

    url = f"{BASE_URL}/{name}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with opener(req, timeout=60) as resp:
        data = resp.read()

    actual = hashlib.sha256(data).hexdigest()
    if expected and actual != expected:
        raise ValueError(
            f"SHA-256 mismatch for {name}\n"
            f"  expected: {expected}\n"
            f"  got:      {actual}"
        )
    if not expected:
        print(
            f"  WARNING: no expected SHA-256 for {name} — got {actual}. "
            "Add to EXPECTED_HASHES and re-commit.",
            file=sys.stderr,
        )

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path, "wb") as f:
        f.write(data)
    return data


def main() -> int:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Fetching openscad-wasm {OPENSCAD_WASM_VERSION}")
    for name in ASSET_FILES:
        data = fetch_asset(name)
        out_path = os.path.join(OUTPUT_DIR, name)
        with open(out_path, "wb") as f:
            f.write(data)
        print(f"  {name}: {len(data):,} bytes -> {out_path}")
    # Record the pinned version for diagnostics.
    with open(os.path.join(OUTPUT_DIR, "VERSION"), "w") as f:
        f.write(OPENSCAD_WASM_VERSION + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
