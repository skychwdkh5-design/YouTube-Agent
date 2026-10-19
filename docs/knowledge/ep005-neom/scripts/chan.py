import sys,json,re,statistics,time
from yts import get
def num(s):
    if not s: return None
    m=re.search(r"([\d.,]+)\s*([KMB]?)",s.replace(",",""))
    if not m: return None
    return int(float(m.group(1))*{"":1,"K":1e3,"M":1e6,"B":1e9}[m.group(2)])
def chan(cid):
    h=get(f"https://www.youtube.com/channel/{cid}/videos?hl=en&gl=US")
    m=re.search(r"var ytInitialData = (\{.*?\});</script>",h,re.S)
    d=json.loads(m.group(1)); subs=None; vids=[]
    def walk(o):
        nonlocal subs
        if isinstance(o,dict):
            if "subscriberCountText" in o and subs is None and isinstance(o["subscriberCountText"],dict): subs=o["subscriberCountText"].get("simpleText")
            if "metadataRows" in o: pass
            for k in("videoRenderer","richItemRenderer"):pass
            if "videoRenderer" in o:
                v=o["videoRenderer"]; vids.append(num(v.get("viewCountText",{}).get("simpleText")))
            for x in o.values(): walk(x)
        elif isinstance(o,list):
            for x in o: walk(x)
    walk(d)
    if subs is None:
        mm=re.search(r'"subscriberCountText":\{"accessibility":\{"accessibilityData":\{"label":"([^"]+)"',h) or re.search(r'([\d.,]+[KM]?) subscribers',h)
        subs=mm.group(1) if mm else None
    vids=[v for v in vids if v]
    return subs,vids
if __name__=="__main__":
    for cid in sys.argv[1:]:
        try:
            s,v=chan(cid); print(cid,s,len(v),"median",int(statistics.median(v)) if v else None,v[:12])
        except Exception as e: print(cid,"ERR",e)
        time.sleep(1)
