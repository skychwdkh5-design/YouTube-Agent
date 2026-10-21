import json
P='research/notes.json'
n=json.load(open(P))
def N(id,text,x,y,w=0.3,h=0.16,style="default",step=None,hl=None):
    d={"id":id,"text":text,"x":x,"y":y,"w":w,"h":h,"style":style}
    if step: d["step"]=step
    return d
def A(a,b,label=None,step=None,color="accent"):
    d={"from":a,"to":b,"color":color}
    if label: d["label"]=label
    if step: d["step"]=step
    return d
DATES=[(2020,"29 SEP"),(2021,"29 SEP"),(2022,"9 OCT"),(2023,"14 OCT"),(2024,"8 OCT"),(2025,"8 OCT"),(2026,"18 OCT")]
SRC_NEWS="Reported by the outlet named; we could not open the original article (see script)"
inf=[]
# --- promise
inf.append({"id":"i_coast","chapter":"promise","claims":["C20"],"anchor_text":"Red Sea coast","min_s":8,"credit":"NASA / ISS photo; Contains modified Copernicus Sentinel data 2026",
 "graphic":{"type":"compare","title":"Saudi Arabia's Red Sea coast","source":"Left: NASA ISS photo iss066e091657 (public domain). Right: Copernicus Sentinel-2 L2A, 40 m",
  "left":{"file":"media/assets/northwestern_coast_of_saudi_.jpg","label":"ISS PHOTO - NOT THE NEOM SITE","credit":"NASA / ISS, 30 Nov 2021"},
  "right":{"geo":{"stack":"evidence/wide/y2026.png","grid":"evidence/wide/grid.json","center":[35.345,28.14],"width_km":45},"label":"SENTINEL-2 - NEOM AREA","credit":"Copernicus Sentinel data 2026"}}})
inf.append({"id":"i_tiers_promise","chapter":"promise","ref":"g_tiers","anchor_text":"first of three things","min_s":9})
# --- plan: reported claims as quote cards
def card(id,claim,head,l1,l2,note,a1,a2,col1="accent",title=None):
    g={"type":"diagram","title":title or "What was reported","source":SRC_NEWS,
       "nodes":[N("h",head,0.5,0.17,0.62,0.13,"plain",1),
                N("a",l1,0.5,0.47,0.84,0.22,col1,1),
                N("b",l2,0.5,0.76,0.84,0.17,"default",2)] if l2 else
               [N("h",head,0.5,0.17,0.62,0.13,"plain",1),N("a",l1,0.5,0.47,0.84,0.22,col1,1),N("b",note,0.5,0.76,0.84,0.17,"red",2)],
       }
    return {"id":id,"chapter":"plan","claims":[claim],"min_s":9,"graphic":g,"steps":[{"anchor_text":a1},{"anchor_text":a2}]}
inf.append(card("i_bloomberg","C2","BLOOMBERG - APRIL 2024","About 2.4 km of The Line expected by 2030","Fewer than 300,000 residents by then",None,"In April 2024, Bloomberg reported","fewer than 300,000 residents"))
inf.append(card("i_semafor","C3","SEMAFOR - 22 MAY 2026","Work on The Line halted until at least after 2030",None,"Unnamed sources. Not officially confirmed","In May 2026, Semafor reported","It has not been officially confirmed"))
inf.append({"id":"i_reports_recap","chapter":"plan","ref":"g_reports","anchor_text":"These are news reports","min_s":4.5})
inf.append(card("i_reuters","C4","REUTERS - ABOUT 4 OCT 2026","NEOM stadium shelved indefinitely",None,"Two sources. No official announcement","In October 2026, Reuters reported","with no official announcement"))
inf.append({"id":"i_opened","chapter":"plan","claims":[],"min_s":12,
 "graphic":{"type":"diagram","title":"How we handled the reports","source":"OrbitalAtlas research log: original articles not reachable from our research setup",
  "nodes":[N("o","ORIGINAL ARTICLE",0.17,0.45,0.28,0.2,"red",1),N("x","NOT OPENED BY US",0.17,0.75,0.28,0.12,"plain",1),
           N("p","Outlet A",0.55,0.3,0.24,0.16,"default",2),N("q","Outlet B",0.55,0.6,0.24,0.16,"default",2),
           N("w","WHO REPORTED WHAT, AND NOTHING MORE",0.89,0.45,0.2,0.34,"accent",2)],
  "arrows":[A("o","p","described",2),A("o","q","described",2),A("p","w",None,2),A("q","w",None,2)]},
 "steps":[{"anchor_text":"We could not open the original articles"},{"anchor_text":"Each report was described by at least two other outlets"}]})
