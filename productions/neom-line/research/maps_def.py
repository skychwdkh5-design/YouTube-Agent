import sys, json as _j
sys.path.insert(0,'/home/user/YouTube-Agent/.claude/skills/yt-geo')
import geostack as _g, numpy as _np
_G=_j.load(open('evidence/stack/grid.json'))
def LL(px,py):
    lo,la=_g.utm_to_lonlat(_np.array([_G['x0']+px*10.0]),_np.array([_G['y_top']-py*10.0]),_G['epsg']); return [round(float(lo[0]),5),round(float(la[0]),5)]
SEG=[35.2165,28.1062]
EXT={k:v for k,v in _j.load(open('research/ndwi_extent.json')).items() if not k.startswith('_')}
def arrow(y): return {"type":"arrow","from":[round(EXT[y]['lon_w'],5),round(EXT[y]['lat'],5)],"to":[round(EXT[y]['lon_e'],5),round(EXT[y]['lat'],5)],"color":"#FFD23F","width":9}
COAST_PIN=LL(30,850); COAST_VIEW=[35.112,28.082]; CORR=LL(700,465); ROAD=LL(200,372); MID=LL(450,430)
MAPS=[
 {"id":"m_coast","chapter":"promise","claims":["C20"],"anchor_text":"The project is called","min_s":6,"asset":"y2026","zoom":[5,8.5],"focus":COAST_VIEW,"focus_to":[35.128,28.087],
  "marks":[{"type":"pin","at":COAST_PIN,"text":"RED SEA COAST","anchor_text":"Saudi Arabia's Red Sea coast","dur":4.5}]},
 {"id":"m_pixel","chapter":"method","claims":["C15"],"anchor_text":"Each pixel in our frames","min_s":3.6,"asset":"y2026","zoom":[3.2,0.55],"focus":SEG,
  "label":{"text":"1 PIXEL = 10 M OF GROUND","style":"tag","slot":"upper"}},
 {"id":"m_visible","chapter":"method","claims":["C15"],"anchor_text":"sharp enough to see","min_s":6,"asset":"y2026","zoom":[7.5,6.5],"focus":MID,
  "marks":[{"type":"pin","at":CORR,"text":"A LONG CLEARED STRIP","anchor_text":"a long cleared strip","dur":3.2},{"type":"pin","at":ROAD,"text":"A ROAD","anchor_text":"or a road","dur":3.0},
           {"type":"label","text":"NOT VISIBLE: PERSON, CRANE, WINDOW","style":"tag","slot":"upper","anchor_text":"but not a person"}]},
 {"id":"m_scenes","chapter":"method","claims":["C16"],"anchor_text":"We picked seven scenes","min_s":8.4,"flip":["y2020","y2021","y2022","y2023","y2024","y2025","y2026"],"step":1.15,"zoom":[11,8],"focus":SEG},
 {"id":"m_notproof","chapter":"segment","claims":["C11"],"anchor_text":"That fits water","min_s":6.2,"asset":"y2026","zoom":[2.6,1.3],"focus":SEG,
  "marks":[{"type":"pin","at":SEG,"text":"DARK SEGMENT","t":0.6,"dur":None},
           {"type":"label","text":"FITS WATER, NOT PROOF","sub":"A SHADOW CAN FOOL IT","style":"tag","slot":"upper","anchor_text":"A shadow can also fool"}]},
 {"id":"m_dates","chapter":"checks","claims":["C14"],"anchor_text":"We tried to break our own result","min_s":15.4,"flip":["y2024","y2025","y2026"],"step":4.6,"zoom":[4.2,3.0],"focus":SEG,
  "marks":[{"type":"label","text":"SENTINEL-2A - 8 OCT 2024","style":"tag","slot":"middle","t":2.3,"dur":2.2},{"type":"label","text":"SENTINEL-2B - 8 OCT 2025","style":"tag","slot":"middle","t":4.8,"dur":4.3},
           {"type":"label","text":"SENTINEL-2C - 18 OCT 2026","style":"tag","slot":"middle","t":9.3}]},
 {"id":"m_l8","chapter":"checks","claims":["C13"],"anchor_text":"Second, does a different satellite agree","min_s":8.8,"wipe":["y2024","l2024"],"zoom":[4.4,2.6],"focus":SEG,"wipe_at":"Landsat 8, at 30 meters",
  "marks":[{"type":"label","text":"SENTINEL-2 - 10 M","style":"tag","slot":"upper","t":0.6,"dur":2.4},{"type":"label","text":"LANDSAT 8 - 30 M, SAME PLACE","style":"tag","slot":"upper","anchor_text":"Landsat 8, at 30 meters","dur":None}]},
 {"id":"m_len","chapter":"checks","claims":["C12"],"anchor_text":"Third, how long is it","min_s":11,"wipe":["y2025","y2026"],"zoom":[3.4,2.6],"focus":SEG,"wipe_at":"about 1.9 kilometers",
  "marks":[dict(arrow("2025"),anchor_text="about 1.6 kilometers",dur=None),{"type":"label","text":"OCT 2025: ABOUT 1.6 KM","style":"tag","slot":"upper","anchor_text":"about 1.6 kilometers","dur":None},
           dict(arrow("2026"),anchor_text="about 1.9 kilometers",dur=None),{"type":"label","text":"OCT 2026: ABOUT 1.9 KM","style":"tag","slot":"middle","anchor_text":"about 1.9 kilometers","dur":None}]},
 {"id":"m_nobuilding","chapter":"limits","claims":[],"limit":True,"anchor_text":"cannot identify any building","min_s":4.3,"asset":"y2026","zoom":[5,1.8],"focus":LL(700,470),"focus_to":SEG,
  "label":{"text":"AT THIS RESOLUTION: NO BUILDING","style":"tag","slot":"upper"}},
]
