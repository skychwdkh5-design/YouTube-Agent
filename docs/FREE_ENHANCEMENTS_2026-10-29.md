# Free production enhancements — additive only (2026-10-29)

## Safety and scope
- This proposal is **opt-in, documentation-only**. Existing scripts, workflows, releases, voices, assets, schedules, upload tokens and publishing approvals are unchanged.
- No paid API calls, subscriptions, trial activations, payment credentials, or automatic publishing. Never treat a service's free website tier as free API access.
- Do not merge until owner approves and a regression check is complete. Maintain the channel's existing factual, license and owner-approval rules.

## Additive services and where they fit
1. **Topic discovery (free):** Google Trends (manual/public signals where permitted), YouTube search, YouTube Studio Research/Inspiration if enabled, public science/technology primary-source feeds (NASA, USGS, NTSB, university and agency releases). Store candidate URL, publisher, publication date, event date, regional relevance, fact evidence and novelty. Never treat popularity as proof of truth.
2. **vidIQ Free:** Optional human-connected Claude MCP integration only if available to the account. Validate access, credits, quotas and terms before enabling. Do not assume an unattended GitHub Actions connector or an unlimited free API. Fall back to the no-cost sources above.
3. **YouTube Analytics:** Reuse existing authorized channel access only after confirming OAuth scopes and API quota. Collect impressions CTR, average view duration, traffic sources and audience-retention curve if accessible. Preserve scope of current OAuth credentials; never rotate or replace tokens implicitly. Don't infer audience retention from incomplete data.
4. **Free music/SFX:** YouTube Audio Library, with per-track attribution rules recorded before use. Keep source URL, track title, artist, license/attribution, date of access, file hash and project use. Existing project music remains untouched.
5. **Free visual tools:** Existing FFmpeg and graphics pipeline; Blender/Kdenlive optional offline enhancement only where actually installed. Use NASA/USGS/open-license source imagery as evidence, with exact per-asset rights and credits. Never replace documentary evidence with generated visuals.
6. **Kling free tier:** Optional manual experiment, **disabled by default**; check whether free credits, commercial use, watermark, export format and API automation are allowed under current terms. No automatic API call, credit consumption or generated-video inclusion without owner approval. AI scenes must be clearly labeled as illustration/reconstruction when necessary.
7. **Free TTS fallback:** Kokoro/Piper only for tests and only if suitable models/licenses and compute are available. Keep currently approved ElevenLabs voices; don't silently replace narration.
8. **DaVinci Resolve Free:** Optional manual finishing on an appropriate machine. Keep FFmpeg renderer as is.

## Suggested non-destructive workflow
- Collect a daily short list of public-source candidate events, labeled with source and dates. No automatic selection based solely on trend scores.
- Produce a 3-hook comparison plus a rights-checked shot list for each selected concept. Prioritize real footage and archival visuals; optional generative inserts are illustrative.
- Record asset provenance, license restrictions, checksums, project filenames and generation cost (zero unless explicitly approved).
- Leave production, QC, publication schedule and owner approval untouched.
- After publishing, compare first-30-second retention, overall average percentage viewed, impressions CTR and subscriber conversion **where available**; avoid fabricated benchmarks.
- First validate on one isolated test episode. Do not trigger live production or scheduling from this document.

## Acceptance checklist before integration
- [ ] Check available quotas and legal licensing against official service documentation.
- [ ] Verify existing workflows remain byte-for-byte unchanged.
- [ ] Test topic scoring against at least 3 independently sourced events.
- [ ] Confirm music and visual attribution per asset.
- [ ] Demonstrate free-only workflow without payment or credit use.
- [ ] Obtain owner approval before merging, deployment, spending or publishing.
