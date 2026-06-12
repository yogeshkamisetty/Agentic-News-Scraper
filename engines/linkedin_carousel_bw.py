"""
linkedin_carousel_bw.py
────────────────────────────────────────────────────────────
Premium B&W LinkedIn Carousel — Minimalist Editorial Style
────────────────────────────────────────────────────────────
Style  : White/Black editorial — Canva "simple carousel" aesthetic
         (Apple / Notion / luxury agency feel)
Format : 10 slides · 600×600 pt square · LinkedIn Document post
Content: Enterprise AI failure patterns + fixes (from master Excel)
Cost   : Zero API calls — pure reportlab + pandas
────────────────────────────────────────────────────────────
"""

import os
from datetime import datetime

import pandas as pd
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas as rl_canvas


# ═══════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════

W = H = 600          # square page (600×600 pt)
M = 52               # outer margin (left / right / top)
FH = 72              # footer zone: y=0 → y=FH
CW = W - M * 2       # usable content width = 496 pt

OUTPUT_FOLDER   = "outputs"
CAROUSEL_FOLDER = os.path.join(OUTPUT_FOLDER, "carousel_bw")
LOGO_PATH       = os.path.join(OUTPUT_FOLDER, "image.png")

TOTAL_SLIDES = 10


# ═══════════════════════════════════════════════════════════
# COLOUR PALETTE  (B&W only — no other colours)
# ═══════════════════════════════════════════════════════════

BLACK       = HexColor("#000000")
WHITE       = HexColor("#FFFFFF")
G_HEADLINE  = HexColor("#111111")   # near-black headlines on white
G_BODY      = HexColor("#3A3A3A")   # body text on white
G_CAPTION   = HexColor("#999999")   # labels, captions, footnotes
G_RULE      = HexColor("#E2E2E2")   # thin dividers on white slides
G_RULE_D    = HexColor("#282828")   # thin dividers on black slides
G_FAINT     = HexColor("#F5F5F5")   # card / pill backgrounds
G_DARK_BODY = HexColor("#AAAAAA")   # body text on black slides
G_TAG_BG    = HexColor("#EFEFEF")   # small tag/badge backgrounds


# ═══════════════════════════════════════════════════════════
# ATOMIC PRIMITIVES
# ═══════════════════════════════════════════════════════════

def _bg(c, dark: bool = False):
    c.setFillColor(BLACK if dark else WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def _hrule(c, y, x0=None, x1=None, dark=False, lw=0.5):
    x0 = M     if x0 is None else x0
    x1 = W - M if x1 is None else x1
    c.saveState()
    c.setStrokeColor(G_RULE_D if dark else G_RULE)
    c.setLineWidth(lw)
    c.line(x0, y, x1, y)
    c.restoreState()


def _accent_line(c, y, dark=False, length=52, lw=1.4):
    """Short bold horizontal accent — placed below section headlines."""
    c.saveState()
    c.setStrokeColor(WHITE if dark else BLACK)
    c.setLineWidth(lw)
    c.line(M, y, M + length, y)
    c.restoreState()


def _vline(c, x, y0, y1, dark=False, lw=0.5):
    c.saveState()
    c.setStrokeColor(G_RULE_D if dark else G_RULE)
    c.setLineWidth(lw)
    c.line(x, y0, x, y1)
    c.restoreState()


def _txt(c, text, x, y, font="Helvetica", size=10, color=None):
    c.saveState()
    if color:
        c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, str(text))
    c.restoreState()


def _txt_r(c, text, x, y, font="Helvetica", size=10, color=None):
    c.saveState()
    if color:
        c.setFillColor(color)
    c.setFont(font, size)
    c.drawRightString(x, y, str(text))
    c.restoreState()


def _txt_c(c, text, x, y, font="Helvetica", size=10, color=None):
    c.saveState()
    if color:
        c.setFillColor(color)
    c.setFont(font, size)
    c.drawCentredString(x, y, str(text))
    c.restoreState()


def _fill_rect(c, x, y, w, h, color):
    c.saveState()
    c.setFillColor(color)
    c.rect(x, y, w, h, fill=1, stroke=0)
    c.restoreState()


def _stroke_rect(c, x, y, w, h, color, lw=0.75):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.rect(x, y, w, h, fill=0, stroke=1)
    c.restoreState()


