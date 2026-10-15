# Competitor analysis - STATUS: BLOCKED (not produced)
Required: >= 10 channels, >= 12 videos with verifiable 500k+ views, transcripts, hook timing. The container cannot reach www.youtube.com, i.ytimg.com or any
transcript service (egress 403), and web search returns no view counts or transcripts I could verify. Writing titles/views/timings from memory would be
fabrication, so no table is given. `viral_patterns.md` and `reference_shotlist.md` are likewise not produced.
Unblocking: allow www.youtube.com (+ i.ytimg.com, youtubei/transcript endpoints) in the environment network policy, or have the owner paste a list of
URLs with Studio-visible numbers / transcripts. Then yt-viral (`swipe.py`) and manual shot logging can run.
