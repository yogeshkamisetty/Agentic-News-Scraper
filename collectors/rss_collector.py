import html
import re

import feedparser
import requests
from bs4 import BeautifulSoup


RSS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*"
}


def clean_summary(text):

    if not text:
        return ""

    text = html.unescape(text)

    soup = BeautifulSoup(
        text,
        "html.parser"
    )

    clean = soup.get_text(
        " ",
        strip=True
    )

    clean = re.sub(
        r"\s+",
        " ",
        clean
    ).strip()

    return clean[:500]


def collect_rss(source, limit=10):

    try:

        response = requests.get(
            source["url"],
            headers=RSS_HEADERS,
            timeout=8
        )

        response.raise_for_status()

        feed = feedparser.parse(
            response.content
        )

    except Exception as exc:

        print(
            f"RSS fetch warning {source['name']}: {str(exc)[:120]}"
        )

        return []

    if getattr(feed, "bozo", False):

        print(
            f"RSS parse warning {source['name']}: "
            f"{getattr(feed, 'bozo_exception', '')}"
        )

    if not getattr(feed, "entries", None):

        print(
            f"RSS warning {source['name']}: 0 entries"
        )

    articles = []

    for entry in feed.entries[:limit]:

        title = entry.get(
            "title",
            ""
        )

        summary = clean_summary(
            entry.get("summary", "")
        )

        articles.append({
            "Title": title,
            "Source": source["name"],
            "Published Date": entry.get(
                "published",
                ""
            ),
            "URL": entry.get(
                "link",
                ""
            ),
            "Summary": summary,
            "Category": "",
            "Company Mentioned": "",
            "Keywords": "",
            "Importance Score": 0,
            "Why It Matters": "",
            "SaaS Impact": "",
            "PM Perspective": ""
        })

    return articles
