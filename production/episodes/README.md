# Orbital Atlas episodes with the ATLAS host

- `engine/` shared episode engine: `host.py` (ATLAS shots/actions on the shared rig),
  `gfx.py` (editorial graphics), `layers.py` (approved cover split into moving layers),
  `render.py` (parallel render + mux), `qc.py` (per-frame host QC), `cues.py`
  (phrase -> narration time), `synth_timing.py` (TEMP layout timing, never shipped).
- `voyager_ep013/`, `artemis_ep014/` episode modules (`episode.py` + `scenes.py`).
- `cover_tools/` scripts that split the approved covers into layers and replace the
  painted host with the rig ATLAS (sources and layers live in /mnt/project-files/<ep>/cover/).
- `test_fragment/` 12 s motion test (EP012 voice used only for lip-sync testing).

Render: `python3 engine/render.py voyager_ep013/episode.py video OUT.mp4`
Frames: `python3 engine/render.py voyager_ep013/episode.py frames DIR --t 0 12.5`
QC:     `python3 engine/qc.py voyager_ep013/episode.py`
Voice: episodes read `/mnt/project-files/<ep>/voice/narration.voice.json` (yt-voice/1) and
fall back to `voice_temp/` (silent layout timing) when no narration exists yet.

Finish (mix + burned subtitles): `python3 engine/finish.py voyager_ep013/episode.py RAW.mp4 CAPTIONS.srt OUT.mp4`
  - synthetic temp SFX (whoosh on scene cuts, low bed), narration on top, measured gain to about -14 LUFS;
  - English subtitles from the yt-captions SRT burned as a separate libass layer, centred at x=1080,
    raised above the source-credit footer; frame 0 is left clean so it equals the cover.
Subtitle safety: `python3 engine/subcheck.py EP.py CAPTIONS.srt --x0 640 --x1 1520 --y0 845`
  (every frame: no ATLAS joint inside the subtitle zone while a cue is on screen).
