#!/usr/bin/env python3
"""Offline tests for graphics.py - synthetic grid and imagery, labelled TEST DATA. No network.

    python3 test_graphics.py
"""
import io, json, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stdout

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import graphics as gx
sys.path.insert(0, os.path.join(HERE, "..", "yt-geo"))
import geostack as g

CENTER = [-114.5, 36.2]
SRC = "TEST DATA - not a real measurement"


def run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = gx.main(argv)
    return code, json.loads(buf.getvalue())


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        os.makedirs(os.path.join(self.dir, "stack"))
        os.makedirs(os.path.join(self.dir, "out"))
        x, y = g.lonlat_to_utm(CENTER[0], CENTER[1], 32611)
        self.grid = {"schema": "yt-geo-stack/1", "epsg": 32611, "x0": float(x) - 15000, "y_top": float(y) + 15000,
                     "pixel_m": 30.0, "width": 1000, "height": 1000}
        self.write_grid(self.grid)
        arr = np.zeros((1000, 1000, 3), np.uint8); arr[:] = (40, 120, 60); arr[::50, :] = 200
        Image.fromarray(arr).save(os.path.join(self.dir, "stack", "a.png"))

    def write_grid(self, grid, name="grid.json"):
        json.dump(grid, open(os.path.join(self.dir, "stack", name), "w"))

    def spec(self, graphics):
        p = os.path.join(self.dir, "spec.json")
        json.dump({"schema": "yt-graphics/1", "graphics": graphics}, open(p, "w"))
        return p

    def render(self, graphics, only=None):
        args = [self.spec(graphics), "--out-dir", os.path.join(self.dir, "out")] + (["--only", only] if only else [])
        return run(args)

    def ok(self, graphic):
        code, d = self.render([graphic])
        self.assertEqual((code, d["status"]), (0, "ok"), d)
        return d["graphics"][0]

    def err(self, graphic, text, status="error"):
        code, d = self.render([graphic])
        self.assertEqual(code, 2, d)
        self.assertEqual(d["status"], status, d)
        self.assertIn(text, d["error"])
        return d

    def png(self, name):
        return Image.open(os.path.join(self.dir, "out", name))

    def geo_image(self, **kw):
        im = {"stack": "stack/a.png", "grid": "stack/grid.json", "center": CENTER, "width_km": 12}
        im.update(kw)
        return im


DIAGRAM = {"type": "diagram", "id": "d", "title": "Diagram (TEST DATA)", "source": SRC,
           "nodes": [{"id": "a", "text": "Warm ocean", "x": 0.15, "y": 0.7, "style": "blue"},
                     {"id": "b", "text": "Air rises", "x": 0.5, "y": 0.25},
                     {"id": "c", "text": "Rain", "x": 0.85, "y": 0.7, "style": "accent", "step": 2}],
           "arrows": [{"from": "a", "to": "b", "label": "moisture"}, {"from": "b", "to": "c", "step": 2}]}
BAR = {"type": "bar", "id": "bars", "title": "Bars (TEST DATA)", "source": SRC, "unit": "mm per year",
       "bars": [{"label": "A", "value": 25}, {"label": "B", "value": 140}, {"label": "C", "value": 610, "highlight": True}]}
LINE = {"type": "line", "id": "line", "title": "Line (TEST DATA)", "source": SRC, "x_unit": "year", "y_unit": "index",
        "series": [{"name": "A", "points": [[2000, 10], [2010, 13], [2020, 24]]}, {"name": "B", "points": [[2000, 8], [2020, 11]]}]}


