import json
import os
import re
from collections import Counter, defaultdict
from urllib.parse import parse_qsl, urlsplit, urlunsplit, urlencode

import pandas as pd
from rapidfuzz import fuzz

from utils.quality_mode import get_quality_mode


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

THEME_CONFIG_PATH = os.path.join(
    PROJECT_ROOT,
    "config",
    "theme_clustering.json"
)

QUALITY_MODE = get_quality_mode()

DEFAULT_STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for",
    "with", "from", "by", "at", "is", "are", "be", "as", "it", "this",
    "that", "they", "their", "your", "into", "over", "after", "about",
    "new", "why", "what", "how", "who", "when", "where", "can", "will",
    "ai", "llm", "model", "models", "update", "updates", "launches",
    "launch", "announces", "announced", "report", "reports", "analysis",
    "system", "systems", "product", "products", "tool", "tools", "platform",
    "platforms", "team", "teams", "use", "using", "based", "build", "built",
    "first", "next", "new", "latest", "week", "today", "future", "market",
    "enterprise", "developer", "developers"
}

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "fbclid", "gclid", "ref", "source", "mc_cid", "mc_eid"
}

THEME_GENERIC_TOKENS = {
    "ai", "model", "models", "system", "systems", "update", "updates",
    "launch", "launches", "announces", "announced", "news", "report",
    "reports", "new", "next", "platform", "platforms", "tool", "tools",
    # newsletter / publication names that leak into theme titles
    "import", "download", "batch", "breakfast", "bites", "latent",
    "space", "ahead", "weekly", "daily", "edition", "issue", "roundup",
    "digest", "newsletter", "podcast", "interview", "recap",
    # weak descriptors
    "guide", "intro", "overview", "deep", "dive", "part", "way", "ways",
    "thing", "things", "story", "today", "week", "year",
}

# Vendor / proper-noun fragments that make poor standalone theme names.
# When a fallback name would be built ONLY from these, we prefer the
# representative article's Category instead (e.g. "Google 2026" -> "AI Update").
THEME_VENDOR_TOKENS = {
    "google", "openai", "anthropic", "meta", "microsoft", "nvidia",
    "amazon", "apple", "alibaba", "deepseek", "mistral", "qwen",
    "gemini", "claude", "gpt", "llama", "apex", "minimax", "cohere",
}

THEME_PRIORITY_RULES = [
    (
        "AI Model Economics",
        ["pricing", "cost", "inference", "price", "cheaper", "lower-cost", "lower cost", "reduce cost"],
    ),
    (
        "Agent Memory Systems",
        ["memory", "persistent", "state", "long-horizon", "long horizon", "context"],
    ),
    (
        "Agent Control & Permissions",
        ["permissions", "permission", "access", "authorization", "sandbox", "tool use"],
    ),
    (
        "Model Evaluation",
        ["benchmark", "eval", "leaderboard", "testing", "assessment"],
    ),
    (
        "RAG Infrastructure",
        ["rag", "retrieval", "vector", "index", "knowledge"],
    ),
    (
        "Developer AI Workflow",
        ["coding", "developer", "terminal", "cli", "debug"],
    ),
    (
        "Enterprise AI Governance",
        ["enterprise", "governance", "compliance", "security", "policy"],
    ),
    (
        "Agent Orchestration",
        ["agent", "agentic", "workflow", "orchestration", "planning", "multi-agent", "multi agent"],
    ),
]

_THEME_CONFIG = None


def load_theme_config():

    global _THEME_CONFIG

    if _THEME_CONFIG is not None:
        return _THEME_CONFIG

    try:
        with open(THEME_CONFIG_PATH, "r", encoding="utf-8") as file:
            _THEME_CONFIG = json.load(file)
    except Exception:
        _THEME_CONFIG = {
            "balanced": {
                "similarity_threshold": 0.62,
                "weights": {
                    "title": 0.32,
                    "context": 0.24,
                    "tokens": 0.20,
                    "company": 0.14,
                    "category": 0.08,
                    "source": 0.02,
                },
                "theme_score": {
                    "cohesion_multiplier": 16,
                    "size_bonus": 2,
                    "max_size_bonus": 10,
                },
                "max_output_themes": 12,
            }
        }

    return _THEME_CONFIG


def get_theme_profile(mode=None):

    config = load_theme_config()
    mode = str(mode or QUALITY_MODE).strip().lower()

    if mode not in config:
        mode = "balanced"

    return config[mode]


