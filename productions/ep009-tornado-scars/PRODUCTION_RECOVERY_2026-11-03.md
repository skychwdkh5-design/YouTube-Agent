# EP009 production recovery decision — 2026-11-03
Owner priority: publish the next Orbital Atlas Long and prepare two Shorts; stop endless animation R&D. Claude budget is constrained.

## Verified current state
- Branch: production/ep009-tornado-scars; PR #46 open; V4 WIP commit 0832d5e present.
- NASA EO-1/MODIS and NOAA GOES originals are in productions/ep009-tornado-scars/media_original/ and SHA manifest.
- 8 approved-style painted PNG illustrations are in root Orbital_Atlas_EP009_illustrated_assets.zip; verification/extraction script supplied.
- Narration draft: productions/ep009-tornado-scars/script_en.md; Short drafts: shorts/short_01.md, shorts/short_02.md.
- V3 pilot exists in conversation, not in git. V4 engine code exists; full V4 pilot untested. Do not assume it works.
- Media rights/claim QC and final narration timing still required. Final voice Adam costs credits and requires explicit owner approval.

## Production-first policy (one bounded pass)
1. No new V4 engine development, no new motion-test loops, no topic research, no vidIQ calls, no regenerating art unless an actual publication-blocking failure demands it and owner authorizes.
2. Prefer robust, demonstrated existing render paths. V3 motions are not automatically approved; use corrected V4 components ONLY when they can be validated in a very short smoke test without branching into engineering. Otherwise revert to restrained documentary edit with verified NASA/NOAA media, motion only when clearly effective. Preserve approved painted art direction.
3. BEFORE expensive render, inspect that narration script, sourced claims, actual runtime, media rights, thumbnail-hook, final English captions, and Shorts are production ready. Produce a brief blocker list; do not burn hours fixing optional aesthetic details.
4. Assemble full Long and 2 Shorts from one shared approved source pack. Run automated QC for codecs, audio, captions, media rights, factual statements, mobile readability, first three-second hook and visual discontinuities.
5. Three thumbnail concepts already documented. Choose strongest existing concept A as working candidate, render from actual verified satellite image; no invented tracks.
6. Paid Adam voice, upload, scheduling and publication are NOT authorized by this document. Obtain an explicit owner approval for each paid use/publish.
7. If no final voice approval, produce review versions with local temporary narration; clearly distinguish review video from release master.
8. Save code/checklists/manifests and reproducible instructions in GitHub branch; video files can be attached externally per repo .gitignore. No merge into main.

## Completion definition
Review-ready = one full Long plus two Shorts exported, accessible to owner, QC reports and thumbnail candidate produced. Publication-ready requires final owner-approved Adam voice, English SRT aligned to it, QC PASS, explicit publish approval.

## Honest stop rule
If the first full-length production attempt hits a genuine blocker, report exact file and error; do not invent independent new work, launch unbounded retries, or spend hours on an optional motion effect.
