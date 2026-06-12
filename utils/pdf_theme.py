from dataclasses import dataclass

from reportlab.lib.colors import Color, HexColor


PAGE_WIDTH = 1080
PAGE_HEIGHT = 1350

MARGIN_X = 88
MARGIN_TOP = 94
MARGIN_BOTTOM = 84

BACKGROUND = HexColor("#070A13")
SURFACE = HexColor("#0E1424")
SURFACE_ALT = HexColor("#111A2F")
BORDER = HexColor("#202B43")
BORDER_SOFT = Color(0.25, 0.31, 0.43, alpha=0.45)
TEXT = HexColor("#E8EEF9")
MUTED = HexColor("#94A3B8")
ACCENT = HexColor("#7C3AED")
ACCENT_2 = HexColor("#06B6D4")
ACCENT_3 = HexColor("#10B981")
ACCENT_4 = HexColor("#F59E0B")
DANGER = HexColor("#EF4444")


CATEGORY_ACCENTS = {
    "Agentic AI": ACCENT,
    "RAG / Infrastructure": ACCENT_2,
    "Developer AI": ACCENT_3,
    "Enterprise AI": ACCENT_4,
    "AI Update": MUTED,
}


@dataclass(frozen=True)
class SlideTheme:
    background: Color = BACKGROUND
    surface: Color = SURFACE
    surface_alt: Color = SURFACE_ALT
    border: Color = BORDER
    text: Color = TEXT
    muted: Color = MUTED
    accent: Color = ACCENT
    accent_2: Color = ACCENT_2
    accent_3: Color = ACCENT_3
    accent_4: Color = ACCENT_4
    danger: Color = DANGER


DEFAULT_THEME = SlideTheme()


def slugify(value):
    import re

    value = str(value or "").lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "theme"


def category_accent(category):
    return CATEGORY_ACCENTS.get(category, ACCENT)


def chip_fill(category):
    accent = category_accent(category)
    return Color(accent.red, accent.green, accent.blue, alpha=0.12)


def chip_border(category):
    accent = category_accent(category)
    return Color(accent.red, accent.green, accent.blue, alpha=0.5)


def subtle_fill(color, alpha=0.10):
    return Color(color.red, color.green, color.blue, alpha=alpha)
