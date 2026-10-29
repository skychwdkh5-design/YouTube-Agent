#!/usr/bin/env python3
"""Optional zero-dependency RSS/Atom topic discovery. Never publishes or modifies episodes."""
import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import html
import json
import re
import sys
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

FEEDS = {
    "nexora": [
        "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    ],
    "orbital-atlas": [
        "https://www.nasa.gov/rss/dyn/earth.rss",
        "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    ],
}
ATOM = "{http://www.w3.org/2005/Atom}"

def plain(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(value or ""))).strip()

def parse_feed(xml_bytes, source):
    root = ET.fromstring(xml_bytes)
    records = []
    for item in root.findall(".//item"):
        title = plain(item.findtext("title"))
        url = (item.findtext("link") or "").strip()
        pub = item.findtext("pubDate") or ""
        if title and url.startswith("https://"):
            records.append({"title": title, "url": url, "published": pub,
                            "source_feed": source, "verification": "SOURCE_REVIEW_REQUIRED"})
    for item in root.findall(f".//{ATOM}entry"):
        title = plain(item.findtext(f"{ATOM}title"))
        links = item.findall(f"{ATOM}link")
        url = next((l.attrib.get("href","") for l in links if l.attrib.get("rel","alternate") == "alternate"),
                   next((l.attrib.get("href","") for l in links), ""))
        pub = item.findtext(f"{ATOM}published") or item.findtext(f"{ATOM}updated") or ""
        if title and url.startswith("https://"):
            records.append({"title": title, "url": url, "published": pub,
                            "source_feed": source, "verification": "SOURCE_REVIEW_REQUIRED"})
    return records

def date_sort(item):
    value = item["published"]
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = parsedate_to_datetime(value)
        except (ValueError, TypeError):
            return 0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()

def collect(feeds, timeout=12):
    found, warnings = [], []
    for feed in feeds:
        if not feed.startswith("https://"):
            warnings.append(f"Rejected non-HTTPS feed: {feed}")
            continue
        try:
            request = Request(feed, headers={"User-Agent": "FreeTopicScout/1.0 (+manual research)"})
            with urlopen(request, timeout=timeout) as response:
                if int(response.headers.get("Content-Length", "0")) > 2_000_000:
                    raise ValueError("Feed too large")
                data = response.read(2_000_001)
                if len(data) > 2_000_000:
                    raise ValueError("Feed too large")
                found.extend(parse_feed(data, feed))
        except Exception as exc:
            warnings.append(f"{feed}: {type(exc).__name__}: {exc}")
    unique = {x["url"]: x for x in found}
    return sorted(unique.values(), key=date_sort, reverse=True), warnings

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=sorted(FEEDS), required=True)
    parser.add_argument("--feed", action="append", help="Additional HTTPS RSS/Atom feed")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--format", choices=["json","markdown"], default="markdown")
    args = parser.parse_args()
    items, warnings = collect(FEEDS[args.channel] + (args.feed or []))
    items = items[:max(0,min(args.limit,50))]
    if args.format == "json":
        print(json.dumps({"channel":args.channel,"candidates":items,"warnings":warnings},ensure_ascii=False,indent=2))
    else:
        print(f"# Topic candidates: {args.channel}\n")
        print("Discovery only; independently verify publication date, event date, claims and asset rights.\n")
        for item in items:
            print(f"- **{item['title']}** | {item['published']} | {item['url']} | VERIFY")
        for warning in warnings:
            print(f"\nWARNING: {warning}", file=sys.stderr)
    return 0 if items else 1

if __name__ == "__main__":
    raise SystemExit(main())
