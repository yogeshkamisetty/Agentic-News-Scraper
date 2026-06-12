import json
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


def build_carousel(
    df,
    top_n=None
):

    if top_n is None:
        top_n = get_content_top_n(
            QUALITY_MODE,
            "carousel"
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

    carousels = []

    for row in top_articles.itertuples():

        title = getattr(
            row,
            "Title",
            "Unknown Update"
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

        slides = [

            {
                "slide": 1,
                "title":
                f"🚨 {category}",
                "content":
                title
            },

            {
                "slide": 2,
                "title":
                "What Happened",
                "content":
                title
            },

            {
                "slide": 3,
                "title":
                "Why It Matters",
                "content":
                why_it_matters
            },

            {
                "slide": 4,
                "title":
                "SaaS Impact",
                "content":
                saas_impact
            },

            {
                "slide": 5,
                "title":
                "PM Perspective",
                "content":
                pm_perspective
            },

            {
                "slide": 6,
                "title":
                "Key Takeaway",
                "content":
                "AI products are "
                "moving toward "
                "autonomous workflows."
            }
        ]

        carousels.append({

            "headline":
            title,

            "category":
            category,

            "slides":
            slides
        })

    return carousels


def save_carousel(
    carousel_data
):

    timestamp = (
        datetime.now()
        .strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
    )

    output_path = (
        f"{OUTPUT_FOLDER}/"
        f"carousel_data_"
        f"{timestamp}.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            carousel_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    return output_path


def main():

    print(
        "\n=== CAROUSEL "
        "GENERATOR ===\n"
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
        f"Using:\n"
        f"{master_file}"
    )

    df = pd.read_excel(
        master_file
    )

    df = select_theme_representatives(
        df,
        top_n=get_content_top_n(
            QUALITY_MODE,
            "carousel"
        ),
        mode=QUALITY_MODE
    )

    print(
        f"\nLoaded "
        f"{len(df)} "
        f"updates"
    )

    carousel_data = (
        build_carousel(df)
    )

    output_file = (
        save_carousel(
            carousel_data
        )
    )

    print(
        "\nCarousel file created:"
    )

    print(
        output_file
    )

    print(
        "\n=== COMPLETE ==="
    )


if __name__ == "__main__":
    main()