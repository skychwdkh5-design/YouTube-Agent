# FUTURE_VISUAL_ROADMAP (deferred - do not start without a new task from the owner)

Baseline: `VISUAL_ENGINE_BASELINE.md` (PRODUCTION_BASELINE_V2C). Gap evidence: `docs/references/library/REFERENCE_COMPARISON.md`. More references will come from the owner.

| # | improvement | why (gap vs references) | starting point in the code |
|---|---|---|---|
| 1 | more advanced 3D motion graphics | references use true 3D type and objects; we have 2.5D transforms | `kinetic.tilt_25d`, `plane.PlaneTilt`, `tools/cesium_proof/` |
| 2 | global Earth -> country camera transitions | VR1 jumps continent -> country every 1-2 s | `orbitalatlas.geo` (Natural Earth globe, class B) not wired into `director` |
| 3 | advanced kinetic typography | VR2 extrusion, camera through letters, denser layouts | `typeset` presets |
| 4 | cinematic text transformations | word morphs / text-to-shape | `typeset`, `interact.KeywordLift` |
| 5 | higher-density layered animations | Shorts change every 1-2 s; long-form caps focus cards | director pacing limits (`min_focus_gap`, `max_focus_per_min`) |
| 6 | more sophisticated transitions | match cuts, masks driven by geography | `transitions`, `fx.LightSweep` |
| 7 | professional audio and sound design | synthesised SFX are simpler than foley; no music bed | `sfx` (needs a licence-checked free library or music source in `ASSET_SOURCE_REGISTRY.md`) |
| 8 | tighter integration of graphics with satellite imagery | references grade and composite heavily; we never recolour evidence | `grade` (presentation layers only), `fx.RegionTint` |
