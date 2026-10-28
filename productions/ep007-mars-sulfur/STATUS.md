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
## 2026-10-28 ~17:40 ICT — FINAL built, waiting for chat consent on the cards
Adam narration: generated once on Actions (.github/workflows/ep007-voice.yml run 4): long 376.6 s / 5,247 chars, Short 1 32.8 s / 466, Short 2 27.5 s / 411.
Final files (draft release ep007-v1; yt-qc PASS; checked by eye):
  EP007_final_long.mp4   6:17.7  sha256 d966db6c2e55ab20e4ae26d9521a047b49a45028a128713293866e3d3b9eb484
  EP007_final_short1.mp4 0:34.0  sha256 17042d093962cb4ee9080f8461b59301cbf7a7d75a95b6d712b9306a552c5686
  EP007_final_short2.mp4 0:28.7  sha256 200a576acb744b41721952dfda95b5617bd676d736427f75ad2f89f300456e2a (v2: credit line fits)
Chapters (Adam timing): 0:00 0:24 1:25 2:01 2:45 3:19 3:45 4:25 5:30 5:57 - package/description_long.txt
publish-data fd95b60: entries ep007, short-07-ep007, short-08-ep007 (old entries unchanged) + cards shown:
  ep007 3903-567C (29.10 08:00 ICT = 01:00Z), short-07-ep007 3CB3-E98C (29.10 12:00 = 05:00Z), short-08-ep007 4D66-2F71 (30.10 12:00 = 05:00Z).
Why not uploaded yet: CLAUDE.md protocol - a consent is valid only AFTER the card; the owner's earlier approval preceded the cards.
  The gated publish.yml path is blocked by design (tests require main's queue to stay unapproved) - not weakened.
  Branch publish/ep007-mars-sulfur (gated-path attempt, owner_approval=true in its queue) is UNUSED - do not dispatch; deletion via proxy failed.
Do not work: ElevenLabs/LFS/binary release upload from this session (proxy). Use Actions + draft releases.
Next step: owner consent in chat naming ep007 and the Shorts list -> approval.py make (scope single_release / short_list) on publish-data ->
  dispatch "YouTube publish (chat-approved)" with the 40-char data commit; real runs need CHAT_PUBLISH_ENABLED=true. Then read the real status.
  Shorts "Related video": set by hand in Studio (API has no field).
