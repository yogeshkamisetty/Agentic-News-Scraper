"""
linkedin_carousel_canva.py
───────────────────────────────────────────────────────────────
LinkedIn Carousel — Canva "Gray Minimal" Template Aesthetic
───────────────────────────────────────────────────────────────
Replicates: KVD Studio · Gray Minimal Social Media LinkedIn Carousel

Key design elements from template:
  • Light gray background  (#EBEBEB — warm off-white gray)
  • Small uppercase brand label  →  centered at very top
  • Centered oval number badge  →  content slides only
  • Large bold left-aligned headline  (Helvetica-Bold, 36–42pt)
  • Left-aligned body copy  (Helvetica, 11pt, dark gray)
  • Pill arrow button  →  bottom-right, black, "›"
  • "Circled word" effect on cover  →  oval outline over one word
  • Company logo  →  cover (small) + CTA (large centered)

Format  : Portrait 4:5  ·  540 × 675 pt  ·  LinkedIn Document post
Slides  : 9  (Hook · Problem · 5 Insights · Summary · CTA)
Content : Top AI signals for software professionals, May 2026
Cost    : Zero API calls
───────────────────────────────────────────────────────────────
"""

import os
from datetime import datetime

from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas as rl_canvas


# ═══════════════════════════════════════════════════════════
# PAGE + LAYOUT CONSTANTS
# ═══════════════════════════════════════════════════════════

W, H  = 540, 675        # 4:5 portrait (LinkedIn carousel)
M     = 46              # outer left/right margin
CW    = W - M * 2       # content width  = 448 pt
CX    = W // 2          # center x       = 270 pt

BRAND  = "AI INTELLIGENCE  ·  2026"
TOTAL  = 9

OUTPUT_FOLDER   = "outputs"
CAROUSEL_FOLDER = os.path.join(OUTPUT_FOLDER, "carousel_canva")
LOGO_PATH       = os.path.join(OUTPUT_FOLDER, "image.png")


# ═══════════════════════════════════════════════════════════
# COLOUR PALETTE
# ═══════════════════════════════════════════════════════════

BG        = HexColor("#EBEBEB")   # template background
BLACK     = HexColor("#111111")   # headlines
G_BODY    = HexColor("#3C3C3C")   # body text
G_LBL     = HexColor("#909090")   # labels / captions
G_RULE    = HexColor("#CECECE")   # thin dividers
G_CARD    = HexColor("#DEDEDE")   # card fill (slightly darker than bg)
WHITE     = HexColor("#FFFFFF")   # reversed text


# ═══════════════════════════════════════════════════════════
# ATOMIC PRIMITIVES
# ═══════════════════════════════════════════════════════════

