"""Design tokens, lifted from the Material 3 set in the design (docs/design/README.md).

Every colour, size and spacing value the interface uses comes from here — widgets never carry a
literal colour or pixel value (docs/conventions.md, UI conventions). Fonts are the system defaults
for now; embedding Inter and the icon set belongs to the first screen's spec (plan 0002, R-3).
"""

from dataclasses import dataclass

PRODUCT_NAME = "Notes&MJ"

COLORS: dict[str, str] = {
    "background": "#0b1326",
    "surface": "#0b1326",
    "surface-container-lowest": "#060e20",
    "surface-container-low": "#131b2e",
    "surface-container": "#171f33",
    "surface-container-high": "#222a3d",
    "surface-container-highest": "#2d3449",
    "surface-variant": "#2d3449",
    "on-surface": "#dae2fd",
    "on-surface-variant": "#c7c4d8",
    "primary": "#c3c0ff",
    "on-primary": "#1d00a5",
    "primary-container": "#4f46e5",
    "on-primary-container": "#dad7ff",
    "secondary": "#4cd7f6",
    "outline": "#918fa1",
    "outline-variant": "#464555",
    "error": "#ffb4ab",
    "error-container": "#93000a",
    "on-error-container": "#ffdad6",
}


@dataclass(frozen=True)
class TypeStyle:
    size_px: int
    line_height_px: int
    weight: int


TYPE_SCALE: dict[str, TypeStyle] = {
    "display": TypeStyle(32, 40, 600),
    "headline-lg": TypeStyle(24, 32, 600),
    "headline-md": TypeStyle(18, 24, 600),
    "headline-sm": TypeStyle(15, 20, 600),
    "body-lg": TypeStyle(15, 24, 400),
    "body-md": TypeStyle(13, 20, 400),
    "body-sm": TypeStyle(12, 16, 400),
    "label-md": TypeStyle(12, 16, 500),
    "label-sm": TypeStyle(11, 14, 500),
}

SPACING_PX: dict[str, int] = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "gutter": 16,
    "lg": 20,
    "margin": 24,
    "xl": 32,
}

RADIUS_PX: dict[str, int] = {"default": 2, "lg": 4, "xl": 8, "full": 12}

# The foreground/background token pairs the interface puts together, plus the ones the error
# surfaces are reserved for. The accessibility criterion is proven over exactly this list
# (tests/unit/test_theme_contrast.py). A second test holds one direction of the other way round:
# every *colour* the stylesheet draws appears here or in DECORATIVE_COLORS. It does not check
# pairings — a new combination of two colours that are already in this list passes it unseen
# (error on primary-container would be 3.70:1), so adding a pairing to the stylesheet still means
# adding it here by hand.
TEXT_PAIRS: tuple[tuple[str, str], ...] = (
    ("on-surface", "background"),
    ("on-surface", "surface"),
    ("on-surface", "surface-container"),
    ("on-surface", "surface-container-high"),
    ("on-surface-variant", "background"),
    ("on-surface-variant", "surface"),
    ("on-surface-variant", "surface-container"),
    ("on-surface-variant", "surface-container-high"),
    ("on-primary-container", "primary-container"),
    ("error", "surface"),
    ("on-error-container", "error-container"),
)

# Colours that carry no text: a contrast ratio says nothing about them, but they still have to be
# declared, so that the audit above cannot be dodged by calling a text colour decorative.
DECORATIVE_COLORS: tuple[str, ...] = ("outline-variant",)
