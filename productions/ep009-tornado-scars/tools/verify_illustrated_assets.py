#!/usr/bin/env python3
"""Verify EP009 archived illustrations against handoff/assets.json, then extract safely."""
import hashlib,json,pathlib,sys,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[3]
HANDOFF=pathlib.Path(__file__).resolve().parents[1]/"handoff"
BUNDLE=ROOT/"Orbital_Atlas_EP009_illustrated_assets.zip"
CONFIG=json.loads((HANDOFF/"assets.json").read_text())
out=HANDOFF/"assets";out.mkdir(parents=True,exist_ok=True)
if not BUNDLE.exists():sys.exit("Missing root ZIP: "+str(BUNDLE))
if hashlib.sha256(BUNDLE.read_bytes()).hexdigest()!=CONFIG["bundle_sha256"]:
    sys.exit("ZIP SHA256 MISMATCH: do not use")
with zipfile.ZipFile(BUNDLE) as z:
    entries=set(z.namelist())
    for a in CONFIG["generated_assets"]:
        entry=a["archive_entry"]
        if entry not in entries or not entry.startswith("assets/"):
            sys.exit("Missing or invalid entry: "+entry)
        data=z.read(entry)
        sha=hashlib.sha256(data).hexdigest()
        if sha!=a["sha256"]:sys.exit("Asset SHA256 mismatch: "+a["id"]+" "+a["name"])
        dest=out/a["name"]
        dest.write_bytes(data)
        print("OK",a["id"],dest,sha)
print("8 illustrations verified and extracted; does NOT imply NASA source files present or owner render approval.")
