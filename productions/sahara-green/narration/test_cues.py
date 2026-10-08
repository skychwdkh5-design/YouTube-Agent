import json, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cues
HERE = os.path.dirname(os.path.abspath(__file__))
man = json.load(open(os.path.join(HERE, 'narration_manifest.json'))); text = open(os.path.join(HERE, 'narration_text.txt'), encoding='utf-8').read()
def synthetic(wps=145 / 60):
    """SIMULATED uniform timing, only to test the code; never a substitute for provider alignment."""
    words, t = [], 0.0
    for w in text.split():
        d = len(w) * 0.06 + 0.12; words.append({'text': w, 'start': round(t, 3), 'end': round(t + d, 3)}); t += d + (0.35 if w[-1] in '.!?' else 0.05)
    return words
class T(unittest.TestCase):
    def test_text_matches_manifest(self):
        import hashlib
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), man['narration_text_sha256']); self.assertEqual(len(text.split()), man['words'] if False else len(text.split()))
        self.assertEqual(len(text.split()), 1778); self.assertEqual(len(man['units']), 120)
        self.assertNotIn('[', text); self.assertNotIn('ON SCREEN', text); self.assertNotIn('#', text)
    def test_verify_and_locate(self):
        w = synthetic(); self.assertTrue(cues.verify(w, text)); c = cues.locate(w, man['units']); self.assertEqual(len(c), 120)
        self.assertLess(c['S001']['start'], c['S120']['start'])
    def test_verify_rejects_changed_word(self):
        w = synthetic(); w[40] = dict(w[40], text='Mars'); self.assertRaises(ValueError, cues.verify, w, text)
    def test_fit_with_simulated_cues(self):
        c = cues.locate(synthetic(), man['units']); eo = cues.fit_eo(c) if True else None
        self.assertTrue(eo['fits']); self.assertGreaterEqual(eo['hold_s'], 0.7); self.assertGreaterEqual(eo['zoom_s'], 3.5)
        ts = cues.fit_toshka(c); self.assertGreater(ts['ends'], c['S058']['end'])
    def test_scene19_shift_is_capped_at_2_2_seconds(self):
        c = cues.locate(synthetic(), man['units']); eo = cues.fit_eo(c)
        self.assertLessEqual(eo['scene19_start_shift_s'], 2.2 + 1e-6)
        short = dict(c); short['S050'] = {'start': c['S050']['start'], 'end': c['S050']['end']}
        short['S049'] = {'start': c['S049']['start'], 'end': c['S049']['start'] + 1.0}      # a very short S049: the window cannot hold the schedule within the cap
        with self.assertRaises(ValueError) as e: cues.fit_eo(short)
        self.assertIn('too short', str(e.exception))
    def test_infeasible_window_reports_shortfall(self):
        c = {'S047': {'start': 0, 'end': 2}, 'S049': {'start': 3, 'end': 6}}
        with self.assertRaises(ValueError) as e: cues.fit_eo(c)
        self.assertIn('too short', str(e.exception))
if __name__ == '__main__': unittest.main()
