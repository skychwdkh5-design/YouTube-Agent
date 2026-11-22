"""Owner rule 2026-11-22: transition sounds and hits stay well under the narration on every release (both channels)."""
import importlib.util, os, tempfile, unittest, wave

try:                                   # the ops workflow runs the stdlib tests only; the render machine has numpy + PIL
    import numpy as np
    HERE = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("motion", os.path.join(HERE, "..", "motion.py"))
    motion = importlib.util.module_from_spec(spec); spec.loader.exec_module(motion)
except ImportError:                    # pragma: no cover
    motion = None


@unittest.skipIf(motion is None, "numpy/PIL not installed (render-machine test)")
class MixTest(unittest.TestCase):
    def test_effects_bed_peaks_well_below_full_scale(self):
        class Hero: t0 = 3.0
        cuts = [{"t": t, "kind": k} for t, k in ((2.0, "whip_l"), (5.0, "whip_r"), (8.0, "zoom"), (11.0, "flash"), (14.0, "glitch"))]
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "fx.wav")
            motion.sound_layer(p, 16.0, cuts, [Hero()], music=True)
            with wave.open(p) as f:
                x = np.frombuffer(f.readframes(f.getnframes()), "<i2").astype(np.float32) / 32768
        peak_db = 20 * np.log10(np.abs(x).max() + 1e-9)
        self.assertLess(peak_db, -14.0, "effects must stay far below the voice (narration peaks around -4 dBFS)")

    def test_effects_are_ducked_under_the_voice(self):
        self.assertIn("sidechaincompress", motion.DUCK)


if __name__ == "__main__":
    unittest.main()
