# Approved paper-cut character (ATLAS, handoff V3)

Status: **technical integration, test scene only.** Not used in any published episode yet.
Owner decision 2026-11-16: Orbital Atlas moves to the approved 2D paper-cut character from
`ATLAS_APPROVED_PAPERCUT_HANDOFF_V3.zip`. This supersedes the old 3D/rig ATLAS
(`production/atlas-rig`, PR #52), which must not be reused. **The character's appearance must not change.**

## What is here

| Path | What |
|---|---|
| `assets/hero_approved_clean.png` | the only character pixels used in renders (518x733 RGBA) |
| `assets/APPROVED_CONCEPT_UNMODIFIED.png` | canonical approved sheet (reference) |
| `assets/MOTION_LIBRARY.json` | approved safe presets: idle, explain, listen, surprise, entrance, exit |
| `assets/SHA256SUMS.txt`, `ASSET_PROVENANCE.json` | checksums / provenance from the handoff |
| `handoff_docs/` | the handoff's README, PRODUCTION_RULES, QA_GATES, CLAUDE_HANDOFF (verbatim) |
| `papercut/host.py` | `HostLayer` + `Cue`: composites the hero into any PIL RGBA frame |
| `papercut/paper.py` | paper texture / cut-paper shape helpers for environments |
| `papercut/qa.py` | automated QA gates + review sheets |
| `scenes/test15.py` | the 15 s 1920x1080 30 fps test scene |
| `tests/test_host.py` | guard tests |

Deliberately **not** copied from the handoff: `experimental_layers/` (forbidden in releases),
`poses/` and `expressions/` (handoff says they need manual edge review first), the old V1/V2 models.

## Rules enforced in code

- Hero PNG is verified by SHA-256 on every load; any other file, or anything under
  `experimental_layers`, raises `HostError`.
- Whole-cutout motion only: translation, roll <= 2 deg, scale <= 3 %, bob <= 10 px at 540p
  (20 px at 1080p), taken from `MOTION_LIBRARY.json`. No limbs, no mouth, no mirroring.
- On-screen width must be 12-24 % of frame width (no upscaling beyond the 518 px source at 1080p).
- One cue at a time; changes of position happen on cuts, eased floats (`drift`) or entrances/exits.
- Sub-pixel premultiplied rendering (no 1-px stepping, no dark fringes); soft paper drop shadow is a
  scene element and does not touch character pixels.

## Use in an episode renderer

```python
from papercut.host import HostLayer, Cue
host = HostLayer((1920, 1080), [
    Cue(0.0, 6.0, "listen", x=200, y=1035, width=300, enter="left"),        # x,y = feet line
    Cue(6.0, 12.0, "explain", x=1780, y=940, width=240, drift=((1760, 930), 6.5, 11.5)),
])
info = host.render(frame_rgba, t)   # call after background/diagram, before captions
```

Layer order (handoff rule): background / footage / diagram -> character -> text and captions.

## Test scene and QA

```
python3 -I scenes/test15.py --earthrise <NASA_ArtemisWow_Earthrise_Final.mp4> --out test.mp4 --log log.json
python3 -I papercut/qa.py --video test.mp4 --log log.json --report qa.json --sheets qa_sheets/
python3 -I tests/test_host.py
```

The Earthrise source is NASA SVS 15110 (in the project files under `media_v2/svs/15110/`).

## Known limits (honest list)

- No joint animation, no walking, no lip sync, no blinking: the pack contains no articulated rig
  and no mouth shapes. The character never "speaks" on screen.
- Only one approved full-body pose is production-ready. Other poses/expressions in the pack need an
  edge review and owner approval before use; expression changes must be whole-pose cuts.
- Cutout edges inherited from the approved asset: flat cut along the bottom of the boots' paper
  border, scarf tip and a short stretch under the raised glove are trimmed close to the ink line.
  We do not retouch the asset (appearance is frozen); hide the boot base under a ground line or
  frame edge if it becomes noticeable.
- Max on-screen size ~460 px wide (24 %); bigger close-ups would need a higher-resolution master.

## Animation system v2 (test 2, 20 s)

- `tools/extract_sheet.py` -> `assets/sheet_cutouts/`: 6 poses, 4 turnaround views, 6 emotion heads and
  the "!!" mark cut 1:1 from the approved sheet (checksums in MANIFEST.json).
- `papercut/actor.py`: `Actor` / `ActorCue` - hard-cut pose switching with the feet line kept,
  blink (3 phases) and loudness-driven mouth (3 states) on the hero, sheet effect marks.
  Glove wave code exists but is NOT used: it tears at the helmet edge.
- `scenes/test20.py`: the 20 s interaction test. Report: `ANIMATION_TEST20.md`.

## Owner rules (Егор, 2026-11-16)

- System approved after test 2, on condition that **at least 70 % of every video is live footage and
  experiments**; the paper-cut ATLAS and graphics fill at most 30 %.
- Plain subtitles are replaced by **motion-graphics captions** in the style Егор uses on "Nexi"
  (approved 2026-11-16, see `production/kinetic_captions/`).

## Articulated rig v3 (parts sheet, 2026-11-17) - CANCELLED by the owner the same day; do not use

- `tools/cut_parts.py` -> `assets/parts_v1/`: 21 parts cut 1:1 from the owner's parts sheet (`source/`), round
  construction tabs removed where they would show over a neighbour; checksums and pegs in `parts.json`.
- `papercut/rig.py`: `Rig` / `Pose` - one uniform scale, joints at shoulders, elbows, wrists, pelvis, hips, knees,
  ankles (boots auto-level), blink inside the one head, glove drawings (fist / point / open), scarf angle input.
- `scenes/test20_rig.py`: 20 s test - point, lean, return, blinks, scarf lag; object-anchored callouts only; SRT.
- `papercut/qa_rig.py`: joint coverage, rigid lengths, motion steps, callout placement, video checks, joint close-ups.
Outputs: `/mnt/project-files/papercut/test20_rig/`. No walking yet.
