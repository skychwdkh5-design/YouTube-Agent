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

## Status: APPROVED standard (Егор, 2026-11-16 11:40Z)

Test 01 approved ("Одобряю, закрепляем"). From now on every Orbital Atlas video uses these kinetic
captions instead of plain burned-in subtitles: yellow accent (255,210,31), Unbounded 900 uppercase,
word-timed pop-in, keyword boxes, count-up hero numbers, HUD frame + countdown ring + "ARCHIVE // source"
label on archive footage. YouTube closed captions (SRT/VTT from /yt-captions) are still uploaded separately.

## Status update (Егор, 2026-11-17)

Superseded for on-screen use: no word-by-word / karaoke captions of every phrase. On-screen text is now only
short object-anchored callouts (see CLAUDE.md "Paper-cut ATLAS and on-screen text"). Full subtitles = separate SRT.
The `Hero` count-up and HUD pieces may be reused only as callouts for verified numbers.
