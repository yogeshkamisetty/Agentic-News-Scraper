"""
carousel_pdf_generator.py
─────────────────────────
Generates visual LinkedIn carousel PDFs from the master Excel dataset.

Output:
  • One 6-slide PDF per top article  → outputs/carousel/
  • One combined review PDF          → outputs/carousel_combined_<date>.pdf

LinkedIn carousels = multi-page PDFs uploaded as Document posts.
Each page becomes a swipeable card on LinkedIn.

Page size: 600×600 pt (square) — optimal for LinkedIn mobile.

Zero API calls. No external dependencies beyond reportlab + pandas.
"""

import os
import re
from datetime import datetime

import pandas as pd
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas


# ── Page dimensions ──────────────────────────────────────────────────────────

W   = 600    # width  (points)
H   = 600    # height (points)
PAD = 44     # left / right padding


# ── Colour palette ───────────────────────────────────────────────────────────

BG          = HexColor("#02040f")
CARD_BG     = HexColor("#0c102a")
BORDER      = HexColor("#1e2347")
CYAN        = HexColor("#00e5ff")
PURPLE      = HexColor("#7c3aed")
TEAL        = HexColor("#00b4d8")
GREEN       = HexColor("#10b981")
TEXT_GRAY   = HexColor("#9ba4b5")
TEXT_LIGHT  = HexColor("#e2e8f0")
DIVIDER     = HexColor("#3730a3")
AMBER       = HexColor("#f59e0b")
RED         = HexColor("#ef4444")

# Semi-transparent glow colours (alpha 0–1)
GLOW_CYAN   = Color(0.000, 0.898, 1.000, alpha=0.07)
GLOW_PURPLE = Color(0.486, 0.227, 0.929, alpha=0.05)
GLOW_TEAL   = Color(0.000, 0.706, 0.847, alpha=0.06)


# ── Category accent mapping ──────────────────────────────────────────────────

_CAT_ACCENT = {
    "Agentic AI":          (PURPLE, Color(0.486, 0.227, 0.929, alpha=0.25)),
    "RAG / Infrastructure":(TEAL,   Color(0.000, 0.706, 0.847, alpha=0.20)),
    "Developer AI":        (GREEN,  Color(0.063, 0.725, 0.506, alpha=0.20)),
    "Enterprise AI":       (CYAN,   Color(0.000, 0.898, 1.000, alpha=0.18)),
    "AI Update":           (TEXT_GRAY, Color(0.608, 0.643, 0.710, alpha=0.15)),
}


# ── File paths ───────────────────────────────────────────────────────────────

OUTPUT_FOLDER   = "outputs"
CAROUSEL_FOLDER = os.path.join(OUTPUT_FOLDER, "carousel")
LOGO_PATH       = os.path.join(OUTPUT_FOLDER, "image.png")


# ─────────────────────────────────────────────────────────────────────────────
# LOW-LEVEL DRAWING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _bg(c):
    """Fill entire page with dark navy."""
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def _glow(c, cx, cy, radius, color):
    """Soft radial glow — 3 concentric circles, alpha fading outward."""
    c.saveState()
    for frac, a_mult in [(1.0, 1.0), (0.65, 0.5), (0.35, 0.25)]:
        r = radius * frac
        try:
            base_a = color.alpha if hasattr(color, "alpha") else 0.05
            fill = Color(color.red, color.green, color.blue,
                         alpha=base_a * a_mult)
            c.setFillColor(fill)
            c.circle(cx, cy, r, fill=1, stroke=0)
        except Exception:
            pass
    c.restoreState()


def _left_strip(c, color=PURPLE, width=4):
    """Solid vertical accent strip on left edge."""
    c.setFillColor(color)
    c.rect(0, 0, width, H, fill=1, stroke=0)


def _hline(c, y, x0=PAD, x1=None, color=DIVIDER, width=1.0):
    """Horizontal rule."""
    if x1 is None:
        x1 = W - PAD
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x0, y, x1, y)
    c.restoreState()


def _text(c, text, x, y, font="Helvetica", size=11, color=TEXT_LIGHT):
    """Single-line text draw."""
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, text)


def _text_block(c, text, x, y, font="Helvetica", size=11,
                color=TEXT_LIGHT, max_w=None, line_h=None):
    """
    Draw wrapped text. Returns y-coordinate after last line.
    """
    if max_w is None:
        max_w = W - PAD * 2
    if line_h is None:
        line_h = size * 1.55

    if not text:
        return y

    c.setFillColor(color)
    c.setFont(font, size)

    lines = simpleSplit(str(text), font, size, max_w)

    for line in lines:
        c.drawString(x, y, line)
        y -= line_h

    return y


