# Chat-to-publish architecture

Goal: after one-time setup the owner controls publishing only by chat: *"Одобряю EP006, публикуй завтра в 19:00"*.
Status: implemented and tested offline, **not active**. The existing gated workflows (Environment review) stay as they are until the owner enables this.

## 1. What Claude can actually do from a session (verified in this project)

| Capability | Tool | Evidence |
|---|---|---|
| Dispatch a workflow with inputs | GitHub MCP `actions_run_trigger` (run_workflow) | dispatched `youtube-check.yml` on a branch ref; ran as the owner |
| Read runs, jobs, logs | `actions_list`, `actions_get`, `get_job_logs` | read the channel check, both dry runs and Stage media |
| Write files to a branch, comment, open PRs | `create_or_update_file`, `push_files`, issue/PR tools | used for PRs #27-#29 |
| Change repository Variables, Secrets or Environments | **none** | owner does this once |
| Upload release assets | **none** | media goes LFS branch -> `stage-media` workflow |
| Cryptographically verify that a chat message came from the owner | **none** | see section 4 |

The GitHub tool connection dropped and returned several times in this session. If it is down when you approve, Claude says so and nothing is published;
the gated workflows still work by hand.

## 2. Flow

1. Claude builds the release (video, thumbnail, description, captions), runs QC and the thumbnail gate, and writes the queue entry on branch `publish-data`.
2. Claude shows the **approval card** (`approval.py card`): id, title, thumbnail, file sha256, publish time in Asia/Ho_Chi_Minh and UTC, flags, and a code derived from the content hash. Then asks: *"Разрешаешь публикацию?"*
3. Owner: *"Да, публикуй"* / *"Одобряю EP006, публикуй завтра в 19:00"*.
4. Claude checks the consent rules (section 3), resolves the time, writes the **approval record** to `publish-data` (`approval.py make`), and dispatches **YouTube publish (chat-approved)** with the 40-char data commit and the approval id.
5. The workflow re-verifies everything from that commit, uploads the video **private with publishAt**, sets thumbnail and captions, reads the video back from YouTube and writes the result to the ledger.
6. Claude reads the run, checks the real status (private, scheduled time), and reports the link. YouTube itself makes the video public at `publishAt`.
7. An audit issue is opened by the workflow, so the owner's GitHub app gets a notification without any click; the release can be cancelled in Studio until its time.

Releases: a **long video** needs its own approval each time (`scope: single_release`, exactly one item, kind long). **Shorts** are approved as a list (`scope: short_list`); once uploaded
with their own times they go out by themselves.

## 3. What an approval binds, and what is refused

The record holds, per item: id, kind, title, publish_at, file sha256, `content_hash` (title, description, tags, flags, related link, file sha256, thumbnail sha256,
captions sha256) and `entry_hash` (= content + time). The workflow recomputes them from the pinned `publish-data` commit and from the draft release manifest. Refused:

- any change after approval (title, description, tags, flags, thumbnail, captions, file, time) -> hashes differ;
- a file in the release whose sha256 is not the approved one;
- a record older than 24 h, dated in the future, tampered, or already executed (single use; `approval_done` in the ledger);
- publish time less than 30 minutes or more than 30 days ahead (a veto window always exists);
- a consent quote that does not name the release, has no approving word, contains a negation (не/нет/stop/cancel...) or is a question;
- a long video inside a Shorts list, or more than one long video in one approval;
- open issues in the queue entry, a title that is not final, a long video without a passing thumbnail review;
- an earlier undetermined upload of the same file (it must be reconciled first, never blindly re-uploaded), a title already on the channel, wrong channel id;
- more than 8 uploads in a UTC day;
- a data commit that is not on `publish-data`, a non-owner dispatcher, the kill switch off (`CHAT_PUBLISH_ENABLED` not `true`), parallel runs (one at a time).

Existing videos are never edited; no step makes anything public immediately.

## 4. The honest limit and how it is contained

Chat messages are not signed. Without an Environment review nothing *technical* separates "the owner said yes" from "Claude says the owner said yes":
the consent is attested by Claude and recorded verbatim (`owner_quote`). The design contains the damage of a mistaken or manipulated consent instead of pretending otherwise:

- it can only release exactly the content that was shown on the card, at the time recorded, scheduled at least 30 minutes ahead;
- it cannot release anything unfinished (title, QC, thumbnail gate) or anything twice;
- the owner is notified by the audit issue and can cancel in Studio before the time;
- the kill switch is a repository variable only the owner can change.

**Optional hardening (recommended once you trust the flow):** create the secret `APPROVAL_TOTP_SECRET` (a base32 key you also add to any free authenticator app).
The workflow then also requires a 6-digit one-time code, typed by you in the approval message, valid for one time-step and usable once. That is the only
mechanism that proves *you* approved. It is off until the secret exists; it costs one extra number per release.

## 5. Permissions and cost

No new permissions. Claude uses the GitHub access it already has (Actions, contents, issues on this repo); the workflow uses `GITHUB_TOKEN` (contents: write for the ledger branch,
issues: write for the audit issue) and the existing YouTube secrets. No paid service; Actions minutes and Release storage stay within the free tier. Branch `publish-data`
(queue, assets, manifest, approvals) is written by Claude through the GitHub API, so no PR merge is needed per release; the **code** (workflows, scripts) only changes through reviewed PRs.

## 6. One-time owner setup (after merging this PR)

1. Run **Seed publish-data branch (one-time)** (Actions).
2. Tell Claude in chat: "разрешаю писать в ветку publish-data" (needed because Claude otherwise only writes to its working branch).
3. Review the self-tests (`python3 -m unittest discover -s .claude/skills/yt-publish`, also run by every workflow) and say "включи chat-publish".
4. Set the repository variable `CHAT_PUBLISH_ENABLED` = `true` (Settings -> Secrets and variables -> Actions -> Variables). Optional: add `APPROVAL_TOTP_SECRET`.
5. First real use: approve a harmless release and watch the audit issue.

Until step 4 the new workflow does nothing; the gated workflows keep working.

## 7. Not done / needs a follow-up

- No live end-to-end test: it needs the workflow on `main`, the data branch and a real approved upload, none of which are allowed yet. Everything is tested offline (verification, hashes,
  consent rules, TOTP vectors, idempotency, workflow lint).
- Cancel from chat (`cancel`) is not implemented (it would edit a video we uploaded); until then cancel in Studio. It can be added and tested on the private test video.
- Public-publish capability of this API project is still unproven (an unaudited project may force private); the first scheduled release will show it.
