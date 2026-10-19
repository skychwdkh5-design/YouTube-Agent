import json,re,time,statistics,urllib.request
from yts import search
import chan2,chan3
qs=["NEOM The Line","The Line Saudi Arabia collapsed","The Line NEOM satellite","NEOM megacity failed explained","Saudi Arabia The Line what happened","NEOM The Line construction update","The Line mirror city analysis","NEOM documentary Saudi megaproject"]
allv={}
for q in qs:
    try:
        for v in search(q): allv.setdefault(v["id"],v)
    except Exception as e: print("ERR",q,str(e)[:60])
    time.sleep(1)
def n(s):
    m=re.search(r"([\d,]+)",s or ""); return int(m.group(1).replace(",","")) if m else 0
def subs(s):
    if not s: return None
    m=re.search(r"([\d.]+)\s*([KMB]?)",s.replace(",","")); 
    return int(float(m.group(1))*{"":1,"K":1e3,"M":1e6,"B":1e9}[m.group(2)]) if m else None
rows=[];chs={}
for v in allv.values():
    if not v["chid"] or n(v["views"])<20000: continue
    c=v["chid"]
    if c not in chs:
        try:
            s,_=chan2.chan(c); vv=[x[1] for x in chan3.vids(c) if x[1]]
            chs[c]=dict(subs=s,subs_n=subs(s),median=int(statistics.median(vv)) if vv else None,n=len(vv))
        except Exception as e: chs[c]=dict(subs=None,subs_n=None,median=None,n=0)
        time.sleep(.6)
    c_=chs[c]; vw=n(v["views"])
    rows.append(dict(id=v["id"],title=v["title"],channel=v["ch"],views=vw,age=v["age"],dur=v["dur"],subs=c_["subs"],subs_n=c_["subs_n"],median=c_["median"],
      mult=round(vw/c_["median"],1) if c_["median"] else None,views_per_sub=round(vw/c_["subs_n"],2) if c_["subs_n"] else None))
rows.sort(key=lambda r:-r["views"]); json.dump(rows,open("neom_videos_all.json","w"),indent=1)
print(len(rows))
