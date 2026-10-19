import sys,json,re,statistics,time
from yts import get
from chan import num
def idata(u):
    for _ in range(4):
        try:
            h=get(u); m=re.search(r"var ytInitialData = (\{.*?\});</script>",h,re.S)
            if m: return json.loads(m.group(1))
        except Exception as e: pass
        time.sleep(2)
def chan(handle_or_id):
    u=f"https://www.youtube.com/channel/{handle_or_id}/videos?hl=en&gl=US" if handle_or_id.startswith("UC") else f"https://www.youtube.com/{handle_or_id}/videos?hl=en&gl=US"
    d=idata(u); 
    if not d: return None,[],[]
    vids=[];subs=None
    def walk(o):
        nonlocal subs
        if isinstance(o,dict):
            if "lockupMetadataViewModel" in o:
                t=json.dumps(o["lockupMetadataViewModel"])
                v=re.search(r'"content": ?"([\d.,]+[KMB]?) views"',t); a=re.search(r'"content": ?"([^"]*ago)"',t); ti=re.search(r'"title":\{"content":"([^"]+)"',t.replace('": ','":'))
                if v: vids.append((num(v.group(1)),a.group(1) if a else None))
            if "subscriberCountText" in o and subs is None:
                x=o["subscriberCountText"]; subs=x.get("simpleText") if isinstance(x,dict) else x
            if "contentMetadataViewModel" in o and subs is None:
                t=json.dumps(o["contentMetadataViewModel"]); m=re.search(r'([\d.,]+[KMB]?) subscribers',t)
                if m: subs=m.group(1)
            for x in o.values(): walk(x)
        elif isinstance(o,list):
            for x in o: walk(x)
    walk(d)
    if subs is None:
        s=json.dumps(d); m=re.search(r'([\d.,]+[KMB]?) subscribers',s); subs=m.group(1) if m else None
    return subs,vids
if __name__=="__main__":
    for c in sys.argv[1:]:
        s,v=chan(c); vv=[x[0] for x in v]
        print(c,"subs",s,"n",len(vv),"median",int(statistics.median(vv)) if vv else None,vv[:15]); time.sleep(1)
