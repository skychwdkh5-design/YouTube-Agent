# EP004 Jakarta - preflight (2026-10-15)

## Baseline decision
- `main` (3b26881) has NO orbitalatlas engine, no autopilot, no visual docs: it is not a usable base.
- Verified base: `origin/production/ep003-v3` (e514a8d). It contains `feature/visual-engine-v2c` and `autonomy/phase3` (both verified ancestors),
  EP003 V3 is recorded USER_APPROVED (approvals.json `release_v3`), FUTURE_VISUAL_ROADMAP.md and the frozen V2C baseline exist.
- Working branch: `claude/orbitalatlas-ep004-jakarta-bm0egv` (the branch the session was assigned; it had no unique commits, so it was reset to the base).
  The brief's suggested name `production/ep004-jakarta` was not used to avoid pushing to a second branch without permission.
- Nothing pushed to `main`. EP001-EP003 files untouched (protected.py: 23 files identical).

## Preflight results
`orbital.py preflight`: ok (ffmpeg, ffprobe, PIL, numpy, ElevenLabs credential present - NOT used, USGS creds present, guard hook, solutions registry 97 entries).
Not installed: rasterio, cv2 (check whether the shipped tools need them before relying on them).

## Network reality (blocks parts of the brief)
Reachable from this container: doi.org (redirect only), m2m.cr.usgs.gov, svs.gsfc.nasa.gov, nasa.gov, earthobservatory.nasa.gov (301).
**Denied by the egress policy (CONNECT 403 / no route): www.esa.int, dataspace.copernicus.eu, sentinel.esa.int, www.youtube.com, i.ytimg.com,
en.wikipedia.org, tandfonline.com, sciencedirect.com, nature.com, mdpi.com, api.crossref.org, api.openalex.org, karya.brin.go.id, eos.org.**
WebFetch cannot resolve www.esa.int either. Only WebSearch (snippets) works for the open web.
Consequences: see BLOCKERS in the milestone report. Nothing was mocked.
