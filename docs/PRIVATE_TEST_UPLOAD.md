# PRIVATE_TEST - one private upload of EP002_Dubai_Short_01_JUST_SEA.mp4

Mode `private_test` of the *YouTube publish* workflow. Owner-authorised on 2026-10-22 for exactly one file.

What it does (and cannot do)
- Uploads that one MP4 as **private**, with **no publishAt**, title prefixed `[PRIVATE TEST] `. No thumbnail, no captions, no schedule.
- Only entries flagged `private_test_allowed` in `publish/queue.json` are accepted (only `short-01-ep002`); the run needs exactly one `--ids` value and the live channel inventory.
- `owner_approval` of every item is neither read nor changed. A later real upload of the same file is not blocked by the test (the ledger keys the test as `private_test:<sha256>`).
- Environment protection stays: a real run waits for your approval on `youtube-approval`.
- Undetermined result (timeout, crash): it never re-uploads; the next run first looks for the video on the channel (by title) and adopts it, otherwise stops.
- After the upload it reads the video back from YouTube and writes to the ledger (branch `publish-ledger`): video id, file sha256, uploadStatus, processingStatus, privacyStatus, publishAt, madeForKids, rejection/failure reasons, notes.
- Limit: a private upload cannot show whether this API project may publish publicly or on a schedule (unaudited projects are locked to private).
- The video is never switched to Public by this tool. Delete the test video yourself in Studio when you no longer need it.

Owner steps (iPad)
1. Merge the PR that adds this mode.
2. Actions -> *YouTube publish (manual, gated)* -> Run workflow: mode `private_test`, ids `short-01-ep002`, **dry_run ON** -> expect `ready (dry run)`.
3. Run again: mode `private_test`, ids `short-01-ep002`, dry_run **OFF**, confirm `UPLOAD private_test` -> approve the `youtube-approval` environment when GitHub asks.