def _rounded_rect(c, x, y, w, h, r, fill_color=None, stroke_color=None, lw=0.75):
    c.saveState()
    if fill_color:
        c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(lw)
    c.roundRect(x, y, w, h, r,
                fill=1 if fill_color else 0,
                stroke=1 if stroke_color else 0)
    c.restoreState()


# ═══════════════════════════════════════════════════════════
# COMPOUND COMPONENTS
# ═══════════════════════════════════════════════════════════

def _bg_watermark_num(c, num_str, dark=False):
    """
    Giant decorative slide number — editorial watermark.
    Near top-right, partially clipped at page edge.
    Color: near-invisible on its own background.
    """
    color = HexColor("#1C1C1C") if dark else G_FAINT
    c.saveState()
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 128)
    tw = c.stringWidth(num_str, "Helvetica-Bold", 128)
    # right edge hits W-M+24 (slightly off page — editorial clip effect)
    c.drawString(W - M - tw + 24, H - 44, num_str)
    c.restoreState()


def _logo(c, x, y, h=20, dark=False):
    """Draw company logo. Falls back to text mark if image missing."""
    if os.path.exists(LOGO_PATH):
        try:
            c.drawImage(
                LOGO_PATH, x, y,
                height=h,
                width=h * 4.2,
                preserveAspectRatio=True,
                mask="auto",
            )
            return
        except Exception:
            pass
    # Text fallback
    _txt(c, "AI SIGNAL ENGINE", x, y + 6,
         font="Helvetica-Bold", size=8,
         color=WHITE if dark else BLACK)


def _footer(c, page_num: int, dark=False):
    """Consistent footer on every slide: thin rule + logo left + counter right."""
    _hrule(c, FH + 6, dark=dark)
    _logo(c, M, FH - 28, h=20, dark=dark)
    _txt_r(c, f"{page_num:02d}  /  {TOTAL_SLIDES:02d}",
           W - M, FH - 22,
           font="Helvetica", size=8,
           color=G_CAPTION)


def _section_label(c, text: str, dark=False) -> float:
    """
    Small ALL-CAPS label at top of content area + rule below.
    Returns y-coordinate where the headline should start.
    """
    y_label = H - M
    _txt(c, text.upper(), M, y_label,
         font="Helvetica", size=7, color=G_CAPTION)
    _hrule(c, y_label - 14, dark=dark)
    return y_label - 34     # first headline baseline


def _headline(c, lines: list, y: float, size=36, dark=False) -> float:
    """
    Draw a pre-split multi-line headline.
    Returns y after the last line.
    """
    lh = int(size * 1.26)
    for line in lines:
        _txt(c, line, M, y,
             font="Helvetica-Bold", size=size,
             color=WHITE if dark else G_HEADLINE)
        y -= lh
    return y


def _body(c, text: str, y: float, dark=False, size=10.5) -> float:
    """Wrapped body paragraph. Returns y after last line."""
    if not text:
        return y
    color  = G_DARK_BODY if dark else G_BODY
    line_h = size * 1.65
    lines  = simpleSplit(str(text), "Helvetica", size, CW)
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    for line in lines:
        c.drawString(M, y, line)
        y -= line_h
    return y


def _bullets(c, items: list, y: float, dark=False) -> float:
    """Em-dash bullet list. Returns y after last item."""
    color_dash = WHITE if dark else BLACK
    color_text = G_DARK_BODY if dark else G_BODY
    for item in items:
        # em-dash
        c.saveState()
        c.setFillColor(color_dash)
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(M, y, "—")
        c.restoreState()
        # item text (wrapped)
        lines = simpleSplit(str(item), "Helvetica", 10.5, CW - 24)
        c.setFillColor(color_text)
        c.setFont("Helvetica", 10.5)
        first = True
        for ln in lines:
            c.drawString(M + 24, y, ln)
            if first:
                first = False
            y -= 17
        y -= 7
    return y


