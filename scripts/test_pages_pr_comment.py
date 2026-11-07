"""Tests for pages_pr_comment.py (the Forgejo PR "📄 Spec pages" comment).

Hermetic: the Forgejo API is a fake ``urlopen`` and the pages tree is a
temp dir, so no network.

Run with: python3 -m unittest test_pages_pr_comment
"""

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import pages_pr_comment  # noqa: E402
from test_pr_preview_comment import FakeForgejo  # noqa: E402

HEAD_SHA = "abcdef12" + "0" * 32
API = "https://git.example/api/v1"
ENV = {
    "PR_NUMBER": "42", "HEAD_SHA": HEAD_SHA, "API_URL": API + "/",
    "REPO": "St-John-Software/3d-models", "TOKEN": "t0k",
}
URL = "https://pages.home.bstjohn.net/3d-models/pr/pr-42/abcdef12/"


def comment(cid, body, login="forgejo-actions"):
    return {"id": cid, "body": body, "user": {"login": login}}


class PagesCommentTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.pages = pathlib.Path(self._tmp.name)
        (self.pages / "index.html").write_text("index")
        for name in ("climbing-frame", "garden-room"):
            (self.pages / name).mkdir()
            (self.pages / name / "index.html").write_text(name)
        (self.pages / "no-page").mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def run_with(self, fake, env=ENV):
        return pages_pr_comment.run(env, pages_dir=self.pages, urlopen=fake,
                                    sleep=lambda _s: None)

    def test_body_links_index_and_each_project(self):
        body = pages_pr_comment.build_body(
            "42", "abcdef12", pages_pr_comment.projects(self.pages))
        self.assertTrue(body.startswith(pages_pr_comment.MARKER))
        self.assertIn(f"]({URL})", body)
        self.assertIn(f"- [climbing-frame]({URL}climbing-frame/)", body)
        self.assertIn(f"- [garden-room]({URL}garden-room/)", body)
        self.assertNotIn("no-page", body)

    def test_creates_comment_when_absent(self):
        fake = FakeForgejo()
        self.assertEqual(self.run_with(fake), "created")
        (method, url, payload, _headers), = fake.writes()
        self.assertEqual(method, "POST")
        self.assertEqual(url, f"{API}/repos/St-John-Software/3d-models/issues/42/comments")
        self.assertIn(URL, payload["body"])

    def test_updates_own_spec_pages_comment(self):
        fake = FakeForgejo([comment(7, pages_pr_comment.MARKER + "\n\nold")])
        self.assertEqual(self.run_with(fake), "updated")
        (method, url, _payload, _headers), = fake.writes()
        self.assertEqual(method, "PATCH")
        self.assertTrue(url.endswith("/issues/comments/7"))

    def test_never_adopts_model_preview_or_foreign_comments(self):
        fake = FakeForgejo([
            comment(5, "## 🔍 Model Preview\n\nmodels"),
            comment(6, pages_pr_comment.MARKER + "\n\nby a human", login="someone"),
        ])
        self.assertEqual(self.run_with(fake), "created")
        (method, _url, _payload, _headers), = fake.writes()
        self.assertEqual(method, "POST")

    def test_rejects_non_numeric_pr_number(self):
        for bad in ("", "42; rm", "pr-42", "٤٢"):
            fake = FakeForgejo()
            with self.subTest(pr=bad), self.assertRaises(ValueError):
                self.run_with(fake, {**ENV, "PR_NUMBER": bad})
            self.assertEqual(fake.requests, [])


if __name__ == "__main__":
    unittest.main()
