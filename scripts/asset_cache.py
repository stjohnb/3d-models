"""Host-level download-cache root shared by threejs_assets and fetch_openscad_wasm.

Both fetchers used to cache under ``.cache/`` inside the checkout, but
``actions/checkout``'s default ``clean: true`` runs ``git clean -ffdx``,
which deletes gitignored paths — wiping the cache before every single
build ever reads it (issue #460). The render cache
(``$HOME/.cache/3d-models/render``, see ``build.yml``) already solves this
by living outside the workspace; this module gives the download caches the
same treatment.
"""

import os

DEFAULT_CACHE_ROOT = os.path.join("~", ".cache", "3d-models")
ENV_VAR = "ASSET_CACHE_DIR"


def cache_root() -> str:
    """Return the host-level download-cache root (env-overridable)."""
    override = os.environ.get(ENV_VAR)
    return os.path.expanduser(override or DEFAULT_CACHE_ROOT)


def cache_dir(*parts: str) -> str:
    """Return a subdirectory of the cache root, e.g. cache_dir("threejs")."""
    return os.path.join(cache_root(), *parts)


def write_atomic(path: str, data: bytes) -> None:
    """Write data to path via a same-directory temp file + os.replace.

    The self-hosted runners are shared and long-lived; two concurrent builds
    can populate the same cache entry, and a half-written file must never be
    readable (mirrors the render cache's `cp … .tmp.$$ && mv` in build.yml).
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)
