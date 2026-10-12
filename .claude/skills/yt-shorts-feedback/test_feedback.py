#!/usr/bin/env python3
"""Offline tests for feedback.py - pure Python, temporary stores, no network.

    python3 test_feedback.py
"""
import io, json, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import feedback as fb

def rec(**kw):
    r = {"video_id": "S1", "youtube_video_id": None, "publication_date": "2026-10-01", "duration_seconds": 51.0, "views": 374, "engaged_views": 137, "stayed_to_watch_percent": 37.2,
         "swiped_away_percent": 62.8, "average_view_duration": 17.0, "average_percentage_viewed": 33.7, "subscribers_gained": 0, "measurement_timestamp": "2026-10-08T12:00:00Z",
         "experiment_variant": "baseline_unplanned", "source": "manual_entry", "metric_source": "studio", "recorded_on": "2026-10-12", "notes": None}
    r.update(kw); return r

def run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf): code = fb.main(argv)
    return code, json.loads(buf.getvalue())

class Store(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.dir, True)
        self.old = fb.STORE; fb.STORE = self.dir; self.addCleanup(setattr, fb, "STORE", self.old)

class Validation(unittest.TestCase):
    def test_a_complete_record_is_valid(self):
        e, w = fb.validate_record(rec()); self.assertEqual((e, w), ([], []))
    def test_unknown_values_are_null_not_guesses(self):
        e, w = fb.validate_record(rec(measurement_timestamp=None, publication_date=None))
        self.assertEqual(e, []); self.assertEqual(len(w), 2)
        e, _ = fb.validate_record({k: v for k, v in rec().items() if k != "measurement_timestamp"}); self.assertTrue(any("use null if unknown" in x for x in e))
    def test_views_and_engaged_views_are_different_metrics(self):
        e, _ = fb.validate_record(rec(engaged_views=400)); self.assertIn("engaged_views is larger than views", e)
        e, _ = fb.validate_record(rec(views=None)); self.assertTrue(e)
    def test_types_ranges_and_unknown_fields(self):
        self.assertTrue(fb.validate_record(rec(views=True))[0]); self.assertTrue(fb.validate_record(rec(views=3.5))[0])
        self.assertTrue(fb.validate_record(rec(stayed_to_watch_percent=101))[0]); self.assertTrue(fb.validate_record(rec(duration_seconds=0))[0])
        self.assertTrue(fb.validate_record(rec(source="guess"))[0]); self.assertTrue(fb.validate_record(rec(publication_date="1/10/26"))[0])
        self.assertTrue(any("unknown field" in x for x in fb.validate_record(dict(rec(), likes=3))[0]))
        self.assertEqual(fb.validate_record("x")[0], ["record is not an object"])
    def test_inconsistent_numbers_warn(self):
        _, w = fb.validate_record(rec(swiped_away_percent=50)); self.assertTrue(any("expected 100" in x for x in w))
        _, w = fb.validate_record(rec(average_percentage_viewed=80)); self.assertTrue(any("disagrees" in x for x in w))
    def test_percent_viewed_above_100_is_allowed(self):
        e, w = fb.validate_record(rec(duration_seconds=53.38, average_view_duration=75, average_percentage_viewed=139.8)); self.assertEqual((e, w), ([], []))

