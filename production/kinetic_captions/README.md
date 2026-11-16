# Kinetic motion-graphics captions (Orbital Atlas)

Replaces plain subtitles (owner decision 2026-11-16). Style taken from the owner's reference reel
(dark HUD, heavy wide uppercase, highlight boxes, count-up numbers, countdown ring), recoloured to the
Orbital Atlas yellow from the thumbnail standard.

- `kcaps.py`: `Captions(words, keywords, heroes, replace, style)` → `.render(frame, t)` as the last layer.
  Words pop in on their yt-voice timings; keywords get a wiping accent box; `Hero` = big count-up number.
- `fonts/`: Unbounded 800/900 (SIL OFL, licence included).
- `scenes/test_captions.py`: 14 s test on NASA Artemis II footage + existing EP014 voice (no new paid audio).

```
python3 -I scenes/test_captions.py --media /mnt/project-files --out test.mp4 [--accent lime] [--frames 1.0,2.5]
```
Output of test 01: `/mnt/project-files/captions/test01/` (ffprobe.txt, control_frames/, contact.jpg).
