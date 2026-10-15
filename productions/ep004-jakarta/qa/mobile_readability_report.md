# EP004 S3 proof - mobile readability (2026-10-15)
Checker: `orbitalatlas.mobile_qa.check_records` on text recorded from rendered frames every 0.25 s (53 frames), rules from `mobile_qa.py` (text >= 30 px, caption >= 48 px at 1080p, title-safe 3.5 % x / 4 % y, contrast >= 3:1, no overlaps).
Result: **0 issues** after two real findings were fixed during the build: (1) captions were 40 px (floor is 48) -> raised to 48; (2) the SENTINEL-1 label plate started at x=60 < 67 px safe margin -> moved to x=84.
| style | min size at 1080p | 6.1-inch phone, landscape full screen | portrait inline |
|---|---|---|---|
| labels and chips | 32 px | 11.6 pt | 6.5 pt |
| captions | 48 px | 17.5 pt | 9.7 pt |
**Not verified (needs a person):** viewing on a real phone, and portrait inline readability - 6.5 pt for labels is small; they are secondary (the caption carries the message). Line widths: cyan LOS segment 11 px, vertical arrow 7 px, ground line 5 px at 1080p (>= the 4.5 px floor). The older rubric asks a 96 px margin; the newer mobile_qa rule (67 px) was applied - chips sit at x=72, y=48 (inside the newer rule, not the older).