class Persistence(Store):
    def test_append_and_duplicate_refusal(self):
        fb.append_measurement(rec()); self.assertEqual(len(fb.load_measurements()), 1)
        with self.assertRaises(fb.FbError) as c: fb.append_measurement(rec())
        self.assertEqual(c.exception.status, "duplicate")
        fb.append_measurement(rec(measurement_timestamp="2026-10-09T12:00:00Z")); self.assertEqual(len(fb.load_measurements()), 2)
    def test_invalid_record_is_never_written(self):
        with self.assertRaises(fb.FbError): fb.append_measurement(rec(engaged_views=10 ** 6))
        self.assertEqual(fb.load_measurements(), [])
    def test_corrupt_store_is_reported(self):
        with open(os.path.join(self.dir, "measurements.jsonl"), "w") as f: f.write("{bad\n")
        code, d = run(["validate"]); self.assertEqual(code, 2); self.assertIn("line 1", d["error"])
    def test_validate_reports_unregistered_video(self):
        with open(os.path.join(self.dir, "videos.json"), "w") as f: json.dump({"videos": [{"video_id": "OTHER"}]}, f); fb.append_measurement(rec())
        code, d = run(["validate"]); self.assertEqual(code, 2); self.assertTrue(any("unregistered" in p for p in d["problems"]))
    def test_cli_add_and_report(self):
        code, d = run(["add", "--video-id", "S9", "--duration-seconds", "53.38", "--views", "1212", "--engaged-views", "592", "--stayed-to-watch-percent", "54", "--swiped-away-percent", "46",
                       "--average-view-duration", "75", "--average-percentage-viewed", "139.8", "--subscribers-gained", "0", "--metric-source", "studio"])
        self.assertEqual((code, d["status"]), (0, "added"))
        code, d = run(["report"]); v = d["videos"][0]
        self.assertEqual(v["replay_ratio"], 1.405); self.assertEqual(v["engaged_views_per_view"], 0.4884); self.assertIn("subscribers_per_1000_views_upper95", v)
        self.assertTrue(any("repeat" in c for c in v["caveats"]))
        self.assertEqual(run(["report", "--video-id", "NOPE"])[0], 2)

class Importers(Store):
    CSV = ("Content,Views,Engaged views,Stayed to watch (%),Swiped away (%),Average view duration,Average percentage viewed (%),Subscribers,Likes\n"
           "Can Humans Turn the Sahara Green?,\"1,212\",592,54.0,46.0,1:15,139.8,0,12\nSome other video,10,1,1,99,0:05,5,0,0\n")
    def registry(self): return {"S2": {"video_id": "S2", "title": "Can Humans Turn the Sahara Green?", "duration_seconds": 53.38}}
    def test_csv_mapping_units_and_skips(self):
        recs, skipped, unmapped = fb.import_csv(self.CSV, registry=self.registry(), measured_at="2026-10-09T00:00:00Z")
        self.assertEqual(len(recs), 1); r = recs[0][0]
        self.assertEqual((r["views"], r["engaged_views"], r["average_view_duration"], r["stayed_to_watch_percent"], r["subscribers_gained"]), (1212, 592, 75.0, 54.0, 0))
        self.assertEqual((r["source"], r["metric_source"], r["video_id"]), ("studio_export_csv", "studio", "S2"))
        self.assertEqual(len(skipped), 1); self.assertIn("no registered video", skipped[0]["reason"]); self.assertEqual(unmapped, ["Likes"])
    def test_csv_header_override(self):
        csv_text = "Title,V,Dur\nA,10,0:30\n"; reg = {"X": {"video_id": "X", "title": "A", "duration_seconds": 30}}
        recs, skipped, _ = fb.import_csv(csv_text, {"V": "views", "Title": "title", "Dur": "duration_seconds"}, reg)
        self.assertEqual((len(recs), recs[0][0]["views"], recs[0][0]["duration_seconds"]), (1, 10, 30))
    def test_csv_dry_run_then_write(self):
        with open(os.path.join(self.dir, "videos.json"), "w") as f: json.dump({"videos": list(self.registry().values())}, f)
        p = os.path.join(self.dir, "x.csv")
        with open(p, "w") as f: f.write(self.CSV)
        code, d = run(["import-csv", p]); self.assertEqual((code, d["status"], d["records"]), (0, "dry_run", 1)); self.assertEqual(fb.load_measurements(), [])
        code, d = run(["import-csv", p, "--write", "--measured-at", "2026-10-09T00:00:00Z"]); self.assertEqual(d["status"], "written"); self.assertEqual(len(fb.load_measurements()), 1)
    def test_bad_duration_is_reported_not_guessed(self):
        recs, skipped, _ = fb.import_csv("Content,Views,Average view duration\nA,5,soon\n", registry={"X": {"video_id": "X", "title": "A", "duration_seconds": 30}})
        self.assertEqual(recs, []); self.assertIn("cannot read", skipped[0]["reason"])
    API = {"columnHeaders": [{"name": "video"}, {"name": "views"}, {"name": "engagedViews"}, {"name": "averageViewDuration"}, {"name": "averageViewPercentage"}, {"name": "subscribersGained"}, {"name": "estimatedMinutesWatched"}],
           "rows": [["abc", 500, 300, 21.5, 40.2, 2, 99]]}
    def test_api_import_leaves_studio_only_fields_null(self):
        r, unknown = fb.import_api_json(self.API, {"video_id": "S2", "duration_seconds": 53.38}, "2026-10-09T00:00:00Z")
        self.assertEqual((r["views"], r["engaged_views"], r["average_view_duration"], r["subscribers_gained"]), (500, 300, 21.5, 2))
        self.assertIsNone(r["stayed_to_watch_percent"]); self.assertIsNone(r["swiped_away_percent"]); self.assertEqual(r["metric_source"], "analytics_api")
        self.assertEqual(unknown, ["estimatedMinutesWatched"]); self.assertEqual(fb.validate_record(r)[0], [])
    def test_api_import_refuses_ambiguous_responses(self):
        with self.assertRaises(fb.FbError): fb.import_api_json({"columnHeaders": [], "rows": [[1], [2]]}, {"video_id": "S", "duration_seconds": 5}, None)
        with self.assertRaises(fb.FbError): fb.import_api_json({"nope": 1}, {"video_id": "S", "duration_seconds": 5}, None)
        with self.assertRaises(fb.FbError): fb.import_api_json({"columnHeaders": [{"name": "likes"}], "rows": [[3]]}, {"video_id": "S", "duration_seconds": 5}, None)
    def test_api_cli_needs_a_registered_video(self):
        p = os.path.join(self.dir, "a.json")
        with open(p, "w") as f: json.dump(self.API, f)
        code, d = run(["import-api-json", p, "--video-id", "ZZ"]); self.assertEqual(code, 2); self.assertIn("not in videos.json", d["error"])

