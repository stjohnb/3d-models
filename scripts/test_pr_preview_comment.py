"""Tests for pr_preview_comment.py (the Forgejo PR "🔍 Model Preview" comment).

Hermetic: the Forgejo API is a fake ``urlopen`` and the changed-file list is
passed in, so no network and no git.

Run with: python3 -m unittest test_pr_preview_comment
"""

import io
import json
import pathlib
import struct
import sys
import tempfile
import unittest
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import pr_preview_comment  # noqa: E402

PR = "42"
HEAD_SHA = "abcdef12" + "0" * 32
VIEWER = "https://www.bstjohn.net/3d-models/pr-preview/pr-42/abcdef12/"
API = "https://git.example/api/v1"
ENV = {
    "PR_NUMBER": PR, "HEAD_SHA": HEAD_SHA, "DIFF_BASE": "base",
    "API_URL": API + "/", "REPO": "St-John-Software/3d-models", "TOKEN": "t0k",
}
CHANGED = ["shelf-brackets/shelf-bracket.scad", "shelf-brackets/meta.json"]


def binary_stl(triangles):
    return b"\0" * 80 + struct.pack("<I", triangles) + b"\0" * (50 * triangles)


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeForgejo:
    """Records requests; serves comment pages; can fail the first N calls."""

    def __init__(self, comments=(), fail_first=0, ignore_paging=False):
        self.comments = list(comments)
        self.fail_first = fail_first
        self.ignore_paging = ignore_paging
        self.requests = []

    def __call__(self, req, timeout=None):
        body = json.loads(req.data) if req.data else None
        self.requests.append((req.get_method(), req.full_url, body, dict(req.header_items())))
        if self.fail_first:
            self.fail_first -= 1
            raise urllib.error.URLError("boom")
        if req.get_method() == "GET":
            if self.ignore_paging:
                return _Response(json.dumps(self.comments).encode())
            page = int(req.full_url.split("page=")[1].split("&")[0])
            chunk = self.comments[(page - 1) * 50: page * 50]
            return _Response(json.dumps(chunk).encode())
        return _Response(json.dumps({"id": 1}).encode())

    def writes(self):
        return [r for r in self.requests if r[0] != "GET"]


