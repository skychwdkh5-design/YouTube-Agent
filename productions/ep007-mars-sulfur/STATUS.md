# EP007 status (2026-10-28)
Done (drafts, NOT approved, NOT published, NOT queued):
- Originals: 10 NASA/JPL files, SHA-256 in fetch_manifest.tsv history; stored in the DRAFT release "ep007-originals"
  (not in Git). Path: .github/workflows/ep007-fetch.yml on this branch (push fetch_list.txt -> runner downloads -> draft release;
  this session downloads release assets via `gh api -H "Accept: application/octet-stream" .../releases/assets/<id>`).
- Script + shot list: beats.py (long), short1.py, short2.py -> script_and_shotlist.md; titles.md; covers/ (make_covers.py).
- Draft renders (local only, git-ignored): EP007_draft_long.mp4 6:06, EP007_draft_short1.mp4 0:34, EP007_draft_short2.mp4 0:29.
  yt-qc PASS (Shorts checked with --width 1080 --height 1920). Temporary voice: Kokoro am_michael (tts_draft.py, speed 0.93/0.95).
Not working: direct download from this cloud session (NASA hosts 403 via proxy); workflow artifacts (blob host 403);
  photojournal.jpl.nasa.gov/tiff/* returns HTML - use assets.science.nasa.gov paths; PIA26363 8192px JPG has a purple seam - use the lossless PNG.
Remaining:
1. Owner reviews script + drafts. 2. After approval only: Adam voice via yt-voice (--confirm), yt-captions, re-render with build.py
   (timing comes from narration timing; adapt build.py to read voice.json words). 3. Owner picks title/cover; full thumbnail gate (section 5)
   recorded in a review file. 4. Optional: delete the temporary workflow and draft release after final render.
Fixes for the next render (owner, 2026-10-28):
- Add HiRISE credit (NASA/JPL-Caltech/University of Arizona) to the top source line of the long video (currently only in the graphic's footer).
- Shorts stay 20-35 s as ordered (do not lengthen to 45-55).
Next step: wait for owner's script/draft approval.