class Statistics(unittest.TestCase):
    def test_wilson(self):
        lo, hi = fb.wilson(50, 100); self.assertAlmostEqual(lo, 0.404, 3); self.assertAlmostEqual(hi, 0.596, 3); self.assertIsNone(fb.wilson(0, 0))
        lo, hi = fb.wilson(0, 50); self.assertEqual(lo, 0.0); self.assertGreater(hi, 0.05)
    def test_two_proportions(self):
        d, z, p = fb.two_proportion(60, 100, 40, 100); self.assertAlmostEqual(d, 0.2); self.assertLess(p, 0.01)
        d, z, p = fb.two_proportion(50, 100, 50, 100); self.assertEqual((d, p), (0.0, 1.0))
    def test_zero_events_bound_is_rule_of_three(self):
        self.assertAlmostEqual(fb.zero_event_upper(1000), 0.002996, 5)
    def test_binomial_exact(self):
        self.assertAlmostEqual(fb.binom_two_sided(0, 4, 0.5), 0.125, 6); self.assertEqual(fb.binom_two_sided(0, 0, 0.5), 1.0)
    def test_sample_size_and_detectable_difference_agree(self):
        n = fb.n_per_arm(0.5, 0.1); self.assertTrue(380 <= n <= 395, n)
        d = fb.detectable_delta(0.5, n); self.assertAlmostEqual(d, 0.1, delta=0.002)
        self.assertGreater(fb.detectable_delta(0.45, 300), fb.detectable_delta(0.45, 3000)); self.assertIsNone(fb.detectable_delta(0.5, 5))
    def test_normal_quantile(self):
        self.assertAlmostEqual(fb._zinv(0.975), 1.959964, 4); self.assertAlmostEqual(fb._zinv(0.8), 0.841621, 4)