# --- method
inf.append({"id":"i_source","chapter":"method","claims":["C16"],"anchor_text":"We used free Sentinel-2 images","min_s":5,
 "graphic":{"type":"diagram","title":"Where the pictures come from","source":"Copernicus Sentinel-2 L2A (ESA / European Union), free, full and open data",
  "nodes":[N("a","SENTINEL-2 SATELLITES",0.5,0.25,0.6,0.18,"blue"),N("b","EUROPEAN COPERNICUS PROGRAM",0.5,0.52,0.6,0.18,"accent"),N("c","FREE, FULL AND OPEN DATA",0.5,0.79,0.6,0.18,"green")],
  "arrows":[A("a","b"),A("b","c")]}})
inf.append({"id":"i_pixel","chapter":"method","claims":["C15"],"anchor_text":"Each pixel in our frames","min_s":8,
 "graphic":{"type":"geo","title":"One pixel = 10 m of ground","source":"Copernicus Sentinel-2 L2A, 10 m, Oct 2026","credit":"Contains modified Copernicus Sentinel data 2026","show_credit":False,"date":"OCT 2026",
  "image":{"stack":"evidence/stack/y2026.png","grid":"evidence/stack/grid.json","center":[35.2165,28.1062],"width_km":0.6,"resample":"nearest"},
  "graticule":False,"scale_bar":True}})
inf.append({"id":"i_visible","chapter":"method","claims":["C15"],"min_s":9,
 "graphic":{"type":"diagram","title":"What 10 m can and cannot show","source":"Pixel size 10 m (Sentinel-2 L2A); statement from our method notes",
  "nodes":[N("a","CAN SEE","0.27" and 0.27,0.2,0.36,0.14,"green",1),N("b","A long cleared strip",0.27,0.46,0.36,0.16,"default",1),N("c","A road",0.27,0.7,0.36,0.14,"default",1),
           N("d","CANNOT SEE",0.73,0.2,0.36,0.14,"red",2),N("e","A person",0.73,0.46,0.36,0.14,"default",2),N("f","A crane",0.73,0.64,0.36,0.12,"default",2),N("g","A window",0.73,0.82,0.36,0.12,"default",2)]},
 "steps":[{"anchor_text":"sharp enough to see"},{"anchor_text":"but not a person"}]})
inf.append({"id":"i_scenes","chapter":"method","claims":["C16"],"anchor_text":"We picked seven scenes","min_s":6,
 "graphic":{"type":"diagram","title":"Seven scenes, 2020 to 2026","source":"Sentinel-2 L2A scene metadata (relative orbit 78, tile T36RYS); Planetary Computer STAC",
  "nodes":[N(f"y{y}",str(y),0.075+0.141*i,0.3,0.125,0.16,"blue") for i,(y,d) in enumerate(DATES)]+[N(f"d{y}",d,0.075+0.141*i,0.55,0.125,0.14,"default") for i,(y,d) in enumerate(DATES)]}})
inf.append({"id":"i_orbit","chapter":"method","claims":["C16"],"min_s":11,
 "graphic":{"type":"diagram","title":"Why the scenes can be compared","source":"Sentinel-2 L2A scene metadata (relative orbit 78, tile T36RYS); Planetary Computer STAC",
  "nodes":[N("o","SAME ORBIT: 78 - PASS AROUND 08:08 UTC",0.5,0.3,0.8,0.2,"accent",1),N("s","SAME SEASON: 29 SEP TO 18 OCT",0.5,0.7,0.8,0.2,"default",2)]},
 "steps":[{"anchor_text":"Same orbit means"},{"anchor_text":"Same season means"}]})
inf.append({"id":"i_cloud","chapter":"method","claims":["C16"],"anchor_text":"The scenes report almost no cloud","min_s":4,"closes_chapter":True,
 "graphic":{"type":"callout","title":"Cloud cover in all seven scenes","source":"Sentinel-2 L2A scene metadata (scene cloud cover 0.03 to 0.06 percent)","value":0.1,"unit":"percent","label":"is the ceiling for reported cloud cover in all seven scenes","decimals":1}})
# --- segment
inf.append({"id":"i_ndwi","chapter":"segment","claims":["C11"],"min_s":16,
 "graphic":{"type":"diagram","title":"Water-like in near-infrared","source":"Sentinel-2 B03/B08 NDWI, our notes: NDWI above zero and B08 below 0.05",
  "nodes":[N("a","NEAR-INFRARED SIGNAL: VERY LOW",0.27,0.3,0.4,0.2,"blue",1),N("b","WATER INDEX (NDWI): ABOVE ZERO",0.73,0.3,0.4,0.2,"blue",1),
           N("c","2024, 2025, 2026: WATER-LIKE",0.5,0.62,0.6,0.18,"green",1),
           N("e","FITS WATER - NOT PROOF. A SHADOW CAN FOOL IT",0.5,0.88,0.84,0.12,"red",2)]},
 "steps":[{"anchor_text":"In near-infrared light"},{"anchor_text":"That fits water"}]})
