# Daily release pipeline (Orbital Atlas + NEXORA)

Owner decision 2026-11-19: every day one finished long video for the production channel of the day, delivered as one
approval card (video link, cover, title, duration, proposed slot). The owner answers **ОК** (button or text) or
**На правку** (+ comment). "ОК" schedules exactly that version at the card's slot; nothing goes public immediately.
For pipeline releases this card rule replaces the "Одобряю ep0NN" phrase; the chat-publish workflow stays for manual releases.

## Who does what

| Part | Where | What |
|---|---|---|
| Timer | Claude scheduled task, daily 09:41 Asia/Ho_Chi_Minh, bound to the project thread "Запустить ежедневный конвейер выпусков" | runs the procedure below; cards and answers stay in that thread |
| State | branch `publish-data`, `pipeline/releases/*.json`, `pipeline/topics/*.json` | one file per release: stage, artifacts + sha256, versions, cards, approval, schedule |
| Engine | `pipeline/engine.py`, CLI `pipeline/run.py` | stages, versions, cards, the owner's answer, slots (stdlib, tested) |
| YouTube (OA) | `.github/workflows/pipeline-ops.yml` on `pipeline-ops` / `pipeline-media/*` | private preview upload, schedule after "ОК", read-back, status, topic scout |
| YouTube (NEXORA) | NEXORA repo, branch `youtube-ops` (existing `nexora-youtube.yml`, secrets `NEXORA_YT_*`) | `publish/requests/<id>.json` = private upload, `publish/approvals/<id>.json` (privacy scheduled + publish_at) = schedule |
| Voice | `pipeline/voice_cache.py` -> /yt-voice (ElevenLabs via the session proxy) | Egor Norrator (Multilingual v2) for OA and NEXORA, with defaults in `pipeline/config/channels.json`; cache by text+voice+parameters; per-release/day/month character limits |
| Render | /yt-render timeline v3 `long` + ATLAS projection (PR #58) | first frame = cover, motion from frame 1, paper callouts, no burned subtitles |
| Gate | `pipeline/qc_gate.py` | /yt-qc long, cover = frame 0, motion, no burned subs, ATLAS placement, final voice, rights ledger, thumbcheck, metadata |
| Release check | `verify-release.yml` (every 15 min, existing) | confirms the video really went public after publishAt; opens an issue if not |

## Schedule

**From 2026-11-22 (owner): one long video EVERY day on EACH channel** - Orbital Atlas and NEXORA both produce daily, each with
its own release, its own ОК card and its own 08:00 slot (`rotation.daily_all_from`; `run.py today` lists `production_channels`
and `start_new`). Before that date: `pipeline/config/channels.json`: production days alternated from 2026-11-03 (even day = Orbital Atlas, odd = NEXORA), long
videos at 08:00 Asia/Ho_Chi_Minh on both channels, OA Shorts slots 12:00 and 18:00. Capacity: one long per production day
(raise `long_per_production_day` later). The slot is the nearest free 08:00 at least 3 h ahead, using the channel's real
YouTube schedule (scheduled + published videos) plus the slots this pipeline already holds (open cards, approvals).

## Daily procedure (what the scheduled session does)

1. `git -C ../pipeline-data pull`; `python3 pipeline/run.py today`. Continue every unfinished release from its `resume`
   point before starting anything new; never start a second release while one of that channel is open.
2. Channel status: push `requests/status-<date>.json` (`{"op": "status", "confirm": true}`) to `pipeline-ops`, read
   `results/` (token check + scheduled videos). `error_kind: auth` -> block the release ("owner must log in again"), send ONE
   message with the re-login link, stop; resume from the saved stage when the owner says it is done.
3. Topic (only if no open release): `topics.py next`. Reserve below 5 -> research: scout op (YouTube Data API, free quota),
   NASA/agency news, previous runs; vidIQ only with credits AND the owner's permission for the paid call; record every
   missing source as a gap (`topics.py gap`). Write candidates with primary sources and licensed media, then `next` again.
   A topic without reliable sources or footage is skipped.
4. `run.py new --channel <ch> --topic t.json`. Then, recording each stage with `run.py stage` as it finishes:
   research + script (English, project CLAUDE.md, growth docs, 3 cover concepts -> thumbnail_hook.json) -> `scripted`;
   `voice_cache.py --confirm` (cache hit = free; `over_limit` -> block at `voiced` and tell the owner) -> `voiced`;
   media with a rights ledger (url, licence, credit per asset) + render -> `rendered`; `qc_gate.py` PASS -> `qc_passed`.
   A technical failure is fixed and only the failing stage is re-run.
5. `run.py version ...` -> `run.py media-branch --confirm` -> push the folder as orphan branch `pipeline-media/<id>-v<n>`;
   read `results/preview-<id>-v<n>.json` -> `run.py preview-result`. The video is now PRIVATE on the channel (owner-only link).
6. `run.py slot --status <status result>` -> `run.py card --slot ...` -> post the card text + cover in the thread, then the
   decision card (options "ОК" / "На правку"). Record the message ids with `run.py card-message`.
7. Owner answer -> `run.py decide --choice ok|changes --actor "principal:Егор" --card <id> [--comment]`.
   `approved` -> `run.py schedule-request --confirm --out <pipeline-ops>/requests/schedule-<id>.json`, push, read the result,
   `run.py schedule-result`, reply with the link and the real publishAt. `ambiguous` -> show the open cards to pick from.
   `expired` -> new slot + new card. `duplicate` -> say it is already done (no new action). `changes` -> fix, new version, new card.
8. Push `publish-data` after every state change (one writer: the scheduled session).

## Guarantees and how they are tested

`pipeline/tests` (run by the ops workflow before every operation): repeated "ок" = no new action; expired card; void card
after a new video/cover/title; foreign or relayed answer refused; ambiguous bare "ок"; resume after a crash without paying for
the voice again; one notification per blocker; upload re-run = one upload; lost upload response = adopt by marker tag, never
blind re-upload; schedule repeated / timed out = one update, read back first; another approval cannot move a scheduled video;
slot taken on the channel = new card; test releases are dry-run only.

## Owner actions that only the owner can do

- Re-login when Google expires the token (app in Testing mode: about weekly) - the pipeline sends one link and waits.
- vidIQ paid calls: only with a separate permission per call.
- Merging the code PRs (the data branches work without merges).

## Discovery text (description, chapters, hashtags, tags)

Owner request 2026-11-20: every release gets a description and hashtags that tell YouTube who the video is for.
`pipeline/seo.py` is part of `qc_gate.py`; a FAIL blocks the card. meta.json must contain:

| field | rule |
|---|---|
| `search_queries` | 3 distinct queries a real US viewer would type, best first (write them before the title) |
| description, opening paragraph | the search snippet: says what the viewer gets, contains the main words of query 1, no link |
| chapters | `0:00 ...` first, at least 3, each at least 10 s, matching the narration sections |
| hashtags | 3-5 at the end, specific to the topic (e.g. `#Pulsar #NASA #Fermi`), channel name never first |
| `tags` | 8-15, include query 1 (or all its words) and the channel name, <= 500 characters, no unrelated tags |

Sources and credits stay below the chapters. Hashtags and tags are weak signals compared with title, thumbnail and
viewer behaviour; they help YouTube classify the topic and the search intent, they do not replace packaging.

## End screen (clickable next video)

Owner request 2026-11-20. YouTube Data API v3 has no end-screen endpoint, so the pipeline prepares everything around it:

1. Script: the last spoken line hands off ("...and this one is next" / "watch this next"), no new facts after it.
2. Timeline: the last shot is a 20 s outro after the narration: `python3 pipeline/endscreen.py outro --channel oa|nx
   --bg <clean footage frame> --out media/outro.mp4` (blurred, dimmed, slow push-in, drifting motes so QC sees no freeze;
   "WATCH NEXT" top-left; the element areas stay free). `end.seconds` = narration end + 20.
3. QC: `endscreen tail` = video length - narration length must be 15-20 s.
4. Before the card: `python3 pipeline/endscreen.py pick --release R --status <channel status json>` stores the video to
   recommend (shared topic words, else the newest public long video, never the release itself or a Short); the card
   text then names it with the Studio steps. The owner adds the elements in Studio (browser): Content → the video →
   End screen → "Import from video" (copies the previous layout) or the "1 video, 1 subscribe" template → pick the
   recommended video → Save. Doing this once on the first release makes "Import from video" a one-click step after.


## Motion pass (2026-11-21)

After yt-render, every release runs `python3 pipeline/motion.py --base base.mp4 --timeline timeline.json --rights rights.json
--voice voice.json --spec motion.json --out final.mp4` (`--start/--dur` for a pilot, `--frames t1,t2` for stills). motion.json
holds the key words, hero numbers (`{"at": "<spoken phrase>", "big": "5.3 M", "above": ..., "below": ...}`, use
`"count_up": false` for years and non-integers), per-shot transition overrides and per-asset source lines. Render the base
with no label layers and `"credit": false` on video/still layers: the pass draws captions, HUD, source line, transitions and
the sound layer, and loudness-normalises to -16 LUFS. Effects sit well under the voice (owner 2026-11-22: whooshes peak near -17 dBFS, side-chain ducked by the narration; `tests/test_motion_mix.py`). The cover frame is passed through untouched.

## Live footage share (QC gate, 2026-11-21)

After the owner's review of El Niño / pulsar / Puncak Jaya v1 (0 % filmed footage, "slideshow"), `qc_gate.py` runs
`pipeline/footage.py`: share = moving seconds of video assets declared `"footage": "live"` in rights.json, divided by the
narrated seconds (cover frame and end-screen tail excluded). Stills never count; a "live" clip that holds still (mean
abs difference < 1.2 on a 96x54 grey thumbnail at 2 fps) does not count for those seconds. Below 60 % = FAIL, no card.
Sources that worked: SVS produced-video / B-roll pages (e.g. 13299/13298 Operation IceBridge Alaska aerials, 13946
Landsat 9 launch). Plan the script around the footage you can get before voicing.
