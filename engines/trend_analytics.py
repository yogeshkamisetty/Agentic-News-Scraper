import os
import sys
from collections import Counter
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


def get_top_categories(df):

    categories = (
        df["Category"]
        .fillna("Unknown")
        .tolist()
    )

    counter = Counter(
        categories
    )

    total = sum(
        counter.values()
    )

    result = []

    for name, count in (
        counter.most_common(5)
    ):

        percentage = round(
            (
                count / total
            ) * 100,
            1
        )

        result.append(
            (
                name,
                count,
                percentage
            )
        )

    return result


def get_top_companies(df):

    companies = []

    for value in (
        df[
            "Company Mentioned"
        ]
        .fillna("")
        .tolist()
    ):

        value = str(
            value
        ).strip()

        if value:

            companies.append(
                value
            )

    counter = Counter(
        companies
    )

    return (
        counter.most_common(10)
    )


def get_top_keywords(df):

    keywords = []

    for row in (
        df["Keywords"]
        .fillna("")
        .tolist()
    ):

        split_keywords = [

            keyword.strip()

            for keyword in
            str(row).split(",")

            if keyword.strip()
        ]

        keywords.extend(
            split_keywords
        )

    counter = Counter(
        keywords
    )

    return (
        counter.most_common(10)
    )


def get_top_updates(df):

    df = select_theme_representatives(
        df,
        top_n=get_content_top_n(
            QUALITY_MODE,
            "trend"
        ),
        mode=QUALITY_MODE
    )

    return (
        df.sort_values(
            by="Importance Score",
            ascending=False
        )
        .head(
            get_content_top_n(
                QUALITY_MODE,
                "trend"
            )
        )
    )


def build_report(df):

    total_signals = len(df)

    avg_score = round(

        df[
            "Importance Score"
        ].mean(),

        2
    )

    categories = (
        get_top_categories(
            df
        )
    )

    companies = (
        get_top_companies(
            df
        )
    )

    keywords = (
        get_top_keywords(
            df
        )
    )

    themes = []
    if "Theme Name" in df.columns and "Theme Score" in df.columns:
        theme_df = df[df["Theme Representative"] == True].copy() if "Theme Representative" in df.columns else df.copy()
        if not theme_df.empty:
            theme_group = (
                theme_df.groupby(["Theme ID", "Theme Name"], dropna=False)
                .agg({
                    "Theme Score": "max",
                    "Title": "first",
                    "Importance Score": "max",
                    "Theme Cluster Size": "max",
                })
                .reset_index()
                .sort_values(by=["Theme Score", "Importance Score"], ascending=False)
            )
            themes = theme_group.head(10).to_dict(orient="records")

    top_updates = (
        get_top_updates(
            df
        )
    )

    report = []

    report.append(
        "# AGENTIC TREND REPORT\n"
    )

    report.append(
        "## Summary\n"
    )

    report.append(
        f"- Total Signals: "
        f"{total_signals}"
    )

    report.append(
        f"- Average "
        f"Importance Score: "
        f"{avg_score}\n"
    )

    report.append(
        "## Top Categories\n"
    )

    for (
        index,
        (
            category,
            count,
            percentage
        )
    ) in enumerate(
        categories,
        start=1
    ):

        report.append(

            f"{index}. "
            f"{category} — "
            f"{count} "
            f"({percentage}%)"
        )

    report.append(
        "\n## Top Companies\n"
    )

    for index, (
        company,
        count
    ) in enumerate(
        companies,
        start=1
    ):

        report.append(

            f"{index}. "
            f"{company} "
            f"({count})"
        )

    report.append(
        "\n## Top Keywords\n"
    )

    for index, (
        keyword,
        count
    ) in enumerate(
        keywords,
        start=1
    ):

        report.append(

            f"{index}. "
            f"{keyword} "
            f"({count})"
        )

    if themes:
        report.append(
            "\n## Top Themes\n"
        )

        for index, theme in enumerate(themes, start=1):
            report.append(
                f"{index}. {theme['Theme Name']} — {theme['Theme Cluster Size']} articles "
                f"(Theme Score: {theme['Theme Score']}, Representative: {theme['Title']})"
            )

    report.append(
        "\n## Highest Signal Updates\n"
    )

    for index, (
        _,
        row
    ) in enumerate(

        top_updates.iterrows(),

        start=1
    ):

        title = row.get(
            "Title",
            "Unknown"
        )

        score = row.get(
            "Importance Score",
            0
        )

        category = row.get(
            "Category",
            "AI"
        )

        report.append(

            f"{index}. "
            f"{title} "
            f"[{category}] "
            f"(Score: {score})"
        )

    return "\n".join(
        report
    )


def save_report(
    content
):

    timestamp = (
        datetime.now()
        .strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
    )

    output_path = (

        f"{OUTPUT_FOLDER}/"
        f"trend_report_"
        f"{timestamp}.md"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            content
        )

    return output_path


def main():

    print(
        "\n=== TREND "
        "ANALYTICS ===\n"
    )

    print(f"Quality mode: {QUALITY_MODE}\n")

    master_file = (
        find_latest_master_file()
    )

    if not master_file:

        print(
            "No master "
            "dataset found."
        )

        return

    print(
        "Using master file:"
    )

    print(
        master_file
    )

    df = pd.read_excel(
        master_file
    )

    print(
        f"\nLoaded "
        f"{len(df)} "
        f"signals"
    )

    report = (
        build_report(
            df
        )
    )

    output_file = (
        save_report(
            report
        )
    )

    print(
        "\nTrend report "
        "generated:"
    )

    print(
        output_file
    )

    print(
        "\n=== COMPLETE ==="
    )


if __name__ == "__main__":
    main()