import html
import re

import feedparser
import requests
from bs4 import BeautifulSoup


USER_AGENT = "python:agentic_news_engine:v1.0"

REDDIT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
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


def collect_reddit(
    subreddit,
    limit=10,
    timeout=6
):

    articles = []

    feed_urls = [
        f"https://www.reddit.com/r/{subreddit}/.rss",
        f"https://old.reddit.com/r/{subreddit}/.rss"
    ]

    for feed_url in feed_urls:

        try:
            response = None
            for attempt in range(3):
                response = requests.get(
                    feed_url,
                    headers=REDDIT_HEADERS,
                    timeout=timeout
                )
                if response.status_code == 429:
                    import time
                    time.sleep(3)
                    continue
                break

            response.raise_for_status()

            feed = feedparser.parse(
                response.content
            )

            if not getattr(feed, "entries", None):
                continue

            for entry in feed.entries[:limit]:

                title = entry.get(
                    "title",
                    ""
                )

                if not title:
                    continue

                summary = clean_summary(
                    entry.get(
                        "summary",
                        ""
                    )
                )

                articles.append({
                    "Title": title,
                    "Source": f"r/{subreddit}",
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

            if articles:
                return articles

        except Exception as e:

            print(
                f"Reddit error {subreddit}: {str(e)[:100]}"
            )

    print(
        f"Reddit warning {subreddit}: no entries found via RSS fallback"
    )

    return articles
