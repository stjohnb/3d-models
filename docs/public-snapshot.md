# Public Snapshot

**Depth: Deep dive.** Read this only when working on the public-mirror sync
(`scripts/sync_public_snapshot.py`) or deciding what is/isn't safe to expose
in the public repo. For everything else read [OVERVIEW.md](OVERVIEW.md)
instead.

Product requirements: [product/publication-safety.md](product/publication-safety.md)

`scripts/sync_public_snapshot.py` builds a sanitized copy of this repository
and (when explicitly requested) pushes it to the public mirror at
[github.com/stjohnb/3d-models](https://github.com/stjohnb/3d-models).

The mirror exists so the blog post can reference the source code without
exposing ongoing development work.

## Safety mechanisms

Four independent layers keep secrets, strategy notes, internal procedures, and
embedded image metadata out of the public mirror.

**1. Explicit public manifest over tracked files.**
The tool enumerates files via `git ls-files -z` — untracked files can never
enter the snapshot. This is the structural guarantee that keeps
`.mcp-claws.json` (which holds live `HOME_ASSISTANT_TOKEN` and
`CLAWS_MCP_AUTH_TOKEN` values and is gitignored) out of the snapshot
regardless of later filtering.

From that tracked set, the tool includes only paths listed in
`SNAPSHOT_INCLUDES`. New docs, playbooks, operator notes, or top-level
directories are private by default until they are intentionally added to that
public manifest. `SNAPSHOT_EXCLUDES` remains as a defense-in-depth blocklist
for paths that must stay private even if a future broad include entry would
otherwise catch them.

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

**3. Image-metadata guard (defense in depth).**
Before any staging or push, the tool also runs every tracked `.jpg`/`.jpeg`/
`.png`/`.webp` file through `scripts/image_metadata.find_metadata()` — the
same check `scripts/test_image_metadata.py` runs against every tracked image.
If any file still carries EXIF, XMP, IPTC/Photoshop, or comment metadata
(including camera/device details), the tool aborts with a non-zero exit code
and lists the offending files; the push path is never reached. If Pillow
cannot be imported, the tool also aborts rather than silently skipping the
check — run it inside `nix develop`.

**4. Staging directory is authoritative.**
Every run rebuilds `--staging-dir` from scratch — the directory is deleted and
recreated before any file is copied in — so a file staged by an earlier run
and since excluded, deleted, or `git rm`'d cannot survive into a later
`--push`. The push step mirrors the explicit included-files list rather than
walking the staging directory, so nothing that was not scanned this run can
reach the mirror.

To make that deletion safe, the tool writes a `.snapshot-staging` marker file
into every staging directory it creates. If `--staging-dir` points at a
directory that is non-empty and carries no marker, the tool aborts with a
non-zero exit code and deletes nothing — use an empty or dedicated path.

## Public Manifest

The snapshot is fail-closed: only tracked paths matched by
`SNAPSHOT_INCLUDES` are eligible for publication. Matching is
path-segment-exact: `scripts` includes `scripts/test_render_view.py` but not
`scripts-private/tool.py`.

| Included path | Reason |
|---|---|
| Model project directories | Public OpenSCAD source, metadata, parameter manifests, project notes, and committed reference images/assets |
| `scans/` | Committed scan reference meshes and their public README |
| `index.html`, `embed.html`, `openscad-worker.js`, viewer assets, schemas, and shared config files | Runtime source needed to inspect and reuse the gallery |
| `scripts/` | Build, validation, rendering, and snapshot tooling plus tests |
| `.github/`, `flake.nix`, `flake.lock`, `.gitignore`, `.openscad-version` | Public CI/toolchain definition for reproducing the build |
| `AGENTS.md`, `.agents/`, `claws.json` | Automation configuration intentionally shown by the mirror |
| `README.public.md` staged as `README.md` | Public-facing repository introduction, replacing the generated private README gallery |
| Selected docs under `docs/` | Public architecture and subsystem documentation |
| Selected playbooks under `playbooks/` | Public operator guides for model design, scanning, and preview renders |

`AGENTS.md` and `.agents/` (renamed from `.claude/agents/` in #494 to keep the
path provider-neutral) are kept deliberately — the blog post discusses the Claude
Code / Claws workflow, so showing that configuration in the snapshot is
intentional. `AGENTS.md` is the canonical root guide that Claws inlines into
every run and points readers at `docs/claws-automation.md`, which is included
in the snapshot and resolves normally.

## How to use

**Stage and review (no network access, safe to run any time):**

```bash
python3 scripts/sync_public_snapshot.py --staging-dir /tmp/snap
```

This prints a summary (files included/excluded, staging path) and exits 0.
Inspect `/tmp/snap` to confirm the snapshot looks right before pushing.
Re-running against the same `--staging-dir` is safe and expected: the
directory is wiped and rebuilt each time.

**Push to the public repo (requires maintainer push credentials for stjohnb/3d-models):**

```bash
python3 scripts/sync_public_snapshot.py --staging-dir /tmp/snap --push
```

> **Warning:** `--push` writes to a **public** repository, and it **replaces
> the mirror's entire commit history with a single orphan commit and
> force-pushes it** — every run, unconditionally. There is no flag to
> preserve history. It requires maintainer push credentials for
> `stjohnb/3d-models` — the Claws GitHub App is not authorised to push there.
> Do not run `--push` in automated pipelines; this is a one-off maintainer
> action.

This is deliberate, not a shortcut. Nothing consumes the mirror's history:
every public link — the model cards, the embed overlay, the standalone-viewer
footer — points at `blob/main`/`tree/main` (`PUBLIC_REPO_URL` /
`public_source_url()`, see "Public source links" in `AGENTS.md`), never a
fixed commit SHA, and the sync is one-directional (see below). A browsable
history on the mirror has no reader, so every push republishes the mirror as
one fresh snapshot commit.

Before force-pushing, the tool clones the mirror and checks for any branch or
tag beyond its default branch (fetching tags first). If it finds any, it
aborts and names them because the mirror is intentionally single-ref and
single-commit. Delete the extra refs on the mirror, then re-run. The branch
that gets replaced is always the clone's own current default branch
(`git symbolic-ref --short HEAD`), not a hard-coded `main`.

Additional options:

```
--target-repo REPO       GitHub repo slug (default: stjohnb/3d-models)
--commit-message MSG     Commit message for the orphan commit (default: "Public snapshot")
```

## `README.public.md`

The repo root has a hand-maintained `README.public.md`: plain project-intro
text with no snapshot/mirror/private-repo language, covering architecture,
conventions, local rendering, and test instructions, and linking only to the
safe doc paths already listed above.

The snapshot **substitutes** it for `README.md`. `SNAPSHOT_RENAMES` in
`scripts/sync_public_snapshot.py` maps `README.public.md` → `README.md`:
`included_files()` drops the tracked `README.md` (the LLM-generated gallery,
whose table is derived from the CI-built `site/models.json` that does not
exist in the mirror), `build_snapshot()` stages `README.public.md`'s contents
under the name `README.md`, and `push_snapshot()` is handed the staged names.
The mirror therefore contains exactly one readme — the public text — and no
`README.public.md`.

The secret scan still runs against the real source file under its own name
(`scan_for_secrets()` reads from the repo root before any staging), so the
substitution does not create a scan blind spot.

If `README.public.md` is ever deleted or untracked, the substitution simply
does not apply and `README.md` ships as-is — the tool does not fail and the
mirror is never left without a readme.

## One-directional sync

The snapshot is one-directional. Changes are never pulled back from
`stjohnb/3d-models` into this repository. The public mirror is a read-only
reference copy; all development happens here. It is also single-commit by
design: every `--push` discards whatever history the mirror had and replaces
it with one fresh orphan commit, so the mirror can never accumulate a
browsable history of its own — see the `--push` warning above.

## CI integration

This script is **not** wired into `build.yml`. It is
a maintainer tool like `scripts/render_view.py` and
`scripts/fetch_terrain_heightmap.py`.
