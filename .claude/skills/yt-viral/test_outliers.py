#!/usr/bin/env python3
"""Offline tests for outliers.py - no network."""
import io, json, os, sys, tempfile, unittest
from contextlib import redirect_stdout
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import outliers as O

AS_OF = dt.datetime(2026, 10, 30, tzinfo=dt.timezone.utc)


def vid(i, views, days_ago, ch="A", dur=600, **kw):
    d = (AS_OF - dt.timedelta(days=days_ago)).isoformat()
    return O.normalize({"channel": ch, "channel_id": ch, "video_id": f"{ch}{i}", "title": f"{ch} video {i}",
                        "views": views, "published": d, "duration": dur, **kw})


def channel(n=10, base=10000, ch="A"):
    return [vid(i, base, 30 + i * 7, ch) for i in range(n)]


class Detect(unittest.TestCase):
    def one(self, videos, vid_id):
        return next(r for r in O.detect(videos, AS_OF)["results"] if r["facts"]["video_id"] == vid_id)

    def test_strong_outlier_is_focus(self):
        vs = channel() + [vid("X", 35000, 40)]
        r = self.one(vs, "AX")
        self.assertEqual((r["facts"]["ratio"], r["assessment"]["tier"], r["assessment"]["data"]), (3.5, "strong", "sufficient"))
        self.assertTrue(r["assessment"]["focus"]); self.assertEqual(r["assessment"]["confidence"], "high")
        self.assertEqual(r["hypotheses"], [])

    def test_tiers(self):
        for views, tier in ((12000, "typical"), (20000, "above"), (45000, "exceptional")):
            self.assertEqual(self.one(channel() + [vid("X", views, 40)], "AX")["assessment"]["tier"], tier)

    def test_insufficient_data_gets_no_tier(self):
        r = self.one(channel(3) + [vid("X", 90000, 40)], "AX")
        self.assertEqual((r["assessment"]["data"], r["assessment"]["tier"], r["assessment"]["focus"]), ("insufficient", None, False))

    def test_young_video_is_provisional_and_excluded_from_baselines(self):
        vs = channel() + [vid("X", 50000, 5)]
        r = self.one(vs, "AX")
        self.assertEqual(r["assessment"]["tier"], "provisional-exceptional")
        self.assertEqual(self.one(vs, "A0")["facts"]["comparables"], 9)   # young video not in A0's baseline

    def test_format_and_channel_separation(self):
        vs = channel() + [vid(f"s{i}", 900000, 40, dur=40) for i in range(10)] + channel(10, 500000, "B")
        r = self.one(vs + [vid("X", 30000, 40)], "AX")
        self.assertEqual((r["facts"]["baseline_median"], r["facts"]["ratio"]), (10000, 3.0))

    def test_window_excludes_old_videos(self):
        vs = channel() + [vid(f"o{i}", 1_000_000, 900 + i) for i in range(10)]
        self.assertEqual(self.one(vs + [vid("X", 30000, 40)], "AX")["facts"]["baseline_median"], 10000)

    def test_uneven_channel_lowers_confidence(self):
        vs = [vid(i, v, 30 + i * 7) for i, v in enumerate([500, 800, 1000, 2000, 10000, 50000, 90000, 120000, 150000, 200000])]
        r = self.one(vs + [vid("X", 200000, 40)], "AX")
        self.assertNotEqual(r["assessment"]["confidence"], "high")

    def test_external_breakout_is_low_confidence_never_focus(self):
        v = vid("X", 50000, 40, breakout=12)
        r = O.detect([v], AS_OF)["results"][0]
        self.assertEqual((r["assessment"]["data"], r["facts"]["ratio"], r["assessment"]["tier"], r["assessment"]["confidence"],
                          r["assessment"]["focus"]), ("external", 12.0, "exceptional", "low", False))
        self.assertEqual(O.detect([v], AS_OF)["focus"], [])
        r = self.one(channel() + [vid("Y", 35000, 40, breakout=99)], "AY")   # own baseline wins over a third-party score
        self.assertEqual((r["facts"]["ratio"], r["assessment"]["data"]), (3.5, "sufficient"))

    def test_aliases_and_iso_duration(self):
        v = O.normalize({"channelTitle": "C", "channelId": "UCc", "videoId": "abc", "viewCount": "1,234",
                         "publishedAt": "2026-10-01T00:00:00Z", "duration": "PT10M13S",
                         "thumbnails": {"default": {"url": "s", "width": 120}, "high": {"url": "h", "width": 480}}})
        self.assertEqual((v["views"], v["duration"], v["thumbnail"], v["channel_id"]), (1234, 613, "h", "UCc"))

    def test_never_says_viral(self):
        out = json.dumps(O.detect(channel() + [vid("X", 10**7, 40)], AS_OF)) + O.markdown(O.detect(channel(), AS_OF))
        self.assertNotIn("viral", out.lower().replace("nothing here is called viral", ""))


class RSS(unittest.TestCase):
    FEED = """<?xml version="1.0"?><feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
 xmlns:media="http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom"><title>Chan</title>
 <entry><yt:videoId>v1</yt:videoId><yt:channelId>UC1</yt:channelId><title>T1</title>
 <link rel="alternate" href="https://www.youtube.com/watch?v=v1"/><published>2026-09-01T00:00:00+00:00</published>
 <media:group><media:thumbnail url="https://i.ytimg.com/vi/v1/hqdefault.jpg"/><media:community>
 <media:statistics views="4321"/></media:community></media:group></entry></feed>"""

    def test_rss(self):
        r = O.parse_rss(self.FEED)[0]
        v = O.normalize(r)
        self.assertEqual((v["channel"], v["video_id"], v["views"], v["duration"]), ("Chan", "v1", 4321, None))
        self.assertEqual(O.fmt_of(v), "unknown")


class CLI(unittest.TestCase):
    def run_cli(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = O.main(argv)
        return code, buf.getvalue()

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "in.json")
            rows = [{"channel": "A", "video_id": f"a{i}", "title": "t", "views": 1000, "published": f"2026-0{1 + i // 4}-1{i % 4}",
                     "duration": 600} for i in range(9)] + [{"channel": "A", "video_id": "x", "title": "big", "views": 3600,
                                                              "published": "2026-03-20", "duration": 600}]
            with open(p, "w") as fh: json.dump({"videos": rows}, fh)
            code, out = self.run_cli([p, "--json", "--as-of", "2026-10-30"])
            rep = json.loads(out)
            self.assertEqual((code, rep["focus"]), (0, ["x"]))
            code, out = self.run_cli([p, "--markdown", "--as-of", "2026-10-30"])
            self.assertIn("## Hypotheses (unverified", out)
            self.assertEqual(self.run_cli([p, "--bogus"])[0], 2)
            self.assertEqual(self.run_cli([os.path.join(d, "missing.json")])[0], 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
