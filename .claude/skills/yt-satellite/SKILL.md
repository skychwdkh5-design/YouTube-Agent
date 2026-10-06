---
name: yt-satellite
description: >-
  Pull real Landsat satellite evidence for a YouTube video from the official
  USGS EROS M2M API - find scenes by place and date, read their metadata,
  check download options, and fetch imagery only when the video needs it.
  Use ONLY when satellite imagery or Landsat data is relevant: "show this
  from space", before/after of a lake, glacier, wildfire, flood, city,
  deforestation, coastline, or any claim that rests on what the ground
  looked like on a date. Not for ordinary YouTube research.
---

# yt-satellite

A satellite image in a video is a claim. This skill makes sure every one of them is a real scene
with an ID, a date and a source - or that the video says plainly that there is none.

```bash
python3 usgs_m2m.py auth
python3 usgs_m2m.py search --point 36.0 -114.75 --radius-km 10 --start 2025-06-01 --end 2025-08-31 --cloud 20
python3 usgs_m2m.py metadata --entity <entityId>
python3 usgs_m2m.py options  --entity <entityId>
```

Everything prints JSON. Default dataset is `landsat_ot_c2_l1` (Landsat 8-9 OLI/TIRS Collection 2
Level-1); pass `--dataset` for another, and `datasets --keyword landsat` lists what exists.

## When to use it - and when not

Use it when the research question depends on what a place looked like from orbit on a date: water
levels, burn scars, ice, urban growth, floods, land clearing. Landsat 8 data starts in 2013, Landsat 9
in late 2021, with a 16-day revisit per satellite and 30 m pixels - it will not show a car, a building
detail or a single day you did not get a pass for.

Do not reach for it for titles, scripts, comments, SEO, retention or any task that is not about the
physical world. The other yt-* skills never need it.

## Credentials

`USGS_M2M_USERNAME` and `USGS_M2M_TOKEN` (an M2M application token) must be in the environment. The
script reads them, never prints them, and logs the session out after every command. Never paste them
into a chat, a file, a commit or a command line. If either is missing the script says which one -
pass that on to the user; do not ask them to type the token into the conversation.

## The workflow

1. **Search** with `--point LAT LON [--radius-km]` or `--bbox MINLON MINLAT MAXLON MAXLAT`, plus
   `--start`/`--end`. Add `--cloud 20` when the image has to be legible.
2. **Pick** by date and cloud cover, then read `metadata` for the scene you would cite.
3. **Check `options`** - this is free and downloads nothing. The browse JPEGs (~6 MB) are usually
   enough for a video; the Level-1 product bundle is over 1 GB and almost never is.
4. **Download only when the user wants the image in hand**, and only after saying what and how big:

   ```bash
   python3 usgs_m2m.py download --entity <id> --product "Full-Resolution Browse (Natural Color) JPEG" \
       --out ./usgs --confirm
   ```

   Without `--confirm` it refuses. Anything over `--max-mb` (default 50) is refused too; raise it
   only when the user explicitly asks for the full product. A network or disk failure mid-file
   deletes the partial file and comes back as a JSON error.
5. **Cleanup is automatic.** After every download request the script removes its order from the
   USGS queue (`download-order-remove`) and reports it under `"cleanup"` as `removed` or `failed`.
   A failed cleanup is not a failed download: if `"status": "ok"` and the file is there, the
   image is good.

## Statuses and edge cases

- `"status": "no_options"` (from `options` or `download`) means USGS lists no download options
  at all for that entity in that dataset. Report it; do not guess another product or scene.
- A bad number (`--point abc 1`, `--max x`, `--max-mb x`, `--cloud 150`) is a JSON error before
  anything touches the API.
- **Near ±180° longitude:** a box that crosses the antimeridian (or a `--point` whose radius
  reaches across it) is refused, not wrapped. Run two `--bbox` searches, one each side of 180/-180,
  and report both.
- **Near the poles:** a box past ±90° latitude is refused. Landsat's WRS-2 grid does not reach the
  poles themselves, so a high-latitude `no_scenes` can be the honest answer.

## No fabrication

- `"status": "no_scenes"` means there is no suitable scene for that place, window and cloud limit.
  Say exactly that. Widening the dates, the area or the cloud limit is a NEW search the user agrees
  to, reported as such - never a silent substitute.
- Never describe what a scene shows until you have looked at its browse image. Metadata tells you
  when and where, not what is in it.
- Never stand in a stock photo, a different satellite or a "representative" image for Landsat
  evidence.
- An error is reported verbatim from the `error` field. It is not a reason to guess.

## What to hand back

For every scene the video will use: `displayId`, acquisition date, cloud cover, the dataset name,
and the credit line **"Landsat imagery courtesy of the U.S. Geological Survey"**. Put that credit in
the description draft (`/yt-seo`) and on screen where the image appears.

## The gate

Nothing here publishes. This skill finds evidence and you decide what goes in the video. The last
line of every run is the question: **use it, or search again?**
