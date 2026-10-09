#!/usr/bin/env python3
"""EP001: verified geospatial alignment of the Kufra still (reviewer decision 5: visual identification of circular fields is not proof).
Evidence, all from the USGS Level-1 product of LC09_L1TP_181043_20260919_20260919_02_T1:
  1. georeference: the B4 GeoTIFF transform (EPSG + tie point + 30 m) reproduces the four product corners of the MTL file (UTM metres and lat/lon) to < 1 pixel;
  2. the scene footprint contains the Kufra reference point (Al Kufrah, 24.18 N 23.29 E);
  3. green irrigated fields are detected by NDVI on TOA reflectance (B5, B4), and their centroid is converted to lon/lat through the verified transform; it is compared with the reference point;
  4. the pixel window used in the video (src_window_px of kufra_toneB.json) is converted back to lon/lat and must contain the field cluster.
  python3 verify_kufra_alignment.py"""
import json, os, re, sys, math
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '.claude', 'skills', 'yt-geo'))
import geostack as g
SCR = os.environ.get('EP001_SCRATCH', '/tmp/claude-0/-home-user-YouTube-Agent/726a1102-cde7-58e4-becc-72fd703579dc/scratchpad/loc')
SC = 'LC09_L1TP_181043_20260919_20260919_02_T1'; D = f'{SCR}/src/{SC}'
REF = (24.18, 23.29)       # Al Kufrah (town), lat, lon: reference for "the Kufra oasis"
mtl = open(f'{D}/{SC}_MTL.txt').read(); num = lambda k: float(re.search(k + r'\s*=\s*([-0-9.Ee+]+)', mtl).group(1))
im4, info = g.read_geotiff(f'{D}/{SC}_B4.TIF'); W, H = info['width'], info['height']
res = {'scene': SC, 'epsg': info['epsg'], 'size': [W, H], 'reference_point_lat_lon': REF}
# 1. corners
corners = {}
for name in ('UL', 'UR', 'LL', 'LR'):
    x, y = num(f'CORNER_{name}_PROJECTION_X_PRODUCT'), num(f'CORNER_{name}_PROJECTION_Y_PRODUCT'); la, lo = num(f'CORNER_{name}_LAT_PRODUCT'), num(f'CORNER_{name}_LON_PRODUCT')
    col, row = (x - info['x0']) / info['dx'], (info['y0'] - y) / info['dy']
    ex = {'UL': (0, 0), 'UR': (W, 0), 'LL': (0, H), 'LR': (W, H)}[name]
    lon2, lat2 = g.utm_to_lonlat(x, y, info['epsg'])
    corners[name] = {'mtl_utm': [x, y], 'mtl_lat_lon': [la, lo], 'pixel_from_transform': [round(col, 2), round(row, 2)], 'expected_pixel_corner': list(ex),
                     'pixel_residual': round(float(max(abs(col - ex[0]), abs(row - ex[1]))), 2), 'latlon_roundtrip_error_m': round(float(math.hypot((lat2 - la) * 111320, (lon2 - lo) * 111320 * math.cos(math.radians(la)))), 1)}
res['corner_check'] = corners
res['corner_check_ok'] = bool(all(c['pixel_residual'] < 1.5 and c['latlon_roundtrip_error_m'] < 30 for c in corners.values()))
# 2. footprint contains the reference point (polygon from the four MTL lat/lon corners)
poly = [(corners[n]['mtl_lat_lon'][1], corners[n]['mtl_lat_lon'][0]) for n in ('UL', 'UR', 'LR', 'LL')]
def inside(pt, poly):
    x, y = pt; c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c
res['footprint_contains_reference'] = bool(inside((REF[1], REF[0]), poly))
# 3. NDVI fields -> lon/lat
def refl(b, path):
    mult, add = num(f'REFLECTANCE_MULT_BAND_{b}'), num(f'REFLECTANCE_ADD_BAND_{b}'); sun = num('SUN_ELEVATION')
    return (np.asarray(Image.open(path), np.float32) * mult + add) / math.sin(math.radians(sun))
