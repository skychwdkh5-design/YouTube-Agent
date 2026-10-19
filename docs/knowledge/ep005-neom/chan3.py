import sys,json,re,statistics,time,urllib.request
from chan import num
KEY="AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
def browse(cid,params="EgZ2aWRlb3PyBgQKAjoA"):
    body=json.dumps({"context":{"client":{"clientName":"WEB","clientVersion":"2.20260101.00.00","hl":"en","gl":"US"}},"browseId":cid,"params":params}).encode()
    r=urllib.request.Request(f"https://www.youtube.com/youtubei/v1/browse?key={KEY}",data=body,headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0 Chrome/120"})
    return json.loads(urllib.request.urlopen(r,timeout=30).read())
def vids(cid):
    d=browse(cid); out=[]
    def walk(o):
        if isinstance(o,dict):
            if "videoRenderer" in o:
                v=o["videoRenderer"]; out.append((v["videoId"],num(v.get("viewCountText",{}).get("simpleText")),v.get("publishedTimeText",{}).get("simpleText"),v["title"]["runs"][0]["text"]))
            elif "lockupViewModel" in o:
                t=json.dumps(o["lockupViewModel"]); m=re.search(r'([\d.,]+[KMB]?) views',t)
                if m: out.append((o["lockupViewModel"].get("contentId"),num(m.group(1)),(re.search(r'"content":"([^"]*ago)"',t) or [0,None])[1],""))
            for x in o.values(): walk(x)
        elif isinstance(o,list):
            for x in o: walk(x)
    walk(d); return out
if __name__=="__main__":
    for c in sys.argv[1:]:
        v=vids(c); vv=[x[1] for x in v if x[1]]
        print(c,len(vv),"median",int(statistics.median(vv)) if vv else None,vv[:20])