def _numbered_items(c, items: list, y: float, dark=False) -> float:
    """
    Numbered list: bold number left, bold text right.
    Used for step summaries and takeaway slides.
    """
    for i, item in enumerate(items, 1):
        num = f"{i:02d}"
        # Number badge
        badge_color = G_RULE_D if dark else G_FAINT
        _fill_rect(c, M, y - 18, 26, 22, badge_color)
        _txt(c, num, M + 5, y - 12,
             font="Helvetica-Bold", size=9,
             color=G_CAPTION)
        # Item text
        _txt(c, item, M + 36, y - 12,
             font="Helvetica-Bold", size=13,
             color=WHITE if dark else G_HEADLINE)
        y -= 34
    return y


def _stat_pair(c, stat1, label1, stat2, label2, y, dark=False) -> float:
    """Two big stats side-by-side with a vertical divider."""
    color_stat  = WHITE if dark else BLACK
    color_label = G_DARK_BODY if dark else G_CAPTION

    # Stat 1
    _txt(c, stat1, M, y, font="Helvetica-Bold", size=54, color=color_stat)
    _txt(c, label1, M, y - 24, font="Helvetica", size=10, color=color_label)

    # Vertical divider
    mid_x = W // 2 - 10
    _vline(c, mid_x, y - 30, y + 40, dark=dark)

    # Stat 2
    _txt(c, stat2, mid_x + 20, y, font="Helvetica-Bold", size=54, color=color_stat)
    _txt(c, label2, mid_x + 20, y - 24, font="Helvetica", size=10, color=color_label)

    return y - 52


def _pill_tag(c, text, x, y, dark=False) -> float:
    """Small black/white filled label pill. Returns width."""
    bg_c = WHITE if dark else BLACK
    tx_c = BLACK if dark else WHITE
    c.setFont("Helvetica-Bold", 8)
    tw = c.stringWidth(text, "Helvetica-Bold", 8)
    pw, ph = tw + 18, 20
    _fill_rect(c, x, y - ph + 4, pw, ph, bg_c)
    _txt(c, text, x + 9, y - 12, font="Helvetica-Bold", size=8, color=tx_c)
    return pw


def _mini_table(c, rows: list, y: float) -> float:
    """
    Simple 2-column table: (label, value, highlight_bool).
    Highlighted row = black bg, white text.
    """
    row_h = 26
    for label, value, highlight in rows:
        bg = BLACK if highlight else G_FAINT
        tx = WHITE if highlight else G_BODY

        _fill_rect(c, M, y - row_h + 4, CW, row_h, bg)

        c.setFont("Helvetica-Bold" if highlight else "Helvetica", 9.5)
        c.setFillColor(tx)
        c.drawString(M + 12, y - 12, label)

        c.setFont("Helvetica-Bold", 9.5)
        c.setFillColor(tx)
        c.drawRightString(W - M - 12, y - 12, value)

        y -= row_h + 2
    return y


# ═══════════════════════════════════════════════════════════
# 10 SLIDE RENDERERS
# ═══════════════════════════════════════════════════════════

def _slide_01_hook(c):
    """
    SLIDE 1 — HOOK  (black)
    Strong attention-grabbing white headline on full black.
    """
    _bg(c, dark=True)

    # Top meta label
    _txt(c, "AI INTELLIGENCE  ·  MAY 2026",
         M, H - M,
         font="Helvetica", size=7, color=G_CAPTION)
    _hrule(c, H - M - 15, dark=True)

    # Headline — 4 impact lines, size decreasing on last
    lines_sizes = [
        ("Enterprise",       44),
        ("AI Agents",        44),
        ("Are Failing.",     44),
        ("Here’s the Fix.",  30),
    ]
    y = H - M - 62
    for line, sz in lines_sizes:
        _txt(c, line, M, y,
             font="Helvetica-Bold", size=sz,
             color=WHITE)
        y -= int(sz * 1.28)

    # Accent line + subtitle
    y -= 10
    _accent_line(c, y, dark=True, length=48)
    y -= 28
    _body(c,
          "What 34 verified AI signals reveal about the "
          "broken enterprise stack — and the 3-layer fix.",
          y, dark=True, size=10)

    # Swipe nudge
    _txt_r(c, "SWIPE  ›",
           W - M, FH + 16,
           font="Helvetica", size=8, color=G_CAPTION)

    _footer(c, 1, dark=True)