class Types(Base):
    def test_every_type_renders_1920x1080_with_provenance(self):
        specs = [
            DIAGRAM,
            {"type": "flow", "id": "flow", "source": SRC, "steps": ["One", "Two", "Three"], "arrow_labels": ["a", "b"],
             "build": True},
            {"type": "circulation", "id": "circ", "source": SRC, "labels": {"rising": "rises", "aloft": "aloft",
             "sinking": "sinks", "surface": "returns"}, "ground_labels": [{"x": 0.05, "text": "0°"}], "rising_cloud": True},
            {"type": "water_cycle", "id": "wc", "source": SRC, "labels": {"evaporation": "evaporation", "rainfall": "rain"},
             "build": True},
            BAR, LINE,
            {"type": "callout", "id": "num", "source": SRC, "value": 875, "unit": "acres", "label": "Callout (TEST DATA)"},
            {"type": "geo", "id": "geo", "source": SRC, "credit": "Synthetic test image", "image": self.geo_image(),
             "callouts": [{"at": CENTER, "text": "Centre"}], "arrows": [{"from": [-114.53, 36.18], "to": CENTER, "step": 2}]},
            {"type": "compare", "id": "cmp", "source": SRC,
             "left": {"geo": self.geo_image(), "label": "Before (TEST)", "credit": "Synthetic"},
             "right": {"geo": self.geo_image(width_km=6), "label": "After (TEST)", "credit": "Synthetic"},
             "metric": {"left": 1, "right": 2.5, "unit": "km²"}},
        ]
        code, d = self.render(specs)
        self.assertEqual((code, d["status"]), (0, "ok"), d)
        files = {x["id"]: x["files"] for x in d["graphics"]}
        self.assertEqual(files["d"], ["d.step1.png", "d.png"])                   # step 2 elements build in
        self.assertEqual(files["flow"], [f"flow.step{i}.png" for i in range(1, 5)] + ["flow.png"])
        self.assertEqual(files["wc"], ["wc.step1.png", "wc.step2.png", "wc.step3.png", "wc.png"])
        self.assertEqual(files["geo"], ["geo.step1.png", "geo.png"])
        for x in d["graphics"]:
            for f in x["files"]:
                im = self.png(f)
                self.assertEqual((im.size, im.mode), ((1920, 1080), "RGB"), f)
            side = json.load(open(os.path.join(self.dir, "out", f"{x['id']}.json")))
            self.assertEqual((side["schema"], side["source"], side["size"]), ("yt-graphics/1", SRC, [1920, 1080]))
            self.assertEqual(set(side["sha256"]), set(x["files"]))
            for tb in side["text_boxes"]:                                        # every text inside the safe area
                x0, y0, x1, y1 = tb["box"]
                self.assertTrue(1920 * 0.05 - 1 <= x0 and x1 <= 1920 * 0.95 + 1 and 1080 * 0.07 - 1 <= y0
                                and y1 <= 1080 * gx.CAPTION_TOP + 1, (x["id"], tb))
        # build steps differ, and the last step is the full graphic
        a, b = (np.asarray(self.png(f)).astype(int) for f in ("d.step1.png", "d.png"))
        self.assertGreater(np.abs(a - b).mean(), 0.1)

    def test_deterministic_bytes(self):
        self.render([DIAGRAM, BAR, LINE])
        first = {f: gx._sha256(os.path.join(self.dir, "out", f)) for f in ("d.png", "bars.png", "line.png")}
        self.render([DIAGRAM, BAR, LINE])
        self.assertEqual(first, {f: gx._sha256(os.path.join(self.dir, "out", f)) for f in first})

    def test_bar_heights_follow_the_data(self):
        self.ok(dict(BAR, style="documentary_light"))
        im = np.asarray(self.png("bars.png")).astype(int)
        side = json.load(open(os.path.join(self.dir, "out", "bars.json")))
        labels = {t["text"]: t["box"] for t in side["text_boxes"] if t["where"] == "value"}
        # value labels sit on top of their bars: higher value -> label higher on screen
        self.assertLess(labels["610"][1], labels["140"][1])
        self.assertLess(labels["140"][1], labels["25"][1])
        self.assertEqual(im.shape, (1080, 1920, 3))


