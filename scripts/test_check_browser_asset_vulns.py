"""Tests for check_browser_asset_vulns.py and browser-asset-scan.yml.

Run with: python3 -m unittest discover -s scripts -p 'test_check_browser_asset_vulns.py'
"""

import io
import json
import os
import re
import tempfile
import unittest
import urllib.error

import check_browser_asset_vulns as c

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW = os.path.join(ROOT, ".forgejo", "workflows", "browser-asset-scan.yml")
PURL = "pkg:npm/three@0.170.0"
TARGET = [("npm", "three", "0.170.0", PURL)]


class FakeResp:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return self.payload if isinstance(self.payload, bytes) else json.dumps(self.payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def opener_for(*responses):
    """Return an opener yielding responses in order; Exceptions are raised."""
    queue = list(responses)
    calls = []

    def opener(req, timeout=None):
        calls.append(json.loads(req.data.decode()))
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return FakeResp(item)

    opener.calls = calls
    return opener


def run_scan(opener, accepted=frozenset()):
    logs = []
    failures = c.scan(TARGET, accepted, opener=opener, log=logs.append)
    return failures, logs


class ScanTests(unittest.TestCase):
    def test_empty_response_no_failures(self):
        failures, logs = run_scan(opener_for({}))
        self.assertEqual(failures, [])
        self.assertIn("osv query npm/three@0.170.0: 0 advisories, 0 accepted", logs)

    def test_one_vuln_one_failure(self):
        failures, logs = run_scan(opener_for({"vulns": [{"id": "GHSA-x", "summary": "bad"}]}))
        self.assertEqual(
            failures, ["Browser asset vulnerability: GHSA-x affects three@0.170.0 bad"]
        )
        self.assertIn("::error::Browser asset vulnerability found", logs)
        self.assertIn(
            "browser asset vulnerability: advisory=GHSA-x package=three "
            "version=0.170.0 summary=bad",
            logs,
        )

    def test_annotations_constant_and_single_line(self):
        err = urllib.error.URLError("down")
        vuln = {"id": "GHSA-x", "summary": "bad\n::error::x"}
        failures, logs = run_scan(opener_for(err, err))
        f2, l2 = run_scan(opener_for({"vulns": [vuln]}))
        constants = {
            "::error::OSV query failed",
            "::error::Browser asset vulnerability found",
        }
        for line in logs + l2:
            if line.startswith("::error::"):
                self.assertIn(line, constants)
        for line in logs + l2 + failures + f2:
            self.assertNotIn("\n", line)

    def test_vex_alias_accepts(self):
        vuln = {"id": "GHSA-x", "aliases": ["CVE-1"], "summary": "bad"}
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "a.json"), "w") as f:
                json.dump({"statements": [{
                    "vulnerability": {"name": "CVE-1"},
                    "products": [{"@id": PURL}],
                    "status": "not_affected",
                    "justification": "vulnerable_code_not_in_execute_path",
                    "impact_statement": "unused",
                }]}, f)
            accepted, vex_failures = c.load_vex(d)
        self.assertEqual(vex_failures, [])
        failures, logs = run_scan(opener_for({"vulns": [vuln]}), accepted)
        self.assertEqual(failures, [])
        self.assertIn("osv query npm/three@0.170.0: 1 advisories, 1 accepted", logs)

    def test_vex_missing_impact_statement_fails(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "a.json"), "w") as f:
                json.dump({"statements": [{
                    "vulnerability": {"name": "CVE-1"},
                    "products": [{"@id": PURL}],
                    "status": "not_affected",
                    "justification": "component_not_present",
                }]}, f)
            accepted, vex_failures = c.load_vex(d)
        self.assertEqual(len(vex_failures), 1)
        self.assertEqual(accepted, set())

    def test_missing_vex_dir(self):
        self.assertEqual(c.load_vex("/nonexistent-vex-dir"), (set(), []))

    def test_urlerror_twice_is_failure(self):
        err = urllib.error.URLError("down")
        opener = opener_for(err, err)
        failures, logs = run_scan(opener)
        self.assertEqual(len(failures), 1)
        self.assertTrue(failures[0].startswith("OSV query failed for three@0.170.0"))
        self.assertEqual(len(opener.calls), 2)
        self.assertIn("::error::OSV query failed", logs)
        self.assertIn("osv query failed: package=three version=0.170.0", logs)

    def test_retry_then_success(self):
        failures, _ = run_scan(opener_for(urllib.error.URLError("x"), {}))
        self.assertEqual(failures, [])

    def test_non_json_is_failure(self):
        failures, _ = run_scan(opener_for(b"<html>", b"<html>"))
        self.assertEqual(len(failures), 1)

    def test_pagination_followed(self):
        opener = opener_for(
            {"vulns": [{"id": "A"}], "next_page_token": "t"},
            {"vulns": [{"id": "B"}]},
        )
        failures, _ = run_scan(opener)
        self.assertEqual(len(failures), 2)
        self.assertEqual(opener.calls[1]["page_token"], "t")


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        with open(WORKFLOW, encoding="utf-8") as f:
            self.text = f.read()

    def test_runs_on(self):
        self.assertIn("runs-on: [container, linux]", self.text)

    def test_uses_pinned(self):
        uses = re.findall(r"^\s*-?\s*uses:\s*(\S+)", self.text, re.M)
        self.assertTrue(uses)
        for u in uses:
            if u.startswith("./"):
                continue
            self.assertRegex(u, r"^https://\S+@[0-9a-f]{40}$")

    def test_schedule_trigger(self):
        self.assertRegex(self.text, r"(?m)^  schedule:")

    def test_enforce_after_scan(self):
        scan = self.text.index("id: scan")
        enforce = self.text.index("Enforce browser asset vulnerability scan")
        self.assertLess(scan, enforce)


if __name__ == "__main__":
    unittest.main()
