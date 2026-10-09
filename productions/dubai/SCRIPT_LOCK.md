# EP002 Dubai — SCRIPT LOCK

Status: LOCKED narration for production. Locked on base commit 3f0452f.

## Approved version
- Narration file: productions/dubai/script_draft_v1_2.md (git blob fdc3e87d117b54daade1b62225bd86f8ddf13d98)
- Structure: productions/dubai/story_structure_v1_4.md (28 scenes, 538 s estimated; v1.4 text not edited; C4 decision below supersedes its fallback note)
- Spoken words: 1225
- VO lines: 30

## Narration hash (reproducible)
Spoken text = every line of script_draft_v1_2.md starting with `VO: `, prefix removed, joined by newline, with one trailing newline, UTF-8.
SHA-256: d050d5e30db834f42315850945b2d4b7eb1a0c99bafa994b1f1b2e49d3360d0d
Reproduce:
`grep '^VO: ' productions/dubai/script_draft_v1_2.md | sed 's/^VO: //' | sha256sum`

## Evidence basis
- Claims 1-13, 21-31 VERIFIED; claim 33 VERIFIED at screenshot scope; 14-20 not used; 32 UNVERIFIED.
- Visual review: USER_SCREENSHOT_VERIFIED for ASTER 2006 and ISS 2022 (see research/visual_evidence_check.md). Screenshots are not in the repo.

## Decisions
- C4 may use the ISS photograph for The World, subject to final crop validation. Narration stays exactly as drafted.
- No ASTER/ISS overlays, wipes or registered before/after (claim 32). 2011 = year only. Nothing after 2022 stated about the islands.

## Remaining visual production risks
1. No full-resolution file inspected; the screenshots are the only visual evidence.
2. Both source images are portrait (about 3072x3797 and 2768x4928); 16:9 crops may cut islands, especially for the ISS frame.
3. Final crops for C1, C3, C4, C5, E2 must be checked in the editor and labeled with source, instrument and year.
4. The ISS photograph was cropped and contrast-enhanced by NASA (claim 27); label it as a photograph.
5. Authorial lines in C5, E2, E4, E5 remain interpretation, flagged in the script NOTE fields.

Any change to a `VO:` line invalidates this lock; recompute the hash.
