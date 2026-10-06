#!/usr/bin/env python3
"""assets.py - every frame in the video has a source and a license, or it does not go in.

    python3 assets.py visuals.md              # check the asset table
    python3 assets.py visuals.md --credits    # also print the credits block for the description
    python3 assets.py visuals.md --json

THE TABLE (visuals.md) is a markdown table, one row per asset:

    | ID | Beat | Type | Description | Source | URL | License | Attribution | AI |

  Type        map, animated-map, satellite, footage, stock, photo, archival, graphic, infographic, ai
  License     public-domain, us-gov, cc0, cc-by, cc-by-sa, odbl, copernicus, google-earth,
              stock:<provider>, original, ai-generated   (cc-by-nc / cc-by-nd / fair use / unknown fail)
  AI          no | stylized | realistic

Rules it enforces, and why:
  - No license, "unknown", or "fair use" fails. Fair use is a defence you argue after a claim, not a
    license you can rely on before one. Replace the asset or get a human to sign it off.
  - NC (non-commercial) fails because a monetized channel is commercial. ND (no-derivatives) fails
    because cropping, labelling or animating a map IS a derivative.
  - Attribution licenses (CC-BY, CC-BY-SA, ODbL, Copernicus, Google Earth) need the credit line, and
    OpenStreetMap, Copernicus and Google credits must name them.
  - AI never stands in for real imagery: a satellite, footage, photo or archival row cannot be AI.
  - A realistic AI visual is allowed only where it is not presented as the real place, and it
    switches on YouTube's altered/synthetic-content disclosure at upload. The tool says so.
  - Search pages, Pinterest and re-uploads on YouTube are not sources. Find the original.

Exit code 0 = PASS, 1 = FAIL.
"""
import json, re, sys

OK_PLAIN = {"public-domain", "us-gov", "cc0", "original", "ai-generated"}
NEEDS_ATTR = {"cc-by", "cc-by-sa", "odbl", "copernicus", "google-earth"}
MUST_NAME = {"odbl": "openstreetmap", "copernicus": "copernicus", "google-earth": "google"}
DISPLAY = {"openstreetmap": "OpenStreetMap", "copernicus": "Copernicus", "google": "Google"}
REAL_IMAGERY = {"satellite", "footage", "photo", "archival"}
TYPES = {"map", "animated-map", "satellite", "footage", "stock", "photo", "archival", "graphic",
         "infographic", "ai"}
BAD_SOURCE = ("google.com/search", "images.google", "pinterest.", "youtube.com", "youtu.be", "tiktok.com")

def norm_license(v):
    v = (v or "").strip().lower().replace(" ", "-").replace("_", "-")
    v = re.sub(r"-?\d(\.\d)?$", "", v)                 # cc-by-4.0 -> cc-by
    alias = {"pd": "public-domain", "public": "public-domain", "us-gov-pd": "us-gov",
             "usgov": "us-gov", "osm": "odbl", "sentinel": "copernicus", "own": "original",
             "ai": "ai-generated", "cc-by-sa-": "cc-by-sa"}
    return alias.get(v, v)

def cells(line): return [c.strip() for c in line.strip().strip("|").split("|")]

def parse(path):
    rows, header = [], None
    for line in open(path, encoding="utf-8"):
        if not line.strip().startswith("|"): continue
        c = cells(line)
        if all(re.fullmatch(r":?-{2,}:?", x) for x in c if x): continue
        if header is None: header = [h.lower() for h in c]; continue
        r = dict(zip(header, c + [""] * (len(header) - len(c))))
        if r.get("id"): rows.append(r)
    return rows

