#!/usr/bin/env python3
"""scout.py - free topic research for the daily pipeline (no vidIQ credits needed).

Runs as op "scout" of yt_ops.py in GitHub Actions (YouTube Data API with the channel's OAuth token: search.list costs
100 quota units of the free 10,000/day, nothing is billed). For every query it finds fresh videos, then collects each
video's channel's OWN recent uploads so /yt-viral outliers.py can compare the video with that author's typical views at
a comparable age. Output: collected videos + outlier rows. Facts only - no hypotheses, no invented numbers.

vidIQ is used instead/in addition only when the account has credits AND the owner authorized the paid call; the
pipeline records "vidiq: unavailable (0 credits)" as a gap otherwise.
"""
import json, os, sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".claude", "skills", "yt-publish"))
sys.path.insert(0, os.path.join(HERE, "..", ".claude", "skills", "yt-viral"))
import publish as P   # noqa: E402
import outliers as OL  # noqa: E402


def search(token, q, days=45, n=15):
    after = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    j = P.api("GET", "search", {"part": "snippet", "q": q, "type": "video", "order": "viewCount", "publishedAfter": after,
                                "relevanceLanguage": "en", "regionCode": "US", "videoDuration": "medium", "maxResults": n}, token=token)
    return [(i["id"]["videoId"], i["snippet"]["channelId"]) for i in j.get("items", [])]


def videos(token, ids):
    out = []
    for k in range(0, len(ids), 50):
        j = P.api("GET", "videos", {"part": "snippet,statistics,contentDetails", "id": ",".join(ids[k:k + 50])}, token=token)
        for v in j.get("items", []):
            out.append({"video_id": v["id"], "channel_id": v["snippet"]["channelId"], "channel": v["snippet"]["channelTitle"],
                        "title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"],
                        "views": int(v.get("statistics", {}).get("viewCount", 0)),
                        "duration": P.parse_duration(v["contentDetails"].get("duration")),
                        "url": f"https://www.youtube.com/watch?v={v['id']}"})
    return out


def channel_uploads(token, cid, n=30):
    j = P.api("GET", "channels", {"part": "contentDetails", "id": cid}, token=token)
    if not j.get("items"):
        return []
    pl = j["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    items = P.api("GET", "playlistItems", {"part": "contentDetails", "playlistId": pl, "maxResults": min(n, 50)}, token=token)
    return [i["contentDetails"]["videoId"] for i in items.get("items", [])]


def run(queries, token=None, max_channels=12):
    token = token or P.access_token()
    hits, gaps = [], []
    for q in queries:
        try:
            hits += [(vid, cid, q) for vid, cid in search(token, q)]
        except P.PublishError as ex:
            gaps.append({"query": q, "error": P.redact(ex)[:160]})
    found = videos(token, list(dict.fromkeys(v for v, _, _ in hits)))
    qmap = {v: q for v, _, q in hits}
    for f in found:
        f["query"] = qmap.get(f["video_id"])
    chans = list(dict.fromkeys(f["channel_id"] for f in sorted(found, key=lambda x: -x["views"])))[:max_channels]
    comp_ids = []
    for c in chans:
        try:
            comp_ids += channel_uploads(token, c)
        except P.PublishError as ex:
            gaps.append({"channel": c, "error": P.redact(ex)[:160]})
    comps = videos(token, [i for i in dict.fromkeys(comp_ids) if i not in {f["video_id"] for f in found}])
    allv = found + comps
    rep = OL.detect([OL.normalize(v) for v in allv])
    keep = {f["video_id"] for f in found}
    res = {"rows": [r for r in rep["results"] if r["facts"].get("video_id") in keep], "focus": [f for f in rep["focus"] if f in keep],
           "as_of": rep["as_of"], "videos": rep["videos"], "channels": rep["channels"]}
    return {"queries": queries, "found": found, "comparables": len(comps), "outliers": res, "gaps": gaps,
            "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "collector": "YouTube Data API (free quota)"}