# --- checks
inf.append({"id":"i_dates","chapter":"checks","claims":["C14"],"min_s":14,
 "graphic":{"type":"diagram","title":"Check 1 of 3: is it repeatable?","source":"Sentinel-2 L2A scene metadata; NDWI per scene (evidence/ndwi.json)",
  "nodes":[N("a","8 OCT 2024",0.2,0.3,0.26,0.16,"blue",1),N("b","8 OCT 2025",0.5,0.3,0.26,0.16,"blue",1),N("c","18 OCT 2026",0.8,0.3,0.26,0.16,"blue",1),
           N("r","SEGMENT PRESENT IN ALL THREE",0.5,0.58,0.8,0.12,"green",2),
           N("a2","SENTINEL-2A",0.2,0.84,0.26,0.14,"accent",3),N("b2","SENTINEL-2B",0.5,0.84,0.26,0.14,"accent",3),N("c2","SENTINEL-2C",0.8,0.84,0.26,0.14,"accent",3)]},
 "steps":[{"anchor_text":"First, was it a one-day accident"},{"anchor_text":"No."},{"anchor_text":"three different Sentinel-2 satellites"}]})
inf.append({"id":"i_l8","chapter":"checks","claims":["C13"],"anchor_text":"Second, does a different satellite agree","min_s":7,
 "graphic":{"type":"geo","title":"Check 2 of 3: Landsat 8, 30 m per pixel","source":"Landsat 8 OLI, 22 Oct 2024, 30 m (USGS)","credit":"Landsat imagery courtesy of the U.S. Geological Survey","show_credit":False,"date":"OCT 2024",
  "image":{"stack":"evidence/landsat/y2024.png","grid":"evidence/landsat/grid.json","center":[35.2165,28.1062],"width_km":6},
  "callouts":[{"at":[35.2119,28.1062],"text":"DARK SEGMENT: ABOUT 0.7 KM"}],"graticule":False,"scale_bar":True}})
inf.append({"id":"i_landsat","chapter":"checks","claims":["C13"],"anchor_text":"It gives about 0.7 kilometers","min_s":7,
 "graphic":{"type":"compare","title":"Check 2 of 3: a different satellite, Oct 2024","source":"Sentinel-2 L2A 10 m (8 Oct 2024) and Landsat 8 OLI 30 m (22 Oct 2024); lengths are our own measures",
  "left":{"geo":{"stack":"evidence/stack/y2024.png","grid":"evidence/stack/grid.json","center":[35.2165,28.1062],"width_km":4},"label":"SENTINEL-2 - 10 M","credit":"Copernicus Sentinel data 2024"},
  "right":{"geo":{"stack":"evidence/landsat/y2024.png","grid":"evidence/landsat/grid.json","center":[35.2165,28.1062],"width_km":4},"label":"LANDSAT 8 - 30 M","credit":"Landsat / USGS"},
  "metric":{"left":1.6,"right":0.7,"unit":"km","decimals":1}}})
inf.append({"id":"i_lengths","chapter":"checks","claims":["C13","C12"],"anchor_text":"It gives about 1.65 kilometers","min_s":7,
 "graphic":{"type":"bar","title":"Same segment, two instruments","source":"Sentinel-2 10 m (NDWI, our measure) and Landsat 8 30 m (our contrast measure); scenes 2-3 weeks apart","unit":"km","decimals":2,
  "bars":[{"label":"S2 Oct 2024","value":1.6},{"label":"L8 Oct 2024","value":0.72,"highlight":True},{"label":"S2 Oct 2025","value":1.6},{"label":"L8 Oct 2025","value":1.65},{"label":"S2 Oct 2026","value":1.92},{"label":"L8 Sep 2026","value":1.65}]}})
inf.append({"id":"i_apart","chapter":"checks","claims":["C13"],"anchor_text":"The two sets of scenes","min_s":6,
 "graphic":{"type":"diagram","title":"The two satellites were not there on the same day","source":"Scene dates: Sentinel-2 L2A and Landsat 8 OLI provenance files",
  "nodes":[N("a","OCT 2024: 8 OCT AND 22 OCT",0.5,0.22,0.8,0.15,"blue",1),N("b","OCT 2025: 8 OCT AND 25 OCT",0.5,0.42,0.8,0.15,"blue",1),N("c","2026: 26 SEP AND 18 OCT",0.5,0.62,0.8,0.15,"blue",1),
           N("d","2 TO 3 WEEKS APART: RESOLUTION OR TIMING? WE CANNOT TELL",0.5,0.86,0.9,0.15,"red",2)]},
 "steps":[{"anchor_text":"The two sets of scenes"},{"anchor_text":"so we cannot tell"}]})
