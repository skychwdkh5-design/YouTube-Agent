#!/usr/bin/env python3
"""Offline tests for fetch_bands.py: 504 retry, timeouts, back-off, permanent errors, resume and skipping finished tiles."""
import os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fetch_bands as fb  # noqa: E402

TILE = {"dataset": "landsat_tm_c2_l1", "bands": "B3,B2,B1", "entity": "E1", "display_id": "LT05_X"}


def touch_all(d, did="LT05_X", bands=("B3", "B2", "B1"), mtl=True):
    for b in bands: open(os.path.join(d, f"{did}_{b}.TIF"), "wb").write(b"x")
    if mtl: open(os.path.join(d, f"{did}_MTL.txt"), "w").write("m")


class Fetch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup); self.d = self.tmp.name
        self.sleeps, self.logs = [], []

    def run_tile(self, runner, attempts=4):
        return fb.fetch_tile(TILE, self.d, attempts, 5, runner=runner, sleep=self.sleeps.append, log=self.logs.append)

    def test_complete_tile_is_skipped_and_never_requested(self):
        touch_all(self.d); calls = []
        r = self.run_tile(lambda *a: calls.append(a) or {"status": "ok"})
        self.assertEqual((r["status"], r["attempts"], calls), ("skipped_complete", 0, []))

    def test_missing_mtl_or_empty_band_is_not_complete(self):
        touch_all(self.d, mtl=False); self.assertFalse(fb.complete("LT05_X", "B3,B2,B1", self.d))
        touch_all(self.d); open(os.path.join(self.d, "LT05_X_B2.TIF"), "wb").close()
        self.assertFalse(fb.complete("LT05_X", "B3,B2,B1", self.d))

    def test_http_504_is_retried_with_exponential_backoff_then_succeeds(self):
        n = []
        def runner(t, d, s):
            n.append(1)
            if len(n) < 3: return {"status": "error", "error": "file download failed: HTTPError: HTTP Error 504: Gateway Time-out; removed partial file"}
            touch_all(d); return {"status": "ok"}
        r = self.run_tile(runner)
        self.assertEqual((r["status"], r["attempts"]), ("ok", 3)); self.assertEqual(self.sleeps, [30, 60])

    def test_timeout_counts_as_transient_and_gives_up_after_the_limit(self):
        r = self.run_tile(lambda *a: {"status": "error", "error": "timed out: attempt exceeded 5s and was killed"}, attempts=3)
        self.assertEqual((r["status"], r["attempts"]), ("failed_gave_up", 3)); self.assertEqual(len(self.sleeps), 2)

    def test_backoff_is_capped(self):
        fb.fetch_tile(TILE, self.d, 8, 5, runner=lambda *a: {"status": "error", "error": "504"}, sleep=self.sleeps.append, log=lambda m: None)
        self.assertEqual(max(self.sleeps), 240)

    def test_permanent_errors_stop_at_once(self):
        for msg in ("no band-file download option for X", "download exceeded --max-mb 120; removed partial file", "authentication failed"):
            self.sleeps.clear()
            r = self.run_tile(lambda *a, m=msg: {"status": "error", "error": m})
            self.assertEqual((r["status"], r["attempts"], self.sleeps), ("failed_permanent", 1, []), msg)

    def test_ok_without_files_is_not_trusted(self):
        r = self.run_tile(lambda *a: {"status": "ok"}, attempts=2)
        self.assertEqual(r["status"], "failed_gave_up")

    def test_partial_progress_resumes_only_what_is_missing(self):
        seen = []
        def runner(t, d, s):                      # first call leaves two bands (as usgs_m2m does), the rerun finds them and finishes
            seen.append(sorted(os.listdir(d)))
            if len(seen) == 1:
                for b in ("B3", "B2"): open(os.path.join(d, f"LT05_X_{b}.TIF"), "wb").write(b"x")
                return {"status": "error", "error": "HTTP Error 504"}
            touch_all(d); return {"status": "ok"}
        r = self.run_tile(runner)
        self.assertEqual(r["status"], "ok"); self.assertEqual(seen[0], []); self.assertEqual(len(seen[1]), 2)

    def test_fetch_all_reports_progress_and_only_ok_when_every_tile_is_done(self):
        t2 = dict(TILE, display_id="LT05_Y", entity="E2"); touch_all(self.d)
        rep = fb.fetch_all({"out_dir": self.d, "tiles": [TILE, t2]}, 2, 5, runner=lambda *a: {"status": "error", "error": "504"}, sleep=lambda s: None, log=self.logs.append)
        self.assertFalse(rep["ok"]); self.assertEqual((rep["complete"], rep["total"]), (1, 2))
        self.assertTrue(any(l.startswith("[2/2]") for l in self.logs))

    def test_classify(self):
        self.assertEqual(fb.classify("HTTP Error 504: Gateway Time-out"), "transient")
        self.assertEqual(fb.classify("no download URL for X (not ready after 300s)"), "transient")
        self.assertEqual(fb.classify("weird"), "unknown")

    def test_a_hanging_child_is_killed_by_the_time_limit(self):
        import subprocess
        orig = fb.subprocess.run
        def fake(cmd, **kw): raise subprocess.TimeoutExpired(cmd, kw["timeout"])
        fb.subprocess.run = fake
        try: j = fb.run_download(TILE, self.d, 7)
        finally: fb.subprocess.run = orig
        self.assertEqual(j["status"], "error"); self.assertIn("exceeded 7s", j["error"])

    def test_cli_requires_confirm(self):
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()) as o: rc = fb.main(["x.json"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
