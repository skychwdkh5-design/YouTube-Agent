"""Tests for the YouTube skill tools.

    python3 -m unittest discover -s tests -v

Three groups:
  - Regression: every original tool, run WITHOUT --profile geo, must produce exactly the output it
    produced before the geography changes (tests/baseline/ was captured from the untouched scripts).
  - Geography mode: --profile geo behaves as designed.
  - New tools and structure: the fact-check, license and topic gates, and the skill/channel layout.
"""
import json, os, re, subprocess, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(ROOT, ".claude", "skills")
FX = os.path.join(ROOT, "tests", "fixtures")
BL = os.path.join(ROOT, "tests", "baseline")

# chapters.py orders tied draft-title words by set iteration, which follows Python's per-process hash
# seed. That is pre-existing behaviour of the original tool; a fixed seed makes the comparison exact.
ENV = dict(os.environ, PYTHONHASHSEED="0")

def read(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as fh: return fh.read()

def run(script, *args, ok=(0,)):
    p = subprocess.run([sys.executable, os.path.join(SK, script), *args], cwd=ROOT,
                       capture_output=True, text=True, env=ENV)
    if p.returncode not in ok:
        raise AssertionError(f"{script} {args} exited {p.returncode}\n{p.stdout}\n{p.stderr}")
    return p

def js(script, *args, ok=(0,)):
    return json.loads(run(script, *args, ok=ok).stdout)

def baseline(name):
    return json.loads(read(BL, name))

def fx(name): return os.path.join("tests", "fixtures", name)


class Regression(unittest.TestCase):
    """Default behaviour of the 7 original tools is byte-for-byte what it was."""

    def test_hookscore_default(self):
        self.assertEqual(js("yt-script/hookscore.py", "--json", fx("hooks.txt")), baseline("hookscore.json"))

    def test_title_default(self):
        self.assertEqual(js("yt-package/title.py", "--json", fx("titles.txt")), baseline("title.json"))

    def test_title_thumb_default(self):
        got = js("yt-package/title.py", "--json", "--title", "The U.S. Town You Can Only Reach Through Canada",
                 "--thumb", "NO ROAD IN")
        self.assertEqual(got, baseline("title_thumb.json"))

    def test_swipe_default(self):
        self.assertEqual(js("yt-viral/swipe.py", fx("collected.json"), "--json", "--min", "1.0"), baseline("swipe.json"))

    def test_retention_unchanged(self):
        got = js("yt-retention/retention.py", fx("retention.csv"), "--json", "--transcript", fx("transcript.srt"))
        self.assertEqual(got, baseline("retention.json"))

    def test_chapters_unchanged(self):
        self.assertEqual(js("yt-chapters/chapters.py", fx("transcript.srt"), "--target", "4", "--json"),
                         baseline("chapters.json"))

    def test_deadair_unchanged(self):
        self.assertEqual(js("yt-edit/deadair.py", fx("transcript.srt"), "--json"), baseline("deadair.json"))

    def test_text_modes_still_run(self):
        for script, args in [("yt-script/hookscore.py", [fx("hooks.txt")]),
                             ("yt-script/hookscore.py", ["--hook", "Why do your videos die at 30 seconds?"]),
                             ("yt-package/title.py", [fx("titles.txt")]),
                             ("yt-viral/swipe.py", [fx("collected.json")]),
                             ("yt-retention/retention.py", [fx("retention.csv"), "--duration", "600"]),
                             ("yt-chapters/chapters.py", [fx("transcript.srt")]),
                             ("yt-edit/deadair.py", [fx("transcript.srt")])]:
            self.assertTrue(run(script, *args).stdout.strip(), script)


class GeoMode(unittest.TestCase):

    def test_hookscore_geo_swaps_stakes_for_anomaly(self):
        r = js("yt-script/hookscore.py", "--json", "--profile", "geo", fx("hooks.txt"))
        for row in r:
            self.assertIn("ANOMALY", row["properties"])
            self.assertNotIn("STAKES", row["properties"])

    def test_hookscore_geo_ranks_geo_hook_above_generic(self):
        geo = "You can only drive to this town in Washington by going through Canada first, and nobody ever fixed it."
        dull = "Today we are going to learn about some interesting geography facts."
        g = js("yt-script/hookscore.py", "--json", "--profile", "geo", "--hook", geo)[0]
        d = js("yt-script/hookscore.py", "--json", "--profile", "geo", "--hook", dull)[0]
        self.assertGreater(g["verdict"], d["verdict"] + 15)
        self.assertEqual(g["formula"], "The Only Way In")
        self.assertEqual(d["formula"], "Unclassified")

    def test_hookscore_geo_beats_default_on_geo_hook(self):
        h = "Why does this little piece of land north of the border belong to Minnesota, when you can't reach it by road?"
        g = js("yt-script/hookscore.py", "--json", "--profile", "geo", "--hook", h)[0]
        d = js("yt-script/hookscore.py", "--json", "--hook", h)[0]
        self.assertGreater(g["verdict"], d["verdict"])

    def test_geo_formulas_file_is_valid(self):
        d = json.loads(read(SK, "yt-script", "hooks-geo.json"))
        ids = [h["id"] for h in d["hooks"]]
        self.assertEqual(len(ids), len(set(ids)))
        general = {h["id"] for h in json.loads(read(SK, "yt-script", "hooks.json"))["hooks"]}
        self.assertFalse(general & set(ids), "geo ids must not collide with the general 21")
        for h in d["hooks"]:
            for k in ("name", "shape", "example", "fails_when", "match"):
                self.assertTrue(h.get(k), f"{h['id']} missing {k}")
            for p in h["match"]: re.compile(p)
            # every formula must recognise its own example
            self.assertTrue(any(re.search(p, h["example"], re.I) for p in h["match"]), h["id"])

    def test_original_formulas_untouched(self):
        self.assertEqual(len(json.loads(read(SK, "yt-script", "hooks.json"))["hooks"]), 21)

    def test_title_geo_counts_places_as_names(self):
        rows = js("yt-package/title.py", "--json", "--profile", "geo", fx("titles.txt"))
        by = {r["title"]: r for r in rows}
        mn = by["Why Does This Part of the U.S. Belong to Minnesota?"]
        self.assertNotIn("no-number", [k for k, _ in mn["issues"]])
        self.assertTrue(any("Minnesota" in g for g in mn["good"]))
        self.assertFalse(any("all-caps" in g for g in mn["good"]), "U.S. must not count as shouting")
        junk = by["This Is the Most Amazing Video You Will Ever See"]
        self.assertIn("no-number", [k for k, _ in junk["issues"]])

    def test_title_geo_pronoun_us_is_not_a_country(self):
        r = js("yt-package/title.py", "--json", "--profile", "geo", "--title", "Come With Us to the Edge of the Map")[0]
        self.assertIn("no-number", [k for k, _ in r["issues"]])

    def test_title_geo_overlapping_names(self):
        r = js("yt-package/title.py", "--json", "--profile", "geo", "--title", "Why New Mexico Is Not Part of Mexico")[0]
        good = " ".join(r["good"])
        self.assertIn("New Mexico", good); self.assertIn("Mexico,", good + ",")

    def test_swipe_geo_uses_geo_formulas(self):
        r = js("yt-viral/swipe.py", fx("collected.json"), "--json", "--min", "1.0", "--profile", "geo")
        names = {o["formula"] for o in r["outliers"]}
        self.assertTrue(names & {"The Only Way In", "The Empty Map"}, names)


class FactCheckGate(unittest.TestCase):
    S = "geo-factcheck/claims.py"

    def test_good_ledger_passes(self):
        self.assertEqual(js(self.S, "--claims", fx("claims_good.md"), "--json")["gate"], "PASS")

    def test_good_script_passes(self):
        r = js(self.S, "--claims", fx("claims_good.md"), "--script", fx("script_good.md"), "--json")
        self.assertEqual(r["gate"], "PASS", r["fails"])

    def test_bad_ledger_fails_for_each_reason(self):
        r = js(self.S, "--claims", fx("claims_bad.md"), "--json", ok=(1,))
        msgs = " | ".join(m for _, m in r["fails"])
        for needle in ("two independent sources", "Tier 3 only", "tertiary", "YYYY-MM-DD", "not one of", "duplicate"):
            self.assertIn(needle, msgs)

    def test_bad_script_fails_for_each_reason(self):
        r = js(self.S, "--claims", fx("claims_good.md"), "--script", fx("script_bad.md"), "--json", ok=(1,))
        kinds = [w for w, _ in r["fails"]]
        msgs = " | ".join(m for _, m in r["fails"])
        self.assertIn("CUT claim is still in the script", msgs)
        self.assertIn("tag not in the ledger", msgs)
        self.assertEqual(kinds.count("UNTAGGED"), 2)          # "1,000 people" and "forty miles"

    def test_visual_notes_are_ignored(self):
        # script_good has "1,000 label" inside a [MAP: ...] note - it must not trip the detector
        r = js(self.S, "--claims", fx("claims_good.md"), "--script", fx("script_good.md"), "--json")
        self.assertFalse([m for w, m in r["fails"] if "label" in m])


class LicenseGate(unittest.TestCase):
    S = "geo-visuals/assets.py"

    def test_good_assets_pass_with_credits(self):
        r = js(self.S, fx("visuals_good.md"), "--json")
        self.assertEqual(r["gate"], "PASS", r["fails"])
        self.assertFalse(r["disclosure_required"])
        self.assertIn("© OpenStreetMap contributors", r["credits"])

    def test_bad_assets_fail_for_each_reason(self):
        r = js(self.S, fx("visuals_bad.md"), "--json", ok=(1,))
        msgs = " | ".join(m for _, m in r["fails"])
        for needle in ("not a source", "no license", "must name OpenStreetMap", "cannot stand in for real satellite",
                       "non-commercial", "defence, not a license", "no-derivatives"):
            self.assertIn(needle, msgs)
        self.assertTrue(r["disclosure_required"])
        self.assertEqual(r["disclosure_assets"], ["V3", "V7"])


    def test_only_first_table_is_data(self):
        r = js(self.S, fx("visuals_multitable.md"), "--json")
        self.assertEqual(r["assets"], 6, "notes tables after the asset table must be ignored")
        self.assertEqual(r["gate"], "PASS")


class TopicGate(unittest.TestCase):
    S = "geo-topics/topicscore.py"

    def test_ranking_and_gates(self):
        r = js(self.S, fx("ideas.md"), "--json")
        by = {x["id"]: x for x in r["ranked"]}
        self.assertNotIn("I5", by, "published ideas are skipped")
        self.assertEqual(by["I3"]["verdict"], "REJECTED", "verify < 3 is rejected whatever it scores")
        self.assertEqual(r["ranked"][-1]["id"], "I3")
        self.assertEqual(by["I4"]["criteria"]["interest"], 3, "unproven interest is capped at 3")

    def test_global_topic_can_win(self):
        r = js(self.S, fx("ideas.md"), "--json")
        self.assertEqual(r["ranked"][0]["region"], "Europe", "region is never scored - a stronger global topic wins")

    def test_empty_backlog_runs(self):
        self.assertEqual(js(self.S, fx("ideas_empty.md"), "--json")["ranked"], [])

    def test_channel_backlog_parses(self):
        r = js(self.S, os.path.join("channel", "ideas.md"), "--json")
        for x in r["ranked"]:
            self.assertNotIn("not scored", " ".join(x["notes"]), x["id"])


class Structure(unittest.TestCase):
    YT = ["yt-audit", "yt-chapters", "yt-comment", "yt-edit", "yt-package", "yt-plan", "yt-retention",
          "yt-script", "yt-seo", "yt-shorts", "yt-viral"]
    GEO = ["geo-topics", "geo-research", "geo-factcheck", "geo-visuals"]

    def test_every_skill_has_valid_frontmatter_and_gate(self):
        for d in self.YT + self.GEO:
            s = read(SK, d, "SKILL.md")
            m = re.match(r"---\nname: ([\w-]+)\ndescription: >-\n(.+?)\n---\n", s, re.S)
            self.assertTrue(m, f"{d}: frontmatter")
            self.assertEqual(m.group(1), d)
            self.assertIn("**ship it, or change it?**", s, f"{d}: the no-publish gate line")
            self.assertIn("Nothing here publishes", s, d)

    def test_voice_skills_read_channel_profile_and_keep_fallback(self):
        for d in ["yt-script", "yt-audit", "yt-comment", "yt-package", "yt-plan", "yt-seo"]:
            s = read(SK, d, "SKILL.md")
            self.assertIn("channel/voice.md", s, d)
            self.assertIn("~/.claude/youtube/voice.md", s, f"{d}: original fallback kept")

    def test_channel_files_exist(self):
        for f in ["channel.md", "voice.md", "editorial.md", "research.md", "visual-style.md", "ideas.md",
                  "templates/brief.md", "templates/claims.md", "templates/script.md", "templates/visuals.md",
                  "templates/package.md", "templates/seo.md", "templates/shorts.md", "templates/post.md"]:
            self.assertTrue(os.path.exists(os.path.join(ROOT, "channel", f)), f)
        self.assertTrue(os.path.exists(os.path.join(ROOT, "CLAUDE.md")))

    def test_templates_work_with_the_gates(self):
        # the empty templates parse; the claims template's single UNVERIFIED row is valid ledger syntax
        r = js("geo-factcheck/claims.py", "--claims", os.path.join("channel", "templates", "claims.md"), "--json")
        self.assertEqual(r["claims"], 1)
        r = js("geo-visuals/assets.py", os.path.join("channel", "templates", "visuals.md"), "--json", ok=(0, 1))
        self.assertEqual(r["assets"], 1)

    def test_no_api_or_publish_calls_in_tools(self):
        for d in self.YT + self.GEO:
            for f in os.listdir(os.path.join(SK, d)):
                if f.endswith(".py"):
                    src = read(SK, d, f)
                    for bad in ("googleapis", "oauth", "requests.post", "urllib.request", "http.client"):
                        self.assertNotIn(bad, src, f"{d}/{f} must not call out")


if __name__ == "__main__":
    unittest.main()
