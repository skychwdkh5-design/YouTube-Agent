# Telegram notifications ("Claude Control")

Status: **APPROVAL ONLY / SILENT MODE** (owner policy, 2026-11-21). Button handler - designed, **not deployed**.
No production workflow calls Telegram yet; wiring needs the owner's permission.

## Silent mode - the rule

Claude writes to the owner in Telegram **only** when the owner personally has to act. Exactly three kinds exist:

| kind | when |
|---|---|
| `APPROVAL_REQUIRED` | approval of a video, a publication or another action |
| `PERMISSION_REQUIRED` | an action needs the owner's permission |
| `HUMAN_INTERVENTION_REQUIRED` | a blocker that cannot be removed safely and automatically |

Never sent (logged as `suppressed`): start, progress, rendering, success, ordinary errors, publications, daily reports,
anything Claude can finish itself within permissions already given (`auto_resolvable: true`).

Before asking, Claude first does safe automatic recovery. `HUMAN_INTERVENTION_REQUIRED` is refused unless
`recovery_attempted` says what was tried. Every message carries: project, what is needed, why Claude cannot continue,
consequences of approve / reject, buttons (Approve / Reject only when safe; "Подробнее" = link) and the link to the
video, task or session.

| guarantee | how |
|---|---|
| one open decision = one notification | `dedup_key`; repeats are dropped while it is open |
| one reminder only | `telegram-sweep.yml` sends one reminder 30+ min after delivery, then silence |
| no approval by timeout | expiry (default 7 days) closes the request as `expired`; no decision is ever recorded by time |
| nothing lost | outbox: request saved on `telegram-data` before delivery; failures stay `queued` and are retried every 10 min; after 6 h undelivered -> one GitHub issue as a fallback |
| suppressed really suppressed | the gate is the only sender; unit tests send every routine kind and assert nothing went out |
| Claude Code permissions | not bypassed: permissions that cannot be granted in Telegram get a link to where to grant them, no buttons |
| publishing | a press is recorded only; it never starts publishing (CLAUDE.md chat-to-publish unchanged) |

Exception: `telegram-setup.yml` / `telegram-test.yml` reply only to the owner's own manual run.

### How to ask (the only allowed senders)

* From a workflow (any repo: Orbital Atlas, NEXORA, ANIMAVERSE):
  ```yaml
  ask-owner:
    uses: skychwdkh5-design/YouTube-Agent/.github/workflows/telegram-notify.yml@main
    with:
      kind: HUMAN_INTERVENTION_REQUIRED
      project: OrbitalAtlas
      need: "Обновить YouTube OAuth: токен отозван"
      why_blocked: "Новый вход в Google может сделать только владелец"
      recovery_attempted: "Два повтора с паузой; токен отклоняется (invalid_grant)"
      on_approve: "После входа загрузки продолжатся сами"
      on_reject: "Загрузки остаются на паузе"
      dedup_key: "OrbitalAtlas/oauth"
      link: "https://github.com/<owner>/<repo>/actions/runs/<id>"
    secrets: inherit
  ```
  The calling repo needs secrets `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (+ `TELEGRAM_CALLBACK_SECRET` for buttons)
  and keeps its own registry on its branch `telegram-data`.
* From a Claude session: push `requests/ask-<name>.json` (same fields) to branch `telegram-ops` (`telegram-ask.yml`).
* After the owner decides elsewhere (e.g. in the chat): `tg.py resolve --key-id <id> --registry <telegram-data>`
  closes the request and removes its buttons, so no reminder follows.

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
| `telegram/control.py` + `test_control.py` | silent-mode gate, dedup, outbox, reminder, expiry (tested) |
| `.github/workflows/telegram-notify.yml` | reusable gate (`workflow_call`), callable from other repos |
| `.github/workflows/telegram-ask.yml` | the same gate for Claude sessions (push to `telegram-ops`) |
| `.github/workflows/telegram-sweep.yml` | every 10 min: retries, the single reminder, expiry, fallback issue |
| `.github/workflows/telegram-decision.yml` | records a verified button press, closes the request, removes buttons |
| `telegram/worker/` | Cloudflare Worker + `wrangler.toml.example` |

## Pairing (one time)

1. Claude generates a one-time code and stores only its sha256 in `requests/setup.json` on branch `telegram-ops`.
2. The owner sends `/start CODE` to the bot in a private chat.
3. `telegram-setup.yml` (op `pair`) calls `getUpdates` **without offset** (nothing consumed), accepts only a private chat
   whose `/start` payload hashes to the stored sha256, and DMs that chat its chat id. Ambiguous or missing -> no DM.
4. The owner adds the number as secret `TELEGRAM_CHAT_ID`.

If the bot already has a webhook (e.g. a Cloudflare bot), `getUpdates` is impossible; the workflow reports
`webhook_active` and **does not** delete the webhook - that is the owner's decision.

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
