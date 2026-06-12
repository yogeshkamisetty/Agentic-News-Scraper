from collections import defaultdict

from utils.quality_mode import (
    get_category_caps,
)


def get_top_updates(
    articles,
    top_n=5,
    mode=None,
    diverse=True
):

    sorted_articles = sorted(
        articles,
        key=lambda x: x.get(
            "Importance Score",
            0
        ),
        reverse=True
    )

    if not mode or not diverse:
        return sorted_articles[:top_n]

    caps = get_category_caps(mode)
    counts = defaultdict(int)
    selected = []
    overflow = []

    for article in sorted_articles:

        category = article.get("Category", "AI Update") or "AI Update"
        cap = caps.get(category, top_n)

        if counts[category] < cap and len(selected) < top_n:
            selected.append(article)
            counts[category] += 1
        else:
            overflow.append(article)

    for article in overflow:

        if len(selected) >= top_n:
            break

        selected.append(article)

    return selected