def _bg(c, dark: bool = False):
    c.setFillColor(BLACK if dark else BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def _hrule(c, y, x0=None, x1=None, color=None, lw=0.5):
    x0 = M       if x0 is None else x0
    x1 = W - M   if x1 is None else x1
    color = G_RULE if color is None else color
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    c.line(x0, y, x1, y)
    c.restoreState()


def _t(c, text, x, y, font="Helvetica", size=11, color=None,
       align="left"):
    c.saveState()
    if color:
        c.setFillColor(color)
    c.setFont(font, size)
    s = str(text)
    if align == "center":
        c.drawCentredString(x, y, s)
    elif align == "right":
        c.drawRightString(x, y, s)
    else:
        c.drawString(x, y, s)
    c.restoreState()


def _wrap(c, text, x, y, size=11, color=None, max_w=None,
          line_h=None, font="Helvetica") -> float:
    """Wrapped body text. Returns final y after last line."""
    if not text:
        return y
    if max_w is None:
        max_w = CW
    if line_h is None:
        line_h = size * 1.7
    if color is None:
        color = G_BODY
    c.saveState()
    c.setFillColor(color)
    c.setFont(font, size)
    for line in simpleSplit(str(text), font, size, max_w):
        c.drawString(x, y, line)
        y -= line_h
    c.restoreState()
    return y


# ═══════════════════════════════════════════════════════════
# COMPOUND COMPONENTS
# ═══════════════════════════════════════════════════════════

def _brand_header(c, dark: bool = False):
    """
    Centered brand label + thin rule — top of every slide.
    Returns y of the rule (content starts below here).
    """
    y_lbl = H - 28
    _t(c, BRAND, CX, y_lbl,
       font="Helvetica", size=7,
       color=G_LBL, align="center")
    rule_y = H - 46
    _hrule(c, rule_y,
           color=HexColor("#4A4A4A") if dark else G_RULE,
           lw=0.4)
    return rule_y


def _pill_button(c, dark: bool = False):
    """
    Small rounded pill at bottom-right with › arrow.
    Matches the Canva template navigation cue.
    """
    btn_w, btn_h = 52, 26
    btn_x = W - M - btn_w
    btn_y = 28
    r = btn_h // 2

    # Fill
    c.saveState()
    c.setFillColor(WHITE if dark else BLACK)
    c.roundRect(btn_x, btn_y, btn_w, btn_h, r, fill=1, stroke=0)

    # Arrow
    c.setFillColor(BLACK if dark else WHITE)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(btn_x + btn_w // 2, btn_y + 7, "›")
    c.restoreState()


def _oval_badge(c, num_str: str, cx: int, cy: int,
                ow: int = 118, oh: int = 54, dark: bool = False):
    """
    Oval outline badge with slide number — the template's
    signature element.  Appears centered on content slides.
    """
    x1 = cx - ow // 2
    y1 = cy - oh // 2
    x2 = cx + ow // 2
    y2 = cy + oh // 2

    # Oval — no fill (transparent), just stroke outline
    c.saveState()
    c.setStrokeColor(WHITE if dark else BLACK)
    c.setFillColor(BG if not dark else BLACK)
    c.setLineWidth(1.4)
    c.ellipse(x1, y1, x2, y2, fill=1, stroke=1)

    # Number inside
    c.setFillColor(WHITE if dark else BLACK)
    c.setFont("Helvetica-Bold", 20)
    tw = c.stringWidth(num_str, "Helvetica-Bold", 20)
    c.drawString(cx - tw / 2, cy - 8, num_str)
    c.restoreState()


def _circled_word(c, canvas_obj, word: str, x: float, y: float,
                  font: str, size: float):
    """
    Cover effect: draws an oval outline around a single word.
    The word itself is drawn FIRST, then the oval overlays it.
    """
    tw = canvas_obj.stringWidth(word, font, size)
    cap_h = size * 0.72   # approximate cap height

    # Draw the word
    canvas_obj.saveState()
    canvas_obj.setFillColor(BLACK)
    canvas_obj.setFont(font, size)
    canvas_obj.drawString(x, y, word)
    canvas_obj.restoreState()

    # Oval (no fill — transparent so word shows through)
    pad_x, pad_y = 9, 7
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(BLACK)
    canvas_obj.setLineWidth(1.5)
    canvas_obj.ellipse(
        x - pad_x,
        y - pad_y,
        x + tw + pad_x,
        y + cap_h + pad_y,
        fill=0, stroke=1
    )
    canvas_obj.restoreState()


def _logo(c, x, y, h=22, centered=False):
    """Draw company logo. Falls back to text if image missing."""
    if os.path.exists(LOGO_PATH):
        try:
            logo_w = h * 4.0
            draw_x = (W - logo_w) / 2 if centered else x
            c.drawImage(
                LOGO_PATH, draw_x, y,
                height=h, width=logo_w,
                preserveAspectRatio=True,
                mask="auto",
            )
            return
        except Exception:
            pass
    # Text fallback
    label = "AI SIGNAL ENGINE"
    c.saveState()
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 9)
    if centered:
        c.drawCentredString(CX, y + 7, label)
    else:
        c.drawString(x, y + 7, label)
    c.restoreState()


def _section_tag(c, label: str, x=None, y=None):
    """Small gray tag box — used on cover, case study slides."""
    if x is None:
        x = M
    if y is None:
        y = H - 80
    font, size = "Helvetica", 7.5
    tw = len(label) * size * 0.6 + 14
    c.saveState()
    c.setFillColor(G_CARD)
    c.roundRect(x, y - 14, tw, 20, 3, fill=1, stroke=0)
    c.setFillColor(G_LBL)
    c.setFont(font, size)
    c.drawString(x + 7, y - 7, label.upper())
    c.restoreState()


# ═══════════════════════════════════════════════════════════
# SLIDE RENDERERS
# ═══════════════════════════════════════════════════════════

def _slide_01_hook(c):
    """
    COVER SLIDE
    ───────────
    Layout   : Brand label → Logo (small) → Large bold headline
               with ONE circled word → subtitle → pill button
    BG       : Light gray (template default)
    Oval     : Around "Bottleneck" — the circled-word cover effect
    """
    _bg(c)
    _brand_header(c)

    # Company logo — small, top-left, under brand rule
    _logo(c, M, H - 78, h=22)

    # ── Headline block ──────────────────────────────────────
    # Line 1 — plain
    y1 = H - 148
    _t(c, "The AI Agent",
       M, y1, font="Helvetica-Bold", size=42, color=BLACK)

    # Line 2 — "Bottleneck" with circled-word oval
    y2 = y1 - 52
    _circled_word(c, c, "Bottleneck", M, y2,
                  font="Helvetica-Bold", size=42)

    # Line 3 — plain
    y3 = y2 - 52
    _t(c, "Isn't the Model.",
       M, y3, font="Helvetica-Bold", size=32, color=BLACK)

    # ── Separator ───────────────────────────────────────────
    sep_y = y3 - 30
    _hrule(c, sep_y, x0=M, x1=M + 60, lw=1.2, color=BLACK)

    # ── Subtitle ────────────────────────────────────────────
    sub_y = sep_y - 24
    _t(c, "WHAT'S REALLY BLOCKING YOUR AI STACK",
       M, sub_y, font="Helvetica", size=8, color=G_LBL)

    # ── Body text ────────────────────────────────────────────
    body_y = sub_y - 26
    _wrap(c,
          "5 signals software engineers and product teams "
          "need to act on — right now.",
          M, body_y, size=11, color=G_BODY)

    # ── Pill button ─────────────────────────────────────────
    _pill_button(c)


def _slide_02_problem(c):
    """
    PROBLEM SLIDE
    ─────────────
    Layout   : Brand → Rule → Large punchy statement
               → Body → Pill
    No oval badge — reserved for insight slides.
    Visual shock via large-size "broken" stat.
    """
    _bg(c)
    _brand_header(c)

    # Section tag
    _section_tag(c, "The Problem", M, H - 68)

    # Large statement
    y = H - 148
    _t(c, "Your agents know",
       M, y, font="Helvetica-Bold", size=36, color=BLACK)
    y -= 46
    _t(c, "what to do.",
       M, y, font="Helvetica-Bold", size=36, color=BLACK)
    y -= 46
    _t(c, "They just can't",
       M, y, font="Helvetica-Bold", size=36, color=BLACK)
    y -= 46
    _t(c, "do it.",
       M, y, font="Helvetica-Bold", size=36, color=BLACK)

    # Rule
    rule_y = y - 26
    _hrule(c, rule_y, x0=M, x1=M + 60, lw=1.2, color=BLACK)

    # Body
    body_y = rule_y - 22
    _wrap(c,
          "Most enterprise AI failures don't trace back to model performance. "
          "They trace back to access, permissions, and tool-calling constraints. "
          "The model sees the path. It just can't walk it.",
          M, body_y, size=11, color=G_BODY)

    _pill_button(c)


def _slide_03_insight_1(c):
    """
    INSIGHT 01 — Permissions are the real bottleneck
    (Key Point 1 from brief)
    """
    _bg(c)
    _brand_header(c)

    # Oval badge centered
    _oval_badge(c, "01", CX, H - 148)

    # Headline (left-aligned, below oval)
    y = H - 228
    _t(c, "Permissions are",
       M, y, font="Helvetica-Bold", size=34, color=BLACK)
    y -= 44
    _t(c, "the real bottleneck.",
       M, y, font="Helvetica-Bold", size=34, color=BLACK)

    # Short rule
    rule_y = y - 24
    _hrule(c, rule_y, x0=M, x1=M + 52, lw=1.2, color=BLACK)

    # Body
    body_y = rule_y - 22
    _wrap(c,
          "AI agents hit walls at the tool-access layer — not the reasoning layer. "
          "They identify the right action but lack authority to execute it. "
          "The fix isn't a smarter model. It's a smarter control plane: "
          "scoped permissions, gated tool access, and auditable guardrails.",
          M, body_y, size=11, color=G_BODY)

    _pill_button(c)


def _slide_04_insight_2(c):
    """
    INSIGHT 02 — MeMo memory model, +26% no retraining
    (Key Point 2 from brief)
    """
    _bg(c)
    _brand_header(c)

    _oval_badge(c, "02", CX, H - 148)

    # Headline with stat built in
    y = H - 228
    _t(c, "+26% performance.",
       M, y, font="Helvetica-Bold", size=34, color=BLACK)
    y -= 44
    _t(c, "No retraining.",
       M, y, font="Helvetica-Bold", size=34, color=BLACK)

    rule_y = y - 24
    _hrule(c, rule_y, x0=M, x1=M + 52, lw=1.2, color=BLACK)

    body_y = rule_y - 22
    _wrap(c,
          "MeMo's memory model lets teams upgrade their LLM without retraining it — "
          "performance jumps 26% simply by improving context management. "
          "Memory is now a first-class product feature, not just a backend detail. "
          "If your agent forgets, it fails. Give it memory first.",
          M, body_y, size=11, color=G_BODY)

    _pill_button(c)


def _slide_05_insight_3(c):
    """
    INSIGHT 03 — AI Agents' Rebuild Era
    (Key Point 3 from brief)
    """
    _bg(c)
    _brand_header(c)

    _oval_badge(c, "03", CX, H - 148)

    y = H - 228
    _t(c, "Agents are entering",
       M, y, font="Helvetica-Bold", size=32, color=BLACK)
    y -= 42
    _t(c, "their rebuild era.",
       M, y, font="Helvetica-Bold", size=32, color=BLACK)

    rule_y = y - 24
    _hrule(c, rule_y, x0=M, x1=M + 52, lw=1.2, color=BLACK)

    body_y = rule_y - 22
    _wrap(c,
          "Enterprises are pulling back from flashy demos and rebuilding with "
          "reliability as the north star. The question has shifted: "
          "not 'what can agents do?' — but 'what can they do consistently, "
          "without supervision, without failure?' That bar is much higher.",
          M, body_y, size=11, color=G_BODY)

    _pill_button(c)


def _slide_06_insight_4(c):
    """
    INSIGHT 04 — Human-AI framework (Pope's Magnifica Humanitas)
    (Key Point 4 from brief — translated for software audience)
    """
    _bg(c)
    _brand_header(c)

    _oval_badge(c, "04", CX, H - 148)

    y = H - 228
    _t(c, "There's a framework",
       M, y, font="Helvetica-Bold", size=32, color=BLACK)
    y -= 42
    _t(c, "for the AI moment.",
       M, y, font="Helvetica-Bold", size=32, color=BLACK)

    rule_y = y - 24
    _hrule(c, rule_y, x0=M, x1=M + 52, lw=1.2, color=BLACK)

    body_y = rule_y - 22
    _wrap(c,
          "Lead with judgment. Delegate execution. Retain agency. "
          "This is the model individual engineers and PMs need right now — "
          "not just for themselves, but for how they design AI workflows. "
          "Automation that removes human agency is fragile. Design for the handoff.",
          M, body_y, size=11, color=G_BODY)

    _pill_button(c)


def _slide_07_insight_5(c):
    """
    INSIGHT 05 — Mistral Vibe + industrial AI push
    (Key Point 5 from brief)
    """
    _bg(c)
    _brand_header(c)

    _oval_badge(c, "05", CX, H - 148)

    y = H - 228
    _t(c, "Industrial AI is",
       M, y, font="Helvetica-Bold", size=36, color=BLACK)
    y -= 46
    _t(c, "the next frontier.",
       M, y, font="Helvetica-Bold", size=36, color=BLACK)

    rule_y = y - 24
    _hrule(c, rule_y, x0=M, x1=M + 52, lw=1.2, color=BLACK)

    body_y = rule_y - 22
    _wrap(c,
          "Mistral's Vibe launch, new data center push, and expansion into industrial AI "
          "signal a direct challenge to OpenAI — not in consumer chat, but in "
          "enterprise and operational environments. The real competition is happening "
          "far from the chatbot interface.",
          M, body_y, size=11, color=G_BODY)

    _pill_button(c)


def _slide_08_summary(c):
    """
    SUMMARY SLIDE
    ─────────────
    5 signals in fast-scan format.
    Numbered list, strong hierarchy.
    """
    _bg(c)
    _brand_header(c)

    # Section tag
    _section_tag(c, "5 Signals to Know", M, H - 68)

    # Intro headline
    y = H - 150
    _t(c, "What every software",
       M, y, font="Helvetica-Bold", size=28, color=BLACK)
    y -= 36
    _t(c, "professional must track.",
       M, y, font="Helvetica-Bold", size=28, color=BLACK)

    rule_y = y - 20
    _hrule(c, rule_y, x0=M, x1=W - M, lw=0.5)

    # Numbered list
    items = [
        "Permissions > model power",
        "Memory = +26% performance, no retraining",
        "Reliability beats novelty in enterprise",
        "Design for human-AI handoff",
        "Industrial AI is the next battleground",
    ]

    y = rule_y - 22
    for i, item in enumerate(items, 1):
        # Number
        c.saveState()
        c.setFillColor(G_CARD)
        c.roundRect(M, y - 16, 24, 22, 3, fill=1, stroke=0)
        c.setFillColor(G_LBL)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawCentredString(M + 12, y - 8, str(i))
        c.restoreState()

        # Item text
        _t(c, item, M + 34, y - 8,
           font="Helvetica", size=10.5, color=G_BODY)

        y -= 30

    _pill_button(c)


def _slide_09_cta(c):
    """
    CTA SLIDE
    ─────────
    Centered layout — logo prominent, headline, black CTA button.
    Minimal. High contrast. Strong close.
    """
    _bg(c)
    _brand_header(c)

    # ── Top message ─────────────────────────────────────────
    y = H - 110
    _t(c, "Stay ahead of the",
       CX, y, font="Helvetica-Bold", size=32,
       color=BLACK, align="center")
    y -= 42
    _t(c, "AI curve.",
       CX, y, font="Helvetica-Bold", size=32,
       color=BLACK, align="center")

    # Short center rule
    mid_rule_y = y - 24
    _hrule(c, mid_rule_y,
           x0=CX - 26, x1=CX + 26,
           lw=1.4, color=BLACK)

    # Tagline
    tag_y = mid_rule_y - 22
    _t(c, "Agentic AI  ·  Enterprise Tools  ·  Developer Intelligence",
       CX, tag_y, font="Helvetica", size=8.5, color=G_LBL, align="center")

    # ── Logo — large, centered ───────────────────────────────
    logo_h = 46
    logo_y = tag_y - 80
    _logo(c, M, logo_y, h=logo_h, centered=True)

    # Thin rule under logo
    _hrule(c, logo_y - 10)

    # ── CTA text ─────────────────────────────────────────────
    cta_lbl_y = logo_y - 30
    _t(c, "FOLLOW  ·  SAVE  ·  SHARE",
       CX, cta_lbl_y, font="Helvetica", size=8, color=G_LBL, align="center")

    # ── Black pill CTA ───────────────────────────────────────
    btn_w, btn_h = 300, 40
    btn_x = (W - btn_w) // 2
    btn_y = cta_lbl_y - 62

    c.saveState()
    c.setFillColor(BLACK)
    c.roundRect(btn_x, btn_y, btn_w, btn_h, 20, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(CX, btn_y + 14, "Follow for daily AI intelligence  ›")
    c.restoreState()

    # Hashtags
    hash_y = btn_y - 26
    _t(c, "#AgenticAI  ·  #EnterpriseAI  ·  #AIForDevs  ·  #TechUpdates",
       CX, hash_y, font="Helvetica", size=7.5, color=G_LBL, align="center")


# ═══════════════════════════════════════════════════════════
# SLIDE REGISTRY
# ═══════════════════════════════════════════════════════════

SLIDES = [
    ("01_hook",                 _slide_01_hook),
    ("02_problem",              _slide_02_problem),
    ("03_permissions",          _slide_03_insight_1),
    ("04_memo_memory",          _slide_04_insight_2),
    ("05_rebuild_era",          _slide_05_insight_3),
    ("06_human_ai_framework",   _slide_06_insight_4),
    ("07_mistral_industrial",   _slide_07_insight_5),
    ("08_summary",              _slide_08_summary),
    ("09_cta",                  _slide_09_cta),
]


# ═══════════════════════════════════════════════════════════
# GENERATORS
# ═══════════════════════════════════════════════════════════

def generate_combined(out_path: str) -> str:
    """All 9 slides in one PDF — the LinkedIn upload file."""
    c = rl_canvas.Canvas(out_path, pagesize=(W, H))
    for _, fn in SLIDES:
        fn(c)
        c.showPage()
    c.save()
    return out_path


def generate_individual(folder: str) -> list:
    """One PDF per slide — for design review."""
    os.makedirs(folder, exist_ok=True)
    paths = []
    for name, fn in SLIDES:
        out = os.path.join(folder, f"{name}.pdf")
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
    print("\n=== CANVA GRAY MINIMAL — LINKEDIN CAROUSEL ===\n")
    print(f"Style  : Gray Minimal (KVD Studio / Canva template)")
    print(f"Format : {W}×{H} pt  ·  4:5 portrait  ·  {len(SLIDES)} slides\n")

    os.makedirs(CAROUSEL_FOLDER, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Combined PDF — upload this to LinkedIn
    combined = os.path.join(CAROUSEL_FOLDER, f"ai_signals_carousel_{ts}.pdf")
    generate_combined(combined)
    print(f"LinkedIn upload file:")
    print(f"  {combined}\n")

    # Individual slide PDFs — for review
    slides_dir = os.path.join(CAROUSEL_FOLDER, "slides")
    individual = generate_individual(slides_dir)
    print("Individual slides:")
    for p in individual:
        print(f"  {p}")

    print(f"\n{len(SLIDES)} slides generated.")
    print("\n=== COMPLETE ===")
    return combined


if __name__ == "__main__":
    main()
