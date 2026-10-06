---
name: geo-factcheck
description: >-
  Verify every factual claim in a geography video - population, borders, area,
  dates, distances, rankings, statistics, superlatives - against primary
  sources, and gate the script until all of them pass. Use for "fact-check
  this", "verify the claims", "is this true", before packaging any geography
  video, and whenever a viewer comment says a fact is wrong.
---

# geo-factcheck

One wrong number in a geography video becomes the top comment. This skill exists so that never
happens. It runs twice per video, and nothing moves past it on a FAIL.

```bash
python3 claims.py --claims channel/videos/<slug>/claims.md                                   # GATE 1
python3 claims.py --claims channel/videos/<slug>/claims.md --script channel/videos/<slug>/script.md   # GATE 2
```

## Before you start

Read `channel/research.md` (source tiers, ledger format, definitions) and `channel/editorial.md`
(wording rules, disputed territories). They are the rules this skill applies.

## GATE 1 - the ledger (after geo-research, before any script)

For every row in `claims.md`:

1. **Open the source and read the figure yourself.** Never verify from memory, from a search
   snippet, or from another video. If the page cannot be reached, the claim stays UNVERIFIED.
2. **Match the definition.** Land vs total area, city vs metro, census count vs estimate, de jure vs
   de facto border. Write the definition into the Claim or Final wording.
3. **Record** source, URL, accessed date (YYYY-MM-DD) and tier for each source.
4. **Set the status:**
   - `VERIFIED` - a Tier 1 source, or Tier 2 where no Tier 1 exists, says exactly this.
   - `SOFTENED` - true only with qualification. Write the Final wording the script must use
     ("one of the most remote", "about 1,000 people as of the 2020 Census").
   - `CONFLICT` - good sources disagree. Either soften to what they agree on or cut it.
   - `UNVERIFIED` - not yet found. Blocks the gate if the script uses it.
   - `CUT` - false or unprovable. It must not appear in the script.
5. **Superlatives, rankings and "only / first / last"** need two independent sources (two domains).
   Prefer "one of the" unless an official record exists.
6. **Population and statistics carry their year** in the wording.

Gate 1 passes when `claims.py --claims` exits 0.

## GATE 2 - the script (after yt-script, before visuals and packaging)

- Every factual sentence in `script.md` carries its tag: `...only by road through Canada [C3].`
- A sentence the detector flags but that is not a claim gets `[NC]`. Use it honestly - "the
  first thing you notice" is NC; "the first town in America to..." never is.
- The script uses the **Final wording** of every SOFTENED claim, word for word in meaning.
- Re-read the script once as a hostile commenter. Anything that sounds stronger than the ledger
  supports gets rewritten, even if the tool passes it.

Gate 2 passes when `claims.py --claims ... --script ...` exits 0. Only then do geo-visuals, yt-package
and yt-seo start.

## After publication - corrections

When `/yt-comment` triage finds a correction:

1. Check it against the ledger and the source. Never argue a fact you have not re-checked.
2. If we were wrong: pin a correction comment, fix the description, add the correction to `post.md`,
   and update `channel/research.md` "Lessons" so the same error cannot recur.
3. If we were right: reply with the source, politely, once.

## What to hand back

The `claims.py` output, the list of claims that changed status, and for every SOFTENED or CUT claim
the exact wording the script must now use.

## The gate

Nothing here publishes. This skill writes and you publish. Every output ends in a block the user
copies, and the last line of every run is the question: **ship it, or change it?**
