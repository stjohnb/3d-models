#!/usr/bin/env python3
"""Build a sanitized public snapshot of this repo for stjohnb/3d-models.

Usage:
    python3 scripts/sync_public_snapshot.py [--staging-dir /tmp/snap] [--push]

Without --push, builds the snapshot into --staging-dir and prints maintainer
instructions for reviewing and pushing. --push writes to the public repo and
requires maintainer push credentials for stjohnb/3d-models.
"""

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

DEFAULT_TARGET_REPO = "stjohnb/3d-models"

# Tracked paths excluded from the public snapshot ("ongoing development").
# Each entry matches a file whose POSIX path == entry OR starts with entry + "/".
SNAPSHOT_EXCLUDES = [
    "ideas",
    "docs/blog-post.md",
    "docs/agent-notes.md",
    "docs/website-checklist-audit.md",
    ".mcp-claws.json",
]

# Source path -> path it is staged/pushed as. The public mirror gets
# README.public.md's text under the name README.md: the tracked README.md is
# the CI-generated gallery (scripts/generate-gallery.py), whose table is built
# from site/models.json — a build artifact that does not exist in the mirror.
# The rename happens at staging time, so scan_for_secrets() still reads the
# real file from the repo root under its own name.
SNAPSHOT_RENAMES = {"README.public.md": "README.md"}

# Files that legitimately contain the secret *patterns* themselves — the
# scanner's own definition, its tests' planted fixtures, and the doc that
# describes the patterns. These hold no real secret values (the live values
# live only in the gitignored, untracked .mcp-claws.json), so scanning them
# produces nothing but false positives. They stay in the snapshot; they are
# just exempt from the self-referential secret scan.
SECRET_SCAN_SKIP = {
    "scripts/sync_public_snapshot.py",
    "scripts/test_sync_public_snapshot.py",
    "docs/public-snapshot.md",
}

# Defense-in-depth secret patterns. If any matches an included file, abort.
SECRET_PATTERNS = [
    re.compile(r"CLAWS_MCP_AUTH_TOKEN\s*=\s*\S"),
    re.compile(r"HOME_ASSISTANT_TOKEN\s*=\s*\S"),
    re.compile(r"home-assistant\.home\.bstjohn\.net"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),  # JWT
    re.compile(r"AKIA[0-9A-Z]{16}"),                                                  # AWS access key id
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
]

# Marker written into a staging directory this tool owns. Its presence is what
# authorises build_snapshot() to wipe a non-empty staging dir; without it we
# refuse, so a mistyped --staging-dir can never delete the maintainer's files.
STAGING_MARKER = ".snapshot-staging"
STAGING_MARKER_TEXT = (
    "Staging directory for scripts/sync_public_snapshot.py.\n"
    "Contents are rebuilt from scratch on every run; do not put files here.\n"
)


class StagingDirError(Exception):
    """Raised when --staging-dir is unsafe to clear or is missing a file."""