def _logo(c, x, y, h=22):
    """Draw company logo if the image file exists."""
    if not os.path.exists(LOGO_PATH):
        return
    try:
        c.drawImage(
            LOGO_PATH,
            x, y,
            height=h,
            width=h * 3,        # approximate 3:1 aspect; clipped if wrong
            preserveAspectRatio=True,
            mask="auto",
        )
    except Exception:
        pass


def _footer(c, slide_num, total, source=""):
    """Page-number chip + thin rule + logo on every slide."""
    rule_y = 48
    _hline(c, rule_y, color=DIVIDER, width=0.5)

    # Logo (left)
    _logo(c, PAD, 18)

    # Source (center, small)
    if source:
        src = str(source)[:35]
        c.setFillColor(TEXT_GRAY)
        c.setFont("Helvetica", 7)
        cw = c.stringWidth(src, "Helvetica", 7)
        c.drawString((W - cw) / 2, 24, src)

    # Slide counter (right)
    label = f"{slide_num} / {total}"
    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(W - PAD, 24, label)


def _category_pill(c, category, x, y):
    """Rounded pill badge with category label. Returns pill width."""
    accent, bg_a = _CAT_ACCENT.get(
        category,
        (TEXT_GRAY, Color(0.6, 0.6, 0.6, alpha=0.2))
    )

    label = str(category).upper()
    c.setFont("Helvetica-Bold", 7)
    tw = c.stringWidth(label, "Helvetica-Bold", 7)
    pw, ph = tw + 18, 17

    # Background
    c.setFillColor(bg_a)
    c.roundRect(x, y - ph + 4, pw, ph, 5, fill=1, stroke=0)

    # Border
    c.setStrokeColor(accent)
    c.setLineWidth(0.75)
    c.roundRect(x, y - ph + 4, pw, ph, 5, fill=0, stroke=1)

    # Label
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x + 9, y - 7, label)

    return pw


def _score_chip(c, score, x, y):
    """Small score badge (top-right area)."""
    label = f"SCORE  {int(score)}"
    c.setFont("Helvetica-Bold", 7)
    tw = c.stringWidth(label, "Helvetica-Bold", 7)
    pw, ph = tw + 14, 16

    c.setFillColor(Color(0.000, 0.898, 1.000, alpha=0.12))
    c.roundRect(x - pw, y - ph + 4, pw, ph, 4, fill=1, stroke=0)
    c.setStrokeColor(CYAN)
    c.setLineWidth(0.5)
    c.roundRect(x - pw, y - ph + 4, pw, ph, 4, fill=0, stroke=1)

    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x - pw + 7, y - 7, label)


def _section_header(c, num_str, title, accent=CYAN):
    """
    Draw:  [big number]  [title text]
            ─────────────────────────
    Returns y of content start.
    """
    y_top = H - PAD - 6

    # Big gradient-style number (purple behind, cyan in front offset)
    c.setFillColor(Color(0.486, 0.227, 0.929, alpha=0.45))
    c.setFont("Helvetica-Bold", 42)
    c.drawString(PAD - 1, y_top - 1, num_str)   # shadow

    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 42)
    c.drawString(PAD, y_top, num_str)

    # Title right of number
    num_w = c.stringWidth(num_str, "Helvetica-Bold", 42)
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(PAD + num_w + 12, y_top + 2, title)

    # Divider
    rule_y = y_top - 14
    c.setStrokeColor(DIVIDER)
    c.setLineWidth(1.5)
    c.line(PAD, rule_y, W - PAD, rule_y)

    return rule_y - 22          # content starts here


def _insight_card(c, text, x, y, w, accent=CYAN):
    """
    Left-bordered card with dark background.
    Returns y after the card.
    """
    if not text:
        return y

    font, size = "Helvetica", 11
    inner_w = w - 24
    lines = simpleSplit(str(text), font, size, inner_w)
    card_h = len(lines) * 18 + 26

    # Card bg
    c.setFillColor(CARD_BG)
    c.roundRect(x, y - card_h, w, card_h, 5, fill=1, stroke=0)

    # Border
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.roundRect(x, y - card_h, w, card_h, 5, fill=0, stroke=1)

    # Left accent strip
    c.setFillColor(accent)
    c.rect(x, y - card_h, 3, card_h, fill=1, stroke=0)

    # Text
    c.setFillColor(TEXT_LIGHT)
    c.setFont(font, size)
    ty = y - 16
    for line in lines:
        c.drawString(x + 14, ty, line)
        ty -= 18

    return y - card_h - 12


