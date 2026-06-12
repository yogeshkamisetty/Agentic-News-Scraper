from datetime import datetime
import os


def generate_linkedin_posts(
    articles,
    top_n=5
):

    if not articles:
        return None

    os.makedirs(
        "outputs",
        exist_ok=True
    )

    timestamp = (
        datetime.now()
        .strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
    )

    output_path = (
        "outputs/"
        f"linkedin_posts_"
        f"{timestamp}.md"
    )

    sorted_articles = sorted(
        articles,
        key=lambda x:
        x.get(
            "Importance Score",
            0
        ),
        reverse=True
    )

    top_articles = (
        sorted_articles[:top_n]
    )

    posts = []

    for index, article in enumerate(
        top_articles,
        start=1
    ):

        title = article.get(
            "Title",
            "Unknown update"
        )

        why_it_matters = (
            article.get(
                "Why It Matters",
                ""
            )
        )

        saas_impact = (
            article.get(
                "SaaS Impact",
                ""
            )
        )

        pm_perspective = (
            article.get(
                "PM Perspective",
                ""
            )
        )

        category = article.get(
            "Category",
            "AI"
        )

        score = article.get(
            "Importance Score",
            0
        )

        post = f"""
# LinkedIn Post {index}

Alert: {category} Update

{title}

Why this matters:
{why_it_matters}

SaaS impact:
{saas_impact}

PM perspective:
{pm_perspective}

Signal score: {score}

Question:
How do you think this changes the future of AI products?

----------------------------------------
"""

        posts.append(post)

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "\n".join(posts)
        )

    return output_path
