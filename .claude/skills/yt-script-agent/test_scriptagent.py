#!/usr/bin/env python3
import itertools, json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scriptagent as sa


def words(n, seed=0):
    """n distinct alphabetic pseudo-words (no digits, no repetition)."""
    al = "abcdefghijklmnop"
    it = itertools.product(al, repeat=4)
    return [("".join(w)) for w in itertools.islice(it, seed, seed + n)]


def sent(n, seed):
    return " ".join(words(n, seed)).capitalize() + "."


CLAIMS = [{"id": "C1", "tier": "original", "text": "t", "confidence": "high", "attribution": "A", "date": "2026-01-01", "url": "https://x"},
          {"id": "C2", "tier": "media", "text": "t", "confidence": "medium", "wording": "reported", "attribution": "B", "date": "2026-01-01", "url": "https://x"},
          {"id": "C3", "tier": "media", "text": "t", "confidence": "low", "wording": "reported", "attribution": "B", "date": "2026-01-01", "url": "https://x"},
          {"id": "C4", "tier": "observation", "text": "t", "confidence": "high", "group": "shows", "evidence": "e.json", "must_cover": True},
          {"id": "C5", "tier": "hypothesis", "text": "t may be x", "confidence": "low"}]


def episode(d, claims=CLAIMS):
    os.makedirs(os.path.join(d, "research"), exist_ok=True)
    json.dump({"schema": "yt-facts/1", "claims": claims}, open(os.path.join(d, "claims.json"), "w"))
    open(os.path.join(d, "e.json"), "w").write("{}")


def script(parts):
    out = []
    for cid, title, body in parts:
        out.append(f"## {cid}: {title}\n{body}\n")
    return "\n".join(out)


def good_script(n_words=950):
    per = n_words // 7
    sk = ["hook", "promise", "plan", "shows", "limits", "close"]
    body = {
        "hook": sent(30, 0) + " Saudi plan {C1}",
        "promise": sent(per, 100) + " It was announced. {C1}",
        "plan": sent(per, 400) + " Outlet reported it. {C2}",
        "shows": sent(per * 2, 900) + " We see it. {C4}",
        "limits": "We cannot say. {L} " + sent(per // 2, 2000) + " It may be x. {C5}",
        "close": sent(per, 3000),
    }
    return body


class Brief(unittest.TestCase):
    def test_skeleton_and_excluded_low_claims(self):
        with tempfile.TemporaryDirectory() as d:
            episode(d)
            b = sa.brief(d)
            self.assertEqual([c["id"] for c in b["chapters"]], ["hook", "promise", "plan", "shows", "limits", "close"])
            self.assertEqual(b["do_not_use"], ["C3"])
            self.assertNotIn("C3", b["claims"])
            self.assertTrue(os.path.exists(os.path.join(d, "tasks", "script.md")))
            self.assertEqual(b["target_words"], [882, 1323])

    def test_insufficient_facts_is_stated(self):
        with tempfile.TemporaryDirectory() as d:
            episode(d, CLAIMS[:2])
            b = sa.brief(d)
            self.assertTrue(b["insufficient_facts"])


EXTRA = [{"id": f"C{i}", "tier": "observation", "text": "t", "confidence": "medium", "group": "shows", "evidence": "e.json"} for i in range(6, 18)]


class Validate(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        episode(self.d, CLAIMS + EXTRA)
        sa.brief(self.d)

    def write(self, body):
        parts = [(k, k.title(), v) for k, v in body.items()]
        open(os.path.join(self.d, "script.md"), "w").write(script(parts))

    def test_missing_script_needs_agent(self):
        self.assertEqual(sa.validate(self.d)["status"], "needs_agent")

    def test_too_short_blocked(self):
        b = good_script(300)
        self.write(b)
        r = sa.validate(self.d)
        self.assertEqual(r["status"], "blocked")
        self.assertTrue(any("under 6 minutes" in p for p in r["problems"]))

    def test_padding_by_repetition_blocked(self):
        b = good_script(1150)
        b["close"] = (sent(40, 7000) + " ") * 8                 # the same sentence again and again
        self.write(b)
        r = sa.validate(self.d)
        self.assertTrue(any("repetition" in p for p in r["problems"]), r["problems"])

    def test_chapter_mismatch_blocked(self):
        b = good_script(1150)
        b.pop("promise")
        self.write(b)
        self.assertTrue(any("do not match" in p for p in sa.validate(self.d)["problems"]))

    def test_must_cover_and_low_claim(self):
        b = good_script(1150)
        b["shows"] = b["shows"].replace("{C4}", "")
        b["plan"] += " Another thing was reported. {C3}"
        self.write(b)
        p = " ".join(sa.validate(self.d)["problems"])
        self.assertIn("must-cover claim C4", p)
        self.assertIn("C3", p)

    def test_good_script_passes(self):
        self.write(good_script(1150))
        r = sa.validate(self.d)
        self.assertEqual(r["status"], "ok", r["problems"])
        self.assertGreaterEqual(r["minutes"], 6.0)

    def test_overlong_blocked(self):
        self.write(good_script(1800))
        self.assertTrue(any("over 9 minutes" in p for p in sa.validate(self.d)["problems"]))


if __name__ == "__main__":
    unittest.main()
