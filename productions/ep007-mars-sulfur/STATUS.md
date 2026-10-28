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
## 2026-10-28 16:xx ICT — owner APPROVED script + edit; asked for final Adam versions and scheduled upload
Schedule (Asia/Ho_Chi_Minh): long 2026-10-29 08:00 (=01:00Z), Short 1 2026-10-29 12:00 (=05:00Z), Short 2 2026-10-30 12:00 (=05:00Z).
Long title (fixed): NASA’s Rover Ran Over a Rock on Mars. This Was Inside.
Done: cover B checked full size + 168x94, no defects -> package/thumbnail_B_final.jpg (unchanged file, thumbcheck PASS earlier).
  package.py -> package/description_long.txt (chapters computed from final timing) + package/texts.json (Short titles/descriptions).
  HiRISE credit now in the top source line (build.py: g_hirise / v_hirise -> NASA/JPL-Caltech/University of Arizona); takes effect at the next render.
  Adam scripts: adam_beats.md (5,139 chars), adam_short1.md (456), adam_short2.md (401); workflow .github/workflows/ep007-voice.yml.
BLOCKER: Adam cannot be generated. This cloud session cannot reach api.elevenlabs.io (proxy 403) and the repository has
  NO ELEVENLABS_API_KEY secret (voice_manifest.txt). Nothing was charged.
  Fix: owner adds repo secret ELEVENLABS_API_KEY (Settings -> Secrets and variables -> Actions), then re-push voice_request.txt.
After the voice: tts timing -> build.py needs a small adapter from voice.json word timings to beat starts; render; yt-qc;
  package.py with final timing; media to LFS branch -> stage-media; queue entries on publish-data with owner_approval
  (owner approved in chat 2026-10-28 15:59 ICT); dispatch gated publish.yml (owner must approve the GitHub environment
  review; chat-publish is NOT active). Related video: API has no field -> set in Studio by hand; descriptions carry no link yet.
Note: short-06-ep004 is already queued for 2026-10-29T01:00Z, same minute as EP007 long.
Next step: owner adds ELEVENLABS_API_KEY secret (or runs this in Claude Code, where Adam worked for EP003/EP004).
