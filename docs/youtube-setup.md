# YouTube API setup (iPad, Safari)

Nothing secret goes into chat. Each value is copied from Google straight into GitHub Secrets.

1. Project: https://console.cloud.google.com/projectcreate -> name `OrbitalAtlas-Publisher` -> Create.
2. Enable API: https://console.cloud.google.com/apis/library/youtube.googleapis.com -> Enable (correct project selected).
3. Consent screen: https://console.cloud.google.com/auth/overview -> Get started -> app name OrbitalAtlas, your email,
   Audience **External**.
4. Scope: https://console.cloud.google.com/auth/scopes -> Add or remove scopes -> `.../auth/youtube`.
5. Audience: https://console.cloud.google.com/auth/audience -> add your Google account as Test user, then
   **Publish app -> In production** (otherwise the token expires every 7 days; the "unverified app" warning is normal for personal use).
6. Client: https://console.cloud.google.com/auth/clients -> Create client -> type **TVs and Limited Input devices**.
   Copy Client ID and secret directly into GitHub (next step).
7. GitHub secrets: https://github.com/skychwdkh5-design/youtube-agent/settings/secrets/actions
   - `YT_CLIENT_ID`, `YT_CLIENT_SECRET`
   - `GH_SECRETS_TOKEN`: fine-grained token from https://github.com/settings/personal-access-tokens/new,
     only this repository, permission *Secrets: Read and write*, 30-day expiry. It only lets the auth job save the refresh token.
8. Actions -> **YouTube auth (one-time)** -> Run workflow. Open the run log: it prints a code. Go to
   https://www.google.com/device, enter the code, choose the OrbitalAtlas channel account. The job stores `YT_REFRESH_TOKEN` itself.
9. Actions -> **YouTube channel check (read-only)** -> Run workflow: prints the channel title and counts.

## Publishing workflows (after the PR is merged)
10. Settings -> Environments (https://github.com/skychwdkh5-design/YouTube-Agent/settings/environments): create
    `youtube-approval` and `youtube-autopilot`, tick **Required reviewers**, add yourself, leave
    "Prevent self-review" OFF (you are the only user). Environments with reviewers work for public repos on every plan;
    a private repo on the Free plan would not support them.
11. Actions -> **Stage media** -> Run (once; it copies 7 MP4s, 379 MB, from LFS into a draft release).
12. Actions -> **YouTube channel check** -> Run: lists all videos on the channel, including EP002-EP004 if they are there.
13. Actions -> **YouTube publish** -> dry run first (default). A real run is separate and needs your explicit go-ahead.

## Second channel «Такое бывает» (ID UCOakEPBhSGwx-2RV0dKGdNA)

Use a **TVs and Limited Input devices** client from the same Google Cloud project. Save the paired credentials as `ANIMAVERSE_YT_CLIENT_ID` and `ANIMAVERSE_YT_CLIENT_SECRET` in YouTube-Agent Actions secrets. Both workflows use that pair with `ANIMAVERSE_YT_REFRESH_TOKEN`.
1. Actions -> **YouTube auth — Такое бывает** -> Run workflow; enter the code from the log at google.com/device, pick the «Такое бывает» channel.
   The job checks `channels.list(mine=true)` and writes the secret only if the ID matches; on a mismatch it stops with nothing written.
2. Actions -> **YouTube channel check — Такое бывает** (read-only) to confirm.

### Private queue test

Add a fine-grained GitHub token restricted to `skychwdkh5-design/ANIMAVERSE` with **Contents: Read-only** as `ANIMAVERSE_RELEASE_READ_TOKEN` in YouTube-Agent Actions secrets. Create a release in ANIMAVERSE, then attach the intended MP4 and `youtube-queue.json`. The release needs to be readable by that token.

```json
{
  "expected_channel_id": "UCOakEPBhSGwx-2RV0dKGdNA",
  "items": [{
    "id": "e01-private-test",
    "mode": "private_test",
    "private_test_allowed": true,
    "kind": "short",
    "media": {"asset": "E01.mp4", "sha256": "replace-with-final-mp4-sha256"},
    "title": "Episode title",
    "title_status": "final",
    "description": "Episode description",
    "default_language": "ru",
    "made_for_kids": false,
    "contains_synthetic_media": false,
    "publish_at": null
  }]
}
```

Set the audience and synthetic media flags for the actual episode. Run **YouTube private queue test — Такое бывает** with the release tag and entry ID. The default is a dry run. Enable **upload_private** for the one private upload. Verify the returned YouTube Studio link and private status. The job checks YouTube inventory for duplicate titles. If a real run fails after upload begins, inspect YouTube Studio before retrying.
