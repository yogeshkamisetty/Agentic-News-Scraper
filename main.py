import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import sys
import time
import re

sys.dont_write_bytecode = True

from collectors.rss_collector import (
    collect_rss
)

from collectors.hackernews_collector import (
    collect_hackernews
)

from collectors.reddit_collector import (
    collect_reddit
)

from collectors.api_collector import (
    collect_producthunt
)

from utils.deduplicator import (
    remove_duplicates
)

from utils.excel_writer import (
    save_to_excel
)



from utils.scorer import (
    calculate_score
)

from utils.category_classifier import (
    detect_category
)

from utils.company_detector import (
    detect_company
)

from utils.insight_generator import (
    generate_insights
)

from utils.top_updates import (
    get_top_updates
)

from utils.source_ranker import (
    apply_source_weight
)

from utils.quality_mode import (
    get_quality_mode,
    get_source_threshold as get_quality_source_threshold
)


QUALITY_MODE = get_quality_mode()
MAX_COLLECTION_WORKERS = 6


def load_portals():

    with open(
        "config/portals.json",
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def collect_articles(
    portal
):

    method = portal.get(
        "method"
    )

    if method == "rss":

        return collect_rss(
            portal,
            limit=10
        )

    elif method == "hackernews":

        return (
            collect_hackernews(
                limit=20
            )
        )

    elif method == "reddit":

        subreddit = portal.get(
            "subreddit"
        )

        return collect_reddit(
            subreddit
        )

    elif method == "producthunt":

        return collect_producthunt()

    return []


def validate_portals(
    portals
):

    errors = []

    valid_methods = {
        "rss",
        "hackernews",
        "reddit",
        "producthunt"
    }

    for index, portal in enumerate(
        portals,
        start=1
    ):

        name = portal.get(
            "name"
        )

        method = portal.get(
            "method"
        )

        label = name or f"portal {index}"

        if not name:
            errors.append(
                f"Portal {index} is missing name"
            )

        if method not in valid_methods:
            errors.append(
                f"{label} has unsupported method: {method}"
            )

        if method == "rss" and not portal.get("url"):
            errors.append(
                f"{label} is missing url"
            )

        if method == "reddit" and not portal.get("subreddit"):
            errors.append(
                f"{label} is missing subreddit"
            )

    return errors


def run_check_now():

    print(
        "\n=== AGENTIC NEWS ENGINE CHECK ===\n"
    )

    portals = load_portals()
    errors = validate_portals(
        portals
    )

    required_paths = [
        "config/portals.json",
        "config/quality_modes.json",
        "config/keywords.json",
        "outputs",
    ]

    for path in required_paths:

        if not os.path.exists(path):
            errors.append(
                f"Missing required path: {path}"
            )

    print(
        f"Quality mode: {QUALITY_MODE}"
    )

    print(
        f"Configured portals: {len(portals)}"
    )

    if errors:

        print(
            "\nCheck failed:"
        )

        for error in errors:
            print(
                f"- {error}"
            )

        return 1

    print(
        "\nCheck passed."
    )

    return 0


def get_mode_source_threshold(
    source,
    mode=None
):

    return get_quality_source_threshold(
        source,
        mode or QUALITY_MODE
    )


def passes_engagement_filter(
    article
):

    summary = article.get(
        "Summary",
        ""
    ).lower()

    if "reddit discussion" in summary:

        score_match = re.search(
            r"score:\s*(\d+)",
            summary
        )

        comments_match = re.search(
            r"comments:\s*(\d+)",
            summary
        )

        upvotes = (
            int(score_match.group(1))
            if score_match
            else 0
        )

        comments = (
            int(
                comments_match.group(1)
            )
            if comments_match
            else 0
        )

        return (
            upvotes >= 5
            and comments >= 5
        )

    return True


def process_article(
    article
):

    title = article.get(
        "Title",
        ""
    )

    summary = article.get(
        "Summary",
        ""
    )

    text = (
        f"{title} "
        f"{summary}"
    ).lower()

    category = detect_category(
        text
    )

    score, keywords = (
        calculate_score(
            text
        )
    )

    source = article.get(
        "Source",
        ""
    )

    score = apply_source_weight(
        score,
        source,
        category=category,
        mode=QUALITY_MODE
    )

    threshold = (
        get_mode_source_threshold(
            source,
            mode=QUALITY_MODE
        )
    )

    if score < threshold:
        return None

    # Bug fix: reject articles whose summaries are too thin to be useful
    # (newsletter teasers, Reddit link stubs, etc.)
    if len(str(summary).strip()) < 60:
        return None

    # Bug fix: require at least 2 distinct keyword hits so a single
    # accidental substring match (e.g. "rag" in "dragon") can't solo-pass.
    if len(keywords) < 2:
        return None

    if not (
        passes_engagement_filter(
            article
        )
    ):
        return None

    company = detect_company(
        title,
        summary
    )

    (
        why_it_matters,
        saas_impact,
        pm_perspective
    ) = generate_insights(
        title,
        summary,
        category
    )

    article[
        "Category"
    ] = category

    article[
        "Company Mentioned"
    ] = company

    article[
        "Keywords"
    ] = ", ".join(
        keywords
    )

    article[
        "Importance Score"
    ] = score

    article[
        "Why It Matters"
    ] = why_it_matters

    article[
        "SaaS Impact"
    ] = saas_impact

    article[
        "PM Perspective"
    ] = pm_perspective

    return article


def main():

    print(
        "\n=== AGENTIC NEWS ENGINE ===\n"
    )

    print(
        f"Quality mode: {QUALITY_MODE}\n"
    )

    portals = load_portals()

    all_articles = []

    raw_count = 0

    total_start = time.time()

    collection_results = []

    with ThreadPoolExecutor(
        max_workers=MAX_COLLECTION_WORKERS
    ) as executor:

        future_to_portal = {
            executor.submit(
                collect_articles,
                portal
            ): portal
            for portal in portals
        }

        for future in as_completed(
            future_to_portal
        ):

            portal = future_to_portal[
                future
            ]

            try:
                articles = future.result()
                error = None
            except Exception as exc:
                articles = []
                error = str(exc)[:120]

            collection_results.append({
                "portal": portal,
                "articles": articles,
                "error": error,
            })

    collection_result_by_name = {
        result["portal"].get("name", "Unknown"): result
        for result in collection_results
    }

    for portal in portals:

        portal_name = portal.get(
            "name",
            "Unknown"
        )

        result = collection_result_by_name.get(
            portal_name,
            {
                "articles": [],
                "error": "missing collection result"
            }
        )

        articles = result["articles"]

        raw_count += len(
            articles
        )

        print(
            f"Collecting from "
            f"{portal_name:<25}"
            f"{len(articles):>3} "
            f"updates"
        )

        if result["error"]:
            print(
                f"  warning: {result['error']}"
            )

        all_articles.extend(
            articles
        )

    raw_deduped_articles, raw_dedupe_stats = (
        remove_duplicates(
            all_articles,
            return_stats=True
        )
    )

    processed_articles = []

    for article in raw_deduped_articles:

        processed = (
            process_article(
                article
            )
        )

        if processed:

            processed_articles.append(
                processed
            )

    clean_articles, dedupe_stats = (
        remove_duplicates(
            processed_articles,
            return_stats=True
        )
    )

    # Rank the final dataset by importance score (highest first) so the
    # saved Excel and LinkedIn outputs are delivered in ranked order.
    filtered_articles = sorted(
        clean_articles,
        key=lambda a: a.get("Importance Score", 0),
        reverse=True
    )

    output_file = (
        save_to_excel(
            filtered_articles
        )
    )



    total_elapsed = round(
        time.time()
        - total_start,
        2
    )

    print(
        "\n=== COLLECTION SUMMARY ==="
    )

    print(
        f"Raw updates: "
        f"{raw_count}"
    )

    print(
        f"After raw dedupe: "
        f"{len(raw_deduped_articles)}"
    )

    print(
        f"Raw dedupe stats: "
        f"{raw_dedupe_stats}"
    )

    print(
        f"After scoring: "
        f"{len(processed_articles)}"
    )

    print(
        f"After dedupe: "
        f"{len(clean_articles)}"
    )

    print(
        f"Dedupe stats: "
        f"{dedupe_stats}"
    )

    print(
        f"Final quality updates: "
        f"{len(filtered_articles)}"
    )

    if output_file:
        print(
            "\nExcel generated successfully:"
        )
        print(output_file)
    else:
        print(
            "\nNo articles passed the quality filter - Excel not saved."
        )



    print(
        f"\nCompleted in "
        f"{total_elapsed}s"
    )

    top_articles = (
        get_top_updates(
            filtered_articles,
            top_n=5,
            mode=QUALITY_MODE
        )
    )

    print(
        "\n=== TOP STORIES TODAY ===\n"
    )

    for index, article in enumerate(
        top_articles,
        start=1
    ):

        print(
            f"{index}. "
            f"{article['Title']} "
            f"(Score: "
            f"{article['Importance Score']})"
        )

    print(
        "\n=== ENGINE COMPLETE ==="
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Collect and package agentic AI market updates."
    )
    parser.add_argument(
        "--check-now",
        action="store_true",
        help="Run fast local configuration checks without network collection."
    )
    args = parser.parse_args()

    if args.check_now:
        raise SystemExit(
            run_check_now()
        )

    main()