def normalize_text(text):

    text = str(text or "").lower().strip()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = re.sub(r"\([^)]+\)", " ", text)
    text = re.sub(r"[|/:;,_–—-]+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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


def tokenize(text):

    tokens = re.findall(r"[a-z0-9]+", normalize_text(text))
    return [
        token
        for token in tokens
        if len(token) > 2 and token not in DEFAULT_STOPWORDS
    ]


def token_set(text):

    return set(tokenize(text))


def split_companies(value):

    value = str(value or "").strip()

    if not value:
        return set()

    return {
        token.strip().lower()
        for token in value.split(",")
        if token.strip()
    }


def jaccard(left, right):

    if not left or not right:
        return 0.0

    return len(left & right) / len(left | right)


def get_theme_similarity(article, representative, weights):

    title_left = normalize_text(article.get("Title", ""))
    title_right = normalize_text(representative.get("Title", ""))

    summary_left = normalize_text(article.get("Summary", ""))
    summary_right = normalize_text(representative.get("Summary", ""))

    combined_left = f"{title_left} {summary_left}".strip()
    combined_right = f"{title_right} {summary_right}".strip()

    title_scores = [
        fuzz.ratio(title_left, title_right),
        fuzz.token_sort_ratio(title_left, title_right),
        fuzz.token_set_ratio(title_left, title_right),
    ]

    context_scores = [
        fuzz.ratio(combined_left, combined_right),
        fuzz.token_sort_ratio(combined_left, combined_right),
        fuzz.token_set_ratio(combined_left, combined_right),
    ]

    title_similarity = sum(title_scores) / (len(title_scores) * 100.0)
    context_similarity = sum(context_scores) / (len(context_scores) * 100.0)

    article_tokens = token_set(combined_left)
    rep_tokens = token_set(combined_right)
    token_similarity = jaccard(article_tokens, rep_tokens)

    company_similarity = jaccard(
        split_companies(article.get("Company Mentioned", "")),
        split_companies(representative.get("Company Mentioned", "")),
    )

    category_similarity = 1.0 if str(article.get("Category", "")).strip() == str(representative.get("Category", "")).strip() else 0.0
    source_similarity = 1.0 if str(article.get("Source", "")).strip() == str(representative.get("Source", "")).strip() else 0.0

    score = (
        weights.get("title", 0.32) * title_similarity
        + weights.get("context", 0.24) * context_similarity
        + weights.get("tokens", 0.20) * token_similarity
        + weights.get("company", 0.14) * company_similarity
        + weights.get("category", 0.08) * category_similarity
        + weights.get("source", 0.02) * source_similarity
    )

    return round(score, 4)


def is_better_article(candidate, existing):

    candidate_score = candidate.get("Importance Score", 0) or 0
    existing_score = existing.get("Importance Score", 0) or 0

    if candidate_score != existing_score:
        return candidate_score > existing_score

    candidate_len = len(str(candidate.get("Title", "") or "")) + len(str(candidate.get("Summary", "") or ""))
    existing_len = len(str(existing.get("Title", "") or "")) + len(str(existing.get("Summary", "") or ""))

    if candidate_len != existing_len:
        return candidate_len > existing_len

    return str(candidate.get("Source", "")) < str(existing.get("Source", ""))


def build_theme_name(articles, fallback_category="AI Update"):

    config = load_theme_config()
    patterns = config.get("theme_patterns", [])

    text = " ".join(
        normalize_text(article.get("Title", ""))
        for article in articles
    )

    lowered = text.lower()

    for pattern in patterns:
        keywords = pattern.get("keywords", [])
        if keywords and any(keyword in lowered for keyword in keywords):
            return pattern.get("name", fallback_category)

    token_counts = Counter()
    for article in articles:
        token_counts.update(tokenize(article.get("Title", "")))
        token_counts.update(tokenize(article.get("Summary", "")))

    # Drop generic tokens, pure-numeric tokens, tokens containing digits
    # (e.g. "qwen3", "440", "2026"), and very short fragments.
    for token in list(token_counts.keys()):
        if (
            token in THEME_GENERIC_TOKENS
            or any(ch.isdigit() for ch in token)
            or len(token) < 4
        ):
            token_counts.pop(token, None)

    top_tokens = [token for token, _ in token_counts.most_common(3)]

    if not top_tokens:
        return fallback_category

    # Use at most the top 2 tokens for the name.
    name_tokens = top_tokens[:2]

    # If the tokens that would form the name are ALL vendor/proper-noun
    # fragments (e.g. "Google Gemini", "Apex Claude"), the result reads as
    # noise rather than a theme — prefer the representative's category.
    if all(token in THEME_VENDOR_TOKENS for token in name_tokens):
        return fallback_category

    return " ".join(_pretty_token(token) for token in name_tokens)


# Acronyms that should keep canonical casing in theme names.
_THEME_ACRONYMS = {
    "llm": "LLM", "llms": "LLMs", "rag": "RAG", "api": "API",
    "apis": "APIs", "mcp": "MCP", "sdk": "SDK", "gpu": "GPU",
    "ai": "AI", "ml": "ML", "saas": "SaaS",
}


def _pretty_token(token):
    """Title-case a token, preserving known acronym casing."""
    cleaned = token.replace("-", " ")
    parts = []
    for word in cleaned.split():
        parts.append(_THEME_ACRONYMS.get(word.lower(), word.title()))
    return " ".join(parts)


def infer_theme_key(article):

    text = normalize_text(f"{article.get('Title', '')} {article.get('Summary', '')}")
    lowered = text.lower()

    for theme_name, keywords in THEME_PRIORITY_RULES:
        if any(keyword in lowered for keyword in keywords):
            return theme_name

    return ""


def compute_theme_score(cluster_articles, representative, avg_similarity, mode=None):

    profile = get_theme_profile(mode)
    scoring = profile.get("theme_score", {})

    max_score = max(
        (article.get("Importance Score", 0) or 0)
        for article in cluster_articles
    )
    cluster_size = len(cluster_articles)

    cohesion_bonus = round(avg_similarity * scoring.get("cohesion_multiplier", 16))
    size_bonus = min(
        max(cluster_size - 1, 0),
        scoring.get("max_size_bonus", 10)
    ) * scoring.get("size_bonus", 2)

    category = str(representative.get("Category", "") or "")
    priority_bonus = 4 if category in {"Agentic AI", "RAG / Infrastructure", "Enterprise AI"} else 0

    return int(max_score + cohesion_bonus + size_bonus + priority_bonus)


def cluster_themes(df, mode=None, return_clusters=False):

    if df.empty:
        empty = df.copy()
        for col in [
            "Theme ID", "Theme Name", "Theme Cluster Size", "Theme Score",
            "Theme Representative", "Theme Representative Article",
            "Theme Supporting Articles", "Theme Similarity Score"
        ]:
            empty[col] = []
        return (empty, [], {}) if return_clusters else empty

    profile = get_theme_profile(mode)
    threshold = profile.get("similarity_threshold", 0.62)
    weights = profile.get("weights", {})

    records = df.sort_values(
        by="Importance Score",
        ascending=False
    ).to_dict(orient="records")

    clusters = []
    theme_counter = 1

    for record in records:
        inferred_theme_key = infer_theme_key(record)

        if inferred_theme_key:
            matched_cluster = None

            for cluster in clusters:
                if cluster.get("theme_key") == inferred_theme_key:
                    matched_cluster = cluster
                    break

            if matched_cluster is not None:
                matched_cluster["articles"].append(record)
                matched_cluster["similarities"].append(1.0)
                matched_cluster["supporting_titles"].append(record.get("Title", ""))
                continue

            theme_id = f"theme_{theme_counter:03d}"
            theme_counter += 1
            clusters.append({
                "theme_id": theme_id,
                "theme_key": inferred_theme_key,
                "representative": record,
                "articles": [record],
                "similarities": [1.0],
                "supporting_titles": [record.get("Title", "")],
            })
            continue

        best_cluster = None
        best_score = 0.0

        for cluster in clusters:
            similarity = get_theme_similarity(
                record,
                cluster["representative"],
                weights
            )
            if similarity > best_score:
                best_score = similarity
                best_cluster = cluster

        if best_cluster and best_score >= threshold:
            best_cluster["articles"].append(record)
            best_cluster["similarities"].append(best_score)
            best_cluster["supporting_titles"].append(record.get("Title", ""))
        else:
            theme_id = f"theme_{theme_counter:03d}"
            theme_counter += 1
            clusters.append({
                "theme_id": theme_id,
                "theme_key": "",
                "representative": record,
                "articles": [record],
                "similarities": [1.0],
                "supporting_titles": [record.get("Title", "")],
            })

    summary_records = []
    annotated_rows = []

    for cluster in clusters:
        articles = cluster["articles"]
        representative = cluster["representative"]
        avg_similarity = sum(cluster["similarities"]) / len(cluster["similarities"])
        theme_name = build_theme_name(
            articles,
            fallback_category=str(representative.get("Category", "AI Update") or "AI Update")
        )
        if cluster.get("theme_key"):
            theme_name = cluster["theme_key"]
        theme_score = compute_theme_score(
            articles,
            representative,
            avg_similarity,
            mode=mode
        )
        cluster_size = len(articles)
        supporting_titles = [
            article.get("Title", "")
            for article in articles
            if article.get("Title", "") != representative.get("Title", "")
        ]

        representative_copy = dict(representative)
        representative_copy.update({
            "Theme ID": cluster["theme_id"],
            "Theme Key": cluster.get("theme_key", ""),
            "Theme Name": theme_name,
            "Theme Cluster Size": cluster_size,
            "Theme Score": theme_score,
            "Theme Representative": True,
            "Theme Representative Article": representative.get("Title", ""),
            "Theme Supporting Articles": json.dumps(supporting_titles, ensure_ascii=False),
            "Theme Similarity Score": round(avg_similarity, 4),
        })

        summary_records.append({
            "theme_id": cluster["theme_id"],
            "theme_key": cluster.get("theme_key", ""),
            "theme_name": theme_name,
            "cluster_size": cluster_size,
            "representative_article": representative.get("Title", ""),
            "theme_score": theme_score,
            "supporting_articles": supporting_titles,
            "average_similarity": round(avg_similarity, 4),
        })

        for article in articles:
            row = dict(article)
            row.update({
                "Theme ID": cluster["theme_id"],
                "Theme Key": cluster.get("theme_key", ""),
                "Theme Name": theme_name,
                "Theme Cluster Size": cluster_size,
                "Theme Score": theme_score,
                "Theme Representative": article.get("Title", "") == representative.get("Title", ""),
                "Theme Representative Article": representative.get("Title", ""),
                "Theme Supporting Articles": json.dumps(supporting_titles, ensure_ascii=False) if article.get("Title", "") == representative.get("Title", "") else "",
                "Theme Similarity Score": round(avg_similarity, 4),
            })
            annotated_rows.append(row)

    annotated_df = pd.DataFrame(annotated_rows)
    annotated_df = annotated_df.sort_values(
        by=["Theme Score", "Importance Score"],
        ascending=False
    ).reset_index(drop=True)

    stats = {
        "theme_count": len(clusters),
        "cluster_sizes": [len(cluster["articles"]) for cluster in clusters],
        "singleton_count": sum(1 for cluster in clusters if len(cluster["articles"]) == 1),
        "multi_article_count": sum(1 for cluster in clusters if len(cluster["articles"]) > 1),
        "average_cluster_size": round(len(records) / len(clusters), 2) if clusters else 0,
        "threshold": threshold,
        "mode": str(mode or QUALITY_MODE),
    }

    if return_clusters:
        return annotated_df, summary_records, stats

    return annotated_df


def select_theme_representatives(df, top_n=None, mode=None):

    if df.empty:
        return df

    if top_n is None:
        top_n = get_theme_profile(mode).get("max_output_themes", 12)

    if "Theme Representative" not in df.columns or "Theme ID" not in df.columns:
        sorted_df = df.sort_values(
            by="Importance Score",
            ascending=False
        )
        return sorted_df.head(top_n)

    reps = df[df["Theme Representative"] == True].copy()

    if reps.empty:
        sorted_df = df.sort_values(
            by=["Theme Score", "Importance Score"],
            ascending=False
        )
        return sorted_df.head(top_n)

    sort_cols = ["Theme Score", "Importance Score"]
    reps = reps.sort_values(
        by=sort_cols,
        ascending=False
    )

    if len(reps) >= top_n:
        return reps.head(top_n)

    chosen_ids = set(reps["Theme ID"].tolist())
    overflow = df[~df["Theme ID"].isin(chosen_ids)].copy()
    overflow = overflow.sort_values(
        by=["Theme Score", "Importance Score"],
        ascending=False
    )

    combined = pd.concat([reps, overflow], ignore_index=True)
    combined = combined.drop_duplicates(subset=["Theme ID"], keep="first")
    combined = combined.sort_values(
        by=["Theme Score", "Importance Score"],
        ascending=False
    )

    return combined.head(top_n)