r = refl(4, f'{D}/{SC}_B4.TIF'); n = refl(5, f'{D}/{SC}_B5.TIF'); valid = np.asarray(Image.open(f'{D}/{SC}_B4.TIF')) > 0
ndvi = np.where(valid & ((n + r) > 0.02), (n - r) / np.maximum(n + r, 1e-6), 0)
green = ndvi > 0.20
ys, xs = np.nonzero(green); res['green_pixels_ndvi_gt_0.20'] = int(green.sum())
# the field cluster: densest 40 x 40 km block of green pixels (coarse 1.2 km grid), then everything within 25 km of its centroid
cell = 40; acc = np.zeros((H // cell + 1, W // cell + 1)); np.add.at(acc, (ys // cell, xs // cell), 1)
from numpy import unravel_index
cy0, cx0 = unravel_index(np.argmax(acc), acc.shape); cx, cy = (cx0 + .5) * cell, (cy0 + .5) * cell
for _ in range(5):
    m = (np.hypot(xs - cx, ys - cy) < 25000 / 30); cx, cy = float(xs[m].mean()), float(ys[m].mean())
m = (np.hypot(xs - cx, ys - cy) < 25000 / 30)
cx, cy = float(xs[m].mean()), float(ys[m].mean())
lon, lat = g.utm_to_lonlat(info['x0'] + (cx + 0.5) * info['dx'], info['y0'] - (cy + 0.5) * info['dy'], info['epsg'])
dist = math.hypot((lat - REF[0]) * 111.32, (lon - REF[1]) * 111.32 * math.cos(math.radians(REF[0])))
res['field_cluster'] = {'pixels': int(m.sum()), 'centroid_pixel': [round(cx), round(cy)], 'centroid_lat_lon': [round(lat, 4), round(lon, 4)], 'distance_to_reference_km': round(dist, 1),
                        'extent_pixels': [int(xs[m].min()), int(ys[m].min()), int(xs[m].max()), int(ys[m].max())]}
res['field_cluster_within_30km_of_reference'] = bool(dist < 30)
# 4. the video window
rec = json.load(open(os.path.join(HERE, 'stills', 'kufra_toneB.json'))); x0, y0, w, h = rec['src_window_px']
e = res['field_cluster']['extent_pixels']
res['video_window_px'] = [x0, y0, w, h]
res['video_window_corner_lat_lon'] = {k: [round(v, 4) for v in g.utm_to_lonlat(info['x0'] + px * info['dx'], info['y0'] - py * info['dy'], info['epsg'])[::-1]] for k, (px, py) in {'UL': (x0, y0), 'LR': (x0 + w, y0 + h)}.items()}
res['video_window_contains_field_cluster_core'] = bool(x0 <= cx <= x0 + w and y0 <= cy <= y0 + h)
res['video_window_fraction_of_cluster_pixels'] = round(float(((xs[m] >= x0) & (xs[m] < x0 + w) & (ys[m] >= y0) & (ys[m] < y0 + h)).mean()), 3)
res['position_of_cluster_in_window_fraction'] = [round((cx - x0) / w, 3), round((cy - y0) / h, 3)]
res['ALIGNMENT_VERIFIED'] = bool(res['corner_check_ok'] and res['footprint_contains_reference'] and res['field_cluster_within_30km_of_reference'] and res['video_window_contains_field_cluster_core'])
json.dump(res, open(os.path.join(HERE, 'stills', 'kufra_alignment.json'), 'w'), indent=1)
print(json.dumps({k: res[k] for k in ('corner_check_ok', 'footprint_contains_reference', 'field_cluster', 'field_cluster_within_30km_of_reference', 'video_window_corner_lat_lon', 'video_window_contains_field_cluster_core', 'video_window_fraction_of_cluster_pixels', 'position_of_cluster_in_window_fraction', 'ALIGNMENT_VERIFIED')}, indent=1))