def _slide_02_problem(c):
    """
    SLIDE 2 — THE PROBLEM  (white)
    Two contrasting stats create instant tension.
    """
    _bg(c, dark=False)
    _bg_watermark_num(c, "02")

    y = _section_label(c, "The Problem")

    # Two-stat grid
    y = _stat_pair(c,
                   "85%", "want agentic AI",
                   "76%", "can’t support it",
                   y)

    y -= 18
    _hrule(c, y)
    y -= 24

    _body(c,
          "HFS Research and MIT Technology Review surveyed enterprise leaders "
          "and found a structural readiness crisis: organizations are rushing "
          "toward autonomous AI without the infrastructure to run it.",
          y, size=10.5)

    # Source footnote
    _txt(c, "Source: HFS Research × MIT Technology Review, 2026",
         M, FH + 18,
         font="Helvetica", size=7.5, color=G_CAPTION)

    _footer(c, 2)


def _slide_03_root_cause(c):
    """
    SLIDE 3 — ROOT CAUSE  (white)
    Simple, blunt insight statement.
    """
    _bg(c, dark=False)
    _bg_watermark_num(c, "03")

    y = _section_label(c, "Root Cause")

    y = _headline(c, ["AI agents", "forget", "everything."],
                  y, size=42)

    y -= 16
    _accent_line(c, y)
    y -= 28

    _body(c,
          "The #1 failure isn’t the model — it’s memory. "
          "Every agent session starts completely fresh. No working memory, "
          "no decision persistence, no compounding. Just repeated "
          "re-ingestion of the same context, over and over.",
          y, size=10.5)

    _footer(c, 3)


def _slide_04_fix01(c):
    """
    SLIDE 4 — FIX 01: Decision context graphs  (white)
    """
    _bg(c, dark=False)
    _bg_watermark_num(c, "04")

    y = _section_label(c, "Fix  01  —  Memory Architecture")

    y = _headline(c, ["Replace RAG with", "decision context", "graphs."],
                  y, size=34)

    y -= 14
    _accent_line(c, y)
    y -= 28

    y = _body(c,
              "Standard RAG retrieves similar documents and stops there. "
              "Decision context graphs give agents structured memory, "
              "time-aware reasoning, and the ability to freeze validated "
              "action sequences that compound over time.",
              y, size=10.5)

    # Attribution pill
    y -= 16
    _fill_rect(c, M, y - 18, 188, 22, G_FAINT)
    _txt(c, "→  Rippletide  (Neo4j ecosystem)",
         M + 10, y - 10,
         font="Helvetica", size=8.5, color=G_BODY)

    _footer(c, 4)


def _slide_05_fix02(c):
    """
    SLIDE 5 — FIX 02: 0.12% working memory  (black accent)
    Visual break with dark background for emphasis.
    """
    _bg(c, dark=True)
    _bg_watermark_num(c, "05", dark=True)

    y = _section_label(c, "Fix  02  —  Working Memory", dark=True)

    # Giant stat as part of the headline
    _txt(c, "0.12%",
         M, y,
         font="Helvetica-Bold", size=54, color=WHITE)
    y -= 68

    y = _headline(c, ["more parameters.", "Full working", "memory."],
                  y, size=32, dark=True)

    y -= 14
    _accent_line(c, y, dark=True)
    y -= 28

    _body(c,
          "Delta-mem’s OSAM matrix delivers genuine agent working memory "
          "at just 0.12% parameter overhead. No fine-tuning required. "
          "Agents stop re-processing already-seen context and maintain "
          "persistent task threads.",
          y, dark=True, size=10.5)

    # Attribution
    _fill_rect(c, M, FH + 22, 148, 20, G_RULE_D)
    _txt(c, "→  Mind Lab Research",
         M + 10, FH + 30,
         font="Helvetica", size=8, color=G_CAPTION)

    _footer(c, 5, dark=True)


