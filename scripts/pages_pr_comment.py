#!/usr/bin/env python3
"""Post or update the "📄 Spec pages" comment on a Forgejo pull request.

pages.yml runs this after "Publish PR spec pages" has synced pages/ to the
private pages host at ``3d-models/pr/pr-<N>/<sha8>/``. The body links the
build's index and each project spec page. It is a separate comment from
build.yml's "🔍 Model Preview" because build.yml may not run for a
pages-only PR. Reuses pr_preview_comment's Forgejo helpers; stdlib only.
See docs/ci-pipeline.md, "pages.yml (spec pages)".

Environment (all required unless noted):
  PR_NUMBER       pull request number (digits only)
  HEAD_SHA        PR head commit; its first 8 characters name the prefix
  API_URL         Forgejo API root, e.g. https://git.example/api/v1
  REPO            owner/name
  TOKEN           run token with write access to the PR's comments
  COMMENT_AUTHOR  optional; login that owns the comment
                  (default: forgejo-actions, the user the run token acts as)
"""

import os
import pathlib
import re
import sys
import time
import urllib.request

import pr_preview_comment

PAGES_ROOT_URL = "https://pages.home.bstjohn.net/3d-models/pr"
PAGES_DIR = pathlib.Path(__file__).resolve().parent.parent / "pages"
MARKER = "## 📄 Spec pages"


def pages_url(pr_number, sha8):
    return f"{PAGES_ROOT_URL}/pr-{pr_number}/{sha8}/"


def projects(pages_dir=PAGES_DIR):
    return sorted(p.parent.name for p in pathlib.Path(pages_dir).glob("*/index.html"))


def build_body(pr_number, sha8, names):
    url = pages_url(pr_number, sha8)
    lines = [
        MARKER, "",
        f"**[Spec pages for `{sha8}`]({url})** (private; LAN or tailnet, signed in)",
        "",
    ]
    lines += [f"- [{name}]({url}{name}/)" for name in names]
    return "\n".join(lines) + "\n"


def run(env, pages_dir=PAGES_DIR, urlopen=urllib.request.urlopen, sleep=time.sleep):
    pr_number = env["PR_NUMBER"]
    if not re.fullmatch(r"[0-9]+", pr_number):
        raise ValueError(f"PR_NUMBER {pr_number!r} is not a PR number")
    sha8 = env["HEAD_SHA"][:8]
    api_url = env["API_URL"].rstrip("/")
    repo = env["REPO"]
    token = env["TOKEN"]

    kw = {"urlopen": urlopen, "sleep": sleep}
    author = env.get("COMMENT_AUTHOR") or pr_preview_comment.DEFAULT_AUTHOR
    existing = pr_preview_comment.find_existing(
        api_url, repo, pr_number, token, author=author, marker=MARKER, **kw)
    body = build_body(pr_number, sha8, projects(pages_dir))
    outcome = pr_preview_comment.upsert_comment(
        api_url, repo, pr_number, token, body, existing, **kw)
    print(f"{outcome.capitalize()} spec pages comment on PR #{pr_number}")
    return outcome


def main():
    missing = [k for k in ("PR_NUMBER", "HEAD_SHA", "API_URL", "REPO", "TOKEN")
               if not os.environ.get(k)]
    if missing:
        print(f"pages_pr_comment: missing environment: {', '.join(missing)}", file=sys.stderr)
        return 2
    run(os.environ)
    return 0


if __name__ == "__main__":
    sys.exit(main())