def _safe(val, fallback=""):
    """Convert NaN / None to empty string."""
    if val is None:
        return fallback
    s = str(val).strip()
    return fallback if s.lower() == "nan" else s


# ─────────────────────────────────────────────────────────────────────────────
# 6 SLIDE TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────

def _slide_cover(c, art, idx, total):
    """Slide 1 — Cover: headline + category + score."""
    _bg(c)
    _glow(c, W,     H,     260, GLOW_CYAN)
    _glow(c, 0,     0,     200, GLOW_PURPLE)
    _left_strip(c, PURPLE)

    category = _safe(art.get("Category"), "AI Update")
    score    = art.get("Importance Score", 0) or 0
    source   = _safe(art.get("Source"))
    title    = _safe(art.get("Title"), "AI Update")

    # Category pill
    _category_pill(c, category, PAD + 8, H - PAD + 2)

    # Score chip top-right
    _score_chip(c, score, W - PAD, H - PAD + 2)

    # Article number badge
    c.setFillColor(Color(0.486, 0.227, 0.929, alpha=0.15))
    c.circle(W - PAD - 14, 80, 16, fill=1, stroke=0)
    c.setFillColor(PURPLE)
    c.setFont("Helvetica-Bold", 9)
    num_label = f"#{idx}"
    nw = c.stringWidth(num_label, "Helvetica-Bold", 9)
    c.drawString(W - PAD - 14 - nw / 2, 76, num_label)

    # Title — large, wrapped, vertically centred in the middle zone
    c.setFillColor(TEXT_LIGHT)
    c.setFont("Helvetica-Bold", 20)
    max_w = W - PAD * 2 - 16
    lines = simpleSplit(title, "Helvetica-Bold", 20, max_w)
    if len(lines) > 4:
        lines = lines[:4]
        last = lines[-1]
        while c.stringWidth(last + "…", "Helvetica-Bold", 20) > max_w and last:
            last = last[:-1]
        lines[-1] = last + "…"

    block_h    = len(lines) * 28
    start_y    = (H + block_h) / 2 + 14

    for line in lines:
        c.drawString(PAD + 8, start_y, line)
        start_y -= 28

    # Source below title
    if source:
        c.setFillColor(TEXT_GRAY)
        c.setFont("Helvetica", 9)
        c.drawString(PAD + 8, 74, source)

    _footer(c, 1, 6)


def _slide_what_happened(c, art, idx, total):
    """Slide 2 — What Happened: summary text."""
    _bg(c)
    _glow(c, W, H, 200, GLOW_PURPLE)

    y = _section_header(c, "02", "What Happened", PURPLE)
    y -= 6

    summary = _safe(art.get("Summary")) or _safe(art.get("Title"))
    # Trim to ~350 chars for readability
    if len(summary) > 350:
        summary = summary[:347] + "…"

    _text_block(c, summary, PAD, y,
                font="Helvetica", size=11,
                color=TEXT_LIGHT,
                max_w=W - PAD * 2,
                line_h=18)

    _footer(c, 2, 6, _safe(art.get("Source")))


def _slide_why(c, art, idx, total):
    """Slide 3 — Why It Matters."""
    _bg(c)
    _glow(c, 0, 0, 200, GLOW_CYAN)

    y = _section_header(c, "03", "Why It Matters", CYAN)
    y -= 10

    content = _safe(art.get("Why It Matters"))
    _insight_card(c, content, PAD, y, W - PAD * 2, CYAN)

    _footer(c, 3, 6, _safe(art.get("Source")))


def _slide_saas(c, art, idx, total):
    """Slide 4 — SaaS Impact."""
    _bg(c)
    _glow(c, W, H, 200, GLOW_PURPLE)

    y = _section_header(c, "04", "SaaS Impact", PURPLE)
    y -= 10

    content = _safe(art.get("SaaS Impact"))
    _insight_card(c, content, PAD, y, W - PAD * 2, PURPLE)

    _footer(c, 4, 6, _safe(art.get("Source")))


def _slide_pm(c, art, idx, total):
    """Slide 5 — PM Perspective."""
    _bg(c)
    _glow(c, W, 0, 200, GLOW_TEAL)

    y = _section_header(c, "05", "PM Perspective", TEAL)
    y -= 10

    content = _safe(art.get("PM Perspective"))
    _insight_card(c, content, PAD, y, W - PAD * 2, TEAL)

    _footer(c, 5, 6, _safe(art.get("Source")))


