"""segcache: stable keys, cache hits, and stream-copy assembly of equal-parameter segments (needs ffmpeg)"""
import os, shutil, subprocess, tempfile, unittest
from orbitalatlas import segcache as SC


def clip(path, color, n=15):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c={color}:s=320x180:r=30", "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", path], check=True)


class TestSegCache(unittest.TestCase):
    def test_key_changes_with_every_part_and_is_stable(self):
        self.assertEqual(SC.sha("a", 1), SC.sha("a", 1)); self.assertNotEqual(SC.sha("a", 1), SC.sha("a", 2)); self.assertNotEqual(SC.sha("ab", "c"), SC.sha("a", "bc"))

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg missing")
    def test_have_and_assemble_copy(self):
        d = tempfile.mkdtemp()
        try:
            k1, k2 = SC.sha("one"), SC.sha("two"); self.assertIsNone(SC.have(d, k1))
            clip(SC.segment_path(d, k1), "red"); clip(SC.segment_path(d, k2), "blue"); self.assertTrue(SC.have(d, k1))
            out = os.path.join(d, "o.mp4"); SC.assemble([SC.have(d, k1), SC.have(d, k2)], out)
            n = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
            self.assertEqual(n, "30")
        finally: shutil.rmtree(d)

    def test_source_of_function_is_part_of_the_key(self):
        def f(): return 1
        def g(): return 2
        self.assertNotEqual(SC.source(f), SC.source(g))


if __name__ == "__main__":
    unittest.main()