def repo_root():
    """Return the absolute path to the git repo root."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def enumerate_tracked_files(root):
    """Return a list of tracked file paths relative to root (POSIX-style).

    Uses NUL-delimited output to handle filenames with spaces correctly.
    """
    result = subprocess.run(
        ["git", "-C", root, "ls-files", "-z"],
        capture_output=True, check=True,
    )
    parts = result.stdout.split(b"\x00")
    return [p.decode() for p in parts if p]


def is_excluded(path, excludes=None):
    """Return True if path should be excluded from the snapshot.

    Matches exact path == entry or path starts with entry + "/" to avoid
    substring false positives (e.g. "ideas-backlog.md" must NOT match "ideas").
    """
    if excludes is None:
        excludes = SNAPSHOT_EXCLUDES
    for e in excludes:
        if path == e or path.startswith(e + "/"):
            return True
    return False


def superseded_targets(files, renames=None):
    """Return rename destinations whose source file is present in ``files``.

    A destination is only dropped from the snapshot when its replacement
    actually exists, so deleting or untracking README.public.md degrades to
    the old behaviour (README.md ships as-is) rather than shipping no readme.
    """
    if renames is None:
        renames = SNAPSHOT_RENAMES
    present = set(files)
    return {dst for src, dst in renames.items() if src in present}


def staged_path(rel_path, renames=None):
    """Return the name ``rel_path`` is staged and pushed under."""
    if renames is None:
        renames = SNAPSHOT_RENAMES
    return renames.get(rel_path, rel_path)


def staged_paths(files, renames=None):
    """Map a list of repo-relative source paths to their staged names."""
    return [staged_path(p, renames) for p in files]


def included_files(root, renames=None):
    """Return tracked files that are not excluded.

    Paths that a rename supersedes (README.md, replaced by README.public.md)
    are dropped; the rename *source* stays in the list so it is secret-scanned
    under its real name before being staged under the new name.
    """
    files = [p for p in enumerate_tracked_files(root) if not is_excluded(p)]
    dropped = superseded_targets(files, renames)
    return [p for p in files if p not in dropped]


def scan_for_secrets(root, files, skip=None):
    """Scan included files for known secret patterns.

    Returns a list of (path, pattern_string) tuples for every hit.
    Reads files as bytes and decodes with errors='ignore' so binary assets
    (e.g. heightmap.png) don't raise. Files in ``skip`` (default
    SECRET_SCAN_SKIP) are not scanned — see that constant for why.
    """
    if skip is None:
        skip = SECRET_SCAN_SKIP
    hits = []
    for rel_path in files:
        if rel_path in skip:
            continue
        abs_path = os.path.join(root, rel_path)
        try:
            with open(abs_path, "rb") as fh:
                content = fh.read().decode("utf-8", "ignore")
        except OSError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                hits.append((rel_path, pattern.pattern))
    return hits


def prepare_staging_dir(staging_dir):
    """Ensure staging_dir exists and is empty, deleting prior contents if safe.

    Raises StagingDirError if staging_dir is a symlink, an existing
    non-directory, or a non-empty directory that lacks the STAGING_MARKER
    file — in all of these cases nothing is deleted.
    """
    path = pathlib.Path(staging_dir)

    if path.is_symlink():
        raise StagingDirError(
            f"{staging_dir} is a symlink; refusing to use it as a staging directory"
        )

    if path.exists():
        if not path.is_dir():
            raise StagingDirError(f"{staging_dir} exists and is not a directory")
        entries = list(path.iterdir())
        if entries:
            if not (path / STAGING_MARKER).is_file():
                raise StagingDirError(
                    f"{staging_dir} is not empty and has no {STAGING_MARKER} marker; "
                    "refusing to delete its contents. Use an empty or dedicated staging directory."
                )
            shutil.rmtree(path)

    path.mkdir(parents=True, exist_ok=True)
    (path / STAGING_MARKER).write_text(STAGING_MARKER_TEXT)


def build_snapshot(root, staging_dir, files, renames=None):
    """Rebuild staging_dir from scratch and copy the given file list into it.

    The staging directory is authoritative: anything already there that is
    not in ``files`` is deleted, so a stale copy from an earlier run can
    never be pushed. Raises StagingDirError if staging_dir is non-empty and
    unmarked. Destination names are passed through SNAPSHOT_RENAMES (or the
    override ``renames``), so a source path like README.public.md is staged
    under its rename target.
    """
    prepare_staging_dir(staging_dir)
    for rel_path in files:
        src = os.path.join(root, rel_path)
        dst = os.path.join(staging_dir, staged_path(rel_path, renames))
        pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def mirror_files(staging_dir, dest_dir, files):
    """Copy exactly ``files`` (paths relative to staging_dir) into dest_dir.

    Explicit list, not os.walk: nothing that is not in ``files`` — including
    STAGING_MARKER — can reach the destination.
    """
    for rel_path in files:
        src = os.path.join(staging_dir, rel_path)
        if not os.path.isfile(src):
            raise StagingDirError(
                f"{rel_path} is missing from {staging_dir}; rebuild the snapshot"
            )
        dst = os.path.join(dest_dir, rel_path)
        pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def push_snapshot(staging_dir, target_repo, files, *, commit_message="Sync public snapshot"):
    """Clone target_repo, mirror staging_dir into it, commit, and push."""
    with tempfile.TemporaryDirectory() as tmp:
        clone_dir = os.path.join(tmp, "clone")
        subprocess.run(
            ["gh", "repo", "clone", target_repo, clone_dir],
            check=True,
        )

        # Remove all tracked content from clone (excluding .git) so deletions propagate.
        tracked = subprocess.run(
            ["git", "-C", clone_dir, "ls-files", "-z"],
            capture_output=True, check=True,
        ).stdout.split(b"\x00")
        for entry in tracked:
            if not entry:
                continue
            target_file = os.path.join(clone_dir, entry.decode())
            if os.path.isfile(target_file):
                os.remove(target_file)

        mirror_files(staging_dir, clone_dir, files)

        subprocess.run(["git", "-C", clone_dir, "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", clone_dir, "commit", "--allow-empty", "-m", commit_message],
            check=True,
        )
        subprocess.run(["git", "-C", clone_dir, "push"], check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a sanitized public snapshot for stjohnb/3d-models.",
    )
    parser.add_argument(
        "--staging-dir",
        default=None,
        help="Directory to write snapshot into (default: a temp dir)",
    )
    parser.add_argument(
        "--target-repo",
        default=DEFAULT_TARGET_REPO,
        help=f"GitHub repo slug to push to (default: {DEFAULT_TARGET_REPO})",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        default=False,
        help="Push snapshot to --target-repo (requires maintainer credentials)",
    )
    parser.add_argument(
        "--commit-message",
        default="Sync public snapshot",
        help="Git commit message for the push (default: 'Sync public snapshot')",
    )
    args = parser.parse_args(argv)

    root = repo_root()

    files = included_files(root)
    all_tracked = enumerate_tracked_files(root)
    excluded_count = len(all_tracked) - len(files)

    hits = scan_for_secrets(root, files)
    if hits:
        print("ERROR: secret pattern found in snapshot — aborting.", file=sys.stderr)
        for path, pattern in hits:
            print(f"  {path}: {pattern}", file=sys.stderr)
        return 1

    own_staging = args.staging_dir is None
    staging_dir = args.staging_dir or tempfile.mkdtemp(prefix="3d-models-snapshot-")

    try:
        build_snapshot(root, staging_dir, files)
    except StagingDirError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    staged = staged_paths(files)
    for src, dst in sorted(SNAPSHOT_RENAMES.items()):
        if src in set(files):
            print(f"Substituted: {src} -> {dst}")

    print(f"Snapshot built: {len(files)} files included, {excluded_count} excluded.")
    print(f"Staging directory: {staging_dir}")
    print("(Staging directory was rebuilt from scratch; stale files removed.)")

    if args.push:
        push_snapshot(staging_dir, args.target_repo, staged, commit_message=args.commit_message)
        print(f"Pushed to {args.target_repo}.")
    else:
        print()
        print("Review the snapshot, then push with:")
        print(f"  python3 scripts/sync_public_snapshot.py --staging-dir {staging_dir} --push")
        if own_staging:
            print("(The staging dir is a temp dir — it will be lost on reboot.)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
