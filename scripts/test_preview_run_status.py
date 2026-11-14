"""Tests for preview_run_status.py (issue clw_01M7BBKPKME3RPGB90GVZV0ZCH).

Hermetic: the Forgejo fetch function is injected, so no network is used.

Run with: python3 -m unittest test_preview_run_status
"""

import datetime
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import preview_run_status as prs  # noqa: E402

ISSUE = "clw_01M77XAC7M4BQGB95KDZ3V963X"
BRANCH = f"claws/preview-issue-{ISSUE}"
UNSET = "0001-01-01T00:00:00Z"


def ts(value):
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))


def run(index, created, started=UNSET, stopped=UNSET, status="waiting",
        workflow="build.yml", ref=BRANCH):
    return {
        "index_in_repo": index,
        "status": status,
        "created": created,
        "started": started,
        "stopped": stopped,
        "workflow_id": workflow,
        "prettyref": ref,
        "html_url": f"https://git.home.bstjohn.net/St-John-Software/3d-models/actions/runs/{index}",
    }


class FakeForgejo:
    """Routes fetch(path) to canned bodies; records every path."""

    def __init__(self, own_runs, repos=(), running=None, waiting=None, fail=None):
        self.own_runs = own_runs
        self.repos = list(repos)
        self.running = running or {}
        self.waiting = waiting or {}
        self.fail = fail
        self.paths = []

    def __call__(self, path):
        self.paths.append(path)
        if self.fail and self.fail in path:
            raise prs.HttpError("https://forge.test" + path, 403)
        if path.startswith("/api/v1/repos/search"):
            data = [
                {"name": n, "owner": {"login": "St-John-Software"}, "has_actions": True}
                for n in self.repos
            ]
            data.append({"name": "other", "owner": {"login": "someone-else"}})
            return {"ok": True, "data": data}
        repo = path.split("/")[5]
        if "status=running" in path:
            return {"workflow_runs": self.running.get(repo, [])}
        if "status=waiting" in path:
            return {"workflow_runs": self.waiting.get(repo, [])}
        return {"workflow_runs": self.own_runs}


def call(fake, now):
    out, err = io.StringIO(), io.StringIO()
    rc = prs.main([ISSUE], fetch=fake, now=ts(now), out=out, err=err)
    return rc, out.getvalue(), err.getvalue()


class FindRunTests(unittest.TestCase):
    def test_picks_newest_matching_build_run(self):
        runs = [
            run(340, "2026-11-12T14:00:00Z", workflow="pr-preview-cleanup.yml"),
            run(339, "2026-11-12T13:50:00Z", ref="claws/preview-issue-999"),
            run(338, "2026-11-12T13:40:00Z", status="success"),
            run(337, "2026-11-12T13:22:35Z", status="success"),
        ]
        self.assertEqual(prs.find_run(runs, BRANCH)["index_in_repo"], 338)

    def test_no_run(self):
        fake = FakeForgejo([run(1, "2026-11-12T13:00:00Z", ref="main")])
        rc, out, _ = call(fake, "2026-11-12T13:10:00Z")
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), f"no build.yml run for {BRANCH} yet")


class TimingTests(unittest.TestCase):
    def test_run_337_queued_and_ran(self):
        fake = FakeForgejo([run(
            337, "2026-11-12T13:22:35Z", "2026-11-12T13:26:27Z",
            "2026-11-12T13:41:21Z", status="success",
        )])
        rc, out, _ = call(fake, "2026-11-12T15:00:00Z")
        self.assertEqual(rc, 0)
        lines = out.splitlines()
        self.assertEqual(lines[0], "run 337 status=success queued=3m52s ran=14m54s")
        self.assertTrue(lines[1].endswith("/actions/runs/337"))
        self.assertNotIn("cause:", out)
        self.assertEqual(len(fake.paths), 1)

    def test_running_run_counts_to_now(self):
        fake = FakeForgejo([run(
            337, "2026-11-12T13:22:35Z", "2026-11-12T13:26:27Z", status="running",
        )])
        _, out, _ = call(fake, "2026-11-12T13:30:27Z")
        self.assertIn("queued=3m52s ran=4m00s", out)

    def test_unset_started_means_queued(self):
        self.assertIsNone(prs.parse_time(UNSET))
        self.assertEqual(prs.fmt_duration(3 * 3600 + 5 * 60 + 3), "3h05m03s")


class VerdictTests(unittest.TestCase):
    OWN = [run(400, "2026-11-12T13:00:00Z")]

    def test_capacity_held_elsewhere(self):
        fake = FakeForgejo(
            self.OWN,
            repos=["3d-models", "production-infra"],
            running={"production-infra": [{
                "index_in_repo": 4300, "workflow_id": "ci.yml",
                "started": "2026-11-12T12:53:00Z",
            }]},
            waiting={"3d-models": self.OWN, "production-infra": [{}, {}]},
        )
        rc, out, _ = call(fake, "2026-11-12T13:10:00Z")
        self.assertEqual(rc, 0)
        self.assertIn("run 400 status=waiting queued=10m00s ran=-", out)
        self.assertIn("org: 1 running, 3 waiting", out)
        self.assertIn("  production-infra#4300 ci.yml running 17m", out)
        self.assertIn(
            "cause: capacity held elsewhere (1 running, 3 waiting across the org; "
            "[container, linux] is shared)",
            out,
        )
        self.assertFalse(any("/other/" in p for p in fake.paths))

    def test_lists_at_most_ten_running(self):
        many = [
            {"index_in_repo": i, "workflow_id": "ci.yml", "started": "2026-11-12T13:00:00Z"}
            for i in range(15)
        ]
        fake = FakeForgejo(self.OWN, repos=["claws"], running={"claws": many})
        _, out, _ = call(fake, "2026-11-12T13:01:00Z")
        self.assertEqual(sum(1 for l in out.splitlines() if l.startswith("  claws#")), 10)
        self.assertIn("(15 running", out)

    def test_no_runner_taking_jobs(self):
        fake = FakeForgejo(self.OWN, repos=["3d-models"], waiting={"3d-models": self.OWN})
        _, out, _ = call(fake, "2026-11-12T13:05:01Z")
        self.assertIn(
            "cause: no runner is taking jobs; matching runners look offline or "
            "draining (fleet-infra docs/forgejo-actions.md)",
            out,
        )

    def test_normal_queueing(self):
        fake = FakeForgejo(self.OWN, repos=["3d-models"], waiting={"3d-models": self.OWN})
        _, out, _ = call(fake, "2026-11-12T13:04:00Z")
        self.assertIn("cause: normal queueing", out)


class ErrorTests(unittest.TestCase):
    def test_http_error_exits_1(self):
        fake = FakeForgejo([], fail="/actions/runs")
        rc, out, err = call(fake, "2026-11-12T13:00:00Z")
        self.assertEqual(rc, 1)
        self.assertEqual(out, "")
        self.assertRegex(err, r"^preview-status: https://forge\.test/api/v1/repos/.+ returned 403\n$")

    def test_bad_usage_exits_2(self):
        err = io.StringIO()
        self.assertEqual(prs.main([], fetch=lambda p: {}, err=err), 2)


if __name__ == "__main__":
    unittest.main()