def _slide_06_fix03(c):
    """
    SLIDE 6 — FIX 03: Proper benchmarking  (white)
    Includes an inline comparison mini-table.
    """
    _bg(c, dark=False)
    _bg_watermark_num(c, "06")

    y = _section_label(c, "Fix  03  —  Model Evaluation")

    y = _headline(c, ["Use real", "benchmarks."],
                  y, size=40)

    y -= 14
    _accent_line(c, y)
    y -= 24

    y = _body(c,
              "SWE-Bench told buyers all models were equal. "
              "DeepSWE proved them wrong.",
              y, size=10.5)

    y -= 18

    # Inline comparison table
    rows = [
        ("GPT-5.5",       "70%  ↑ Leader",  True),
        ("Claude Opus",   "54%  * exploited",     False),
        ("Gemini Pro",    "~48%",                  False),
    ]
    y = _mini_table(c, rows, y)

    y -= 6
    _txt(c,
         "* Claude Opus found exploiting git log gold-hash artifacts.  "
         "Source: Datacurve / DeepSWE, 2026",
         M, y - 4,
         font="Helvetica", size=7.5, color=G_CAPTION)

    _footer(c, 6)


def _slide_07_mistakes(c):
    """
    SLIDE 7 — MISTAKES TO AVOID  (white)
    4 bullets, each a sharp one-liner.
    """
    _bg(c, dark=False)
    _bg_watermark_num(c, "07")

    y = _section_label(c, "Mistakes to Avoid")

    y = _headline(c, ["What’s silently", "breaking your", "AI."],
                  y, size=38)

    y -= 14
    _accent_line(c, y)
    y -= 30

    mistakes = [
        "Trusting a single vendor’s benchmark",
        "Deploying stateless agents in production",
        "Skipping governance before going live",
        "Treating AI strategy as ‘buy a subscription’",
    ]
    _bullets(c, mistakes, y)

    _footer(c, 7)


def _slide_08_case_study(c):
    """
    SLIDE 8 — CASE STUDY: Rippletide  (white)
    Real-world example with company name pill.
    """
    _bg(c, dark=False)
    _bg_watermark_num(c, "08")

    y = _section_label(c, "Case Study")

    # Company name pill
    _pill_tag(c, "RIPPLETIDE", M, y + 4)
    y -= 28

    y = _headline(c, ["How one startup", "fixed enterprise", "agent memory."],
                  y, size=34)

    y -= 14
    _accent_line(c, y)
    y -= 28

    _body(c,
          "Built on Neo4j’s graph infrastructure, Rippletide’s "
          "decision context graph makes agents non-regressive: validated "
          "action chains are frozen and compounded across sessions. "
          "The first real alternative to stateless RAG in production.",
          y, size=10.5)

    _footer(c, 8)


def _slide_09_takeaway(c):
    """
    SLIDE 9 — KEY TAKEAWAY  (black)
    Final summary of the 3-layer fix — strong visual impact.
    """
    _bg(c, dark=True)
    _bg_watermark_num(c, "09", dark=True)

    y = _section_label(c, "Key Takeaway", dark=True)

    y = _headline(c, ["The 3-layer", "enterprise AI", "stack."],
                  y, size=38, dark=True)

    y -= 14
    _accent_line(c, y, dark=True)
    y -= 32

    items = [
        "Structured memory — not basic RAG",
        "Real-world multi-benchmark validation",
        "Governance before deployment",
    ]
    _numbered_items(c, items, y, dark=True)

    _footer(c, 9, dark=True)


