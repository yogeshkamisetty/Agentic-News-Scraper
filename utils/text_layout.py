from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.platypus import Paragraph

from utils.pdf_theme import DEFAULT_THEME


def clean_text(value):
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"", "nan", "none"}:
        return ""
    return text


def make_style(name, font_name="Helvetica", font_size=18, leading=None,
               color=None, alignment=TA_LEFT, bold=False, italic=False):
    if leading is None:
        leading = int(font_size * 1.25)
    if color is None:
        color = DEFAULT_THEME.text
    if bold and italic:
        font_name = "Helvetica-BoldOblique"
    elif bold:
        font_name = "Helvetica-Bold"
    elif italic:
        font_name = "Helvetica-Oblique"
    return ParagraphStyle(
        name,
        fontName=font_name,
        fontSize=font_size,
        leading=leading,
        textColor=color,
        alignment=alignment,
    )


def wrap_lines(text, font_name, font_size, width):
    text = clean_text(text)
    if not text:
        return []
    return simpleSplit(text, font_name, font_size, width)


def fit_text(text, font_name, start_size, min_size, width, height, leading_ratio=1.22, max_lines=None):
    text = clean_text(text)
    if not text:
        return min_size, [], False

    size = start_size
    truncated = False

    while size >= min_size:
        leading = int(size * leading_ratio)
        lines = wrap_lines(text, font_name, size, width)
        if max_lines is not None:
            lines = lines[:max_lines]
        used_height = len(lines) * leading
        if used_height <= height:
            return size, lines, False
        size -= 1

    size = min_size
    leading = int(size * leading_ratio)
    lines = wrap_lines(text, font_name, size, width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated = True
    else:
        truncated = len(lines) * leading > height

    return size, lines, truncated


def paragraph_from_text(text, style):
    text = clean_text(text)
    if not text:
        text = ""
    return Paragraph(text.replace("\n", "<br/>"), style)


def draw_paragraph_box(canvas, text, x, top_y, width, height, style,
                       min_size=None, max_lines=None, debug_label="", warn_prefix=""):
    text = clean_text(text)
    if not text:
        return top_y, False, True

    font_name = style.fontName
    start_size = style.fontSize
    if min_size is None:
        min_size = max(8, start_size - 6)

    fit_size, lines, truncated = fit_text(
        text,
        font_name,
        start_size,
        min_size,
        width,
        height,
        leading_ratio=(style.leading / float(style.fontSize)) if style.fontSize else 1.22,
        max_lines=max_lines,
    )
    leading = int(fit_size * ((style.leading / float(style.fontSize)) if style.fontSize else 1.22))

    y = top_y
    canvas.setFillColor(style.textColor)
    canvas.setFont(font_name, fit_size)

    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated = True

    for line in lines:
        canvas.drawString(x, y, line)
        y -= leading

    if truncated and warn_prefix:
        print(f"[carousel][warn] {warn_prefix}{' ' + debug_label if debug_label else ''} truncated")

    return y, truncated, False


def draw_bullets(canvas, items, x, top_y, width, line_height, bullet_gap, style,
                 max_lines_per_item=3, debug_prefix=""):
    y = top_y
    used = 0
    truncated_any = False

    for item in items:
        item = clean_text(item)
        if not item:
            continue

        fit_size, lines, truncated = fit_text(
            item,
            style.fontName,
            style.fontSize,
            max(8, style.fontSize - 4),
            width - bullet_gap,
            line_height * max_lines_per_item,
            leading_ratio=style.leading / float(style.fontSize),
            max_lines=max_lines_per_item,
        )
        leading = int(fit_size * (style.leading / float(style.fontSize)))
        canvas.setFillColor(style.textColor)
        canvas.setFont(style.fontName, fit_size)

        canvas.drawString(x, y, "•")
        line_y = y
        for idx, line in enumerate(lines):
            canvas.drawString(x + bullet_gap, line_y, line)
            line_y -= leading
        y = line_y - int(leading * 0.2)
        used += 1
        truncated_any = truncated_any or truncated

    if truncated_any and debug_prefix:
        print(f"[carousel][warn] {debug_prefix} bullet overflow; text truncated")

    return y, used, truncated_any


def draw_chip(canvas, text, x, y, fill, border, text_color, font_size=10,
              padding_x=12, height=24):
    text = clean_text(text)
    if not text:
        return x

    width = canvas.stringWidth(text, "Helvetica-Bold", font_size) + padding_x * 2
    canvas.setFillColor(fill)
    canvas.setStrokeColor(border)
    canvas.setLineWidth(1)
    canvas.roundRect(x, y - height + 5, width, height, 10, fill=1, stroke=1)
    canvas.setFillColor(text_color)
    canvas.setFont("Helvetica-Bold", font_size)
    canvas.drawString(x + padding_x, y - 13, text)
    return x + width + 10
