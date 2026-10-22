---
name: yt-publish
description: Upload finished Shorts and long videos to the OrbitalAtlas YouTube channel through the official YouTube Data API v3 (OAuth 2.0), with a duplicate guard, a publish ledger and a real-status check. Use for "upload this", "publish", "schedule", "connect YouTube", "check my channel". Uploads are PRIVATE unless the owner explicitly approves visibility. Not for editing existing videos.
---

# yt-publish

One tool: `publish.py` (stdlib only, no paid services). Setup walkthrough: `docs/youtube-setup.md`.

## Rules
- Never publish, schedule, make public/unlisted, or touch an existing video without the owner's explicit
  go-ahead in this conversation. The tool has no edit/delete command by design.
- Always `plan` first, show the owner the request body, then `upload --confirm`.
  `--approve-visibility` only after the owner approves that specific upload going visible/scheduled.
- `made_for_kids` and `contains_synthetic_media` are the owner's decisions - ask, never default.
- Never ask for, print or store the client secret / refresh token in chat or in the repo.

## Flow
1. `plan --spec ep.json` - validates metadata, Short rules (vertical/square, <=180 s via ffprobe), duplicate check.
2. `upload --spec ep.json --confirm` - resumable upload, ledger `started` -> `uploaded` -> `verified`
   (`publish/ledger.jsonl`), then reads the video back and reports YouTube's real `privacyStatus`.
3. `status --video-id ID` any time later.

A file whose SHA-256 is already in the ledger (even an interrupted `started` record) is refused.

## Related video on Shorts
The public API has no field for the Shorts "Related video" link. Tool-side substitute: `related_long_url`
in a Short's spec adds "Full video: <url>" to its description. The real Related-video link is set by hand in
YouTube Studio: Content -> Shorts -> the Short -> Details -> Related video -> pick the long video.

## Limits to know
- Quota: 10,000 units/day; one upload costs ~1,600 (about 6 uploads/day).
- API projects not yet audited by YouTube get every upload locked to private (checked and reported after
  upload). Audit form: https://support.google.com/youtube/contact/yt_api_form
- Google app left in "Testing" => refresh token dies after 7 days. Publish the app to "In production".