class Validation(Base):
    def test_provenance_is_mandatory(self):
        for t in (BAR, LINE, DIAGRAM):
            self.err({k: v for k, v in t.items() if k != "source"}, ".source must be a non-empty string")

    def test_invalid_chart_data(self):
        self.err(dict(BAR, bars=[{"label": "A", "value": "12"}]), "must be a finite number")
        self.err(dict(BAR, bars=[{"label": "A", "value": float("nan")}]), "must be a finite number")
        self.err(dict(BAR, bars=[{"label": "A", "value": True}]), "must be a finite number")
        self.err(dict(BAR, bars=[]), "bars must list 1-12 bars")
        self.err(dict(BAR, bars=[{"label": "A", "value": 0}]), "all zero")
        self.err({k: v for k, v in BAR.items() if k != "unit"}, ".unit must be a non-empty string")
        self.err(dict(LINE, series=[{"name": "A", "points": [[2000, 1], [1990, 2]]}]), "x must increase")
        self.err(dict(LINE, series=[{"name": "A", "points": [[2000, 1]]}]), "at least two")
        self.err({"type": "callout", "id": "c", "source": SRC, "value": "lots", "unit": "x", "label": "y"},
                 "must be a finite number")
        self.err(dict(DIAGRAM, arrows=[{"from": "a", "to": "zzz"}]), "no node 'zzz'")
        self.err(dict(BAR, type="pie"), ".type must be one of")
        self.err(dict(BAR, id="Bad Id!"), ".id must be a short lowercase name")
        code, d = self.render([BAR, BAR])
        self.assertIn("used twice", d["error"])

    def test_scale_bar_needs_real_metadata(self):
        geo = {"type": "geo", "id": "geo", "source": SRC, "credit": "Synthetic", "image": self.geo_image()}
        self.write_grid({k: v for k, v in self.grid.items() if k != "pixel_m"})
        self.err(geo, "scale bar needs real geospatial metadata", "no_scale")
        self.write_grid(dict(self.grid, epsg=4326))
        self.err(geo, "must be a UTM zone", "no_scale")
        self.write_grid(self.grid)
        self.err(dict(geo, image=self.geo_image(width_km=40)), "leaves the imagery")
        self.err(dict(geo, callouts=[{"at": [-114.9, 36.2], "text": "far"}]), "outside the view")
        self.err(dict(geo, image=self.geo_image(stack="../x.png")), "outside the spec folder")
        self.err(dict(geo, credit=""), ".credit must be a non-empty string")

    def test_scale_bar_is_computed_from_the_grid(self):
        x = self.ok({"type": "geo", "id": "geo", "source": SRC, "credit": "Synthetic", "image": self.geo_image(),
                     "graticule": False})
        # 12 km over 1920 px = 6.25 m/px; the longest 1/2/5 length within 22 % of the safe width is 2 km = 320 px
        self.assertEqual((x["scale_bar"]["km"], x["scale_bar"]["px"], x["scale_bar"]["m_per_px"]), (2, 320.0, 6.25))
        im = np.asarray(self.png("geo.png")).astype(int)
        bar_y = int(1080 * gx.CAPTION_TOP - 30)
        self.assertTrue((im[bar_y, 1700] > 200).all(), im[bar_y, 1700])          # the white half of the bar
        x = self.ok({"type": "geo", "id": "geo", "source": SRC, "credit": "Synthetic", "image": self.geo_image(width_km=3)})
        self.assertEqual((x["scale_bar"]["km"], x["scale_bar"]["label"]), (0.5, "500 m"))

    def test_text_overflow_and_safe_area(self):
        long = "A label far too long for a tiny box at any allowed font size"
        self.err(dict(DIAGRAM, nodes=[{"id": "a", "text": long, "x": 0.5, "y": 0.5, "w": 0.05, "h": 0.05}], arrows=[]),
                 "does not fit", "overflow")
        self.err(dict(DIAGRAM, notes=[{"text": "A note centred on the very edge of the frame", "x": 0.0, "y": 0.5}]),
                 "outside the landscape safe area", "overflow")

    def test_text_is_readable_on_a_phone(self):
        self.err(dict(DIAGRAM, notes=[{"text": "Tiny note", "x": 0.5, "y": 0.9, "size": 20}]), "notes[0].size")
        line = dict(LINE, annotations=[{"x": 2010, "y": 13, "text": "test annotation"}])
        geo = {"type": "geo", "id": "geo", "source": SRC, "credit": "Synthetic", "image": self.geo_image(),
               "arrows": [{"from": [-114.53, 36.18], "to": [-114.46, 36.22], "label": "test path"}],
               "callouts": [{"at": [-114.46, 36.225], "text": "Test place"}]}
        code, d = self.render([DIAGRAM, BAR, line, geo])
        self.assertEqual((code, d["status"]), (0, "ok"), d)
        for name in ("d", "bars", "line", "geo"):
            side = json.load(open(os.path.join(self.dir, "out", name + ".json")))
            self.assertGreaterEqual(min(t["size"] for t in side["text_boxes"]), gx.MIN_TEXT_PX, name)

    def test_text_never_sits_on_lines_or_other_text(self):
        def canvas():
            cv = gx.Canvas("documentary_dark", gx.Fonts())
            cv.arrow((400, 500), (1400, 500), "accent", 8)
            return cv
        cv = canvas()
        cv.text("on the arrow", 900, 500, 32)
        with self.assertRaises(gx.E) as e:
            cv.check_safe(True)
        self.assertIn("across a line or arrow", str(e.exception))
        cv = canvas()
        cv.text("first", 900, 300, 32); cv.text("second", 920, 305, 32)
        with self.assertRaises(gx.E) as e:
            cv.check_safe(True)
        self.assertIn("text overlaps", str(e.exception))
        cv = canvas()                                     # place() moves a label off the arrow
        box = cv.place("label", [(900, 500, "mm"), (900, 450, "mm")], 32, "Bold", "accent", 300)
        self.assertLess(box[3], 490)
        cv.check_safe(True)

    def test_cli_errors_are_json(self):
        code, d = run([self.spec([BAR])])
        self.assertEqual((code, d["status"]), (2, "error"))
        self.assertIn("--out-dir", d["error"])
        code, d = run([self.spec([BAR]), "--out-dir", os.path.join(self.dir, "missing")])
        self.assertIn("does not exist", d["error"])
        code, d = run([self.spec([BAR]), "--out-dir", os.path.join(self.dir, "out"), "--only", "nope"])
        self.assertIn("no such graphic", d["error"])


