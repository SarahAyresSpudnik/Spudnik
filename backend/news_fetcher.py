import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx

from db import get_news_cache, set_news_cache

# Identifies this app honestly -- no browser spoofing. All six sources
# below were checked for a real feed before landing here; see the task
# notes for the two (TechCrunch, Phoronix) whose robots.txt disallows
# named AI-crawler bots (ClaudeBot/Claude-Web) even though the wildcard
# `*` rule -- which is what this User-Agent matches -- explicitly allows
# feed access. Flagged to Sarah rather than silently deciding it's fine.
USER_AGENT = "Spudnik/1.0 (+personal single-user news digest, not a training crawler)"

# Refresh-on-load with a TTL cache, not a scheduled job -- this is a
# weekly digest, not a live ticker. Re-fetching all six feeds on every
# single page view would be the "heavier infrastructure" this is meant
# to avoid; an hour-old digest is plenty fresh for this purpose.
CACHE_TTL_SECONDS = 60 * 60

ATOM_NS = "{http://www.w3.org/2005/Atom}"

SOURCES = [
    {"label": "TechCrunch", "feed_url": "https://techcrunch.com/feed/"},
    {"label": "Phoronix", "feed_url": "https://www.phoronix.com/rss.php"},
    {"label": "InfoQ", "feed_url": "https://feed.infoq.com/"},
    {"label": "TLDR Web Dev", "feed_url": "https://tldr.tech/api/rss/dev"},
    {"label": "The Robot Report", "feed_url": "https://www.therobotreport.com/feed/"},
    {"label": "TLDR AI", "feed_url": "https://tldr.tech/api/rss/ai"},
]

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _strip_html(text):
    # Feed descriptions vary from plain text (Phoronix) to embedded
    # <img>/<p> HTML (InfoQ) -- strip tags and collapse whitespace so
    # every source renders as a plain blurb.
    if not text:
        return ""
    text = _TAG_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


def _entry_link(entry):
    link = (entry.findtext("link") or "").strip()
    if link:
        return link
    # Atom-style <link href="..."/> fallback, in case a source's feed
    # ever switches formats.
    link_el = entry.find(f"{ATOM_NS}link")
    return link_el.get("href", "") if link_el is not None else ""


def _fetch_one(source, max_items=5, timeout=10):
    try:
        resp = httpx.get(
            source["feed_url"],
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            follow_redirects=True,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        return {"source": source["label"], "error": str(e), "items": []}

    channel = root.find("channel")
    entries = channel.findall("item") if channel is not None else root.findall(f"{ATOM_NS}entry")

    items = []
    for entry in entries[:max_items]:
        title = (entry.findtext("title") or "").strip()
        description = _strip_html(entry.findtext("description") or "")
        # TLDR's feed has no <description> at all -- one item per daily
        # digest issue, so the title (already a condensed teaser) doubles
        # as the blurb rather than leaving it blank.
        summary = description if description else title
        if len(summary) > 220:
            summary = summary[:217].rstrip() + "..."
        items.append({
            "title": title,
            "summary": summary,
            "link": _entry_link(entry),
            "published": (entry.findtext("pubDate") or "").strip(),
        })

    return {"source": source["label"], "error": None, "items": items}


def _cache_is_fresh(fetched_at_iso):
    try:
        fetched_at = datetime.fromisoformat(fetched_at_iso)
    except (TypeError, ValueError):
        return False
    age = datetime.now(timezone.utc) - fetched_at
    return age.total_seconds() < CACHE_TTL_SECONDS


def get_news():
    # One entry per source, always -- a broken/slow feed reports its own
    # error rather than disappearing from the list, so it's visible which
    # of the six actually failed instead of silently missing.
    results = []
    for source in SOURCES:
        cached = get_news_cache(source["label"])

        if cached and _cache_is_fresh(cached["fetched_at"]):
            results.append({
                "source": source["label"],
                "error": None,
                "items": json.loads(cached["items_json"]),
                "fetched_at": cached["fetched_at"],
            })
            continue

        fetched = _fetch_one(source)

        if fetched["error"] and cached:
            # Fetch failed but a stale cache exists -- serve that instead
            # of an empty card, while still surfacing the fetch error.
            results.append({
                "source": source["label"],
                "error": fetched["error"],
                "items": json.loads(cached["items_json"]),
                "fetched_at": cached["fetched_at"],
            })
            continue

        if not fetched["error"]:
            set_news_cache(source["label"], json.dumps(fetched["items"]))

        results.append({
            "source": source["label"],
            "error": fetched["error"],
            "items": fetched["items"],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })

    return results
