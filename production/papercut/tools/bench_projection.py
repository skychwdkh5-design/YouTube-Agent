#!/usr/bin/env python3
"""Render-speed comparison for the ATLAS projection: old (approved PR #56 scene code) vs new (ProjectionEngine).

  # 1) overlay only, same frames / hand path / machine (no video encode):
  python3 -I tools/bench_projection.py overlay --old-root <checkout of main before the engine> [--pr57 projection_pr57.py]
  # 2) ATLAS composite only (old full-frame vs new region composite), same check:
  python3 -I tools/bench_projection.py host --old-root <old checkout>
  # 3) the whole approved 20 s scene with the new engine (compare with the old script run the same way):
  python3 -I tools/bench_projection.py scene --media /mnt/project-files --out new.mp4 --log new.json

Nothing here calls a paid API or uploads anything.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FPS, DUR = 30, 20.0
N = int(FPS * DUR)
PAGES = [(0.55, "EARTH TO ORION", "link"), (6.35, "NO DIRECT PATH", "blocked"), (11.35, "DARK MOON", "dark"),
         (14.50, "NASA ANIMATION", "flash"), (16.45, "RARE VIEW", "view")]


def _load(name, path, extra_path=None):
    if extra_path:
        sys.path.insert(0, str(extra_path))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def hand(t):          # the approved glove position with the idle bob (same path for every implementation)
    return 355.4 + 0.8 * math.sin(t * 1.3), 758.2 + 5.4 * math.sin(2 * math.pi * t / 2.5)


def background():
    rng = np.random.default_rng(1)
    return Image.fromarray(rng.integers(0, 255, (1080, 1920, 3), dtype=np.uint8)).convert("RGBA")


def timeit(fn, bg):
    fn(bg.copy(), 0.0)                       # warm-up (fonts, first panel) is counted separately
    t0 = time.perf_counter()
    for i in range(N):
        fn(bg.copy(), i / FPS)
    return (time.perf_counter() - t0) / N * 1000


def copy_cost(bg):
    t0 = time.perf_counter()
    for _ in range(N):
        bg.copy()
    return (time.perf_counter() - t0) / N * 1000


def engine_cues(mod, end=DUR):
    starts = [p[0] for p in PAGES] + [end]
    return [mod.ProjectionCue(starts[i], starts[i + 1], PAGES[i][1], PAGES[i][2]) for i in range(len(PAGES))]


def cmd_overlay(a):
    bg = background()
    res = {"frames": N, "frame_copy_ms": round(copy_cost(bg), 2)}
    old = _load("old_scene", Path(a.old_root) / "production/papercut/scenes/test20_projection.py",
                Path(a.old_root) / "production/papercut")
    op = old.Projection()
    res["old_pr56_scene_ms"] = round(timeit(lambda f, t: op.draw(f, t, hand(t)), bg), 2)
    for k in [k for k in list(sys.modules) if k == "papercut" or k.startswith("papercut.")]:
        del sys.modules[k]
    sys.path.insert(0, str(ROOT))
    from papercut import projection as newp
    if a.pr57:
        p57 = _load("projection_pr57", Path(a.pr57))
        e57 = p57.ProjectionEngine(engine_cues(p57, DUR + 1))
        res["pr57_engine_ms"] = round(timeit(lambda f, t: e57.render(f, t, hand(t)), bg), 2)
    ne = newp.ProjectionEngine(engine_cues(newp, DUR + 1))
    res["new_engine_ms"] = round(timeit(lambda f, t: ne.render(f, t, hand(t)), bg), 2)
    res["new_engine_cache"] = ne.stats
    print(json.dumps(res, indent=1))


def cmd_host(a):
    bg = background()
    res = {"frames": N}
    for label, root in (("old", Path(a.old_root) / "production/papercut"), ("new", ROOT)):
        for k in [k for k in list(sys.modules) if k == "papercut" or k.startswith("papercut.")]:
            del sys.modules[k]
        sys.path.insert(0, str(root))
        actor_mod = importlib.import_module("papercut.actor")
        sys.path.remove(str(root))
        act = actor_mod.Actor((1920, 1080), [actor_mod.ActorCue(0.0, DUR, "hero", 250.0, 985.0, 400, "idle",
                                                                 blinks=[2.9, 5.9], pop=False, name="hero")])
        res[f"{label}_actor_ms"] = round(timeit(lambda f, t: act.render(f, t), bg), 2)
        f = bg.copy()
        act.render(f, 3.3)
        res[f"{label}_sha_frame_3.3s"] = __import__("hashlib").sha256(f.tobytes()).hexdigest()[:16]
    res["identical_pixels"] = res["old_sha_frame_3.3s"] == res["new_sha_frame_3.3s"]
    print(json.dumps(res, indent=1))


def cmd_scene(a):
    """The approved 20 s scene (scenes/test20_projection.py) with its Projection replaced by the engine."""
    sys.path.insert(0, str(ROOT))
    from papercut.projection import ProjectionEngine, ProjectionCue
    scene = _load("test20_projection", ROOT / "scenes/test20_projection.py")
    starts = [p[0] for p in scene.PAGES] + [scene.DUR + 1]

    class EngineProjection:
        def __init__(self):
            self.e = ProjectionEngine([ProjectionCue(starts[i], starts[i + 1], p[1], p[2])
                                       for i, p in enumerate(scene.PAGES)], box=scene.PANEL)

        def draw(self, frame, t, hand_xy):
            r = self.e.render(frame, t, hand_xy)
            return None if r is None else {"page": r["page"], "box": r["box"]}

    scene.Projection = EngineProjection
    sys.argv = ["test20_projection.py", "--media", a.media, "--out", a.out, "--log", a.log]
    scene.main()


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    o = sp.add_parser("overlay"); o.add_argument("--old-root", required=True); o.add_argument("--pr57")
    h = sp.add_parser("host"); h.add_argument("--old-root", required=True)
    s = sp.add_parser("scene"); s.add_argument("--media", required=True); s.add_argument("--out", required=True)
    s.add_argument("--log", required=True)
    a = ap.parse_args()
    {"overlay": cmd_overlay, "host": cmd_host, "scene": cmd_scene}[a.cmd](a)


if __name__ == "__main__":
    main()
