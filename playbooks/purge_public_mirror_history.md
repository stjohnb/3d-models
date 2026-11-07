# Playbook: Purge Public Mirror History (GPS Leak, #536/#538)

`power-workshop/images/photos/IMG_2823.jpg` through `IMG_2827.jpg` were
committed to this repo carrying embedded GPS coordinates for the maintainer's
home. #537 stripped the metadata from the working tree and added
`scripts/image_metadata.py` / `scripts/test_image_metadata.py` so no tracked
image can carry EXIF/XMP/IPTC/comment metadata again. That fixed the path
going forward; it did not remove the coordinates already published in the
commit history of the public mirror, `stjohnb/3d-models`. This playbook is
the maintainer-only completion of that fix. It requires push credentials for
`stjohnb/3d-models` that the Claws GitHub App does not have — none of the
steps below can be automated by Claws.

Read [docs/public-snapshot.md](../docs/public-snapshot.md) first for how
`scripts/sync_public_snapshot.py` works and why `--push` now always replaces
the mirror's entire history.

## Step 1+2: republish the mirror as a single orphan commit

```bash
nix develop
python3 scripts/sync_public_snapshot.py --staging-dir /tmp/snap --push
```

Pillow is required for the image-metadata guard, hence `nix develop` rather
than a bare `python3`. This one command does both of the originally separate
follow-up steps: it rebuilds the snapshot from the now-stripped images, and
`--push` replaces the mirror's entire commit history with a single orphan
commit and force-pushes it — so `IMG_2823.jpg`–`IMG_2827.jpg` with GPS data
are no longer reachable from any ref on the mirror afterward.

If the command aborts naming extra branches or tags on the mirror, delete
those refs on `stjohnb/3d-models` first (they pin the old blobs independently
of the default branch), then re-run.

## Step 3: ask GitHub Support to purge cached views and unreferenced objects

A force-push moves the branch ref, but it does not guarantee the old commits'
objects are gone: GitHub can keep them reachable by SHA, and cached blob
pages, the commit list, and raw content URLs can persist independently of any
ref until a purge runs.

Open a support request (https://support.github.com) naming `stjohnb/3d-models`
and ask for:

- unreferenced objects to be garbage-collected, and
- cached views (commit pages, blob pages, raw URLs) for the removed commits
  to be purged, and
- any `refs/pull/*/head` refs from PRs ever opened against the mirror to be
  included in the purge — GitHub keeps these independently of branches and
  tags, `check_mirror_refs()` cannot see or delete them (they aren't fetched
  by a normal clone), and only GitHub Support can reach them. A clean
  `check_mirror_refs()` result before step 1+2 does not mean no ref still
  pins the leaked blobs.

Once GitHub confirms, spot-check that the old commit SHAs 404 — e.g. a
`blob/<old-sha>/power-workshop/images/photos/IMG_2823.jpg` URL from before the
purge should no longer resolve.

**#538 stays open until this step is confirmed.** Steps 1+2 alone move the
default branch forward; they do not prove the leak is gone from GitHub's
storage.

## Step 4: decide whether to rewrite this private repo's history

This repository's own history still contains the original, metadata-bearing
images (that is normal — it's private, and #536/#537 already fixed what's
tracked going forward). The recommendation is **do not rewrite it**:

- It is private — nobody outside the maintainer and Claws can read it.
- The images are already stripped in the working tree; nothing currently
  checked out carries the metadata.
- A history rewrite (e.g. `git filter-repo`) would invalidate every open PR
  ref, every worktree, and every Claws branch built against the current
  history — a large, ongoing cost to close a risk that is already
  effectively closed by the repo being private.

This is a judgment call the maintainer can revisit; it is not something
automation should decide or perform.

## Caveat: pre-purge copies

Any fork or clone of `stjohnb/3d-models` taken before this purge keeps the
old objects regardless of what happens to the mirror or to GitHub's storage.
The purge removes the leak from the canonical mirror and GitHub's own
infrastructure; it cannot reach copies that already left it.
