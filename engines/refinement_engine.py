"""
Refinement Engine
Combines existing Excel outputs, normalizes fields, deduplicates stories,
re-ranks signals, and emits a content-ready refined dataset.

Run:
    python engines/refinement_engine.py

Output:
    outputs/refined_agentic_updates.xlsx
    outputs/refined_agentic_updates_<timestamp>.xlsx
"""

from __future__ import annotations

import os
import sys
import json
from datetime import datetime
from typing import List

import pandas as pd


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from collectors.rss_collector import clean_summary as clean_text
from utils.category_classifier import detect_category
from utils.company_detector import detect_company
from utils.deduplicator import remove_duplicates
from utils.insight_generator import generate_insights
from utils.scorer import calculate_score
from utils.source_ranker import apply_source_weight
from utils.quality_mode import (
    get_quality_mode,
    get_refine_min_score,
)
from utils.theme_clustering import cluster_themes


OUTPUT_FOLDER = "outputs"
BASE_OUTPUT = "refined_agentic_updates.xlsx"
QUALITY_MODE = get_quality_mode()


CANONICAL_COLUMNS = [
    "Title",
    "Source",
    "Published Date",
    "URL",
    "Summary",
    "Category",
    "Company Mentioned",
    "Keywords",
    "Importance Score",
    "Why It Matters",
    "SaaS Impact",
    "PM Perspective",
]


def find_excel_files() -> List[str]:

    files = []

    for file_name in os.listdir(OUTPUT_FOLDER):
        if not file_name.endswith(".xlsx"):
            continue

        if file_name.startswith("agentic_updates_") or file_name.startswith("master_agentic_updates_"):
            files.append(os.path.join(OUTPUT_FOLDER, file_name))

    files.sort()
    return files


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:

    rename_map = {
        "Importance_Score": "Importance Score",
        "Why_It_Matters": "Why It Matters",
        "SaaS_Impact": "SaaS Impact",
        "PM_Perspective": "PM Perspective",
        "Company_Mentioned": "Company Mentioned",
    }

    df = df.rename(columns=rename_map)

    for column in CANONICAL_COLUMNS:
        if column not in df.columns:
            df[column] = "" if column != "Importance Score" else 0

    return df[CANONICAL_COLUMNS].copy()


def recompute_refined_score(row: pd.Series, mode=None) -> int:

    title = str(row.get("Title", "") or "")
    summary = str(row.get("Summary", "") or "")
    source = str(row.get("Source", "") or "")
    text = f"{title} {summary}".lower()

    base_score, _ = calculate_score(text)
    category = str(row.get("Category", "") or "").strip()
    score = apply_source_weight(base_score, source, category=category, mode=mode)

    if any(keyword in text for keyword in ["agent", "agentic", "workflow", "orchestration"]):
        score += 5

    if any(keyword in text for keyword in ["memory", "retrieval", "rag", "reasoning", "permissions", "tool use"]):
        score += 5

    if len(summary) > 200:
        score += 2

    return int(score)


def refine_dataframe(df: pd.DataFrame, mode=None) -> pd.DataFrame:

    rows = []

    for _, row in df.iterrows():
        title = str(row.get("Title", "") or "").strip()
        summary = clean_text(str(row.get("Summary", "") or ""))
        source = str(row.get("Source", "") or "").strip()
        url = str(row.get("URL", "") or "").strip()
        text = f"{title} {summary}".strip()

        category = str(row.get("Category", "") or "").strip()
        if not category:
            category = detect_category(text)

        company = str(row.get("Company Mentioned", "") or "").strip()
        if not company:
            company = detect_company(title, summary)

        refined_score = recompute_refined_score(row, mode=mode)

        if refined_score < get_refine_min_score(mode):
            continue

        if not row.get("Why It Matters") or not row.get("SaaS Impact") or not row.get("PM Perspective"):
            why_it_matters, saas_impact, pm_perspective = generate_insights(title, summary, category)
        else:
            why_it_matters = row.get("Why It Matters", "")
            saas_impact = row.get("SaaS Impact", "")
            pm_perspective = row.get("PM Perspective", "")

        keywords = str(row.get("Keywords", "") or "").strip()

        rows.append({
            "Title": title,
            "Source": source,
            "Published Date": row.get("Published Date", ""),
            "URL": url,
            "Summary": summary,
            "Category": category,
            "Company Mentioned": company,
            "Keywords": keywords,
            "Importance Score": refined_score,
            "Why It Matters": why_it_matters,
            "SaaS Impact": saas_impact,
            "PM Perspective": pm_perspective,
        })

    refined_df = pd.DataFrame(rows)

    if refined_df.empty:
        return refined_df

    refined_rows, stats = remove_duplicates(
        refined_df.to_dict(orient="records"),
        return_stats=True,
    )

    refined_df = pd.DataFrame(refined_rows)
    refined_df = refined_df.sort_values(by="Importance Score", ascending=False).reset_index(drop=True)

    clustered_df, theme_summary, theme_stats = cluster_themes(
        refined_df,
        mode=mode,
        return_clusters=True,
    )

    print(f"Refinement dedupe stats: {stats}")
    print(f"Theme cluster stats: {theme_stats}")

    clustered_df.attrs["theme_summary"] = theme_summary
    clustered_df.attrs["theme_stats"] = theme_stats

    return clustered_df


def save_refined_file(df: pd.DataFrame) -> str:

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    base_path = os.path.join(OUTPUT_FOLDER, BASE_OUTPUT)
    df.to_excel(base_path, index=False)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    timestamped_path = os.path.join(OUTPUT_FOLDER, f"refined_agentic_updates_{timestamp}.xlsx")
    df.to_excel(timestamped_path, index=False)

    theme_summary = df.attrs.get("theme_summary", [])
    if theme_summary:
        theme_path = os.path.join(OUTPUT_FOLDER, f"theme_clusters_{timestamp}.json")
        with open(theme_path, "w", encoding="utf-8") as file:
            json.dump(theme_summary, file, indent=2, ensure_ascii=False)
        print(f"Saved theme cluster summary: {theme_path}")

    return timestamped_path


def main():

    print("\n=== REFINEMENT ENGINE ===\n")
    print(f"Quality mode: {QUALITY_MODE}\n")

    excel_files = find_excel_files()

    if not excel_files:
        print("No source Excel files found.")
        return

    frames = []

    for file_path in excel_files:
        try:
            df = pd.read_excel(file_path)
            frames.append(normalize_columns(df))
            print(f"Loaded {os.path.basename(file_path)} ({len(df)} rows)")
        except Exception as exc:
            print(f"Failed to load {file_path}: {exc}")

    if not frames:
        print("No valid data loaded.")
        return

    merged = pd.concat(frames, ignore_index=True)
    print(f"Merged rows: {len(merged)}")

    refined = refine_dataframe(merged, mode=QUALITY_MODE)

    if refined.empty:
        print("No refined rows remained after scoring and dedupe.")
        return

    output_file = save_refined_file(refined)

    print(f"Refined rows: {len(refined)}")
    print(f"Saved refined dataset: {output_file}")
    print("\n=== COMPLETE ===\n")


if __name__ == "__main__":
    main()
