# YouTube-Agent

Claude Code workspace for running a YouTube channel. The skills live in `.claude/skills/yt-*`.
This file is the project-level audience strategy; every yt-* skill follows it.

## Audience strategy

- **Primary market: United States.** Highest priority for topics, hooks, titles, thumbnails,
  scripts and monetization. The US score is the dominant factor in every decision.
- **Secondary markets: Sweden, Norway, Denmark.**
- **Content language: English.** Do not translate scripts into Swedish, Norwegian or Danish unless
  the user asks.

### Choosing topics

Favour stories with strong visual and curiosity pull: unusual geography, strange borders, islands
and isolated territories, satellite discoveries, dramatic landscape changes, natural disasters,
abandoned places, unusual infrastructure, extreme environments, mysteries visible from orbit,
before/after transformations, unusual human impact on landscapes.

When comparing topics, rate each on:

1. US audience potential (dominant)
2. Sweden audience potential
3. Norway audience potential
4. Denmark audience potential
5. International English-speaking potential
6. Visual strength
7. Curiosity / click potential
8. Availability of reliable evidence
9. Availability of useful satellite imagery, when relevant
10. Monetization suitability

Decision rules:

- Never reject a strong US topic because its Scandinavian relevance is low.
- When two topics have similar US potential, prefer the one with stronger international and
  Scandinavian potential.
- Scandinavian appeal means the underlying story travels - not that it mentions Sweden, Norway or
  Denmark. Never force a Scandinavian angle into a video.
- A topic with no reliable evidence loses to one with evidence, whatever its other scores.

### Writing titles, hooks and scripts

- Natural English written for a US viewer, with American hook style and pacing.
- Avoid US slang an international English speaker would not follow.
- Explain US-specific concepts in a few words when they matter (a county, a state highway, the
  lower 48, a federal agency).
- Prefer units and references both audiences get; when a US unit is used for a key number, a
  metric equivalent in passing is fine.

### Satellite research

`/yt-satellite` works worldwide - Landsat covers the whole globe. Stories in Sweden, Norway, Denmark
or anywhere else may use it when satellite evidence materially improves the story. The no-
fabrication rules in that skill apply everywhere: no scene, no satellite claim.