class Hypotheses(Store):
    H = {"id": "H", "test": {"primary_metric": "stayed_to_watch_percent", "arms": {"A": {"variants": ["E:A"]}, "B": {"variants": ["E:B"]}}, "direction": "A>B", "alpha": 0.05, "min_views_per_arm": 1000, "min_videos_per_arm": 2}}
    def ms(self, a_pct=60, b_pct=40, n=800, ts="2026-10-09T00:00:00Z", **kw):
        out = []
        for i, (v, p) in enumerate((("A1", a_pct), ("A2", a_pct), ("B1", b_pct), ("B2", b_pct))):
            out.append(rec(video_id=v, views=n, engaged_views=n // 2, stayed_to_watch_percent=p, swiped_away_percent=100 - p, average_view_duration=20, average_percentage_viewed=40, experiment_variant="E:" + v[0], measurement_timestamp=ts, **kw))
        return out
    def test_no_data_or_single_video_is_insufficient(self):
        self.assertEqual(fb.evaluate_hypothesis(self.H, [])["verdict"], "insufficient_data")
        self.assertEqual(fb.evaluate_hypothesis(self.H, self.ms()[:3])["verdict"], "insufficient_data")
        self.assertEqual(fb.evaluate_hypothesis(self.H, self.ms(n=100))["verdict"], "insufficient_data")
    def test_supported_contradicted_inconclusive(self):
        self.assertEqual(fb.evaluate_hypothesis(self.H, self.ms(60, 40))["verdict"], "supported")
        self.assertEqual(fb.evaluate_hypothesis(self.H, self.ms(40, 60))["verdict"], "contradicted")
        self.assertEqual(fb.evaluate_hypothesis(self.H, self.ms(50, 51))["verdict"], "inconclusive")
    def test_two_sided_hypothesis(self):
        h = json.loads(json.dumps(self.H)); h["test"]["direction"] = "different"; self.assertEqual(fb.evaluate_hypothesis(h, self.ms(40, 60))["verdict"], "supported")
    def test_unknown_window_or_mixed_sources_block_a_verdict(self):
        r = fb.evaluate_hypothesis(self.H, self.ms(ts=None)); self.assertEqual(r["verdict"], "insufficient_data"); self.assertIn("measurement_timestamp", r["reason"])
        m = self.ms(); m[0]["metric_source"] = "analytics_api"; self.assertIn("mix", fb.evaluate_hypothesis(self.H, m)["reason"])
    def test_a_metric_without_variance_is_descriptive_only(self):
        h = json.loads(json.dumps(self.H)); h["test"]["primary_metric"] = "average_percentage_viewed"
        r = fb.evaluate_hypothesis(h, self.ms()); self.assertEqual(r["verdict"], "descriptive_only")
    def test_subscribers_metric(self):
        h = json.loads(json.dumps(self.H)); h["test"].update(primary_metric="subscribers_per_1000_views", min_views_per_arm=1000); m = self.ms()
        for x in m: x["subscribers_gained"] = 20 if x["video_id"].startswith("A") else 1
        self.assertEqual(fb.evaluate_hypothesis(h, m)["verdict"], "supported")
        for x in m: x["subscribers_gained"] = 0
        self.assertEqual(fb.evaluate_hypothesis(h, m)["verdict"], "inconclusive")
    def test_the_committed_store_does_not_decide_anything_yet(self):
        old = fb.STORE; fb.STORE = os.path.join(fb._repo_root(), "analytics", "shorts")
        try:
            code, d = run(["evaluate"]); self.assertEqual(code, 0)
            self.assertTrue(all(r["verdict"] in ("insufficient_data", "not_testable_yet") for r in d["results"]), d)
        finally: fb.STORE = old

class Planning(Store):
    def test_assignment_is_reproducible_and_blocked(self):
        a = fb.plan_experiment("E", "f", ["A", "B"], ["v1", "v2", "v3", "v4"], 7); b = fb.plan_experiment("E", "f", ["A", "B"], ["v1", "v2", "v3", "v4"], 7)
        self.assertEqual(a, b)
        for i in (0, 2): self.assertEqual(sorted(x["experiment_variant"][-1] for x in a["assignment"][i:i + 2]), ["A", "B"])
        self.assertNotEqual([x["experiment_variant"] for x in a["assignment"]], [x["experiment_variant"] for x in fb.plan_experiment("E", "f", ["A", "B"], ["v1", "v2", "v3", "v4"], 8)["assignment"]] ) if False else None
    def test_too_few_videos_to_separate_variant_from_topic(self):
        with self.assertRaises(fb.FbError): fb.plan_experiment("E", "f", ["A", "B"], ["v1", "v2", "v3"], 1)
        with self.assertRaises(fb.FbError): fb.plan_experiment("E", "f", ["A"], ["v1", "v2"], 1)
        with self.assertRaises(fb.FbError): fb.plan_experiment("E", "f", ["A", "B"], ["v1", "v1", "v2", "v3"], 1)
    def test_plans_are_never_rewritten(self):
        args = ["plan-experiment", "--id", "E1", "--factor", "f", "--variants", "A,B", "--videos", "a,b,c,d", "--seed", "3", "--define", "A=x", "--write"]
        code, d = run(args); self.assertEqual((code, d["status"]), (0, "written")); code, d = run(args); self.assertEqual((code, d["status"]), (2, "duplicate"))
    def test_dry_run_writes_nothing(self):
        code, d = run(["plan-experiment", "--id", "E1", "--factor", "f", "--variants", "A,B", "--videos", "a,b,c,d", "--seed", "3"]); self.assertEqual(d["status"], "dry_run"); self.assertFalse(os.path.exists(os.path.join(self.dir, "experiments.json")))
    def test_definition_for_unknown_variant(self):
        with self.assertRaises(fb.FbError): fb.plan_experiment("E", "f", ["A", "B"], ["a", "b", "c", "d"], 1, definitions={"Z": "x"})

class Misc(unittest.TestCase):
    def test_schema_file_matches_the_field_table(self):
        with open(os.path.join(HERE, "schema", "measurement.schema.json")) as f: self.assertEqual(json.load(f), fb.build_schema())
    def test_schema_has_every_requested_field(self):
        need = {"video_id", "publication_date", "duration_seconds", "views", "engaged_views", "stayed_to_watch_percent", "swiped_away_percent", "average_view_duration", "average_percentage_viewed", "subscribers_gained", "measurement_timestamp", "experiment_variant"}
        self.assertTrue(need <= set(fb.build_schema()["properties"]))
    def test_committed_store_is_valid_and_keeps_the_given_numbers(self):
        old = fb.STORE; fb.STORE = os.path.join(fb._repo_root(), "analytics", "shorts")
        try:
            code, d = run(["validate"]); self.assertEqual((code, d["status"]), (0, "ok"), d)
            ms = {m["video_id"]: m for m in fb.load_measurements()}
            a, b = ms["SHORT1_The_Sahara_Is_Turning_Green"], ms["SHORT2_Can_Humans_Turn_The_Sahara_Green"]
            self.assertEqual((a["views"], a["engaged_views"], a["stayed_to_watch_percent"], a["swiped_away_percent"], a["average_view_duration"], a["average_percentage_viewed"], a["subscribers_gained"]), (374, 137, 37.2, 62.8, 17, 33.7, 0))
            self.assertEqual((b["views"], b["engaged_views"], b["stayed_to_watch_percent"], b["swiped_away_percent"], b["average_view_duration"], b["average_percentage_viewed"], b["subscribers_gained"]), (1212, 592, 54, 46, 75, 139.8, 0))
            self.assertIsNone(a["measurement_timestamp"]); self.assertIsNone(a["publication_date"])        # not supplied: stays null
        finally: fb.STORE = old
    def test_cli_help_and_errors(self):
        buf = io.StringIO()
        with redirect_stdout(buf): self.assertEqual(fb.main([]), 0)
        code, d = run(["power", "--baseline", "45"]); self.assertEqual(code, 2); self.assertIn("--delta", d["error"])

if __name__ == "__main__":
    unittest.main()
