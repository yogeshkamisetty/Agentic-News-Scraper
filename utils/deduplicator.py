import re
from collections import Counter
from urllib.parse import parse_qsl, urlsplit, urlunsplit, urlencode

from rapidfuzz import fuzz


HEADLINE_SIMILARITY_THRESHOLD = 82
HEADLINE_TOKEN_SET_THRESHOLD = 85
HEADLINE_OVERLAP_THRESHOLD = 0.40
CONTEXT_SIMILARITY_THRESHOLD = 78
CONTEXT_OVERLAP_THRESHOLD = 0.25
TITLE_EXACT_THRESHOLD = 95

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "fbclid",
    "gclid",
    "ref",
    "source",
    "mc_cid",
    "mc_eid"
}

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for",
    "with", "from", "by", "at", "is", "are", "be", "as", "it", "this",
    "that", "they", "their", "your", "into", "over", "after", "about",
    "new", "why", "what", "how", "who", "when", "where", "can", "will"
}

LAST_DEDUP_STATS = {}


def normalize_title(title):

    title = str(title or "").lower().strip()
    title = re.sub(r"\[[^\]]+\]", " ", title)
    title = re.sub(r"\([^\)]*\)", " ", title)
    title = re.sub(r"[|/:;,_–—-]+", " ", title)
    title = re.sub(r"[^a-z0-9\s]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def canonicalize_url(url):

    url = str(url or "").strip()

    if not url:
        return ""

    parts = urlsplit(url)
    netloc = parts.netloc.lower().replace("www.", "").replace("old.", "")
    path = re.sub(r"/+$", "", parts.path.lower())

    query = urlencode(
        sorted(
            (
                key,
                value
            )
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
            if key.lower() not in TRACKING_PARAMS
        )
    )

    return urlunsplit((parts.scheme.lower(), netloc, path, query, ""))


def significant_tokens(text):

    tokens = re.findall(r"[a-z0-9]+", normalize_title(text))
    return {
        token
        for token in tokens
        if len(token) > 2 and token not in STOPWORDS
    }


def hybrid_similarity(left, right):

    ratio = fuzz.ratio(left, right)
    token_sort = fuzz.token_sort_ratio(left, right)
    token_set = fuzz.token_set_ratio(left, right)

    return (
        (ratio * 0.2)
        + (token_sort * 0.4)
        + (token_set * 0.4)
    )


def article_strength(article):

    score = article.get("Importance Score", 0) or 0
    title = str(article.get("Title", "") or "")
    summary = str(article.get("Summary", "") or "")

    return (
        score,
        len(title) + len(summary)
    )


def is_better_article(candidate, existing):

    candidate_score, candidate_length = article_strength(candidate)
    existing_score, existing_length = article_strength(existing)

    if candidate_score != existing_score:
        return candidate_score > existing_score

    if candidate_length != existing_length:
        return candidate_length > existing_length

    return str(candidate.get("Source", "")) < str(existing.get("Source", ""))


def remove_duplicates(articles, return_stats=False):

    unique_articles = []
    stats = Counter()

    for article in articles:

        title = normalize_title(article.get("Title", ""))
        summary = normalize_title(article.get("Summary", ""))
        combined = f"{title} {summary}".strip()
        url = canonicalize_url(article.get("URL", ""))
        article_tokens = significant_tokens(combined)
        title_tokens = significant_tokens(title)

        matched_index = None
        matched_reason = None

        for index, existing in enumerate(unique_articles):

            existing_title = normalize_title(existing.get("Title", ""))
            existing_summary = normalize_title(existing.get("Summary", ""))
            existing_combined = f"{existing_title} {existing_summary}".strip()
            existing_url = canonicalize_url(existing.get("URL", ""))
            existing_tokens = significant_tokens(existing_combined)
            existing_title_tokens = significant_tokens(existing_title)

            if url and existing_url and url == existing_url:
                matched_index = index
                matched_reason = "url"
                break

            if title and existing_title and title == existing_title:
                matched_index = index
                matched_reason = "title_exact"
                break

            headline_ratio = fuzz.ratio(title, existing_title)
            headline_token_sort = fuzz.token_sort_ratio(title, existing_title)
            headline_token_set = fuzz.token_set_ratio(title, existing_title)
            headline_hybrid = hybrid_similarity(title, existing_title)

            context_ratio = fuzz.ratio(combined, existing_combined)
            context_token_sort = fuzz.token_sort_ratio(combined, existing_combined)
            context_token_set = fuzz.token_set_ratio(combined, existing_combined)
            context_hybrid = hybrid_similarity(combined, existing_combined)

            headline_overlap = 0.0
            if title_tokens and existing_title_tokens:
                headline_overlap = len(title_tokens & existing_title_tokens) / len(title_tokens | existing_title_tokens)

            overlap = 0.0
            if article_tokens and existing_tokens:
                overlap = len(article_tokens & existing_tokens) / len(article_tokens | existing_tokens)

            if (
                headline_hybrid >= HEADLINE_SIMILARITY_THRESHOLD
                and headline_overlap >= HEADLINE_OVERLAP_THRESHOLD
            ) or (
                headline_token_set >= HEADLINE_TOKEN_SET_THRESHOLD
                and headline_overlap >= 0.30
            ) or (
                context_hybrid >= CONTEXT_SIMILARITY_THRESHOLD
                and overlap >= CONTEXT_OVERLAP_THRESHOLD
            ) or (
                context_token_set >= HEADLINE_TOKEN_SET_THRESHOLD + 3
                and overlap >= 0.20
            ) or headline_ratio >= TITLE_EXACT_THRESHOLD or context_ratio >= TITLE_EXACT_THRESHOLD:
                matched_index = index
                matched_reason = "fuzzy"
                break

        if matched_index is None:
            unique_articles.append(article)
            stats["kept"] += 1
            continue

        stats[f"duplicate_{matched_reason}"] += 1

        if is_better_article(article, unique_articles[matched_index]):
            unique_articles[matched_index] = article
            stats["replaced"] += 1
        else:
            stats["discarded"] += 1

    global LAST_DEDUP_STATS
    LAST_DEDUP_STATS = dict(stats)
    LAST_DEDUP_STATS["input_count"] = len(articles)
    LAST_DEDUP_STATS["output_count"] = len(unique_articles)

    if return_stats:
        return unique_articles, LAST_DEDUP_STATS

    return unique_articles