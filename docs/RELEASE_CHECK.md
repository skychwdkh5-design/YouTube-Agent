# Independent release check

Workflow `Verify scheduled releases (read-only)` (`.github/workflows/verify-release.yml`, script `.claude/skills/yt-publish/release_check.py`).
It runs every 15 minutes on GitHub, with no Claude session, and answers one question: did a scheduled video really become public?

Flow, from the ledger (`publish-ledger`) alone: a video is *awaiting release* when the ledger has a `verified` event (ok, with `publishAt`) and no `release_confirmed`.

| Situation | What happens |
|---|---|
| before `publishAt` + 3 min | nothing, no YouTube call (a run with nothing due makes no network call at all) |
| public | ledger `release_confirmed` (with the delay in seconds); an open failure issue gets a comment and is closed |
| still private | ledger `release_check` (attempt n); at attempt 3 **one** GitHub Issue is opened (it notifies the owner) with the YouTube status fields and what to do; checks continue, so a late release is still confirmed |
| video missing on the channel | issue at once |
| `publishAt` moved into the future (Studio) | `release_rescheduled`, no alarm |
| 48 h after `publishAt` | `release_check_abandoned`, stop |

Guarantees: only `videos.list` (1 quota unit) plus the OAuth token refresh; no upload, no edit, no visibility or time change; one issue per video; manual runs default to dry run;
runs in the same concurrency group as the upload workflows (one ledger writer at a time); private test videos and unverified uploads are ignored.
Cost: public repository, free Actions minutes; quota negligible.

Caveats: scheduled workflows run only from the default branch and GitHub disables them after 60 days without repository activity; runs can start a few minutes late.
