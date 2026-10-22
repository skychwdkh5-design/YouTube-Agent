# After merging PR #28 - owner checklist (iPad)

Nothing below uploads or publishes anything until step 5, and step 5 needs its own approval.

1. **Merge PR #28**: https://github.com/skychwdkh5-design/YouTube-Agent/pull/28 -> *Merge pull request*.
   (Open question first or later: EP002 Short 02 AI label, see `docs/review/EP002_SHORT_02_AI_DISCLOSURE_REVIEW.md`. It only blocks that one Short.)
2. **Create two Environments**: https://github.com/skychwdkh5-design/YouTube-Agent/settings/environments -> *New environment*
   - `youtube-approval`: tick *Required reviewers*, add yourself, leave "Prevent self-review" OFF, Save.
   - `youtube-autopilot`: same.
3. **Run Stage media** (Actions -> *Stage media (LFS -> draft release)* -> *Run workflow*, once). Copies the 7 MP4s (379 MB) into a **draft** release and checks every sha256.
   Do not re-run needlessly: each run that fetches from LFS uses GitHub LFS bandwidth (1 GB/month free).
4. **Run the dry-run Publish**: Actions -> *YouTube publish (manual, gated)* -> mode `approval` (then `autopilot`), ids `all`, **dry_run left ON**.
   Expected: every item shows `blocked` for "no owner approval" only (EP002 Short 02 also for the open AI question) and no other problem.
5. **Separate approval for ONE private test upload** - tell me in chat which file (I suggest a Short). Nothing is uploaded before you say so.
   After it: I read back the real status (private? scheduled? or locked by an unaudited API project) and the ledger.

Later (not now): approve each video's `owner_approval` in `publish/queue.json` (sha256 + publish_at), then a real run needs the phrase `UPLOAD <mode>` and your Environment approval.
