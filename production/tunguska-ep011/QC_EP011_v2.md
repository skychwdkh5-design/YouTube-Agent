# EP011 v2 (new opening, 0-12 s) - QC 2026-11-06

File: EP011_final_1080p_v2.mp4 - sha256 8bf8717bf1ccce907ac411b50a18c7fc68963a41a889455f034072b95f4a3335, 195,806,201 bytes.

- Changed: frames 0-359 only (0-12 s). Frame 0 = owner's new cover (thumbs/cover_v2.png); the plate comes alive with drifting smoke,
  glow flicker and heat shimmer, a 2.5D push toward the epicenter, and dissolves into the existing film at 11.5-12.0 s.
- The cover's inset "archive photo" is generated imagery; in the film it is replaced by the real May 1929 Kulik expedition photo in the same frame.
- Unchanged: script, Adam narration, audio track (bit-identical AAC stream), everything after 12 s (PSNR inf at 300-330 s; 50 dB at 12.5-72.5 s from re-encoded GOPs only).
- yt-qc --profile long: PASS (1920x1080, 30/1 fps, 8:09.3, full decode clean, no black frames, no freezes >= 2.5 s, -15.0 LUFS).
- Frame 0 vs new cover: mean abs difference 2.8-4.9/255 outside the inset (compression/denoise), 10-12/255 overall with the real 1929 photo in the inset.
- Motion 0-14 s: frame-to-frame change rises and falls smoothly (median 4.8, peak 12.4 at ~10 s at the fastest point of the push); no single-frame jumps; intentional 0.6 s hold on the cover at the start.
- Not uploaded. The publish-data queue still points to v1 (sha 30b6e1f8...); switching to v2 needs a new store run, queue update, new card and the owner's approval.
