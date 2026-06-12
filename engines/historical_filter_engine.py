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

from utils.deduplicator import remove_duplicates


OUTPUT_FOLDER = "outputs"

SIMILARITY_THRESHOLD = 80


def load_excel_files():

    dataframes = []

    excel_files = [

        file for file in os.listdir(
            OUTPUT_FOLDER
        )

        if (
            file.endswith(".xlsx")
            and file.startswith(
                "agentic_updates_"
            )
        )
    ]

    if not excel_files:

        print(
            "No Excel files found."
        )

        return pd.DataFrame()

    print(
        f"Found "
        f"{len(excel_files)} "
        f"Excel files\n"
    )

    for file in excel_files:

        path = os.path.join(
            OUTPUT_FOLDER,
            file
        )

        try:

            df = pd.read_excel(
                path
            )

            print(
                f"Loaded: {file} "
                f"({len(df)} rows)"
            )

            dataframes.append(df)

        except Exception as e:

            print(
                f"Failed to load "
                f"{file}: {e}"
            )

    if not dataframes:

        return pd.DataFrame()

    return pd.concat(
        dataframes,
        ignore_index=True
    )


def deduplicate_articles(df):

    print(
        f"\nDeduplicating "
        f"{len(df)} rows..."
    )

    unique_rows, stats = remove_duplicates(
        df.to_dict(orient="records"),
        return_stats=True
    )

    print(
        f"After dedupe: "
        f"{len(unique_rows)} unique updates"
    )

    print(
        f"Dedupe stats: {stats}"
    )

    return pd.DataFrame(
        unique_rows
    )


def save_master_file(df):

    timestamp = (
        datetime.now()
        .strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
    )

    output_path = (
        f"{OUTPUT_FOLDER}/"
        f"master_agentic_updates_"
        f"{timestamp}.xlsx"
    )

    df = df.sort_values(
        by="Importance Score",
        ascending=False
    )

    df.to_excel(
        output_path,
        index=False
    )

    return output_path


def main():

    print(
        "\n=== HISTORICAL "
        "FILTER ENGINE ===\n"
    )

    merged_df = (
        load_excel_files()
    )

    if merged_df.empty:

        print(
            "No valid data found."
        )

        return

    print(
        f"\nMerged rows: "
        f"{len(merged_df)}"
    )

    clean_df = (
        deduplicate_articles(
            merged_df
        )
    )

    output_file = (
        save_master_file(
            clean_df
        )
    )

    print(
        "\nMaster file created:"
    )

    print(
        output_file
    )

    print(
        "\n=== COMPLETE ==="
    )


if __name__ == "__main__":
    main()