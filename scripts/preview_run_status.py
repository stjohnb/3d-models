#!/usr/bin/env python3
"""Report the state of an issue preview's build.yml run, and why it waits.

Called by `scripts/request-issue-preview.sh --status <issue-id>`. Forgejo's
run list shows a queued run and a running one alike, so a long cold render
(~15 min after it starts) is easy to misread as a stuck queue (issue
clw_01M7BBKPKME3RPGB90GVZV0ZCH). This prints the newest build.yml run on
claws/preview-issue-<id> with its queued and running time separately, and,
while it waits, what else across the org holds the shared
[container, linux] runners.

Read-only; stdlib only. Reads $CLAWS_FORGEJO_BASE_URL (default
https://git.home.bstjohn.net) and a token from $CLAWS_FORGEJO_READ_TOKEN,
then $FORGEJO_TOKEN, else anonymous. The token is sent only in the
Authorization header and never printed.
"""

import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

OWNER = "St-John-Software"
REPO = "3d-models"
WORKFLOW = "build.yml"
PAGE_LIMIT = 50
MAX_RUNNING_LISTED = 10
STALL_SECONDS = 5 * 60
DEFAULT_BASE_URL = "https://git.home.bstjohn.net"


class HttpError(Exception):
    def __init__(self, url, code):
        super().__init__(f"{url} returned {code}")
        self.url = url
        self.code = code


def make_fetch(base_url, token):
    """Return fetch(path) -> parsed JSON for GETs against the Forgejo API."""

    def fetch(path):
        url = base_url.rstrip("/") + path
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        if token:
            req.add_header("Authorization", f"token {token}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            raise HttpError(url, exc.code) from None
        except urllib.error.URLError as exc:
            raise HttpError(url, exc.reason) from None

    return fetch


def parse_time(value):
    """Parse a Forgejo timestamp; None for unset (`0001-…`) or missing."""
    if not value or value.startswith("0001-"):
        return None
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))


def fmt_duration(seconds):
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h{m:02d}m{s:02d}s"
    return f"{m}m{s:02d}s"


def runs_path(repo, status=None):
    query = {"page": 1, "limit": PAGE_LIMIT}
    if status:
        query["status"] = status
    return (
        f"/api/v1/repos/{OWNER}/{urllib.parse.quote(repo)}/actions/runs?"
        + urllib.parse.urlencode(query)
    )


def find_run(runs, branch):
    """Newest build.yml run on branch, or None."""
    matching = [
        r for r in runs
        if r.get("workflow_id") == WORKFLOW and r.get("prettyref") == branch
    ]
    if not matching:
        return None
    return max(matching, key=lambda r: (r.get("created") or "", r.get("index_in_repo") or 0))


def run_timings(run, now):
    """(queued_seconds, ran_seconds or None) for a run at time now."""
    created = parse_time(run.get("created")) or now
    started = parse_time(run.get("started"))
    stopped = parse_time(run.get("stopped"))
    if started is None:
        return (now - created).total_seconds(), None
    return (started - created).total_seconds(), ((stopped or now) - started).total_seconds()


def org_repos(fetch):
    """Every org repo with Actions enabled, paging the repo search API.

    /orgs/{org}/repos needs the read:organization scope, which the agents'
    read token lacks, so search what the token can see and keep the org's.
    """
    names = []
    page = 1
    while True:
        body = fetch(
            "/api/v1/repos/search?"
            + urllib.parse.urlencode({"page": page, "limit": PAGE_LIMIT})
        )
        data = body.get("data", []) if isinstance(body, dict) else body
        for repo in data:
            if (repo.get("owner") or {}).get("login") != OWNER:
                continue
            if repo.get("archived") or repo.get("has_actions") is False:
                continue
            names.append(repo["name"])
        if len(data) < PAGE_LIMIT:
            return names
        page += 1


def explain_wait(fetch, queued_seconds, now, out):
    running, waiting_count = [], 0
    for repo in org_repos(fetch):
        for run in fetch(runs_path(repo, "running")).get("workflow_runs") or []:
            running.append((repo, run))
        waiting_count += len(fetch(runs_path(repo, "waiting")).get("workflow_runs") or [])

    print(f"org: {len(running)} running, {waiting_count} waiting", file=out)
    running.sort(key=lambda item: item[1].get("started") or "")
    for repo, run in running[:MAX_RUNNING_LISTED]:
        started = parse_time(run.get("started"))
        minutes = int((now - started).total_seconds() // 60) if started else 0
        print(
            f"  {repo}#{run.get('index_in_repo')} {run.get('workflow_id')} running {minutes}m",
            file=out,
        )

    if running:
        verdict = (
            f"capacity held elsewhere ({len(running)} running, {waiting_count} waiting "
            "across the org; [container, linux] is shared)"
        )
    elif queued_seconds > STALL_SECONDS:
        verdict = (
            "no runner is taking jobs; matching runners look offline or draining "
            "(fleet-infra docs/forgejo-actions.md)"
        )
    else:
        verdict = "normal queueing"
    print(f"cause: {verdict}", file=out)


def report(issue, fetch, now, out):
    branch = f"claws/preview-issue-{issue}"
    runs = fetch(runs_path(REPO)).get("workflow_runs") or []
    run = find_run(runs, branch)
    if run is None:
        print(f"no {WORKFLOW} run for {branch} yet", file=out)
        return 0

    queued, ran = run_timings(run, now)
    ran_text = fmt_duration(ran) if ran is not None else "-"
    print(
        f"run {run.get('index_in_repo')} status={run.get('status')} "
        f"queued={fmt_duration(queued)} ran={ran_text}",
        file=out,
    )
    print(run.get("html_url") or "", file=out)

    if run.get("status") == "waiting":
        explain_wait(fetch, queued, now, out)
    return 0


def main(argv=None, fetch=None, now=None, out=None, err=None):
    argv = sys.argv[1:] if argv is None else argv
    out = out or sys.stdout
    err = err or sys.stderr
    if len(argv) != 1:
        print("usage: preview_run_status.py <issue-id>", file=err)
        return 2
    if fetch is None:
        base = os.environ.get("CLAWS_FORGEJO_BASE_URL") or DEFAULT_BASE_URL
        token = os.environ.get("CLAWS_FORGEJO_READ_TOKEN") or os.environ.get("FORGEJO_TOKEN")
        fetch = make_fetch(base, token)
    now = now or datetime.datetime.now(datetime.timezone.utc)
    try:
        return report(argv[0], fetch, now, out)
    except HttpError as exc:
        print(f"preview-status: {exc.url} returned {exc.code}", file=err)
        return 1


if __name__ == "__main__":
    sys.exit(main())