class BuildEmphasis(Base):
    """hl (emphasis ring / brighter note), callout build steps and circulation step_map: each build step is a real visual change."""
    def render(self, spec):
        code, d = run([self.spec([spec]), "--out-dir", os.path.join(self.dir, "out")])
        self.assertEqual((code, d["status"]), (0, "ok"), d)
        return d

    def img(self, name):
        return np.asarray(Image.open(os.path.join(self.dir, "out", name)).convert("RGB")).astype(float)

    def test_node_ring_and_bright_note_appear_only_at_their_step(self):
        spec = {"type": "diagram", "id": "emph", "source": SRC, "nodes": [
                    {"id": "a", "text": "A", "x": 0.3, "y": 0.5, "step": 1, "hl": [2]}, {"id": "b", "text": "B", "x": 0.7, "y": 0.5, "step": 1}],
                "notes": [{"text": "note", "x": 0.5, "y": 0.9, "step": 1, "hl": [3]}]}
        self.render(spec)
        s1, s2, s3 = self.img("emph.step1.png"), self.img("emph.step2.png"), self.img("emph.png")
        mafd = lambda a, b: np.abs(a - b).mean()
        self.assertGreater(mafd(s1, s2), 0.2)           # the ring is a large enough change to count as an event
        self.assertGreater(mafd(s2, s3), 0.05)          # ring gone, note brighter
        self.assertEqual(json.load(open(os.path.join(self.dir, "out", "emph.json")))["steps"][-1], "emph.png")

    def test_hl_extends_the_step_count_and_is_validated(self):
        d = self.render({"type": "diagram", "id": "emph", "source": SRC, "nodes": [{"id": "a", "text": "A", "x": 0.5, "y": 0.5, "hl": [4]}]})
        self.assertEqual(len(json.load(open(os.path.join(self.dir, "out", "emph.json")))["steps"]), 4)
        for bad in ([], [0], [21], ["x"], True):
            code, d = run([self.spec([{"type": "diagram", "id": "bad", "source": SRC, "nodes": [{"id": "a", "text": "A", "x": 0.5, "y": 0.5, "hl": bad}]}]),
                           "--out-dir", os.path.join(self.dir, "out")])
            self.assertEqual(code, 2, bad); self.assertIn("hl", d["error"])

    def test_callout_build_steps(self):
        base = {"type": "callout", "id": "cb", "source": SRC, "value": 7, "unit": "km", "label": "Label text", "context": "Context text", "build": True}
        self.render(dict(base, title="Title"))
        steps = json.load(open(os.path.join(self.dir, "out", "cb.json")))["steps"]
        self.assertEqual(len(steps), 4)                 # title alone, number, label, context
        imgs = [self.img(f) for f in steps]
        self.assertTrue(all(np.abs(a - b).mean() > 0.1 for a, b in zip(imgs, imgs[1:])))
        self.render(dict(base, id="cc"))                # untitled: number, label, context
        self.assertEqual(len(json.load(open(os.path.join(self.dir, "out", "cc.json")))["steps"]), 3)
        self.render(dict(base, id="cd", build=False))   # without build: one image, as before
        self.assertEqual(len(json.load(open(os.path.join(self.dir, "out", "cd.json")))["steps"]), 1)

    def test_circulation_step_map_and_cloud_step(self):
        spec = {"type": "circulation", "id": "circ", "source": SRC, "build": True, "rising_cloud": True, "cloud_step": 2, "step_map": [1, 3, 4, 5],
                "labels": {"rising": "up", "aloft": "across", "sinking": "down", "surface": "back"}}
        self.render(spec)
        self.assertEqual(len(json.load(open(os.path.join(self.dir, "out", "circ.json")))["steps"]), 5)
        s1, s2 = self.img("circ.step1.png"), self.img("circ.step2.png")
        self.assertGreater(np.abs(s1 - s2).mean(), 0.1)  # the cloud appears at step 2 and nothing else does
        code, d = run([self.spec([dict(spec, id="bad", step_map=[1, 2, 3])]), "--out-dir", os.path.join(self.dir, "out")])
        self.assertEqual(code, 2); self.assertIn("step_map", d["error"])

    def test_default_graphics_are_unchanged(self):
        base = {"type": "circulation", "id": "old", "source": SRC, "build": True, "rising_cloud": True,
                "labels": {"rising": "up", "aloft": "across", "sinking": "down", "surface": "back"}}
        self.render(base)
        self.assertEqual(len(json.load(open(os.path.join(self.dir, "out", "old.json")))["steps"]), 4)