inf.append({"id":"i_growth","chapter":"checks","claims":["C12"],"anchor_text":"That difference of 0.3 kilometers","min_s":12,
 "graphic":{"type":"diagram","title":"A 0.3 km difference: three explanations","source":"Sentinel-2 10 m, Oct 2025 (1.6 km) and Oct 2026 (1.9 km); our NDWI measure",
  "nodes":[N("a","GROWTH?",0.5,0.2,0.5,0.15,"blue",1),N("b","A DIFFERENT WATER LEVEL?",0.5,0.4,0.5,0.15,"blue",2),N("c","WHERE OUR THRESHOLD FALLS?",0.5,0.6,0.5,0.15,"blue",3),
           N("d","WE DO NOT CLAIM THAT IT GREW. WE CANNOT TELL.",0.5,0.85,0.8,0.15,"red",4)]},
 "steps":[{"anchor_text":"That difference of 0.3 kilometers"},{"anchor_text":"different water level"},{"anchor_text":"where our threshold falls"},{"anchor_text":"So we do not claim"}]})
inf.append({"id":"i_verdict","chapter":"checks","claims":["C14","C13","C12"],"min_s":7,
 "graphic":{"type":"diagram","title":"Three checks, one open number","source":"Our checks 1-3 (Sentinel-2 dates, Landsat 8 agreement, length at 10 m)",
  "nodes":[N("a","3 DATES, 3 SATELLITES: AGREE",0.5,0.2,0.7,0.15,"green",1),N("b","LANDSAT 8 SEES IT TOO",0.5,0.42,0.7,0.15,"green",1),N("c","PRESENT IN 2024, 2025, 2026",0.5,0.64,0.7,0.15,"green",1),N("d","LENGTH: 1.6 OR 1.9 KM? UNSETTLED",0.5,0.87,0.7,0.15,"red",2)]},
 "steps":[{"anchor_text":"That is the honest result"},{"anchor_text":"one number refuses to settle"}]})
# --- limits
inf.append({"id":"i_nobuilding","chapter":"limits","claims":[],"anchor_text":"cannot identify any building","min_s":8,
 "graphic":{"type":"geo","title":"At 10 m: no building can be identified here","source":"Copernicus Sentinel-2 L2A, 10 m, Oct 2026","credit":"Contains modified Copernicus Sentinel data 2026","show_credit":False,"date":"OCT 2026",
  "image":{"stack":"evidence/stack/y2026.png","grid":"evidence/stack/grid.json","center":[35.2165,28.1062],"width_km":2.5},
  "callouts":[{"at":[35.2165,28.1062],"text":"DARK SEGMENT"}],"graticule":False,"scale_bar":True}})
inf.append({"id":"i_cannot","chapter":"limits","claims":[],"min_s":10,
 "graphic":{"type":"diagram","title":"What we cannot say","source":"Limitations listed in the script (L)",
  "nodes":[N("a","THAT IT IS A FINISHED CITY",0.5,0.3,0.7,0.18,"red",1),N("b","THAT THIS CORRIDOR IS THE LINE",0.5,0.65,0.7,0.18,"red",2)]},
 "steps":[{"anchor_text":"We also cannot say this is a finished city"},{"anchor_text":"We cannot prove that this corridor"}]})
inf.append({"id":"i_nomatch","chapter":"limits","claims":[],"min_s":10,
 "graphic":{"type":"diagram","title":"Why we stop here","source":"Limitations listed in the script (L)",
  "nodes":[N("c","NO OFFICIAL NEOM MAP TO MATCH IT AGAINST",0.5,0.3,0.8,0.18,"plain",1),N("d","A SIMILAR PICTURE IN 2025 AND 2026 DOES NOT PROVE A PAUSE",0.5,0.65,0.8,0.22,"red",2)]},
 "steps":[{"anchor_text":"We had no official NEOM map"},{"anchor_text":"A similar picture in 2025"}]})
for i in inf:
    if i["id"] in ("i_opened","i_nobuilding","i_cannot","i_nomatch"): i["exempt"]=True
n["infographics"]=inf
json.dump(n,open(P,'w'),indent=1,ensure_ascii=False)
print(len(inf))
