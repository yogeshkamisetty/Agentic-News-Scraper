from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime
import re

import requests


HACKERNEWS_TOP_STORIES_URL = (
    "https://hacker-news.firebaseio.com/v0/topstories.json"
)

ITEM_URL = (
    "https://hacker-news.firebaseio.com/v0/item/{}.json"
)


def build_article(item):

    title = item.get(
        "title",
        ""
    )

    if not title:
        return None

    score = item.get(
        "score",
        0
    )

    url = item.get(
        "url",
        ""
    )

    comments = item.get(
        "descendants",
        0
    )

    text = item.get(
        "text",
        ""
    )

    if text:
        text = re.sub(
            r"<[^>]+>",
            " ",
            text
        )
        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

    summary_bits = [
        "HN discussion",
        f"Score: {score}",
        f"Comments: {comments}"
    ]

    if text:
        summary_bits.append(
            text[:280]
        )

    return {

        "Title":
        title,

        "Source":
        "Hacker News",

        "Published Date":
        datetime
        .utcfromtimestamp(
            item.get("time", 0)
        )
        .isoformat()
        if item.get("time")
        else "",

        "URL":
        url,

        "Summary":
        " | ".join(summary_bits)
    }


def fetch_story(story_id):

    try:

        item_response = requests.get(
            ITEM_URL.format(story_id),
            timeout=5
        )
        item_response.raise_for_status()
        item = item_response.json()

        if not item:
            return None

        return build_article(item)

    except Exception:

        return None


def collect_hackernews(
    limit=20,
    total_timeout=12
):

    articles = []

    try:

        response = requests.get(
            HACKERNEWS_TOP_STORIES_URL,
            timeout=3
        )

        response.raise_for_status()

        story_ids = (
            response.json()
            [:limit]
        )

        if not story_ids:
            print("Hacker News warning: 0 top stories returned")

        executor = ThreadPoolExecutor(max_workers=8)

        futures = [
            executor.submit(
                fetch_story,
                story_id
            )
            for story_id in story_ids
        ]

        done, pending = wait(
            futures,
            timeout=total_timeout
        )

        for future in done:

            article = future.result()

            if article:
                articles.append(article)

        if pending:
            print(
                "Hacker News warning: "
                f"{len(pending)} item fetches timed out"
            )

        executor.shutdown(
            wait=False,
            cancel_futures=True
        )

    except Exception as e:

        print(
            "Hacker News error:",
            e
        )

    return articles