def _slide_takeaway(c, art, idx, total):
    """Slide 6 — Key Takeaway + CTA."""
    _bg(c)
    _glow(c, W / 2, H / 2, 280, GLOW_CYAN)

    y = _section_header(c, "06", "Key Takeaway", CYAN)
    y -= 16

    # Takeaway = first sentence of Why It Matters
    why    = _safe(art.get("Why It Matters"))
    sentences = [s.strip() for s in why.split(".") if s.strip()]
    takeaway  = sentences[0] if sentences else _safe(art.get("Title"))[:80]

    y = _text_block(c, takeaway, PAD, y,
                    font="Helvetica-Bold", size=14,
                    color=TEXT_LIGHT,
                    max_w=W - PAD * 2,
                    line_h=22)

    # ── CTA section ──────────────────────────────────
    cta_y = 148
    _hline(c, cta_y + 20)

    c.setFillColor(CYAN)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(PAD, cta_y, "Follow for daily AI intelligence →")

    url = _safe(art.get("URL"))
    if url:
        # Shorten long URLs
        display_url = url if len(url) <= 55 else url[:52] + "…"
        c.setFillColor(TEXT_GRAY)
        c.setFont("Helvetica", 8)
        c.drawString(PAD, cta_y - 18, display_url)

    _footer(c, 6, 6)


# ─────────────────────────────────────────────────────────────────────────────
# CAROUSEL BUILDER
# ─────────────────────────────────────────────────────────────────────────────

_SLIDES = [
    _slide_cover,
    _slide_what_happened,
    _slide_why,
    _slide_saas,
    _slide_pm,
    _slide_takeaway,
]


def _safe_filename(title, idx):
    """Turn an article title into a safe filename."""
    slug = re.sub(r"[^\w\s-]", "", str(title).lower())
    slug = re.sub(r"[\s_-]+", "_", slug).strip("_")
    slug = slug[:50]
    return f"{idx:02d}_{slug}"


def _write_pdf(articles, output_path):
    """Write all articles (6 slides each) to a single PDF."""
    c = canvas.Canvas(output_path, pagesize=(W, H))

    for idx, art in enumerate(articles, start=1):
        for slide_fn in _SLIDES:
            slide_fn(c, art, idx, len(articles))
            c.showPage()

    c.save()


def generate_carousels(articles):
    """
    Generates:
      • One individual 6-slide PDF per article → CAROUSEL_FOLDER/
      • One combined PDF with all articles     → OUTPUT_FOLDER/

    Returns (individual_paths, combined_path).
    """
    os.makedirs(CAROUSEL_FOLDER, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    individual_paths = []

    for idx, art in enumerate(articles, start=1):
        name     = _safe_filename(art.get("Title", "article"), idx)
        out_path = os.path.join(CAROUSEL_FOLDER, f"{name}.pdf")

        c = canvas.Canvas(out_path, pagesize=(W, H))
        for slide_fn in _SLIDES:
            slide_fn(c, art, idx, len(articles))
            c.showPage()
        c.save()

        individual_paths.append(out_path)

    # Combined review PDF
    combined_path = os.path.join(
        OUTPUT_FOLDER,
        f"carousel_combined_{timestamp}.pdf"
    )
    _write_pdf(articles, combined_path)

    return individual_paths, combined_path


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

def find_latest_master_file():
    """Return path to the most recent master_agentic_updates_*.xlsx."""
    try:
        files = [
            f for f in os.listdir(OUTPUT_FOLDER)
            if f.startswith("master_agentic_updates_")
            and f.endswith(".xlsx")
        ]
    except FileNotFoundError:
        return None

    if not files:
        return None

    files.sort()
    return os.path.join(OUTPUT_FOLDER, files[-1])


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():

    print("\n=== LINKEDIN CAROUSEL PDF GENERATOR ===\n")

    master_file = find_latest_master_file()

    if not master_file:
        print("No master Excel file found in outputs/")
        print("Run main.py first to generate the dataset.")
        return

    print(f"Source : {master_file}")

    df = pd.read_excel(master_file)
    df = df.sort_values(
        "Importance Score",
        ascending=False
    )

    top_n    = 10
    articles = df.head(top_n).to_dict("records")

    print(f"Articles: {len(articles)}  ×  6 slides = {len(articles) * 6} pages\n")

    individual_paths, combined_path = generate_carousels(articles)

    print("Individual carousel PDFs (upload one per LinkedIn post):")
    for p in individual_paths:
        print(f"  {p}")

    print(f"\nCombined review PDF:")
    print(f"  {combined_path}")

    print(
        f"\nGenerated {len(individual_paths)} carousels"
        f" + 1 combined PDF"
    )

    print("\n=== COMPLETE ===")


if __name__ == "__main__":
    main()
