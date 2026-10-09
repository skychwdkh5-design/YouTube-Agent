# EP002 Dubai — Diagnostic Preview QA

Base: 0579238. Script: `visuals/preview/render_diagnostic_preview.py` (video only, no audio; frames piped to ffmpeg libx264). Output stays local and uncommitted: `productions/dubai/visuals/_local_assets/previews/EP002_diagnostic_preview.mp4`. SCRIPT_LOCK and narration untouched; no TTS, no paid API.

## File
H.264 High, yuv420p, 1920x1080, 30 fps, 1980 frames, 66.000 s, 15,058,048 bytes (about 14.4 MiB), SHA-256 prefix `be702e3b586766bf`. Full decode pass (`ffmpeg -f null`) clean. Delivered to the user through the Claude interface (SendUserFile reported delivery; receipt on the user's side not confirmed).

## Segments (66 s)
Title 3 s · B1 10 s · D1 12 s · E1 16 s · ISS 8 s · variation test 14 s (E4 push-in/dissolve 5 s, E5 plan cuts 5 s, H3 vs E5 split 4 s) · credits 3 s.

## Checks and findings
- No-data borders: exact-zero pixels in the R_PALM rectangle (140,1445,800,450) of all 12 frames = 0.000 %. Per-second near-black scan flagged only the title, credits, the E1 background, and the split-screen bars (layout, not no-data).
- B1: the 4x crop shows the small light patch with a bright edge and a faint plume; the thin yellow ring with the words "light patch in open water" fades in only after the push finishes. Readable, soft, not a palm, none claimed.
- D1: Palm Jebel Ali (palm2.jpg crop 60,2780,1280,720) then Palm Jumeirah (915,1905,960,540), same image and date, labelled by name; circular barriers visible on both. Correct.
- E1: 12 tiles of one pixel rectangle, year labels; the two 2002 frames labelled "2002 (Feb)" and "2002 (Oct)" (first render had two bare "2002" labels, fixed); 2011 appears as year only. The tiles show the palm sitting a few tens of original pixels differently from frame to frame (2004-2011 palm nearer the left edge, coast offset in 2010): visual proof that the frames are not co-registered. The video says "not geographically registered" and uses no overlay or wipe.
- ISS: labelled as a photograph (cropped and contrast-enhanced by NASA); the move runs between the two palm islands.
- Variation: E4 push-in adds motion and the year flip works; E5 plan = three hard labeled cuts repeating the hook stills; H3 wide versus E5 mid crop of the same palm look too similar.
- Softness: R_PALM at 1920 px is a 2.4x upscale and visibly soft; B1 at 4x is softer. Acceptable for ASTER; avoid going tighter.

## Repetition assessment
E4 and E5 echo H1/H2 deliberately; E4 differs by motion and text, E5 by labeled cuts across instruments. H3/E5 ISS crops are near-duplicates. Suggested fixes before the full cut: make E5's ISS shot a different subject (for example Palm Jebel Ali or The World) or drop E5's ISS cut; keep E4's push-in; vary crops for the six ASTER-2006 scenes.

## Fixes made during QA
Tag moved to top-left so it no longer collides with E1 header and E4 year label; 2002 labels disambiguated; year labels given a dark outline.

## Not done
No audio, no captions, no final render, no timing against narration.
