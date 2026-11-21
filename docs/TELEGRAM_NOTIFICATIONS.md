# Telegram notifications ("Claude Control")

Status: notifications - test path only; button handler - designed, **not deployed**. No production workflow is changed.

## Why it is built this way

* The repository is **public**: anyone can read run logs, workflow inputs and branches. So the bot token and the chat id
  never appear in logs or files. The token lives only in the `TELEGRAM_BOT_TOKEN` secret; the chat id is found once by
  pairing and delivered **only to the owner's Telegram chat**, then stored as the `TELEGRAM_CHAT_ID` secret.
  `telegram/tg.py` scrubs both from every output and masks them in Actions logs.
* **GitHub Actions is not a server.** It can send messages, but it cannot receive a button press. Presses go to a small
  always-on Cloudflare Worker (`telegram/worker/worker.js`) that only authenticates and forwards them as
  `repository_dispatch` to `telegram-decision.yml`.
* **A Telegram press is not publishing consent.** CLAUDE.md requires consent in the Claude chat, bound to the last
  approval card. `telegram-decision.yml` only records the decision on branch `telegram-data`; it never dispatches,
  schedules or publishes. Using presses as consent would need a separate, explicit owner decision and a protocol change.

## Files

| File | Role |
|---|---|
| `telegram/tg.py` | stdlib client: `check`, `pair`, `send-test`, `notify`, `decide`; token/chat-id hygiene; HMAC buttons |
| `telegram/test_tg.py` | unit tests (run in every Telegram workflow) |
| `.github/workflows/telegram-setup.yml` | token/webhook check and one-time pairing (manual or push to `telegram-ops`) |
| `.github/workflows/telegram-test.yml` | sends "✅ Claude Control подключён к GitHub. Система уведомлений работает" |
| `.github/workflows/telegram-notify.yml` | reusable (`workflow_call`): `video_ready`, `error`, `approval`, `info` |
| `.github/workflows/telegram-decision.yml` | records a verified button press (record only) |
| `telegram/worker/` | Cloudflare Worker + `wrangler.toml.example` |

## Pairing (one time)

1. Claude generates a one-time code and stores only its sha256 in `requests/setup.json` on branch `telegram-ops`.
2. The owner sends `/start CODE` to the bot in a private chat.
3. `telegram-setup.yml` (op `pair`) calls `getUpdates` **without offset** (nothing consumed), accepts only a private chat
   whose `/start` payload hashes to the stored sha256, and DMs that chat its chat id. Ambiguous or missing -> no DM.
4. The owner adds the number as secret `TELEGRAM_CHAT_ID`.

If the bot already has a webhook (e.g. a Cloudflare bot), `getUpdates` is impossible; the workflow reports
`webhook_active` and **does not** delete the webhook - that is the owner's decision.

## Notification types

| kind | when | buttons |
|---|---|---|
| `video_ready` | final render stored / QC passed / release scheduled | - |
| `error` | a workflow step failed (link to the run) | - |
| `approval` | a decision is needed (request id registered on `telegram-data` with expiry first) | ✅ / ❌ (signed) |
| `info` | status replies (e.g. "decision recorded") | - |

Wiring into production workflows (e.g. `uses: ./.github/workflows/telegram-notify.yml` in a final job with
`if: failure()`) is a later, owner-approved step.

## Button security

`callback_data = <y|n>:<request_id>:<sig>`, `sig = base64url(HMAC-SHA256(TELEGRAM_CALLBACK_SECRET, "v1|action|id|chat"))[:22]`
(≤ 64 bytes). The Worker checks the webhook `secret_token` header, the presser's id = owner chat and the signature, then
answers the press and dispatches. The workflow re-checks the signature and owner, that the request exists, is not expired
and was not decided before (single use), and records it.

## Enabling the button handler later (not done now)

1. Secret `TELEGRAM_CALLBACK_SECRET` (random, ≥ 32 chars) in GitHub **and** in the Worker.
2. Fine-grained PAT, this repository only, *Contents: Read and write* -> Worker secret `GITHUB_TOKEN`.
3. `npx wrangler deploy` from `telegram/worker`, then the Worker secrets listed in `worker.js`.
4. `setWebhook` with `url=<worker url>`, `secret_token=<TELEGRAM_WEBHOOK_SECRET>`, `allowed_updates=["callback_query"]`.
   After this, `getUpdates` stops working for this bot (pairing must be finished first).

If the same bot already serves another webhook, use a **separate bot** for Claude Control instead of replacing it.
