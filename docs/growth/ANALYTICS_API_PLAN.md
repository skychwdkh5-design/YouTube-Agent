# YouTube Analytics API — connection plan (read-only)

Status: **plan only.** Nothing in OAuth, Google Cloud, GitHub secrets or workflows changes until the owner
approves this plan step by step. The publishing token (`YT_REFRESH_TOKEN`, docs/youtube-setup.md) is never touched, re-issued or re-scoped.

## Goal
Fill `metrics.json` for `.claude/skills/yt-retention/episode_report.py` automatically at day 7 and day 28 instead of exporting from Studio.

## Minimal rights
- One scope: `https://www.googleapis.com/auth/yt-analytics.readonly` (read reports for the owner's channel).
- Not requested: `youtube`, `youtube.upload`, `youtube.force-ssl`, `yt-analytics-monetary.readonly`.
- A **separate refresh token** in its own secret `YT_ANALYTICS_REFRESH_TOKEN` - never a combined token with publishing scopes.
- Read access only: the job calls `reports.query` (YouTube Analytics API v2) and, for thumbnail impressions/CTR,
  the YouTube Reporting API (same scope). Which reach fields exist per traffic source is verified in step 4,
  not assumed; until then CTR by source keeps coming from the Studio export.

## Steps (each needs the owner's go)
1. **Decide the client.** Option A (recommended): a new OAuth client of type *TVs and Limited Input devices*
   used only for analytics. Option B: reuse the existing client. Either way the consent screen gets the
   analytics scope added - that is a change to the Google Cloud project, so it waits for approval.
2. **Issue the token** with only the analytics scope, signed in as the OrbitalAtlas channel account. The owner copies it straight
   into GitHub Secrets as `YT_ANALYTICS_REFRESH_TOKEN`; nothing secret goes into chat or the repo.
3. **Read-only workflow** `.github/workflows/youtube-analytics.yml` (manual + weekly): job permissions `contents: write` limited to a data branch
   `analytics-data`, its own GitHub environment holding only `YT_ANALYTICS_REFRESH_TOKEN` and the client id/secret, no access
   to publishing secrets, no dispatch of other workflows, `concurrency` separate from publishing.
4. **Dry run**: one call for one published video; print the fields returned; nothing written. Compare with Studio.
5. **Snapshot**: write `metrics.json` per video at day 7 and day 28 to `analytics-data`; `episode_report.py`
   reads them. No video, metadata, playlist or schedule is ever changed by this job.

## Rollback
Delete the secret and the workflow; revoke the app at https://myaccount.google.com/permissions. The
publishing token keeps working because it is a different token.

## Risks
- If the OAuth app is in *Testing*, refresh tokens expire after 7 days - the consent screen must be *In production*.
- Google may show an "unverified app" warning for the sensitive scope; acceptable for one owner account.
- API numbers can differ slightly from Studio (processing delay, ~2-3 days): snapshots note the date.
- Quotas are generous for one channel; the job makes a few calls per week.
