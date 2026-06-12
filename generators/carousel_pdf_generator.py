"""
Theme-level LinkedIn Carousel PDF Generator
-------------------------------------------
Creates one professional 6-slide PDF per theme from the refined intelligence layer.

Input:
    outputs/refined_agentic_updates.xlsx
    or latest outputs/refined_agentic_updates_*.xlsx

Output:
    outputs/carousels/carousel_<theme_slug>.pdf

Design goals:
    - premium dark-mode editorial aesthetic
    - narrative-driven slide flow
    - theme-level clustering, not article-level repetition
    - text overflow protection and slide diagnostics
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime

import pandas as pd
from reportlab.lib.colors import Color, HexColor
from reportlab.pdfgen import canvas

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.pdf_theme import (
    BACKGROUND,
    BORDER,
    DEFAULT_THEME,
    MARGIN_BOTTOM,
    MARGIN_TOP,
    MARGIN_X,
    PAGE_HEIGHT,
    PAGE_WIDTH,
    CATEGORY_ACCENTS,
    chip_border,
    chip_fill,
    category_accent,
    slugify,
    subtle_fill,
)
from utils.quality_mode import get_quality_mode
from utils.text_layout import (
    clean_text,
    draw_bullets,
    draw_chip,
    draw_paragraph_box,
    fit_text,
)
from utils.theme_clustering import (
    cluster_themes,
    select_theme_representatives,
)


OUTPUT_FOLDER = os.path.join("outputs", "carousels")
QUALITY_MODE = get_quality_mode()


def ensure_output_folder():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def find_refined_file():
    base_path = os.path.join("outputs", "refined_agentic_updates.xlsx")
    if os.path.exists(base_path):
        return base_path

    candidates = sorted(
        [
            os.path.join("outputs", file_name)
            for file_name in os.listdir("outputs")
            if file_name.startswith("refined_agentic_updates_") and file_name.endswith(".xlsx")
        ]
    )

    if candidates:
        return candidates[-1]

    candidates = sorted(
        [
            os.path.join("outputs", file_name)
            for file_name in os.listdir("outputs")
            if file_name.startswith("master_agentic_updates_") and file_name.endswith(".xlsx")
        ]
    )

    if candidates:
        return candidates[-1]

    return None


def load_theme_groups(mode=None):
    source_file = find_refined_file()
    if not source_file:
        raise FileNotFoundError("No refined or master dataset found in outputs/")

    df = pd.read_excel(source_file)
    if df.empty:
        raise ValueError(f"Dataset is empty: {source_file}")

    if "Theme ID" not in df.columns or "Theme Representative" not in df.columns:
        clustered_df, _, stats = cluster_themes(df, mode=mode, return_clusters=True)
        print(f"[carousel] Fallback clustering applied: {stats}")
        df = clustered_df

    theme_reps = select_theme_representatives(
        df,
        top_n=None,
        mode=mode
    )

    if theme_reps.empty:
        theme_reps = df[df.get("Theme Representative", False) == True].copy() if "Theme Representative" in df.columns else df.copy()

    if theme_reps.empty:
        raise ValueError("No theme representatives found after clustering.")

    groups = []
    theme_ids = theme_reps["Theme ID"].dropna().tolist() if "Theme ID" in theme_reps.columns else []
    if not theme_ids and "Theme ID" in df.columns:
        theme_ids = df["Theme ID"].dropna().unique().tolist()

    for theme_id in theme_ids:
        theme_df = df[df["Theme ID"] == theme_id].copy()
        if theme_df.empty:
            continue

        rep_rows = theme_df[theme_df.get("Theme Representative", False) == True].copy() if "Theme Representative" in theme_df.columns else pd.DataFrame()
        if rep_rows.empty:
            rep_row = theme_df.sort_values(by=["Theme Score", "Importance Score"], ascending=False).iloc[0]
        else:
            rep_row = rep_rows.sort_values(by=["Theme Score", "Importance Score"], ascending=False).iloc[0]

        supporting = theme_df.sort_values(by="Importance Score", ascending=False).to_dict(orient="records")
        groups.append({
            "theme_id": theme_id,
            "theme_name": clean_text(rep_row.get("Theme Name", "")) or clean_text(rep_row.get("Category", "AI Update")) or "AI Update",
            "theme_score": int(rep_row.get("Theme Score", rep_row.get("Importance Score", 0)) or 0),
            "cluster_size": len(theme_df),
            "representative": rep_row.to_dict() if hasattr(rep_row, "to_dict") else dict(rep_row),
            "supporting_articles": supporting,
            "source_file": source_file,
        })

    groups = sorted(
        groups,
        key=lambda item: (
            item["theme_score"],
            item["cluster_size"]
        ),
        reverse=True
    )

    return groups, source_file


def theme_hook(theme_name, representative):
    text = f"{theme_name} is no longer a single headline; it is starting to behave like a market pattern."
    name = theme_name.lower()

    if any(token in name for token in ["pricing", "cost", "economics"]):
        text = "Cost pressure is changing buyer expectations and forcing sharper product economics."
    elif any(token in name for token in ["memory", "state", "context"]):
        text = "Memory and long-horizon state are emerging as the real bottleneck in production agents."
    elif any(token in name for token in ["permission", "control", "access"]):
        text = "The hard problem is shifting from model quality to controlled action and tool access."
    elif any(token in name for token in ["rag", "retrieval", "knowledge"]):
        text = "Retrieval quality and grounding infrastructure are now shaping product reliability."
    elif any(token in name for token in ["developer", "coding", "workflow", "terminal"]):
        text = "Developer workflows are shifting toward agent-assisted execution, review, and verification."
    elif any(token in name for token in ["enterprise", "governance", "compliance"]):
        text = "Enterprise buyers are now asking for governance, reliability, and measurable ROI before scale-up."

    headline = clean_text(representative.get("Title", ""))
    return text, headline


def build_theme_story(theme):
    rep = theme["representative"]
    supporting = theme["supporting_articles"]
    theme_name = theme["theme_name"]
    category = clean_text(rep.get("Category", "AI Update")) or "AI Update"

    hook, rep_headline = theme_hook(theme_name, rep)
    summary = clean_text(rep.get("Summary", ""))
    why = clean_text(rep.get("Why It Matters", ""))
    saas = clean_text(rep.get("SaaS Impact", ""))
    pm = clean_text(rep.get("PM Perspective", ""))

    supporting_titles = [
        clean_text(item.get("Title", ""))
        for item in supporting
        if clean_text(item.get("Title", "")) and clean_text(item.get("Title", "")) != rep_headline
    ]

    source_set = sorted({clean_text(item.get("Source", "")) for item in supporting if clean_text(item.get("Source", ""))})

    slide_1_meta = [
        f"{category}",
        f"{theme['cluster_size']} articles",
        f"Theme score {theme['theme_score']}",
        f"{len(source_set)} sources",
    ]

    slide_2_points = [
        f"Anchor signal: {summary or rep_headline}",
    ]
    slide_2_points.extend([
        f"Supporting signal: {title}"
        for title in supporting_titles[:4]
    ])

    slide_3_points = [
        why or hook,
        f"This is a repeating market signal, not a one-off article in {theme_name}.",
        f"The article that best anchors the story is: {rep_headline}.",
    ]

    slide_4_points = [
        saas or "SaaS teams should read this theme through workflow design, pricing, and operating-model choices.",
        "Expect consequences for monetization, cost structure, and feature packaging.",
        "The right response is to translate the signal into product and business decisions.",
    ]

    slide_5_points = [
        pm or "PMs should watch roadmap tradeoffs, user trust, and where the product needs stronger controls.",
        "The opportunity is to turn experimentation into a repeatable product capability.",
        "The risk is shipping a surface-level feature without the reliability behind it.",
    ]

    slide_6_takeaway = clean_text(
        f"{theme_name} should be treated as a strategic narrative, not a stream of individual updates. Collapse the cluster into one market thesis and use the supporting signals as evidence."
    )

    cta = "If this theme is shaping your roadmap, what would you change first — product, pricing, or operating model?"

    return {
        "theme_name": theme_name,
        "category": category,
        "representative_headline": rep_headline,
        "hook": hook,
        "meta": slide_1_meta,
        "summary": summary,
        "supporting_titles": supporting_titles,
        "why_points": slide_3_points,
        "saas_points": slide_4_points,
        "pm_points": slide_5_points,
        "takeaway": slide_6_takeaway,
        "cta": cta,
        "supporting_articles": supporting,
        "representative": rep,
        "supporting_sources": source_set,
    }


def draw_background(c, accent):
    c.setFillColor(BACKGROUND)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    c.setFillColor(Color(accent.red, accent.green, accent.blue, alpha=0.12))
    c.circle(PAGE_WIDTH - 120, PAGE_HEIGHT - 120, 170, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1, alpha=0.04))
    c.circle(120, PAGE_HEIGHT - 140, 100, fill=1, stroke=0)
    c.setFillColor(BORDER)
    c.rect(0, 0, 12, PAGE_HEIGHT, fill=1, stroke=0)


def draw_footer(c, page_num, accent, theme_name):
    c.setStrokeColor(BORDER)
    c.setLineWidth(1)
    c.line(MARGIN_X, 74, PAGE_WIDTH - MARGIN_X, 74)
    c.setFillColor(DEFAULT_THEME.muted)
    c.setFont("Helvetica", 8)
    c.drawString(MARGIN_X, 48, "AI Intelligence Engine • Theme-level carousel")
    c.drawRightString(PAGE_WIDTH - MARGIN_X, 48, f"{page_num}/6")
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN_X, 28, clean_text(theme_name)[:45])


def draw_slide_title(c, title, subtitle, accent):
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN_X, PAGE_HEIGHT - MARGIN_TOP, title.upper())

    if subtitle:
        c.setFillColor(DEFAULT_THEME.muted)
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN_X, PAGE_HEIGHT - MARGIN_TOP - 20, subtitle)

    c.setStrokeColor(Color(accent.red, accent.green, accent.blue, alpha=0.35))
    c.setLineWidth(1)
    c.line(MARGIN_X, PAGE_HEIGHT - MARGIN_TOP - 34, PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - MARGIN_TOP - 34)


def draw_card(c, x, y_top, width, height, fill, border, radius=22):
    c.setFillColor(fill)
    c.setStrokeColor(border)
    c.setLineWidth(1.2)
    c.roundRect(x, y_top - height, width, height, radius, fill=1, stroke=1)


def draw_cover(c, story, accent):
    draw_background(c, accent)

    theme_name = story["theme_name"]
    representative = story["representative_headline"]
    hook = story["hook"]
    meta = story["meta"]

    draw_slide_title(c, "THEME CAROUSEL", "Executive briefing for LinkedIn document format", accent)

    # Feature card
    card_x = MARGIN_X
    card_y = PAGE_HEIGHT - 220
    card_w = PAGE_WIDTH - MARGIN_X * 2
    card_h = 360
    draw_card(c, card_x, card_y, card_w, card_h, DEFAULT_THEME.surface, BORDER)

    # Chips
    chip_y = PAGE_HEIGHT - 250
    x = card_x + 30
    x = draw_chip(c, meta[0], x, chip_y, chip_fill(story["category"]), chip_border(story["category"]), accent, font_size=10)
    x = draw_chip(c, meta[1], x, chip_y, subtle_fill(accent, 0.12), Color(accent.red, accent.green, accent.blue, alpha=0.35), accent, font_size=10)
    x = draw_chip(c, meta[2], x, chip_y, subtle_fill(accent, 0.08), Color(accent.red, accent.green, accent.blue, alpha=0.25), accent, font_size=10)

    # Theme name
    theme_style = type("S", (), {"fontName": "Helvetica-Bold", "fontSize": 52, "leading": 62, "textColor": DEFAULT_THEME.text})()
    _, _, truncated = draw_paragraph_box(
        c,
        theme_name,
        card_x + 32,
        PAGE_HEIGHT - 316,
        card_w - 64,
        110,
        theme_style,
        min_size=28,
        max_lines=2,
        debug_label="cover theme",
        warn_prefix="cover"
    )

    # Headline
    headline_style = type("S", (), {"fontName": "Helvetica", "fontSize": 20, "leading": 28, "textColor": DEFAULT_THEME.text})()
    draw_paragraph_box(
        c,
        representative,
        card_x + 32,
        PAGE_HEIGHT - 412,
        card_w - 64,
        72,
        headline_style,
        min_size=16,
        max_lines=3,
        debug_label="cover headline",
        warn_prefix="cover"
    )

    # Hook callout
    callout_y = PAGE_HEIGHT - 496
    c.setFillColor(Color(accent.red, accent.green, accent.blue, alpha=0.14))
    c.setStrokeColor(Color(accent.red, accent.green, accent.blue, alpha=0.45))
    c.roundRect(card_x + 32, callout_y - 84, card_w - 64, 84, 18, fill=1, stroke=1)
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(card_x + 50, callout_y - 28, "Strategic hook")
    hook_style = type("S", (), {"fontName": "Helvetica", "fontSize": 16, "leading": 24, "textColor": DEFAULT_THEME.text})()
    draw_paragraph_box(
        c,
        hook,
        card_x + 50,
        callout_y - 42,
        card_w - 100,
        44,
        hook_style,
        min_size=13,
        max_lines=2,
        debug_label="cover hook",
        warn_prefix="cover"
    )

    draw_footer(c, 1, accent, theme_name)


def draw_slide_two(c, story, accent):
    draw_background(c, accent)
    draw_slide_title(c, "WHAT HAPPENED", "Representative article + supporting signal references", accent)

    card_x = MARGIN_X
    card_y = PAGE_HEIGHT - 190
    card_w = PAGE_WIDTH - MARGIN_X * 2
    card_h = 920
    draw_card(c, card_x, card_y, card_w, card_h, DEFAULT_THEME.surface, BORDER)

    rep = story["representative"]

    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(card_x + 30, card_y - 40, "Representative article")

    rep_title_style = type("S", (), {"fontName": "Helvetica-Bold", "fontSize": 24, "leading": 32, "textColor": DEFAULT_THEME.text})()
    draw_paragraph_box(
        c,
        story["representative_headline"],
        card_x + 30,
        card_y - 72,
        card_w - 60,
        86,
        rep_title_style,
        min_size=17,
        max_lines=3,
        debug_label="slide2 headline",
        warn_prefix="slide 2"
    )

    body_style = type("S", (), {"fontName": "Helvetica", "fontSize": 16, "leading": 24, "textColor": DEFAULT_THEME.text})()
    draw_paragraph_box(
        c,
        story["summary"] or rep.get("Summary", ""),
        card_x + 30,
        card_y - 174,
        card_w - 60,
        150,
        body_style,
        min_size=13,
        max_lines=6,
        debug_label="slide2 summary",
        warn_prefix="slide 2"
    )

    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(card_x + 30, card_y - 354, "Supporting signal references")

    bullets = [
        f"{article.get('Title', '')} • {article.get('Source', '')}"
        for article in story["supporting_articles"][1:5]
    ]
    if not bullets:
        bullets = ["No additional supporting articles available for this theme."]

    bullet_style = type("S", (), {"fontName": "Helvetica", "fontSize": 14, "leading": 20, "textColor": DEFAULT_THEME.text})()
    draw_bullets(
        c,
        bullets,
        card_x + 36,
        card_y - 388,
        card_w - 72,
        110,
        22,
        bullet_style,
        max_lines_per_item=2,
        debug_prefix="slide 2 supporting"
    )

    draw_footer(c, 2, accent, story["theme_name"])


def draw_slide_three(c, story, accent):
    draw_background(c, accent)
    draw_slide_title(c, "WHY IT MATTERS", "Strategic implications and market meaning", accent)

    card_x = MARGIN_X
    card_y = PAGE_HEIGHT - 190
    card_w = PAGE_WIDTH - MARGIN_X * 2
    card_h = 920
    draw_card(c, card_x, card_y, card_w, card_h, DEFAULT_THEME.surface, BORDER)

    body_style = type("S", (), {"fontName": "Helvetica", "fontSize": 18, "leading": 28, "textColor": DEFAULT_THEME.text})()
    draw_paragraph_box(
        c,
        story["why_points"][0],
        card_x + 30,
        card_y - 42,
        card_w - 60,
        170,
        body_style,
        min_size=14,
        max_lines=6,
        debug_label="slide3 why lead",
        warn_prefix="slide 3"
    )

    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(card_x + 30, card_y - 236, "Market interpretation")

    bullets = story["why_points"][1:]
    bullet_style = type("S", (), {"fontName": "Helvetica", "fontSize": 15, "leading": 22, "textColor": DEFAULT_THEME.text})()
    draw_bullets(
        c,
        bullets,
        card_x + 36,
        card_y - 270,
        card_w - 72,
        220,
        22,
        bullet_style,
        max_lines_per_item=2,
        debug_prefix="slide 3 why"
    )

    draw_footer(c, 3, accent, story["theme_name"])


def draw_slide_four(c, story, accent):
    draw_background(c, accent)
    draw_slide_title(c, "SAAS IMPACT", "Product, workflow, monetization, and operations", accent)

    card_x = MARGIN_X
    card_y = PAGE_HEIGHT - 190
    card_w = PAGE_WIDTH - MARGIN_X * 2
    card_h = 920
    draw_card(c, card_x, card_y, card_w, card_h, DEFAULT_THEME.surface, BORDER)

    body_style = type("S", (), {"fontName": "Helvetica", "fontSize": 17, "leading": 26, "textColor": DEFAULT_THEME.text})()
    draw_paragraph_box(
        c,
        story["saas_points"][0],
        card_x + 30,
        card_y - 42,
        card_w - 60,
        150,
        body_style,
        min_size=14,
        max_lines=5,
        debug_label="slide4 saas lead",
        warn_prefix="slide 4"
    )

    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(card_x + 30, card_y - 220, "Business impact")

    bullets = story["saas_points"][1:]
    bullet_style = type("S", (), {"fontName": "Helvetica", "fontSize": 15, "leading": 22, "textColor": DEFAULT_THEME.text})()
    draw_bullets(
        c,
        bullets,
        card_x + 36,
        card_y - 254,
        card_w - 72,
        260,
        22,
        bullet_style,
        max_lines_per_item=2,
        debug_prefix="slide 4 saas"
    )

    draw_footer(c, 4, accent, story["theme_name"])


def draw_slide_five(c, story, accent):
    draw_background(c, accent)
    draw_slide_title(c, "PM PERSPECTIVE", "Roadmap opportunities, UX tradeoffs, and risks", accent)

    card_x = MARGIN_X
    card_y = PAGE_HEIGHT - 190
    card_w = PAGE_WIDTH - MARGIN_X * 2
    card_h = 920
    draw_card(c, card_x, card_y, card_w, card_h, DEFAULT_THEME.surface, BORDER)

    body_style = type("S", (), {"fontName": "Helvetica", "fontSize": 17, "leading": 26, "textColor": DEFAULT_THEME.text})()
    draw_paragraph_box(
        c,
        story["pm_points"][0],
        card_x + 30,
        card_y - 42,
        card_w - 60,
        150,
        body_style,
        min_size=14,
        max_lines=5,
        debug_label="slide5 pm lead",
        warn_prefix="slide 5"
    )

    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(card_x + 30, card_y - 220, "Product decisions")

    bullets = story["pm_points"][1:]
    bullet_style = type("S", (), {"fontName": "Helvetica", "fontSize": 15, "leading": 22, "textColor": DEFAULT_THEME.text})()
    draw_bullets(
        c,
        bullets,
        card_x + 36,
        card_y - 254,
        card_w - 72,
        260,
        22,
        bullet_style,
        max_lines_per_item=2,
        debug_prefix="slide 5 pm"
    )

    draw_footer(c, 5, accent, story["theme_name"])


def draw_slide_six(c, story, accent):
    draw_background(c, accent)
    draw_slide_title(c, "KEY TAKEAWAY + CTA", "Synthesis and LinkedIn call to action", accent)

    card_x = MARGIN_X
    card_y = PAGE_HEIGHT - 190
    card_w = PAGE_WIDTH - MARGIN_X * 2
    card_h = 920
    draw_card(c, card_x, card_y, card_w, card_h, DEFAULT_THEME.surface, BORDER)

    takeaway_style = type("S", (), {"fontName": "Helvetica-Bold", "fontSize": 24, "leading": 34, "textColor": DEFAULT_THEME.text})()
    draw_paragraph_box(
        c,
        story["takeaway"],
        card_x + 30,
        card_y - 52,
        card_w - 60,
        170,
        takeaway_style,
        min_size=17,
        max_lines=5,
        debug_label="slide6 takeaway",
        warn_prefix="slide 6"
    )

    c.setFillColor(Color(accent.red, accent.green, accent.blue, alpha=0.13))
    c.setStrokeColor(Color(accent.red, accent.green, accent.blue, alpha=0.4))
    c.roundRect(card_x + 30, card_y - 300, card_w - 60, 92, 18, fill=1, stroke=1)
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(card_x + 48, card_y - 252, "Recommended LinkedIn framing")

    cta_style = type("S", (), {"fontName": "Helvetica", "fontSize": 16, "leading": 24, "textColor": DEFAULT_THEME.text})()
    draw_paragraph_box(
        c,
        story["cta"],
        card_x + 48,
        card_y - 268,
        card_w - 96,
        54,
        cta_style,
        min_size=13,
        max_lines=2,
        debug_label="slide6 cta",
        warn_prefix="slide 6"
    )

    c.setFillColor(DEFAULT_THEME.muted)
    c.setFont("Helvetica", 10)
    c.drawString(card_x + 30, card_y - 350, f"Representative article: {story['representative_headline'][:120]}")
    c.drawString(card_x + 30, card_y - 376, f"Supporting articles in theme: {len(story['supporting_articles'])}")

    draw_footer(c, 6, accent, story["theme_name"])


def render_theme_pdf(theme):
    ensure_output_folder()

    story = build_theme_story(theme)
    theme_slug = slugify(story["theme_name"])
    output_path = os.path.join(OUTPUT_FOLDER, f"carousel_{theme_slug}.pdf")
    accent = category_accent(story["category"])

    print(f"Generating carousel: {story['theme_name']}")
    print(f"Slides: 6")
    print(f"Supporting articles: {len(story['supporting_articles']) - 1 if len(story['supporting_articles']) > 0 else 0}")

    c = canvas.Canvas(output_path, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    c.setTitle(f"Carousel - {story['theme_name']}")
    c.setAuthor("Agentic News Engine")
    c.setSubject(f"LinkedIn carousel for {story['theme_name']}")
    c.setCreator("Agentic News Engine")

    draw_cover(c, story, accent)
    c.showPage()
    draw_slide_two(c, story, accent)
    c.showPage()
    draw_slide_three(c, story, accent)
    c.showPage()
    draw_slide_four(c, story, accent)
    c.showPage()
    draw_slide_five(c, story, accent)
    c.showPage()
    draw_slide_six(c, story, accent)
    c.save()

    print(f"Saved: {output_path}\n")
    return output_path


def main():
    print("\n=== LINKEDIN CAROUSEL PDF GENERATOR ===\n")
    print(f"Quality mode: {QUALITY_MODE}\n")

    groups, source_file = load_theme_groups(mode=QUALITY_MODE)
    print(f"Loaded theme groups from: {source_file}")
    print(f"Themes available: {len(groups)}\n")

    outputs = []
    for theme in groups:
        try:
            output = render_theme_pdf(theme)
            outputs.append(output)
        except Exception as exc:
            print(f"[carousel][error] Failed theme {theme.get('theme_name', 'Unknown')}: {exc}")

    summary = {
        "source_file": source_file,
        "quality_mode": QUALITY_MODE,
        "theme_count": len(groups),
        "generated": len(outputs),
        "output_folder": OUTPUT_FOLDER,
        "timestamp": datetime.now().isoformat(),
    }
    print("Carousel generation summary:")
    print(json.dumps(summary, indent=2))
    print("\n=== COMPLETE ===\n")


if __name__ == "__main__":
    main()
