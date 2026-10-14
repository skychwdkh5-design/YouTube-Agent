#!/usr/bin/env python3
"""Tests for procs.py: the pgrep -f self-match trap, interpreter/script matching, bounded waiting."""
import os, subprocess, sys, tempfile, time, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import procs  # noqa: E402


class Procs(unittest.TestCase):
    def test_shell_command_line_mentioning_the_name_is_not_a_match(self):
        self.assertFalse(procs.is_match(["/bin/bash", "-c", "until ! pgrep -f fetch_bands; do sleep 20; done"], "fetch_bands"))

    def test_interpreter_running_the_script_is_a_match(self):
        self.assertTrue(procs.is_match(["python3", "/x/y/fetch_bands.py", "spec.json"], "fetch_bands"))
        self.assertTrue(procs.is_match(["/usr/bin/python3", "-u", "fetch_bands.py"], "fetch_bands.py"))
        self.assertFalse(procs.is_match(["python3", "other.py", "fetch_bands"], "fetch_bands"))
        self.assertFalse(procs.is_match([], "x"))

    def test_finds_a_real_process_and_never_the_caller(self):
        d = tempfile.mkdtemp(); s = os.path.join(d, "sleeper_xyz.py"); open(s, "w").write("import time; time.sleep(30)")
        p = subprocess.Popen([sys.executable, s])
        try:
            time.sleep(0.3)
            self.assertEqual(procs.find("sleeper_xyz"), [p.pid])
            self.assertNotIn(os.getpid(), procs.find("test_procs"))     # this test file's own interpreter is excluded as 'self'
        finally:
            p.kill(); p.wait()
        self.assertEqual(procs.find("sleeper_xyz"), [])

    def test_wait_is_bounded_and_reports_progress(self):
        logs, t = [], [0.0]
        ok = procs.wait_gone("x", timeout=10, poll=5, log=logs.append, finder=lambda n: [42], sleep=lambda s: t.__setitem__(0, t[0] + s), clock=lambda: t[0])
        self.assertFalse(ok); self.assertIn("timeout after 10s", logs[-1]); self.assertGreaterEqual(len(logs), 2)

    def test_wait_returns_true_when_gone(self):
        seq = iter([[1], [1], []])
        self.assertTrue(procs.wait_gone("x", 60, 1, log=lambda m: None, finder=lambda n: next(seq), sleep=lambda s: None, clock=lambda: 0))


if __name__ == "__main__":
    unittest.main()
