"""Per-project last-commit dates for the landing page's recency ordering.

The landing gallery in ``index.html`` sorts projects by "interesting and
recent first" (issue #345). Interest is derived from data already present in
``models.json``; recency needs a signal that doesn't exist in any committed
file, so CI asks git for the committer date of the newest commit touching each
project directory and publishes it as ``updated`` on the ``models.json`` entry.

This requires a full-history checkout (``fetch-depth: 0``). With a shallow
clone ``git log`` simply reports nothing for most directories, every
``updated`` is absent, and the grid falls back to interest-only ordering —
a silent degradation rather than a build failure, which is deliberate.
"""

import subprocess


def project_updated(dirs, repo_root="."):
    """Return ``{dir: ISO-8601 committer date}`` for each directory's last commit.

    Directories with no commit touching them — and every directory, when git
    is unavailable or ``repo_root`` isn't a repository — are omitted from the
    result. A missing date must degrade gracefully, never fail the build.
    """
    updated = {}
    try:
        for d in dirs:
            proc = subprocess.run(
                ["git", "log", "-1", "--format=%cI", "--", d],
                cwd=repo_root,
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                continue
            date = proc.stdout.strip()
            if date:
                updated[d] = date
    except (OSError, subprocess.SubprocessError):
        return {}
    return updated
