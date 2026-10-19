import json,re,time,statistics,sys
from yts import search
import chan2,chan3
topics={"aral":["Aral Sea","Aral Sea satellite","Aral Sea disappeared why"],"gsl":["Great Salt Lake drying","Great Salt Lake satellite","Great Salt Lake disappearing"],"salton":["Salton Sea","Salton Sea satellite dust"]}
def n(s):
    m=re.search(r"([\d,]+)",s or ""); return int(m.group(1).replace(",","")) if m else 0
def subs(s):
    if not s: return None
    m=re.search(r"([\d.]+)\s*([KMB]?)",s.replace(",","")); return int(float(m.group(1))*{"":1,"K":1e3,"M":1e6,"B":1e9}[m.group(2)]) if m else None
out={}
for t,qs in topics.items():
    allv={}
    for q in qs:
        try:
            for v in search(q): allv.setdefault(v["id"],v)
        except Exception as e: print("ERR",q)
        time.sleep(1)
    out[t]=list(allv.values())
chs={}
res={}
for t,vs in out.items():
    rows=[]
    for v in sorted(vs,key=lambda v:-n(v["views"]))[:40]:
        if n(v["views"])<100000 or not v["chid"]: continue
        c=v["chid"]
        if c not in chs:
            try: s,_=chan2.chan(c); vv=[x[1] for x in chan3.vids(c) if x[1]]; chs[c]=(s,subs(s),int(statistics.median(vv)) if vv else None)
            except Exception: chs[c]=(None,None,None)
            time.sleep(.5)
        s,sn,m=chs[c]; vw=n(v["views"])
        rows.append(dict(id=v["id"],title=v["title"][:70],ch=v["ch"],views=vw,age=v["age"],dur=v["dur"],subs=s,subs_n=sn,median=m,mult=round(vw/m,1) if m else None))
    res[t]=rows
json.dump(res,open("alt_topics.json","w"),indent=1)
for t,rows in res.items():
    print("==",t,len(rows))
    for r in rows[:14]: print(r["views"],r["age"],r["dur"],r["ch"][:20],r["subs"],r["median"],r["mult"],"|",r["title"][:55])
