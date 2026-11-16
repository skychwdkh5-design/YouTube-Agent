"""Guard tests for the paper-cut host layer:  python3 -I tests/test_host.py"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image  # noqa: E402

from papercut import host as Hm  # noqa: E402
from papercut.qa import check_assets  # noqa: E402


def expect_error(fn, text):
    try:
        fn()
    except Hm.HostError as e:
        assert text in str(e), e
        return
    raise AssertionError(f"expected HostError containing {text!r}")


def main():
    a = check_assets()
    assert all(v["pass"] for v in a.values()), a
    # experimental layers and foreign art are refused
    expect_error(lambda: Hm.load_hero(Path("/x/experimental_layers/head.png")), "forbidden")
    expect_error(lambda: Hm.load_hero(Hm.SOURCE_PATH), "not the approved hero")
    # size gate and preset whitelist
    expect_error(lambda: Hm.HostLayer((1920, 1080), [Hm.Cue(0, 1, "idle", 500, 900, width=600)]), "12-24")
    expect_error(lambda: Hm.HostLayer((1920, 1080), [Hm.Cue(0, 1, "wave_arm", 500, 900, width=300)]), "unknown preset")
    # motion stays inside the QA gates for every preset over a long window
    for name in Hm.LOOP_PRESETS:
        h = Hm.HostLayer((1920, 1080), [Hm.Cue(0, 20, name, 960, 900, width=300)])
        for i in range(600):
            s = h.state(i / 30)
            assert abs(s["roll_deg"]) <= Hm.GATE_ROLL_DEG
            assert abs(s["scale"] - 1) * 100 <= Hm.GATE_SCALE_PCT
            assert abs(s["bob_px"]) <= Hm.GATE_BOB_PX_AT_540 * 2
    # entrance starts fully off-frame and lands on the cue position
    h = Hm.HostLayer((1920, 1080), [Hm.Cue(0, 5, "listen", 300, 1000, width=300, enter="left")])
    fr = Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))
    info0 = h.render(fr, 0.0)
    assert info0["bbox"] is None or info0["bbox"][2] <= 0, info0
    s = h.state(1.0)
    assert math.isclose(s["x"], 300) and s["phase"] == "hold"
    # rendering is whole-cutout only: alpha mass is preserved within resampling tolerance
    fr = Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))
    info = h.render(fr, 2.0)
    x0, y0, x1, y1 = info["bbox"]
    assert 0 <= x0 < x1 <= 1920 and 0 <= y0 < y1 <= 1080
    # actor: open/open face is the untouched hero; every sheet cutout matches its manifest checksum
    import json
    import numpy as np
    from papercut import actor as A
    faces = A.build_face_variants(Hm.load_hero())
    assert np.array_equal(np.asarray(faces[("open", "open")]), np.asarray(Hm.load_hero()))
    man = json.loads((A.CUT_DIR / "MANIFEST.json").read_text())
    for name in man["items"]:
        A.load_cutout(name)
    try:
        A.Actor((1920, 1080), [A.ActorCue(0, 1, "pose_point", 300, 900, 330, talk=[(0, 1)])])
        raise AssertionError("talk on a sheet pose must be refused")
    except Hm.HostError:
        pass
    print("OK: paper-cut host + actor guards")


if __name__ == "__main__":
    main()
