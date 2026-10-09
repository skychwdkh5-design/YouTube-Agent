"""Phase D proof: a geographically accurate locator, Earth -> Arabian Peninsula -> Persian Gulf -> United Arab Emirates -> Dubai,
handed off with a GeoFocus transition to NASA documentary evidence (the ISS photograph, class A, NOT georeferenced).

Data: Natural Earth (public domain) via data/natural_earth (tools/fetch_natural_earth.sh). Evidence image: productions/dubai/visuals/iss067e003785_lrg.jpg.
Usage: python3 -m orbitalatlas.demo.geo_locator_proof OUT.mp4 [--size 1920x1080] [--frames t1,t2 --png DIR] [--qa]"""
import argparse, json, os, sys
import numpy as np
from PIL import Image
from orbitalatlas import geo as G, layers as L, sequence as SQ, transitions as TR, text as T, qa as QA

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.environ.get("ORBITALATLAS_GEODATA", os.path.join(ROOT, "data", "natural_earth"))
ISS = os.path.join(ROOT, "productions", "dubai", "visuals", "iss067e003785_lrg.jpg")
T_MAP, T_TR, T_ISS = 12.6, 1.0, 3.0            # seconds: map shot, transition overlap, evidence shot  -> total 14.6 s


def build(size=(1920, 1080)):
    gd = G.GeoData(DATA)
    land = gd.land("10m")
    ras = G.GeoRaster()
    ras.add(land, (-180, -90, 180, 90), 0.08)                      # whole Earth
    ras.add(land, (30, 8, 72, 42), 0.01)                           # Middle East
    ras.add(land, (51.0, 22.0, 57.6, 26.9), 0.0025)                # UAE + Gulf coast
    coast = gd.ring_lines(land)
    dubai = gd.place("Dubai", "United Arab Emirates")              # (lon, lat) from Natural Earth populated places
    arabia = G.polygon_centroid(G._polys(gd.feature("ne_10m_geography_regions_polys", "NAME", "ARABIAN PENINSULA")["geometry"]))
    gulf_f = gd.feature("ne_10m_geography_marine_polys", "name", "Persian Gulf"); gulf = G.polygon_centroid(G._polys(gulf_f["geometry"]))
    uae = gd.country("United Arab Emirates"); uae_main = max(uae, key=lambda p: len(p[0]))        # mainland ring = polygon with most vertices
    uae_c = G.polygon_centroid([uae_main])
    anchors = {"dubai": dubai, "gulf": gulf, "uae": uae_c, "arabia": arabia}
    keys = [dict(t=0.0, lon=22.0, lat=20.0, span_km=15000, bearing=0, arc=0.0),
            dict(t=3.4, lon=45.0, lat=24.0, span_km=4300, ease="smoother", arc=0.10),
            dict(t=6.2, lon=51.5, lat=26.3, span_km=1450, ease="smoother"),
            dict(t=8.8, lon=54.6, lat=24.3, span_km=720, ease="smoother"),
            dict(t=11.4, lon=55.12, lat=25.2, span_km=185, ease="in_out_cubic"),
            dict(t=T_MAP, lon=55.12, lat=25.2, span_km=165, ease="out_cubic")]
    cam = G.GeoCamera(keys, size, anchors=anchors)
    src = "Natural Earth 1:10M, public domain"
    k = size[1] / 1080
    ov = [
        G.Breadcrumb([("EARTH", 0.0, 3.0), ("ARABIAN PENINSULA", 3.0, 5.9), ("PERSIAN GULF", 5.9, 8.5), ("UNITED ARAB EMIRATES", 8.5, 11.2), ("DUBAI", 11.2, None)], out_t=T_MAP - T_TR + 0.1),
        L.SourceChip((0.96, 0.925), "STYLISED MAP · NATURAL EARTH 1:10M · NOT SATELLITE IMAGERY", 0.4, out_t=T_MAP - T_TR + 0.2, accent=T.THEME.cyan, anchor="right"),
        G.ScaleBar(1.5, out_t=T_MAP - T_TR + 0.1),
        G.GeoLabel(arabia, "ARABIAN PENINSULA", 2.5, px_frac=0.05, out_t=5.4, source=src + " (regions)", color=T.THEME.text),
        G.GeoFill(G._polys(gulf_f["geometry"]), (47.0, 23.5, 57.8, 31.0), T.THEME.cyan, 5.0, dur=1.2, alpha=0.30, water_only=True, res_deg=0.01, source=src + " (marine polygon; approximate extent of the named water body)", out_t=8.0),
        G.GeoLabel(gulf, "PERSIAN GULF", 5.2, px_frac=0.05, angle=-26, color=T.THEME.text, out_t=7.3, source=src + " (marine polys)"),
        G.GeoFill(uae, (51.0, 22.0, 57.6, 26.9), T.THEME.amber, 7.5, dur=1.3, alpha=0.38, anchor=dubai, max_km=520, res_deg=0.0025, source=src + " (admin-0 countries)"),
        G.GeoPolyline(np.array(uae_main[0]), 7.6, dur=1.9, color=T.THEME.amber, width=3.2, closed=False, source=src + " (admin-0 countries, mainland ring)"),
        G.GeoLabel(uae_c, "UNITED ARAB EMIRATES", 8.4, px_frac=0.031, color=T.THEME.amber, track=0.2, out_t=9.4, source=src, offset_px=(-60 * k, 70 * k)),
        G.GeoMarker(dubai, 0.7, None, color=T.THEME.amber, r=22, out_t=3.2, source=src + " (populated places): target ping"),
        G.GeoMarker(dubai, 10.6, "DUBAI", color=T.THEME.amber, label_offset=(80, -70), source=src + " (populated places)"),
    ]
    mapscene = G.GeoScene(cam, ras, coast, size=size, overlays=ov, name="geo_map", max_blur_samples=14)
    # --- evidence shot: class A, a photograph, NOT georeferenced
    iss = Image.open(ISS).convert("RGB").transpose(Image.ROTATE_270); W, H = iss.size
    chips = [L.SourceChip((0.04, 0.045), "NASA ISS ASTRONAUT PHOTOGRAPH ISS067-E-3785 · 6 APR 2022", 0.25, accent=T.THEME.cyan),
             L.SourceChip((0.04, 0.045 + 0.058), "PHOTOGRAPH, NOT SATELLITE IMAGERY · NOT GEOREGISTERED · VIEW ROTATED 90°", 0.4, accent=T.THEME.amber, px_frac=0.0145)]
    evid = L.Scene(iss, [dict(t=0, center=(W / 2, H / 2), height=H, ease="smoother"), dict(t=T_ISS, center=(1980, 1300), height=1250, ease="out_cubic")], size=size, overlays=chips, name="evidence")
    gf = np.array(cam.view(T_MAP).pt(*dubai)[:2], float).ravel() / np.array(size)
    seq = SQ.Sequence([SQ.Shot(mapscene, T_MAP), SQ.Shot(evid, T_ISS)], [TR.GeoFocus((float(gf[0]), float(gf[1])), radius=0.15, duration=T_TR, a_zoom=1.25, b_zoom=1.2)])
    return seq, dict(map=mapscene, evidence=evid, data=dict(dubai=dubai, arabia=arabia, gulf=gulf, uae=uae_c))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--size", default="1920x1080"); ap.add_argument("--frames"); ap.add_argument("--png"); ap.add_argument("--qa", action="store_true")
    a = ap.parse_args(); size = tuple(int(x) for x in a.size.split("x")); seq, parts = build(size)
    print("duration", round(seq.duration, 2), "problems", seq.problems, "data", {k: tuple(round(float(x), 3) for x in v) for k, v in parts["data"].items()})
    if a.frames:
        os.makedirs(a.png, exist_ok=True)
        for t in [float(x) for x in a.frames.split(",")]: seq.render(t).save(os.path.join(a.png, f"g_{t:05.2f}.png"))
        sys.exit(0)
    n = SQ.render_video(seq, a.out, fps=30); print("frames", n)
    if a.qa:
        sched = seq.schedule(); r = QA.run_video(a.out, QA.QAConfig(fps=30.0), schedule=sched, problems=seq.problems); print(json.dumps(r, indent=1))
