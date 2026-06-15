"""
rss_collector.py
────────────────
Resilient RSS/Atom feed collector.

Hardening features:
  • Retry with backoff on transient failures (timeouts, 429, 5xx)
  • Longer, configurable timeout
  • Multi-field summary extraction (summary → content → description)
  • Multi-field date extraction (published → updated → pubDate)
  • Graceful per-feed failure — never raises, always returns a list
  • Consistent article schema for downstream processing
"""

import html
import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup


RSS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

# Network behaviour
DEFAULT_TIMEOUT = 15          # seconds per attempt
MAX_RETRIES = 2               # additional attempts after the first
RETRY_BACKOFF = 1.5          # seconds, multiplied by attempt number
RETRYABLE_STATUS = {429, 500, 502, 503, 504}

# Empty article schema — keeps downstream columns consistent
ARTICLE_FIELDS = {
    "Category": "",
    "Company Mentioned": "",
    "Keywords": "",
    "Importance Score": 0,
    "Why It Matters": "",
    "SaaS Impact": "",
    "PM Perspective": "",
}


def clean_summary(text):
    """Strip HTML, decode entities, collapse whitespace, cap length."""
    if not text:
        return ""

    text = html.unescape(text)
    soup = BeautifulSoup(text, "html.parser")
    clean = soup.get_text(" ", strip=True)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:500]


def _extract_summary(entry):
    """
    Pull the best available text body from an entry.
    Order: summary → content[].value → description → subtitle.
    """
    candidates = []

    if entry.get("summary"):
        candidates.append(entry.get("summary"))

    content = entry.get("content")
    if content:
        for block in content:
            value = block.get("value") if isinstance(block, dict) else None
            if value:
                candidates.append(value)

    if entry.get("description"):
        candidates.append(entry.get("description"))

    if entry.get("subtitle"):
        candidates.append(entry.get("subtitle"))

    # Return the longest cleaned candidate (richest content)
    best = ""
    for raw in candidates:
        cleaned = clean_summary(raw)
        if len(cleaned) > len(best):
            best = cleaned
    return best


def _extract_date(entry):
    """Best available publication date."""
    for field in ("published", "updated", "pubDate", "created"):
        value = entry.get(field)
        if value:
            return value
    return ""


def _fetch_feed(url, timeout):
    """
    Fetch a feed with retry/backoff.
    Returns parsed feedparser object, or None on hard failure.
    """
    last_exc = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=RSS_HEADERS, timeout=timeout)

            if response.status_code in RETRYABLE_STATUS:
                last_exc = f"HTTP {response.status_code}"
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF * (attempt + 1))
                    continue
                return None

            response.raise_for_status()
            return feedparser.parse(response.content)

        except requests.exceptions.RequestException as exc:
            last_exc = str(exc)[:120]
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF * (attempt + 1))
                continue

    if last_exc:
        # surfaced by caller via the None return
        _fetch_feed.last_error = last_exc
    return None


def collect_rss(source, limit=10, timeout=DEFAULT_TIMEOUT):
    """
    Collect up to `limit` articles from a single RSS/Atom source.
    Never raises — returns [] on any failure.
    """
    name = source.get("name", "Unknown")
    url = source.get("url", "")

    if not url:
        print(f"RSS warning {name}: no URL configured")
        return []

    feed = _fetch_feed(url, timeout)

    if feed is None:
        err = getattr(_fetch_feed, "last_error", "fetch failed")
        print(f"RSS fetch warning {name}: {err}")
        return []

    if getattr(feed, "bozo", False) and not getattr(feed, "entries", None):
        print(
            f"RSS parse warning {name}: "
            f"{str(getattr(feed, 'bozo_exception', ''))[:80]}"
        )
        return []

    entries = getattr(feed, "entries", None) or []

    if not entries:
        print(f"RSS warning {name}: 0 entries")
        return []

    articles = []

    for entry in entries[:limit]:
        title = (entry.get("title") or "").strip()
        if not title:
            continue

        article = {
            "Title": title,
            "Source": name,
            "Published Date": _extract_date(entry),
            "URL": entry.get("link", ""),
            "Summary": _extract_summary(entry),
        }
        article.update(ARTICLE_FIELDS)
        articles.append(article)

    return articles
