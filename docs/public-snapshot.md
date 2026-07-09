# Public Snapshot

`scripts/sync_public_snapshot.py` builds a sanitized copy of this repository
and (when explicitly requested) pushes it to the public mirror at
[github.com/stjohnb/3d-models](https://github.com/stjohnb/3d-models).

The mirror exists so the blog post can reference the source code without
exposing ongoing development work.

## Safety mechanisms

Two independent layers prevent secrets and strategy notes from leaking.

**1. Tracked-files-only enumeration.**
The tool enumerates files via `git ls-files -z` — untracked files can never
enter the snapshot. This is the structural guarantee that keeps
`.mcp-claws.json` (which holds live `HOME_ASSISTANT_TOKEN` and
`CLAWS_MCP_AUTH_TOKEN` values and is gitignored) out of the snapshot
regardless of the exclusion list.

**2. Secret-scan guard (defense in depth).**
Before any staging or push, the tool scans every included file's contents for
known secret patterns (`CLAWS_MCP_AUTH_TOKEN`, `HOME_ASSISTANT_TOKEN`,
JWT-shaped strings, AWS access key IDs, PEM private key headers, and the HA
hostname). If any match, the tool aborts with a non-zero exit code and lists
the offending files. The push path is never reached.

The scanner's own machinery is exempt from this scan, because it necessarily
contains the pattern strings themselves: the tool source
(`scripts/sync_public_snapshot.py`), its tests' planted fixtures
(`scripts/test_sync_public_snapshot.py`), and this document. These hold no
real secret values — the live values live only in the gitignored, untracked
`.mcp-claws.json` — so they stay in the snapshot but skip the secret scan
(see `SECRET_SCAN_SKIP`).

## Exclusion set

The following tracked paths are excluded from the snapshot. Matching is
path-segment-exact: `ideas` excludes `ideas/rejected.md` but not
`ideas-backlog.md`.

| Excluded path | Reason |
|---|---|
| `ideas/` | Strategy backlog, `rejected.md`, cross-project/LLM-benchmark and Claws notes — "ongoing development" the issue specifically calls out |
| `docs/blog-post.md` | Unpublished draft — the very document that will reference this snapshot |
| `docs/website-checklist-audit.md` | Internal audit, not public-facing |
| `.mcp-claws.json` | Belt-and-suspenders; already untracked/gitignored |

Everything else is included: all model project directories, `index.html`,
`embed.html`, `openscad-worker.js`, `scripts/`, `*.schema.json`,
`filament-colors.json`, `README.md`, `llms.txt`, `robots.txt`,
`favicon.svg`, `site.webmanifest`, `CLAUDE.md`, `.claude/agents/`,
`playbooks/`, `docs/OVERVIEW.md`, `docs/ci-pipeline.md`,
`docs/OPENSCAD_LIBRARIES.md`, and `.github/workflows/`.

`CLAUDE.md` and `.claude/agents/` are kept deliberately — the blog post
discusses the Claude Code / Claws workflow, so showing that configuration in
the snapshot is intentional. (`CLAUDE.md` references `ideas/rejected.md`,
which won't exist in the snapshot — a harmless dangling doc reference.)

## How to use

**Stage and review (no network access, safe to run any time):**

```bash
python3 scripts/sync_public_snapshot.py --staging-dir /tmp/snap
```

This prints a summary (files included/excluded, staging path) and exits 0.
Inspect `/tmp/snap` to confirm the snapshot looks right before pushing.

**Push to the public repo (requires maintainer push credentials for stjohnb/3d-models):**

```bash
python3 scripts/sync_public_snapshot.py --staging-dir /tmp/snap --push
```

> **Warning:** `--push` writes to a **public** repository. It requires
> maintainer push credentials for `stjohnb/3d-models` — the Claws GitHub App
> is not authorised to push there. Do not run `--push` in automated pipelines;
> this is a one-off maintainer action.

Additional options:

```
--target-repo REPO       GitHub repo slug (default: stjohnb/3d-models)
--commit-message MSG     Commit message (default: "Sync public snapshot")
```

## `README.public.md`

The repo root also has a hand-maintained `README.public.md`: plain project-
intro text with no snapshot/mirror/private-repo language, covering
architecture, conventions, local rendering, and test instructions, and
linking only to the safe doc paths already listed above. It is meant to
replace `README.md` in the public snapshot (the LLM-generated gallery
README isn't meaningful without the CI-populated `models.json`/thumbnails
that don't exist in the mirror). As of this writing,
`scripts/sync_public_snapshot.py` does **not yet** swap it in — the
snapshot still stages `README.md` as-is — so wiring `README.public.md` into
the sync step is outstanding follow-up work, not yet implemented.

## One-directional sync

The snapshot is one-directional. Changes are never pulled back from
`stjohnb/3d-models` into this repository. The public mirror is a read-only
reference copy; all development happens here.

## CI integration

This script is **not** wired into `build.yml` or `notify-failures.yml`. It is
a maintainer tool like `scripts/render_view.py` and
`scripts/fetch_terrain_heightmap.py`.
