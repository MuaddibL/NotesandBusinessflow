"""The single QSS stylesheet, built from the design tokens (docs/conventions.md)."""

from app.ui.tokens import COLORS, RADIUS_PX, SPACING_PX, TYPE_SCALE


def stylesheet() -> str:
    """Every rule reads its values from the token tables — no literals below this line."""
    body = TYPE_SCALE["body-md"]
    label = TYPE_SCALE["label-md"]
    headline = TYPE_SCALE["headline-md"]
    return f"""
QWidget {{
    background-color: {COLORS["background"]};
    color: {COLORS["on-surface"]};
    font-size: {body.size_px}px;
}}

QWidget#sidebar {{
    background-color: {COLORS["surface-container"]};
    border-right: 1px solid {COLORS["outline-variant"]};
}}

QLabel#brand {{
    color: {COLORS["on-surface"]};
    font-size: {headline.size_px}px;
    font-weight: {headline.weight};
    padding: {SPACING_PX["gutter"]}px;
}}

QListWidget#sections {{
    background-color: transparent;
    border: none;
    padding: {SPACING_PX["sm"]}px;
    font-size: {label.size_px}px;
}}

QListWidget#sections::item {{
    padding: {SPACING_PX["md"]}px;
    border-radius: {RADIUS_PX["xl"]}px;
    color: {COLORS["on-surface-variant"]};
}}

QListWidget#sections::item:selected {{
    background-color: {COLORS["surface-container-high"]};
    color: {COLORS["on-surface"]};
}}

QLabel#emptyStateTitle {{
    color: {COLORS["on-surface"]};
    font-size: {TYPE_SCALE["headline-lg"].size_px}px;
    font-weight: {TYPE_SCALE["headline-lg"].weight};
}}

QLabel#emptyStateDetail {{
    color: {COLORS["on-surface-variant"]};
    font-size: {TYPE_SCALE["body-lg"].size_px}px;
}}
"""
