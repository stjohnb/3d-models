"""Unit tests for capped-openscad.sh's exit-code propagation contract.

Stubs `timeout` and `openscad` as scripts on PATH so the wrapper's cap
detection can be exercised without real systemd or OpenSCAD. `systemd-run`
is deliberately excluded from PATH so every test runs the deterministic
ulimit/timeout fallback branch.
"""

import os
import shutil
import stat
import subprocess
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "capped-openscad.sh")
BASH = shutil.which("bash")


class CappedOpenscadTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._bindir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def _write_stub(self, name, body):
        path = os.path.join(self._bindir, name)
        with open(path, "w") as f:
            f.write(f"#!{BASH}\n" + body)
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def _run(self, openscad_body, timeout_body='exec "$2" "${@:3}"\n'):
        self._write_stub("openscad", openscad_body)
        self._write_stub("timeout", timeout_body)
        env = dict(os.environ)
        env["PATH"] = self._bindir
        return subprocess.run(
            [BASH, SCRIPT, "-o", "x.stl", "y.scad"],
            env=env,
            capture_output=True,
            text=True,
        )

    def test_success_propagates_zero(self):
        result = self._run("exit 0\n")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("exceeded memory/time cap", result.stderr)

    def test_generic_failure_not_flagged_as_cap(self):
        result = self._run("exit 1\n")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("exceeded memory/time cap", result.stderr)

    def test_timeout_exit_flagged_as_cap(self):
        result = self._run(
            openscad_body="exit 0\n",
            timeout_body="exit 124\n",
        )
        self.assertEqual(result.returncode, 124)
        self.assertIn("exceeded memory/time cap", result.stderr)

    def test_oom_kill_exit_flagged_as_cap(self):
        result = self._run(
            openscad_body="exit 0\n",
            timeout_body="exit 137\n",
        )
        self.assertEqual(result.returncode, 137)
        self.assertIn("exceeded memory/time cap", result.stderr)


if __name__ == "__main__":
    unittest.main()
