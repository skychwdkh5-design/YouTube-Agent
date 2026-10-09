# Episode 001: SCRIPT LOCK v1.1 (2026-10-08)

| Item | Value |
|---|---|
| Script | `productions/sahara-green/script.md`, "SCRIPT LOCK v1.1" |
| Spoken words | 1,778 (everything under the headings, minus Markdown headings and every [ID] tag) |
| Estimated runtime | about 12.3 minutes at 145 words per minute, plus pauses; limit for the long format is 15 minutes |
| Integrity hash | SHA-256 of the narration text (everything from the line "## COLD OPEN" to the end of the file, UTF-8): `d646001c83d3421d43510ece1926d7bd49bc197dcdde07b94fd2f4f3a049f335` (v1.0 recomputed by the same method: `14a046218fa590d06f44605bb6ad6ed1965ab85da8bcb88216e3d91a8e5ed950`; see the hash note below) |
| Opening hook | unchanged: "You could turn the Sahara green. Geological records suggest it has happened more than 230 times before. But this time, what you'd change thousands of miles away is the part that's easy to miss." |
| Claim IDs | 47, all with a row in `story/claims.md`; 46 VERIFIED and 1 narrated as a hypothesis (G14) |
| Blocked / unverified claims in the narration | none |

## Change from v1.0
Exactly one sentence (ACT 4): "each roughly a kilometer across" became "each about half a mile across". Spoken words 1,777 to 1,778. Every other spoken word is unchanged. See `story/source_audit_round10.md`.

## Hash note (found in v1.1)
The v1.0 file recorded `e58756dff1179d5ae6d20d29f2f9d9215d6820899300e6630196e464446dfa18`. That value does not reproduce from the committed v1.0 script (commit 706a280) by the stated method or by any variant tried (with or without trailing newline, from the heading or the next line, to each section end). The most likely cause is that it was computed before a last edit in that commit. The v1.0 and v1.1 hashes in the table were both computed now with one method: UTF-8 bytes of everything from the line "## COLD OPEN" to the end of `script.md`, trailing newline included (`python3`: `t[t.index("## COLD OPEN"):]`). Use only these two values for comparison.

## What the lock means
The spoken text has been checked against the full source texts listed in `story/source_audit_round2.md` to `story/source_audit_round10.md`. It does not mean the video is produced. Voice, captions and render are separate steps. If a single word of the narration changes, the hash changes and the change needs a new audit entry.

## Accepted limitations (recorded, not hidden)
1. **Kemena et al. (G5, G6, G6b).** The reviewer accepted the complete author manuscript as the supporting source. The published journal PDF (Climate Dynamics 50(11-12):4561-4581, doi:10.1007/s00382-017-3890-8) was not directly compared with the manuscript. The two are not claimed to be textually identical, and the journal metadata was not verified by full-text inspection.
2. **L1 (resolved in v1.1).** "About half a mile across" is supported by Level-1 source-band measurements (2024 median 819 m, 2010 matched circles 803-804 m, uncertainty about ±30 m). No longer a limitation.
3. **Agency summaries.** S4-S7b, S12, S13, P10, P14, P18, P23, L2, L3, L4, G17-G19 are NASA or UNCCD descriptions of studies, read in full as web pages or reports; the underlying papers were not all read. The narration attributes them ("NASA says", "UNCCD documents credit", "a UN report ... based on figures reported to the Wall's own agency").
4. **Larrasoaña et al. 2013 (P20)** is a 2013 compilation; later literature was not checked. The number 230 is inferred from sapropel markers and is narrated as a reconstruction.
5. The storyboard timings are estimates from v0.1 and must be redone after the voice pass.
