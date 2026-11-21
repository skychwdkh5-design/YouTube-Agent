"""seo.py - the discovery standard for every pipeline release (owner request 2026-11-20).

YouTube decides who sees a video mostly from viewer behaviour, the title and the thumbnail; the
description, chapters, hashtags and tags are the text signals that tell it what the video is about
and who searches for it. This module checks those text signals on meta.json before a card is shown.

meta.json fields used:
  title, description, tags, search_queries (3 queries a real US viewer would type, best first)

Rules (FAIL blocks the card):
  queries     3 distinct search queries are written down for the release
  hook        the first 150 characters of the description (the search snippet / above "...more")
              contain the main words of query 1 and carry no link
  chapters    at least 3 chapters, the first at 0:00, increasing, each >= 10 s long
  hashtags    3-5 hashtags in the description, specific to the topic (the first is not the channel
              name), no spaces, no duplicates; YouTube shows the first 3 above the title
  tags        8-15 tags, <= 500 characters in total, include query 1 (or its words) and the channel name
"""
import re

STOP = {"a", "an", "the", "of", "in", "on", "to", "for", "and", "or", "is", "are", "was", "how", "why", "what", "does", "do",
        "did", "this", "that", "from", "with", "by", "at", "it", "its", "new", "just"}
HASHTAG = re.compile(r"(?<![\w&])#([A-Za-z0-9_]+)")
CHAPTER = re.compile(r"^\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s+\S", re.M)


def _words(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in STOP and len(w) > 1}


def _chapters(desc):
    out = []
    for m in CHAPTER.finditer(desc):
        a, b, c = m.groups()
        out.append(int(a) * 3600 + int(b) * 60 + int(c) if c is not None else int(a) * 60 + int(b))
    return out


def check(meta, channel_name, duration=None):
    """Returns a list of (name, ok, detail)."""
    title, desc = meta.get("title", ""), meta.get("description", "")
    tags = [t.strip() for t in meta.get("tags", []) if t and t.strip()]
    qs = [q.strip() for q in meta.get("search_queries", []) if q and q.strip()]
    res = []
    res.append(("seo: 3 search queries", len(qs) >= 3 and len({q.lower() for q in qs}) == len(qs), {"queries": qs}))
    q1 = _words(qs[0]) if qs else set()
    head = desc.strip().split("\n\n")[0][:150]          # the opening paragraph as the snippet shows it
    hit = q1 & _words(head)
    res.append(("seo: description hook", bool(q1) and len(hit) >= max(1, (len(q1) + 1) // 2) and "http" not in head,
                {"first_150": head, "query_words": sorted(q1), "found": sorted(hit)}))
    ch = _chapters(desc)
    ok = len(ch) >= 3 and ch[0] == 0 and all(b - a >= 10 for a, b in zip(ch, ch[1:]))
    if ok and duration:
        ok = ch[-1] < duration - 10
    res.append(("seo: chapters", ok, {"starts_s": ch}))
    hs = HASHTAG.findall(desc)
    low = [h.lower() for h in hs]
    chan = re.sub(r"[^a-z0-9]", "", channel_name.lower())
    res.append(("seo: hashtags", 3 <= len(hs) <= 5 and len(set(low)) == len(low) and bool(hs) and low[0] != chan,
                {"hashtags": ["#" + h for h in hs]}))
    total = sum(len(t) + (2 if " " in t else 0) + 1 for t in tags)
    tag_words = set().union(*[_words(t) for t in tags]) if tags else set()
    has_q1 = bool(qs) and (qs[0].lower() in [t.lower() for t in tags] or (q1 and q1 <= tag_words))
    has_chan = any(re.sub(r"[^a-z0-9]", "", t.lower()) == chan for t in tags)
    res.append(("seo: tags", 8 <= len(tags) <= 15 and total <= 500 and has_q1 and has_chan,
                {"count": len(tags), "chars": total, "query1_covered": has_q1, "channel_tag": has_chan}))
    return res