class _SiteHarness(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.site = pathlib.Path(self._tmp.name, "site")
        self.site.mkdir()
        (self.site / "shelf-bracket.png").write_bytes(b"png")
        (self.site / "shelf-bracket.stl").write_bytes(binary_stl(3))
        (self.site / "models.json").write_text(json.dumps({
            "Shelf Brackets": {"dir": "shelf-brackets", "files": []},
        }))
        (self.site / "validation.json").write_text(json.dumps([
            {"name": "shelf-bracket.stl", "passed": True, "triangles": 3,
             "volume": 10.5, "bbox_mm": {"x": 1, "y": 2, "z": 3},
             "bounds_mm": {"min_z": 0.0}, "sits_on_bed": True},
        ]))
        (self.site / "interference.json").write_text(json.dumps([
            {"part_a": "a.stl", "part_b": "b.stl", "passed": True,
             "overlap_volume_mm3": 0.0},
        ]))
        self.sleeps = []

    def tearDown(self):
        self._tmp.cleanup()

    def run_with(self, api, changed=CHANGED):
        return pr_preview_comment.run(
            ENV, site=self.site, urlopen=api, sleep=self.sleeps.append,
            changed=changed,
        )


class BodyTests(_SiteHarness):
    def test_create_body_has_thumbnails_and_tables(self):
        api = FakeForgejo()
        self.assertEqual(self.run_with(api), "created")
        (method, url, payload, headers), = api.writes()
        self.assertEqual(method, "POST")
        self.assertEqual(url, f"{API}/repos/St-John-Software/3d-models/issues/42/comments")
        self.assertEqual(headers["Authorization"], "token t0k")
        body = payload["body"]
        self.assertTrue(body.startswith("## 🔍 Model Preview\n"))
        self.assertIn(f"**[View interactive 3D models]({VIEWER})**", body)
        self.assertIn("### Shelf Brackets", body)
        self.assertIn(f"![shelf bracket]({VIEWER}shelf-bracket.png)", body)
        self.assertIn("**shelf bracket** — 234 bytes · 3 triangles", body)
        self.assertIn("### ✅ Mesh Validation", body)
        self.assertIn("### ✅ Mating Part Interference", body)
        self.assertNotIn("Previous builds", body)

    def test_update_carries_previous_builds(self):
        old = ("## 🔍 Model Preview\n\n**[View](https://www.bstjohn.net/3d-models/"
               "pr-preview/pr-42/11111111/)**\n- pr-preview/pr-42/22222222/\n"
               "- pr-preview/pr-42/11111111/ pr-preview/pr-42/abcdef12/ "
               "pr-preview/pr-7/33333333/")
        comments = [{"id": n, "body": "noise"} for n in range(60)]
        comments.append({"id": 99, "body": old, "user": {"login": "forgejo-actions"}})
        api = FakeForgejo(comments)
        self.assertEqual(self.run_with(api), "updated")
        gets = [r[1] for r in api.requests if r[0] == "GET"]
        self.assertEqual(len(gets), 2, "marker is on page 2; stop once found")
        self.assertIn("page=1&limit=50", gets[0])
        (method, url, payload, _), = api.writes()
        self.assertEqual(method, "PATCH")
        self.assertEqual(url, f"{API}/repos/St-John-Software/3d-models/issues/comments/99")
        body = payload["body"]
        self.assertIn("<summary>Previous builds (2)</summary>", body)
        self.assertIn(
            "- [`11111111`](https://www.bstjohn.net/3d-models/pr-preview/pr-42/11111111/)", body
        )
        self.assertIn("22222222", body)
        self.assertNotIn("33333333", body)
        self.assertNotIn("[`abcdef12`]", body)
        self.assertLess(body.index("View interactive"), body.index("Previous builds"))
        self.assertLess(body.index("Previous builds"), body.index("### Shelf Brackets"))

    def test_comment_quoting_the_marker_is_not_overwritten(self):
        quoted = {"id": 5, "body": "> CI said:\n> ## 🔍 Model Preview\nlooks off"}
        api = FakeForgejo([quoted])
        self.assertEqual(self.run_with(api), "created")
        (method, _, _, _), = api.writes()
        self.assertEqual(method, "POST")

    def test_marker_comment_by_another_author_is_not_adopted(self):
        """The run token cannot PATCH someone else's comment (403)."""
        human = {"id": 5, "body": "## 🔍 Model Preview\nmy notes",
                 "user": {"login": "bstjohn"}}
        ours = {"id": 6, "body": "## 🔍 Model Preview\nold",
                "user": {"login": "forgejo-actions"}}
        api = FakeForgejo([human, ours])
        self.assertEqual(self.run_with(api), "updated")
        (method, url, _, _), = api.writes()
        self.assertEqual(method, "PATCH")
        self.assertTrue(url.endswith("/issues/comments/6"))

        api = FakeForgejo([human])
        self.assertEqual(self.run_with(api), "created")

    def test_comment_author_override(self):
        bot = {"id": 7, "body": "## 🔍 Model Preview\nold", "user": {"login": "ci-bot"}}
        api = FakeForgejo([bot])
        result = pr_preview_comment.run(
            {**ENV, "COMMENT_AUTHOR": "ci-bot"}, site=self.site, urlopen=api,
            sleep=self.sleeps.append, changed=CHANGED,
        )
        self.assertEqual(result, "updated")

    def test_short_page_ends_the_search(self):
        api = FakeForgejo([{"id": n, "body": "noise"} for n in range(3)])
        self.assertEqual(self.run_with(api), "created")
        gets = [r for r in api.requests if r[0] == "GET"]
        self.assertEqual(len(gets), 1)

    def test_server_ignoring_page_param_does_not_loop(self):
        comments = [{"id": n, "body": "noise"} for n in range(80)]
        api = FakeForgejo(comments, ignore_paging=True)
        self.assertEqual(self.run_with(api), "created")
        gets = [r for r in api.requests if r[0] == "GET"]
        self.assertEqual(len(gets), 2, "second page repeats the first; stop")

    def test_previous_builds_capped(self):
        shas = [f"{n:08x}" for n in range(12)]
        block = pr_preview_comment.previous_builds_block(PR, shas)
        self.assertIn("Previous builds (10 — 2 older omitted)", block)
        self.assertEqual(block.count("- [`"), 10)


class RetryTests(_SiteHarness):
    def test_retries_then_succeeds(self):
        api = FakeForgejo(fail_first=2)
        self.assertEqual(self.run_with(api), "created")
        self.assertEqual(self.sleeps, [2, 4])

    def test_gives_up_after_three_attempts(self):
        api = FakeForgejo(fail_first=3)
        with self.assertRaises(urllib.error.URLError):
            self.run_with(api)
        self.assertEqual(len(api.requests), 3)
        self.assertEqual(api.writes(), [])


class SkipTests(_SiteHarness):
    def test_skips_without_models_or_validation(self):
        (self.site / "validation.json").unlink()
        api = FakeForgejo()
        self.assertEqual(self.run_with(api, changed=["docs/x.md"]), "skipped")
        self.assertEqual(api.requests, [])

    def test_validation_rows_alone_still_comment(self):
        api = FakeForgejo()
        self.assertEqual(self.run_with(api, changed=[]), "created")


class MainTests(unittest.TestCase):
    def test_missing_env_exits_2(self):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(pr_preview_comment.main(), 2)


if __name__ == "__main__":
    unittest.main()
