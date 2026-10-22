# Chat-to-publish end-to-end test (dry runs), 2026-10-22

Setup checked first: PR #30 merged; branch `publish-data` exists and its `queue.json`, `media.json` and EP005 assets are identical to `main`; ledger branch holds only the earlier
private test (video `Zz8o2QMdVKY`, private, verified); repository variable `CHAT_PUBLISH_ENABLED` is **not set** (the workflow log shows `ENABLED:` empty).
Claude created the card (`approval.py card --log`), wrote a synthetic **dry-run-only** approval (`consent_channel: e2e-test`) and the card log to `publish-data` through the GitHub API,
and dispatched the workflow itself. Nothing was uploaded; no real approval exists.

| # | Test | Dispatch | Result |
|---|---|---|---|
| 1 | Positive: card + approval + dry run | `dry_run=true`, data commit A | success: approval verified offline, EP005 master (297 MB) downloaded from the draft release with sha256 ok, EP005 `ready (dry run)`, `publish_at 2026-10-23T12:00:00Z` |
| 2 | No approval | unknown approval id | failed at the data/approval step; nothing after it ran |
| 3 | Changed SHA-256 | data commit B (EP005 sha in `media.json` altered) | `approval refused: ep005: file sha256 differs from the approved one`; media fetch and run skipped |
| 4 | Data commit not on `publish-data` | `main` commit | failed at the ancestry check; nothing after it ran |
| 5 | Kill switch off, real run | `dry_run=false` | job **skipped** (variable unset) |
| 6 | Positive again on the final workflow (pipefail) | `dry_run=true` | see run list |

Offline (unit tests, 86): real run with a test approval refused; consent text rules; last-card binding; label rules; expiry/replay/cap; hash binding; TOTP vectors; one upload per approval.

Not tested live (not allowed yet): a real run with the variable on and a real approval; the audit issue; TOTP in Actions; first public release by `publishAt`.
Found and fixed during the test: failed steps could be masked by `| tee` (now `bash -eo pipefail`); the ledger-save step failed after early failures.
Side note: while reverting test commit B on `publish-data` a hand-typed copy of `media.json` had a typo (one `source.path`); it was caught by diffing against the original and corrected in the next commit. The tip is identical to the original.
