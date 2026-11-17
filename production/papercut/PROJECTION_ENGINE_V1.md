# ATLAS projection engine

Status: **integrated in the shared renderer** (`/yt-render`, timeline v3 `profile: long`, block `atlas`).
Owner-approved format (2026-11-17, PR #56): the approved paper ATLAS stays the same drawing (whole-cutout idle
motion, blink and mouth inside the one head; **no joints, arms or legs are animated**) and a paper projection
opens from his raised glove with small topic details that change with the narration. More animation goes into
the projection, diagrams, footage and camera, never into his limbs.

## Files

| Path | What |
|---|---|
| `papercut/projection.py` | `ProjectionEngine` (approved look, cached), `ProjectionCue`, `cues_from_script` / `resolve_anchor` (pages on spoken words) |
| `papercut/atlas_layer.py` | `AtlasLayer`: approved ATLAS (`Actor`, hero drawing only) + projection; mouth from narration loudness, blinks, glove point |
| `papercut/host.py` | `_composite` now works only in the layer's region (pixel-identical, ~2x faster ATLAS) |
| `tools/bench_projection.py` | old vs new speed comparison on identical inputs |
| `tests/test_projection.py` | engine, timing, look-vs-approved, host identity, layer tests |
| `.claude/skills/yt-render/compose.py` | timeline key `atlas`, per-frame placement QA, manifest section |

## In an episode timeline (yt-render v3, profile long)

```json
"atlas": {
  "host": {"x": 250, "y": 985, "height": 400, "on": [[0, 21.5]]},
  "projection": {
    "box": [330, 318, 680, 578],
    "pages": [
      {"at": {"phrase": "Orion moved"}, "title": "EARTH TO ORION", "kind": "link"},
      {"at": {"phrase": "blocked the direct path"}, "title": "NO DIRECT PATH", "kind": "blocked"},
      {"at": {"phrase": "keep watching"}, "title": "CREW WATCHES", "kind": "view"},
      {"at": {"phrase": "wait for contact"}, "title": "GROUND WAITS", "kind": "wait"},
      {"at": {"phrase": "rare chance"}, "title": "DARK MOON", "kind": "dark"}
    ],
    "end": {"phrase": "lunar surface", "edge": "end", "offset": 0.4}
  }
}
```

- `host`: feet line `x, y`, `height` (default 400 px at 1080p), `on` = windows when ATLAS is on screen
  (default the whole video), `preset` idle/explain/listen/surprise, optional `enter`/`exit` left/right.
  His mouth moves only while words are spoken (from the yt-voice word timings + narration loudness).
- `pages[].at`: seconds, `{"word": i}` or `{"phrase": "..."}` (optional `occurrence`, `edge`, `offset`) resolved
  against the narration's word timings; the page lands `lead` (default 0.15 s) before the word.
  A page lasts until the next one; `until` closes the panel early (it re-opens for the next page).
  `end` closes the last page (default: last word + 0.6 s).
- `kind`: `link`, `blocked`, `dark`, `flash`, `view`, `wait`, `label` (small paper diagrams; `link` and `wait`
  loop, `blocked` and `flash` animate in).
- Tags: 1-4 words, at most 24 characters, must fit at >= 22 px. Only verified facts.

Refused at plan time: a page whose phrase is not in the narration, overlapping/too-short pages (< 1 s),
a box outside the frame, a box over ATLAS's face/helmet, a page outside an ATLAS window, `atlas` in Shorts.
Warning: ATLAS on screen more than 30 % of the video (owner rule: >= 70 % live footage and experiments).

The manifest gets `atlas.pages`, `frames_by_state` (opening / open / turning / closing) and
`placement_issues` (projection over the face, a caption or the frame edge, checked on every frame).

Layer order: footage / graphics -> projection beam + panel -> ATLAS -> labels, captions, source credit.
On-screen text rules are unchanged: no burned sentence subtitles in new episodes (SRT goes separately).

## Direct use in a scene script

```python
from papercut.atlas_layer import AtlasLayer
layer = AtlasLayer.from_spec(spec, words, "voice/narration.wav", frame_size=(1920, 1080), duration=21.5)
info = layer.render(frame_rgba, t)      # after footage, before text
```

## Checks

```bash
python3 -m unittest discover -s production/papercut/tests -p 'test_projection.py'
python3 -I production/papercut/tests/test_host.py
cd .claude/skills/yt-render && python3 -m unittest test_compose
```
