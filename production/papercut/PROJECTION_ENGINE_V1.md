# ATLAS Projection Engine: reusable overlay (draft)

This directory provides the **API**, not automatic wiring into every episode yet.
The existing 20-second PR #56 demonstration remains unchanged.

## Ownership and limits
- Approved paper ATLAS remains unchanged. No jointed arms or legs; do not enable the old articulated rig.
- Projection is a separate scene overlay. Diagrams, camera, live footage and object callouts can animate.
- SRT remains separate. No burned-in sentence-by-sentence subtitles.
- At least 70% of each episode is live footage / experiments / archive, per approved editorial rules.
- No automatic uploads, scheduling, paid voice calls, or changes to production defaults.

## Per-episode configuration

```json
{
  "projection": [
    {"start": 0, "end": 6.3, "title": "EARTH TO ORION", "kind": "link"},
    {"start": 6.3, "end": 11.3, "title": "NO DIRECT PATH", "kind": "blocked"},
    {"start": 11.3, "end": 15, "title": "DARK MOON", "kind": "dark"}
  ]
}
```

Kinds: `link`, `blocked`, `dark`, `flash`, `view`, `label`.
Times are seconds on the episode timeline. Cues cannot overlap. Use only verified
facts in short titles. The caller must give a safe, non-overlapping screen box.

## Use

```python
from papercut.projection import ProjectionEngine, cues_from_dict

engine = ProjectionEngine(cues_from_dict(plan["projection"]),
                          box=(330, 318, 680, 578),
                          font_path="production/kinetic_captions/fonts/unbounded-latin-800-normal.woff")
# Draw footage, diagram and existing ATLAS (no limb motion) first.
# hand_xy comes from the *approved* host position and transformation.
info = engine.render(frame_rgba, t, hand_xy)
# Then draw object callouts and credit/source labels.
```

## Validation before merging

```bash
python3 -m unittest discover -s production/papercut/tests -p 'test_projection.py'
```

This API uses PIL and caches static diagram panels per page. Actual render-speed gains
remain **unmeasured**. Integration with the central episode render/timeline, physical
placement QC, full-frame performance, page-transition animation and real-time
playback inspection remain future work. Do not claim it is production-ready before
those tests. The draft is deliberately separate from the old `test20_projection.py`.
