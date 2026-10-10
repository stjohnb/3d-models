#!/usr/bin/env python3
"""Post or update the "🔍 Model Preview" comment on a Forgejo pull request.

build.yml runs this on every ``pull_request`` build, after "Deploy PR
preview" has synced site/ to ``pr-preview/pr-<N>/<sha8>/``. The body is the
same markdown scripts/preview_summary.py renders for issue previews
(thumbnails of changed models, size and triangle counts, mesh validation,
interference), pointed at the PR preview prefix, plus a "Previous builds"
list carried over from the comment it replaces. Talks to the Forgejo
issues API with the run token; stdlib only. See docs/ci-pipeline.md,
step 20.

Environment (all required unless noted):
  PR_NUMBER       pull request number
  HEAD_SHA        PR head commit; its first 8 characters name the deploy prefix
  DIFF_BASE       commit to diff against (build.yml's diff_base step)
  API_URL         Forgejo API root, e.g. https://git.example/api/v1
  REPO            owner/name
  TOKEN           run token with write access to the PR's comments
  COMMENT_AUTHOR  optional; login that owns the preview comment
                  (default: forgejo-actions, the user the run token acts as)
"""

import json
import os
import re
import sys
import time
import urllib.request

import preview_summary

PREVIEW_ROOT = "https://www.bstjohn.net/3d-models/pr-preview"
MARKER = "## 🔍 Model Preview"
# Forgejo's Actions run token acts as this built-in user. Only its comments
# are updated: the token cannot PATCH anyone else's, so adopting a human's
# comment that happens to start with the marker would 403 every build.
DEFAULT_AUTHOR = "forgejo-actions"
MAX_PREV_BUILDS = 10
ATTEMPTS = 3
BACKOFF_SECONDS = 2
PAGE_LIMIT = 50
MAX_PAGES = 100


def preview_url(pr_number, sha8):
    return f"{PREVIEW_ROOT}/pr-{pr_number}/{sha8}/"


def previous_shas(body, pr_number, current):
    """Deployed SHAs linked from an earlier comment, newest first as listed."""
    pattern = re.compile(rf"pr-preview/pr-{re.escape(str(pr_number))}/([a-f0-9]{{8}})/")
    shas = []
    for sha in pattern.findall(body or ""):
        if sha != current and sha not in shas:
            shas.append(sha)
    return shas


def previous_builds_block(pr_number, shas):
    if not shas:
        return ""
    shown = shas[:MAX_PREV_BUILDS]
    hidden = len(shas) - len(shown)
    suffix = f" — {hidden} older omitted" if hidden else ""
    lines = [f"<details>\n<summary>Previous builds ({len(shown)}{suffix})</summary>\n\n"]
    lines += [f"- [`{sha}`]({preview_url(pr_number, sha)})\n" for sha in shown]
    lines.append("\n</details>\n\n")
    return "".join(lines)


def build_body(summary, pr_number, prev):
    """The preview markdown with the previous-builds block after the link."""
    markdown = summary["markdown"]
    link = f"**[View interactive 3D models]({summary['viewer_url']})**\n\n"
    block = previous_builds_block(pr_number, prev)
    if not block or link not in markdown:
        return markdown
    at = markdown.index(link) + len(link)
    return markdown[:at] + block + markdown[at:]


def should_skip(summary):
    return not summary["models"] and not summary["validation"]


def _request(method, url, token, payload=None, urlopen=urllib.request.urlopen,
             sleep=time.sleep):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Authorization": f"token {token}", "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    for attempt in range(1, ATTEMPTS + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=30) as resp:
                raw = resp.read()
            return json.loads(raw) if raw else None
        except Exception as err:  # noqa: BLE001 — retry any transport/API error
            if attempt == ATTEMPTS:
                raise
            delay = BACKOFF_SECONDS * attempt
            print(f"{method} {url} attempt {attempt} failed: {err}. Retrying in {delay}s...")
            sleep(delay)
    return None


def find_existing(api_url, repo, pr_number, token, author=DEFAULT_AUTHOR, **kw):
    """First comment on the PR by ``author`` whose body starts with the marker.

    Matching the start, not anywhere in the body, keeps a comment that merely
    quotes the heading from being overwritten. Paging stops on a short page or
    one with no unseen ids, in case the server ignores page/limit and returns
    the full list every time.
    """
    seen = set()
    for page in range(1, MAX_PAGES + 1):
        url = f"{api_url}/repos/{repo}/issues/{pr_number}/comments?page={page}&limit={PAGE_LIMIT}"
        comments = _request("GET", url, token, **kw) or []
        ids = {comment.get("id") for comment in comments}
        if not ids - seen:
            return None
        seen |= ids
        for comment in comments:
            login = (comment.get("user") or {}).get("login")
            if login == author and (comment.get("body") or "").startswith(MARKER):
                return comment
        if len(comments) < PAGE_LIMIT:
            return None
    return None


def upsert_comment(api_url, repo, pr_number, token, body, existing, **kw):
    if existing:
        url = f"{api_url}/repos/{repo}/issues/comments/{existing['id']}"
        _request("PATCH", url, token, {"body": body}, **kw)
        return "updated"
    url = f"{api_url}/repos/{repo}/issues/{pr_number}/comments"
    _request("POST", url, token, {"body": body}, **kw)
    return "created"


def run(env, site="site", urlopen=urllib.request.urlopen, sleep=time.sleep,
        changed=None):
    pr_number = env["PR_NUMBER"]
    sha8 = env["HEAD_SHA"][:8]
    api_url = env["API_URL"].rstrip("/")
    repo = env["REPO"]
    token = env["TOKEN"]
    if changed is None:
        changed = preview_summary.changed_from_git(env["DIFF_BASE"])

    summary = preview_summary.build_summary(
        f"pr-{pr_number}", sha8, env["HEAD_SHA"], changed, site,
        base_url=preview_url(pr_number, sha8),
    )
    if should_skip(summary):
        print("No changed model thumbnails or validation results found, skipping comment")
        return "skipped"

    kw = {"urlopen": urlopen, "sleep": sleep}
    author = env.get("COMMENT_AUTHOR") or DEFAULT_AUTHOR
    existing = find_existing(api_url, repo, pr_number, token, author=author, **kw)
    prev = previous_shas(existing["body"], pr_number, sha8) if existing else []
    body = build_body(summary, pr_number, prev)
    outcome = upsert_comment(api_url, repo, pr_number, token, body, existing, **kw)
    print(f"{outcome.capitalize()} preview comment on PR #{pr_number}")
    return outcome


def main():
    missing = [k for k in ("PR_NUMBER", "HEAD_SHA", "DIFF_BASE", "API_URL", "REPO", "TOKEN")
               if not os.environ.get(k)]
    if missing:
        print(f"pr_preview_comment: missing environment: {', '.join(missing)}", file=sys.stderr)
        return 2
    run(os.environ)
    return 0


if __name__ == "__main__":
    sys.exit(main())
