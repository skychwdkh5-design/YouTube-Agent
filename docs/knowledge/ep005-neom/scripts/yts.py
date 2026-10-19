import sys,json,re,urllib.request,urllib.parse
def get(u):
    r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) Chrome/120 Safari/537.36","Accept-Language":"en-US,en;q=0.9","Cookie":"CONSENT=YES+1"})
    return urllib.request.urlopen(r,timeout=30).read().decode("utf8","replace")
def search(q):
    h=get("https://www.youtube.com/results?search_query="+urllib.parse.quote(q)+"&hl=en&gl=US")
    m=re.search(r"var ytInitialData = (\{.*?\});</script>",h,re.S)
    d=json.loads(m.group(1)); out=[]
    def walk(o):
        if isinstance(o,dict):
            if "videoRenderer" in o:
                v=o["videoRenderer"]
                out.append(dict(id=v["videoId"],title=v["title"]["runs"][0]["text"],
                  views=v.get("viewCountText",{}).get("simpleText"),age=v.get("publishedTimeText",{}).get("simpleText"),
                  dur=v.get("lengthText",{}).get("simpleText"),ch=v.get("ownerText",{}).get("runs",[{}])[0].get("text"),
                  chid=v.get("ownerText",{}).get("runs",[{}])[0].get("navigationEndpoint",{}).get("browseEndpoint",{}).get("browseId")))
            for x in o.values(): walk(x)
        elif isinstance(o,list):
            for x in o: walk(x)
    walk(d); return out
if __name__=="__main__":
    for q in sys.argv[1:]:
        print("##",q)
        for v in search(q): print(v["id"],"|",v["views"],"|",v["age"],"|",v["dur"],"|",v["ch"],"|",v["title"])
