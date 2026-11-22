#!/usr/bin/env python3
"""EP009: fetch exact NASA/NOAA originals, verify media headers and write proof manifest.
Requires network in GitHub Actions runner. Does not modify releases, tokens or YouTube.
"""
from __future__ import annotations
import argparse, hashlib, json, mimetypes, pathlib, shutil, subprocess, time, urllib.request
from PIL import Image

SOURCES = [
  {"id":"M01","name":"nasa_tuscaloosa_EO1_20110502.jpg","url":"https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/images/imagerecords/50000/50434/tuscaloosa_ali_2011112_lrg.jpg?w=4096","page":"https://science.nasa.gov/earth/earth-observatory/tornado-track-in-tuscaloosa-alabama-50434/","credit":"NASA Earth Observatory / Jesse Allen and Robert Simmon, NASA EO-1 team","kind":"image","min_width":1900,"min_height":2300},
  {"id":"M02_before","name":"nasa_modis_before_20110412.jpg","url":"https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/images/imagerecords/50000/50370/Alabama_amo_2011102_lrg.jpg?w=4096","page":"https://science.nasa.gov/earth/earth-observatory/tornado-tracks-in-tuscaloosa-alabama-50370/","credit":"NASA Earth Observatory / Jeff Schmaltz, MODIS Rapid Response Team at NASA GSFC","kind":"image","min_width":1800},
  {"id":"M02_after","name":"nasa_modis_after_20110428.jpg","url":"https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/images/imagerecords/50000/50370/Alabama_amo_2011118_lrg.jpg?w=4096","page":"https://science.nasa.gov/earth/earth-observatory/tornado-tracks-in-tuscaloosa-alabama-50370/","credit":"NASA Earth Observatory / Jeff Schmaltz, MODIS Rapid Response Team at NASA GSFC","kind":"image","min_width":1200},
  {"id":"M03","name":"noaa_goes13_outbreak_2011.mp4","url":"https://www.nesdis.noaa.gov/s3/migrated/unitedstates_goe_2011118_hd.mp4","page":"https://www.nesdis.noaa.gov/content/revisiting-april-2011-tornado-super-outbreak-orbit","credit":"NOAA NESDIS GOES-13 (verify video-specific third-party attribution)","kind":"video"},
]
def download(src, dest, timeout=60):
    # HTTP no cache-busting or transformations: obtain provider original.
    req=urllib.request.Request(src["url"],headers={"User-Agent":"OrbitalAtlasEditorialArchive/1.0 (research; source archive)","Accept":"image/jpeg,video/mp4,*/*"})
    with urllib.request.urlopen(req,timeout=timeout) as r, dest.open("wb") as out:
        size=0
        while True:
            chunk=r.read(1024*1024)
            if not chunk:break
            size+=len(chunk)
            if size>150*1024*1024: raise ValueError("Asset exceeds 150 MB safety limit")
            out.write(chunk)
    return size
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="productions/ep009-tornado-scars/media_original")
    ap.add_argument("--strict",action="store_true",help="Fail if any required download fails")
    args=ap.parse_args()
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    log=[]
    for src in SOURCES:
        dest=out/src["name"]; item={k:v for k,v in src.items() if k not in ("min_width",)}
        item.update(status="MISSING",sha256=None,bytes=0)
        for attempt in range(3):
            try:
                n=download(src,dest)
                if n<10000:raise ValueError("Suspiciously small download")
                if src["kind"]=="image":
                    with Image.open(dest) as im:
                        im.verify()
                    with Image.open(dest) as im:
                        w,h=im.size
                        if w<src["min_width"] or h<src.get("min_height",400):raise ValueError(f"Below expected image resolution {w}x{h}")
                        item["dimensions"]=[w,h]
                else:
                    with dest.open("rb") as f:head=f.read(128)
                    if b"ftyp" not in head: raise ValueError("Not valid MP4 header")
                    if shutil.which("ffprobe"):
                        p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1",str(dest)],capture_output=True,text=True)
                        if p.returncode: raise ValueError("ffprobe rejected video")
                        item["ffprobe"]=p.stdout.strip()
                item.update(status="DOWNLOADED_NEEDS_EDITORIAL_REVIEW",sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),bytes=n,local_path=str(dest))
                break
            except Exception as e:
                item["error"]=str(e)[:200]
                if dest.exists():dest.unlink()
                time.sleep(2*(attempt+1))
        log.append(item)
    (out/"download_manifest.json").write_text(json.dumps({"format":1,"verified_by":"automated format/hash checks only; editorial fact/license review still needed","assets":log},indent=2))
    ok=sum(x["status"].startswith("DOWNLOADED") for x in log)
    print(f"EP009 original media: {ok}/{len(log)} downloaded. See download_manifest.json")
    for x in log: print(x["id"],x["status"],x.get("error",""))
    if ok<len(log):raise SystemExit(2)
if __name__=="__main__":main()