def check(rows):
    fails, warns, disclose, credits = [], [], [], []
    for r in rows:
        aid = r.get("id", "?")
        typ = (r.get("type") or "").lower()
        lic_raw = r.get("license", "")
        lic = norm_license(lic_raw)
        attr = r.get("attribution", "").strip()
        ai = (r.get("ai") or "no").strip().lower()
        src = f"{r.get('source','')} {r.get('url','')}".lower()
        if typ not in TYPES: warns.append((aid, f"type '{typ or '-'}' is not one of {', '.join(sorted(TYPES))}"))
        if not r.get("source") and not r.get("url") and lic not in {"original", "ai-generated"}:
            fails.append((aid, "no source - where did this come from?"))
        if any(b in src for b in BAD_SOURCE):
            fails.append((aid, "a search page, Pinterest or a re-upload is not a source - find the original"))
        if not lic or lic in {"unknown", "?", "-", "tbd"}:
            fails.append((aid, "no license - nothing goes in without one")); continue
        if "fair" in lic:
            fails.append((aid, "'fair use' is a defence, not a license - replace it or get human sign-off")); continue
        if lic.startswith("cc-by-nc"):
            fails.append((aid, "non-commercial license on a monetized channel - replace it")); continue
        if "nd" in lic.split("-") and lic.startswith("cc"):
            fails.append((aid, "no-derivatives license - cropping, labelling or animating it is a derivative")); continue
        known = lic in OK_PLAIN or lic in NEEDS_ATTR or lic.startswith("stock:")
        if not known:
            fails.append((aid, f"license '{lic_raw}' is not recognised - use one of the listed names")); continue
        if lic.startswith("stock:") and not (r.get("url") or re.search(r"\d{4,}", r.get("source", ""))):
            warns.append((aid, "stock asset with no URL or asset ID - you will not find the license later"))
        if lic in NEEDS_ATTR:
            if not attr: fails.append((aid, f"{lic} requires an attribution line"))
            elif lic in MUST_NAME and MUST_NAME[lic] not in attr.lower():
                fails.append((aid, f"{lic} attribution must name {DISPLAY[MUST_NAME[lic]]}"))
        if lic == "us-gov": warns.append((aid, "U.S. government work - usually public domain; credit the agency anyway"))
        if ai not in {"no", "stylized", "realistic"}:
            fails.append((aid, f"AI must be no, stylized or realistic (got '{ai}')"))
        is_ai = ai != "no" or typ == "ai" or lic == "ai-generated"
        if is_ai and typ in REAL_IMAGERY:
            fails.append((aid, f"AI cannot stand in for real {typ} - use real imagery or relabel it as an illustration"))
        if is_ai and lic != "ai-generated":
            warns.append((aid, "AI visual - license should read ai-generated, with the tool named in Source"))
        if ai == "realistic":
            disclose.append(aid)
            warns.append((aid, "realistic AI - must not be presented as the real place; tick the synthetic-content disclosure at upload"))
        if attr: credits.append(attr)
    return fails, warns, disclose, list(dict.fromkeys(credits))

def main():
    a = sys.argv[1:]
    as_json, want_credits = "--json" in a, "--credits" in a
    files = [x for x in a if not x.startswith("--")]
    if not files: print(__doc__); sys.exit(2)
    rows = parse(files[0])
    fails, warns, disclose, credits = check(rows)
    out = {"gate": "PASS" if not fails else "FAIL", "assets": len(rows), "fails": fails, "warnings": warns,
           "disclosure_required": bool(disclose), "disclosure_assets": disclose, "credits": credits}
    if as_json: print(json.dumps(out, indent=1))
    else:
        print(f"\n  {files[0]}: {len(rows)} assets")
        for w, m in fails: print(f"    FAIL  {w:<6} {m}")
        for w, m in warns: print(f"    warn  {w:<6} {m}")
        print(f"\n  UPLOAD: altered/synthetic disclosure {'REQUIRED (' + ', '.join(disclose) + ')' if disclose else 'not triggered by these assets'}")
        if want_credits and credits:
            print("\n  Credits block for the description:\n")
            for c in credits: print(f"    {c}")
        print(f"\n  GATE: {out['gate']}\n")
    sys.exit(0 if not fails else 1)

if __name__ == "__main__":
    main()
