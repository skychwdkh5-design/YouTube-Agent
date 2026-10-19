# Audit, 2026-10-14 (Phase 1 of the autonomy setup)

What exists, where it lives, what survives a new session and what was lost. Every statement below was
checked against `git` (all 16 remote branches fetched) or the GitHub PR list on 2026-10-14. What could
**not** be checked is listed at the end - this audit does not claim to have read everything.

## 1. Where the history actually is

`main` holds only the generic skills (PRs #1-#13, #15). Almost everything about EP001/EP002 sits on
side branches, five of them never merged. A fresh clone shows `main` only; `git fetch origin
'+refs/heads/*:refs/remotes/origin/*'` is needed to see the rest (git pack: 1.47 GiB, mostly media branches).

| branch | PR | state | holds |
|---|---|---|---|
| `main` | - | 3b26881 | 18 skills, yt-render/qc/voice/captions/geo/graphics/satellite, `docs/production-pipeline.md` |
| `claude/youtube-agent-ep002-dubai-ts2kg8` | #17 open | 70 commits ahead of main | EP002 episode, `orbitalatlas/` engine, `docs/production-knowledge/` (the memory base), CLAUDE.md autonomy rules, 3 OrbitalAtlas skills |
| `production/ep002-dubai` | - | merged into #17's branch | EP002 research, motion POC, visual master docs |
| `production/ep001-sahara-green` | #14 open | 55 commits ahead, 470 files, 275 MB tracked | EP001 research (10 audit rounds), script lock, 6,808-credit narration with cache, 19 graphics, timeline, QC JSON, Shorts specs, branding |
| `feature/shorts-performance-feedback` | #16 open | 2 commits, WIP, "tests not yet updated" | Shorts measurement store / hypotheses / experiments |
| `preservation/benchmarks` | - | 1 commit | text of benchmark productions + inventory |
| `media/ep002-dubai-final` | - | 7 commits | EP002 v1-v4.1 masters (parts + one Git LFS file), captions, SHA-256 |
| `media/ep002-dubai-audio` | - | 1 commit | EP002 narration mp3 + raw TTS cache (12 MB + 11 MB) |
| `media/kilauea-2018-short` | - | 1 commit | Kilauea 2018 Short, "not for merge" |
| `claude/eloquent-einstein-pnbzok`, `claude/happy-davinci-g1wme4`, `claude/yt-script-ssjxjb` | none | stale | A **different** earlier concept: a faceless US geography channel, Northwest Angle research, script V2, production package (Oct 6). Not part of OrbitalAtlas EP001/EP002. |
| `claude/eager-volta-pf3wqg`, `claude/sharp-carson-1wirfn`, `claude/youtube-agent-skill-review-or2qqk`, `chore/ep001-pipeline-reuse` | #1-#15 merged | fully in main | skill development |

## 2. What was recoverable

* **Technical problems and fixes:** ~35 distinct ones, from commit messages, `TROUBLESHOOTING.md`, `LESSONS_LEARNED.md`,
  EP001 reports and code. They are now structured entries in `knowledge/solutions.json` (49 entries) with root cause,
  fix, reuse condition, reference, verification and regression test.
* **Prompts:** there are no "prompts" to recover in the sense of image-generation prompts: both episodes use real
  satellite/NASA imagery, ElevenLabs narration text and procedural graphics. The reusable "prompts" are the locked scripts
  (`productions/dubai/narration/vo_text.txt`, EP001 `narration_text.txt` on its branch), the voice settings
  (Adam, `eleven_multilingual_v2`, stability 0.55, similarity 0.75, style 0) and the skills' SKILL.md files.
* **Narration:** EP001 mp3 chunks (7 cache files, ~12 MB) are committed on `production/ep001-sahara-green`;
  EP002 narration and raw cache are on `media/ep002-dubai-audio`. The WAV can be re-assembled for free.
* **Masters:** EP002 v1-v4.1 on `media/ep002-dubai-final` (v4.1 as a single Git LFS file, SHA-256 `504412b3...`).
* **Visual presets:** no preset *files*; the style is code and docs: `productions/dubai/preview/kit.py`,
  `docs/ORBITALATLAS_VISUAL_MASTER.md`, `docs/MOTION_DESIGN_STANDARDS.md`, yt-graphics `documentary_dark/light`,
  EP001 "visual lock" v1.3 and tone-B Landsat curve.
* **Hooks:** none existed before today. There was no `.claude/settings.json`.
* **Analytics:** none. `yt-retention` reads a Studio CSV the owner exports; nothing was ever published, so there is
  no performance data. The Shorts feedback loop (PR #16) is unmerged and exploratory.

## 3. What was lost or is unavailable

* **EP001 final master (747 s) and its Shorts MP4s are not stored anywhere in git.** The final report says the master
  was left in the old container (`/root/ep001_final_out/`). It can be re-rendered (timeline, narration cache, graphics
  specs and QC JSON are on the branch) but the Landsat source bands (1.946 GB, 68 files) are not in git:
  `restore_source_bands.py` re-downloads them and needs USGS M2M credentials.
* **Full conversation history of earlier sessions.** Only the commit trailers (`Claude-Session: ...`) and this session's
  transcript are visible. Reasoning that was never written into a commit message or a doc is gone. Auto memory under
  `~/.claude/projects/` is container-local and empty for a fresh session - nothing durable lived there.
* **EP002 Cesium/GIBS frames** are regenerable (~11 min) but not stored.
* **Not verifiable here:** ElevenLabs plan / commercial-use status; remaining credits (the key cannot read the balance);
  whether the GitHub PR review threads contain decisions not mirrored in commits (comments were not read).

## 4. What persisted between sessions before this change, and what did not

| persisted (in git) | lost between sessions |
|---|---|
| Skills, scripts, tests (main) | decisions only said in chat |
| `docs/production-knowledge/*` (EP002 branch only, unmerged) | EP001 lessons (they lived in EP001 reports on another branch) |
| CLAUDE.md autonomy policy (EP002 branch only) | which branch holds what |
| Paid TTS cache on `media/*` branches | tests of `orbitalatlas/` (needed `-t .`, undocumented) |
| QC JSON and checksums per episode | any enforcement: rules were prose, no hook, no gate |

## 5. Findings worth acting on

1. Knowledge was split across unmerged branches; EP001's lessons were not in the EP002 knowledge base.
2. `TROUBLESHOOTING.md` had 30 unstructured rows with no root cause, reuse condition, reference or test. Replaced by the registry.
3. Two renderers exist: the generic `yt-render` timeline v3 (used for EP001) and the EP002 scene code in
   `productions/dubai/preview/` (hand-written per scene). The second is not yet reusable for EP003 without rewriting scenes;
   the autopilot standardises on the first plus the `orbitalatlas/` engine.
4. `orbitalatlas/tests` failed when run like every other test file (now documented and handled by `kb.py verify`).
5. EP001's chunk-size lesson (502 at ~30 s, billed twice) conflicts with EP002's 2,470-character chunks succeeding: the
   limit is environment-dependent. The autopilot uses 1,700 unless a free probe proves more.

## 6. Addendum (phase 2): can EP001's final materials be recovered without paying again?

Checked 2026-10-14 by actually doing it (scratch directory, nothing overwritten, nothing downloaded):

| item | result |
|---|---|
| Narration WAV (747.357 s) | **Rebuilt from the 7 saved ElevenLabs responses on `production/ep001-sahara-green`: byte-identical** to the recorded sha256 `49e53528cd44...`; chunk offsets and 1,778 word timings identical. Zero cost. (`tools/autopilot/recover_narration.py`) |
| Normalised narration (-16 LUFS file used by the master) | Rebuilt by the committed `audio_normalization_test.py`: byte-identical `114ba576...` |
| Captions, 139 graphics, 6 Landsat/NASA stills, final timeline, QC JSON, thumbnail/branding specs | present on the branch |
| 5 Landsat sequences (`seq_*.mp4`) | **missing**: built from 1.946 GB of source bands that are not in git. Restore needs the USGS M2M download (`restore_source_bands.py`, credentials are present in this environment, free, ~2 GB: NOT done) and `build_sequences.py` |
| CALIPSO dust clip (`calipso_dust_30fps.mp4`) | **missing**: re-download from NASA SVS (host reachable) and convert to 30 fps |
| Final master `FINAL_EP001_1080P.mp4` and the 2 Shorts | **not stored anywhere**; sha256 recorded (`7547d970...`). The renderer is deterministic and the manifest lists a sha256 per 60 s segment, so a rebuild after restoring the 6 videos can be PROVEN identical or shown to differ - it has not been attempted |

Verdict: everything paid is recoverable at zero cost; the master is rebuildable for free but needs ~2 GB of free downloads and about an hour of rendering. No re-voicing is needed.
