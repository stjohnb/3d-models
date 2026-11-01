"""Single source of truth for the pinned Three.js runtime assets.

Both the deployed viewers and the standalone viewers run the same three
files, verified against the SHA-256 hashes below:

* ``scripts/fetch_threejs.py`` stages them under ``site/vendor/three/<version>/``
  so ``index.html`` / ``embed.html`` load them same-origin (issue #403).
* ``scripts/generate-standalone.py`` inlines the same verified bytes as
  base64 data URIs.

Bumping the version means: change ``THREEJS_VERSION``, run
``python3 scripts/fetch_threejs.py --print-hashes`` and paste the printed
digests into ``THREEJS_ASSETS``, update the import maps in ``index.html``
and ``embed.html``, and update ``docs/OVERVIEW.md``.
"""

import hashlib
import os
import urllib.request

import asset_cache

THREEJS_VERSION = "0.170.0"

# url: where the bytes come from; sha256: the only bytes we accept;
# path: destination relative to the vendor dir (and the import-map layout).
THREEJS_ASSETS = {
    "three": {
        "url": f"https://cdn.jsdelivr.net/npm/three@{THREEJS_VERSION}/build/three.module.min.js",
        "sha256": "08fd7545d13d2c7fb65ab691530a802dafefd638596501854f267d0fb13c39e7",
        "path": "three.module.min.js",
    },
    "STLLoader": {
        "url": f"https://cdn.jsdelivr.net/npm/three@{THREEJS_VERSION}/examples/jsm/loaders/STLLoader.js",
        "sha256": "a0a83c88b269c94e25b690fae770d350c4728c81853195186976be7af0f8a3b3",
        "path": "addons/loaders/STLLoader.js",
    },
    "OrbitControls": {
        "url": f"https://cdn.jsdelivr.net/npm/three@{THREEJS_VERSION}/examples/jsm/controls/OrbitControls.js",
        "sha256": "80efaadea4f8a636a65fb0bd08bfef62f3d93a0bb94e2e7500f23176c5c07f4e",
        "path": "addons/controls/OrbitControls.js",
    },
}

VENDOR_DIR = os.path.join("site", "vendor", "three", THREEJS_VERSION)
IMPORTMAP_PREFIX = f"./vendor/three/{THREEJS_VERSION}/"


def cache_dir() -> str:
    """Host-level cache dir for the upstream Three.js downloads."""
    return asset_cache.cache_dir("threejs")


def _cache_path(url: str) -> str:
    """Return a deterministic local cache path for a URL."""
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    basename = url.rsplit("/", 1)[-1]
    return os.path.join(cache_dir(), f"{url_hash}_{basename}")


def fetch_url(url: str, expected_sha256: str) -> bytes:
    """Download a URL with a single retry, mandatory SHA-256 verification, and a verified local cache fallback."""
    expected_sha256 = asset_cache.require_sha256(expected_sha256, url)
    cache_file = _cache_path(url)

    if os.path.isfile(cache_file):
        try:
            with open(cache_file, "rb") as f:
                data = f.read()
        except OSError:
            data = None
        if data is not None and hashlib.sha256(data).hexdigest() == expected_sha256:
            print(f"  Cache hit: {cache_file}")
            return data
        # Stale or unreadable — fall through and re-download.

    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
        except Exception as e:
            if attempt == 0:
                print(f"  Retry {url}: {e}")
                continue
            # Both attempts failed — try cache fallback
            if os.path.isfile(cache_file):
                print(f"  CDN unreachable, using cached copy: {cache_file}")
                with open(cache_file, "rb") as f:
                    data = f.read()
                # Still verify the cached data
                actual = hashlib.sha256(data).hexdigest()
                if actual != expected_sha256:
                    raise ValueError(
                        f"Cached file SHA-256 mismatch for {url}\n"
                        f"  expected: {expected_sha256}\n"
                        f"  got:      {actual}"
                    )
                return data
            raise
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected_sha256:
            raise ValueError(
                f"SHA-256 mismatch for {url}\n"
                f"  expected: {expected_sha256}\n"
                f"  got:      {actual}"
            )
        # Cache the verified data for future runs
        asset_cache.write_atomic(cache_file, data)
        return data
    raise RuntimeError(f"Failed to fetch {url}")
