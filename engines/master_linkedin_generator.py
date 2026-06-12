import os
import sys
from datetime import datetime

import pandas as pd

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.quality_mode import (
    get_content_top_n,
    get_quality_mode,
)
from utils.theme_clustering import select_theme_representatives


OUTPUT_FOLDER = "outputs"
QUALITY_MODE = get_quality_mode()


def find_latest_master_file():

    refined_files = [

        file for file in os.listdir(
            OUTPUT_FOLDER
        )

        if (
            file.startswith(
                "refined_agentic_updates_"
            )
            and file.endswith(
                ".xlsx"
            )
        )
    ]

    if refined_files:

        refined_files.sort()

        return os.path.join(
            OUTPUT_FOLDER,
            refined_files[-1]
        )

    files = [

        file for file in os.listdir(
            OUTPUT_FOLDER
        )

        if (
            file.startswith(
                "master_agentic_updates_"
            )
            and file.endswith(
                ".xlsx"
            )
        )
    ]

    if not files:
        return None

    files.sort()

    return os.path.join(
        OUTPUT_FOLDER,
        files[-1]
    )


def generate_posts(
    df,
    top_n=None
):

    if top_n is None:
        top_n = get_content_top_n(
            QUALITY_MODE,
            "linkedin"
        )

    df = select_theme_representatives(
        df,
        top_n=top_n,
        mode=QUALITY_MODE
    )

    sorted_df = df.sort_values(
        by="Importance Score",
        ascending=False
    )

    top_articles = (
        sorted_df.head(top_n)
    )

    posts = []

    for index, row in enumerate(
        top_articles.itertuples(),
        start=1
    ):

        title = getattr(
            row,
            "Title",
            "Unknown update"
        )

        category = getattr(
            row,
            "Category",
            "AI"
        )

        why_it_matters = getattr(
            row,
            "Why_It_Matters",
            ""
        )

        saas_impact = getattr(
            row,
            "SaaS_Impact",
            ""
        )

        pm_perspective = getattr(
            row,
            "PM_Perspective",
            ""
        )

        score = getattr(
            row,
            "Importance_Score",
            0
        )

        post = f"""
# LinkedIn Post {index}

🚨 {category}

{title}

Why this matters:
{why_it_matters}

SaaS impact:
{saas_impact}

PM perspective:
{pm_perspective}

Signal Score: {score}

Question:
How do you think this changes the future of AI products?

----------------------------------------
"""

        posts.append(post)

    return "\n".join(posts)


def save_posts(content):

    timestamp = (
        datetime.now()
        .strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
    )

    output_path = (
        f"{OUTPUT_FOLDER}/"
        f"master_linkedin_posts_"
        f"{timestamp}.md"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(content)

    return output_path


def main():

    print(
        "\n=== MASTER "
        "LINKEDIN GENERATOR ===\n"
    )

    print(f"Quality mode: {QUALITY_MODE}\n")

    master_file = (
        find_latest_master_file()
    )

    if not master_file:

        print(
            "No master file found."
        )

        return

    print(
        f"Using master file:\n"
        f"{master_file}"
    )

    df = pd.read_excel(
        master_file
    )

    df = select_theme_representatives(
        df,
        top_n=get_content_top_n(
            QUALITY_MODE,
            "linkedin"
        ),
        mode=QUALITY_MODE
    )

    print(
        f"\nLoaded "
        f"{len(df)} "
        f"unique updates"
    )

    content = (
        generate_posts(df)
    )

    output_file = (
        save_posts(content)
    )

    print(
        "\nLinkedIn posts generated:"
    )

    print(
        output_file
    )

    print(
        "\n=== COMPLETE ==="
    )


if __name__ == "__main__":
    main()