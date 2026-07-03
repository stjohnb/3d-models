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
    "docs/website-checklist-audit.md",
    ".mcp-claws.json",
]

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


def included_files(root):
    """Return tracked files that are not excluded."""
    return [p for p in enumerate_tracked_files(root) if not is_excluded(p)]


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


def build_snapshot(root, staging_dir, files):
    """Copy the given file list from root into staging_dir.

    Creates parent directories as needed. staging_dir is created if missing.
    """
    pathlib.Path(staging_dir).mkdir(parents=True, exist_ok=True)
    for rel_path in files:
        src = os.path.join(root, rel_path)
        dst = os.path.join(staging_dir, rel_path)
        pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def push_snapshot(staging_dir, target_repo, *, commit_message="Sync public snapshot"):
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

        # Mirror staging_dir into clone.
        for dirpath, _dirs, filenames in os.walk(staging_dir):
            for fname in filenames:
                src = os.path.join(dirpath, fname)
                rel = os.path.relpath(src, staging_dir)
                dst = os.path.join(clone_dir, rel)
                pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

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

    build_snapshot(root, staging_dir, files)

    print(f"Snapshot built: {len(files)} files included, {excluded_count} excluded.")
    print(f"Staging directory: {staging_dir}")

    if args.push:
        push_snapshot(staging_dir, args.target_repo, commit_message=args.commit_message)
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
