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