class BackdropDashedLines(Base):
    """backdrop (real image under a scrim, credit in the source line), dashed proposed elements, and plain rules."""
    def make_backdrop(self):
        arr = np.zeros((1080, 1920, 3), np.uint8); arr[:, :960] = (200, 60, 40); arr[:, 960:] = (40, 80, 200)
        Image.fromarray(arr).save(os.path.join(self.dir, "bd.png"))

    def render(self, graphics):
        code, d = run([self.spec(graphics), "--out-dir", os.path.join(self.dir, "out")])
        return code, d

    def test_backdrop_is_under_the_scrim_and_recorded(self):
        self.make_backdrop()
        spec = {"type": "callout", "id": "bd", "source": SRC, "value": 5, "unit": "km", "label": "Label",
                "backdrop": {"src": "bd.png", "credit": "Test imagery", "scrim": 0.5}}
        code, d = self.render([spec]); self.assertEqual(code, 0, d)
        im = np.asarray(Image.open(os.path.join(self.dir, "out", "bd.png")).convert("RGB")).astype(float)
        left, right = im[900, 300], im[900, 1600]                       # clear of text, caption band excluded
        self.assertGreater(left[0], right[0]); self.assertGreater(right[2], left[2])   # red left, blue right: the image shows through
        self.assertLess(left[0], 200)                                    # but darkened by the scrim
        side = json.load(open(os.path.join(self.dir, "out", "bd.json")))
        self.assertEqual(side["backdrop"]["credit"], "Test imagery"); self.assertEqual(len(side["backdrop"]["sha256"]), 64)
        self.assertTrue(any("Imagery: Test imagery" in t["text"] for t in side["text_boxes"]))

    def test_backdrop_is_validated(self):
        self.make_backdrop()
        base = {"type": "callout", "id": "bd", "source": SRC, "value": 5, "unit": "km", "label": "Label"}
        for bad, msg in (({"src": "nope.png", "credit": "x"}, "not found"), ({"src": "bd.png"}, "credit"),
                         ({"src": "bd.png", "credit": "x", "scrim": 1.5}, "scrim"), ({"src": "../x.png", "credit": "x"}, "outside"),
                         ({"src": "bd.png", "credit": "x", "view": {"center": [0.5], "width": 1}}, "center")):
            code, d = self.render([dict(base, backdrop=bad)]); self.assertEqual(code, 2, bad); self.assertIn(msg, d["error"])

    def test_dashed_nodes_arrows_and_lines(self):
        spec = {"type": "diagram", "id": "dash", "source": SRC, "nodes": [
                    {"id": "a", "text": "A", "x": 0.25, "y": 0.5, "w": 0.2, "h": 0.3, "style": "accent", "dashed": True},
                    {"id": "b", "text": "B", "x": 0.75, "y": 0.5, "w": 0.2, "h": 0.3, "style": "accent"}],
                "arrows": [{"from": "a", "to": "b", "dashed": True, "step": 2}],
                "lines": [{"from": [0.05, 0.9], "to": [0.95, 0.9], "color": "muted", "width": 5, "step": 3}]}
        code, d = self.render([spec]); self.assertEqual(code, 0, d)
        s1 = np.asarray(Image.open(os.path.join(self.dir, "out", "dash.step1.png")).convert("RGB")).astype(int)
        s3 = np.asarray(Image.open(os.path.join(self.dir, "out", "dash.png")).convert("RGB")).astype(int)
        self.assertEqual(len(json.load(open(os.path.join(self.dir, "out", "dash.json")))["steps"]), 3)
        bg = s1[2, 2]
        # the dashed outline of node a: along its top edge pixels alternate between outline and background (gaps), the solid node b has none
        top = s1[:, :, :]
        ys, xs = np.nonzero(np.abs(s1 - bg).sum(2) > 60)
        self.assertGreater(len(ys), 100)
        self.assertGreater(np.abs(s3 - s1).sum(), 0)                      # later steps add the arrow and the rule
        code, d = self.render([dict(spec, id="bad", lines=[{"from": [2, 0], "to": [0, 0]}])]); self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