def _slide_10_cta(c):
    """
    SLIDE 10 — CTA  (white)
    Clean centered layout: headline → logo → tagline → CTA button.
    """
    _bg(c, dark=False)

    # Top area label + rule
    _txt_c(c, "FOLLOW FOR DAILY AI INTELLIGENCE",
           W // 2, H - M,
           font="Helvetica", size=7, color=G_CAPTION)
    _hrule(c, H - M - 14)

    # Centered headline block
    headline_y = H - M - 56
    _txt_c(c, "Stay ahead of",
           W // 2, headline_y,
           font="Helvetica-Bold", size=32, color=G_HEADLINE)
    _txt_c(c, "the AI curve.",
           W // 2, headline_y - 42,
           font="Helvetica-Bold", size=32, color=G_HEADLINE)

    # Short accent line centered
    mid = W // 2
    c.saveState()
    c.setStrokeColor(BLACK)
    c.setLineWidth(1.4)
    c.line(mid - 26, headline_y - 64, mid + 26, headline_y - 64)
    c.restoreState()

    # Tagline
    tag_y = headline_y - 86
    _txt_c(c, "Agentic AI  ·  Enterprise Tools  ·  Developer Intelligence",
           W // 2, tag_y,
           font="Helvetica", size=9.5, color=G_CAPTION)

    # ── Logo (centered, prominent) ────────────────────────
    logo_h = 48
    logo_w = logo_h * 4.2
    logo_x = (W - logo_w) / 2
    logo_y = tag_y - 86

    if os.path.exists(LOGO_PATH):
        try:
            c.drawImage(
                LOGO_PATH, logo_x, logo_y,
                height=logo_h, width=logo_w,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            _txt_c(c, "AI SIGNAL ENGINE",
                   W // 2, logo_y + 18,
                   font="Helvetica-Bold", size=14, color=BLACK)
    else:
        _txt_c(c, "AI SIGNAL ENGINE",
               W // 2, logo_y + 18,
               font="Helvetica-Bold", size=14, color=BLACK)

    # Light rule below logo
    _hrule(c, logo_y - 14)

    # ── CTA button (black, rounded) ───────────────────────
    btn_w, btn_h = 286, 38
    btn_x = (W - btn_w) / 2
    btn_y = logo_y - 70

    _rounded_rect(c, btn_x, btn_y, btn_w, btn_h, 5,
                  fill_color=BLACK)
    _txt_c(c, "Save this post.  Share with your team.",
           W // 2, btn_y + 13,
           font="Helvetica-Bold", size=9.5, color=WHITE)

    # Hashtags
    _txt_c(c, "#AgenticAI  ·  #EnterpriseAI  ·  #ProductManagement  ·  #AIForDevs",
           W // 2, FH + 16,
           font="Helvetica", size=7.5, color=G_CAPTION)

    _footer(c, 10)


# ═══════════════════════════════════════════════════════════
# SLIDE REGISTRY
# ═══════════════════════════════════════════════════════════

SLIDES = [
    _slide_01_hook,
    _slide_02_problem,
    _slide_03_root_cause,
    _slide_04_fix01,
    _slide_05_fix02,
    _slide_06_fix03,
    _slide_07_mistakes,
    _slide_08_case_study,
    _slide_09_takeaway,
    _slide_10_cta,
]

SLIDE_TITLES = [
    "01_hook",
    "02_problem",
    "03_root_cause",
    "04_fix_memory_graphs",
    "05_fix_working_memory",
    "06_fix_benchmarks",
    "07_mistakes",
    "08_case_study_rippletide",
    "09_takeaway",
    "10_cta",
]


# ═══════════════════════════════════════════════════════════
# GENERATOR FUNCTIONS
# ═══════════════════════════════════════════════════════════

def generate_combined(output_path: str):
    """All 10 slides in one PDF (the LinkedIn upload file)."""
    c = rl_canvas.Canvas(output_path, pagesize=(W, H))
    for fn in SLIDES:
        fn(c)
        c.showPage()
    c.save()
    return output_path


def generate_individual(folder: str):
    """One PDF per slide (for review / individual preview)."""
    os.makedirs(folder, exist_ok=True)
    paths = []
    for fn, title in zip(SLIDES, SLIDE_TITLES):
        out = os.path.join(folder, f"{title}.pdf")
        c = rl_canvas.Canvas(out, pagesize=(W, H))
        fn(c)
        c.showPage()
        c.save()
        paths.append(out)
    return paths


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    print("\n=== B&W LINKEDIN CAROUSEL GENERATOR ===\n")
    print("Style   : Minimalist editorial (white/black)")
    print("Slides  : 10  |  Format: 600×600 pt square")
    print("Content : Enterprise AI failure patterns + fixes\n")

    os.makedirs(CAROUSEL_FOLDER, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # ── Combined PDF (the LinkedIn upload) ──────────────────
    combined_path = os.path.join(
        CAROUSEL_FOLDER,
        f"linkedin_carousel_{timestamp}.pdf"
    )
    generate_combined(combined_path)
    print(f"LinkedIn carousel PDF (upload this):")
    print(f"  {combined_path}\n")

    # ── Individual slide PDFs (for design review) ───────────
    slides_folder = os.path.join(CAROUSEL_FOLDER, "slides")
    individual = generate_individual(slides_folder)
    print("Individual slide previews:")
    for p in individual:
        print(f"  {p}")

    print(f"\nTotal: {len(SLIDES)} slides generated")
    print("\n=== COMPLETE ===")
    return combined_path


if __name__ == "__main__":
    main()
