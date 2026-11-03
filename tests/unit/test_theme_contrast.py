"""Accessibility (spec 0002, User experience): every text/surface pair reaches WCAG AA.

The tokens are fixed values, so the ratio is computed rather than screenshotted — cheap,
repeatable, and it catches a palette change by itself (plan 0002, G8).
"""

import re

import pytest

from app.ui.theme import stylesheet
from app.ui.tokens import COLORS, DECORATIVE_COLORS, TEXT_PAIRS

MINIMUM_RATIO = 4.5
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}")


def _linearize(channel: int) -> float:
    value = channel / 255
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def _relative_luminance(color: str) -> float:
    red, green, blue = (int(color[index : index + 2], 16) for index in (1, 3, 5))
    return 0.2126 * _linearize(red) + 0.7152 * _linearize(green) + 0.0722 * _linearize(blue)


def contrast_ratio(foreground: str, background: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(foreground), _relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


@pytest.mark.parametrize(("foreground", "background"), TEXT_PAIRS)
def test_every_text_surface_pair_meets_wcag_aa(foreground: str, background: str) -> None:
    ratio = contrast_ratio(COLORS[foreground], COLORS[background])

    assert ratio >= MINIMUM_RATIO, f"{foreground} on {background} is only {ratio:.2f}:1"


def test_every_colour_the_stylesheet_draws_is_audited() -> None:
    """Otherwise the audit is a list someone has to remember to update, and silently drifts.

    Compared by value, not by token name: two tokens may share a hex today, and contrast is a
    property of the value either way.
    """
    audited = {COLORS[token] for pair in TEXT_PAIRS for token in pair}
    audited |= {COLORS[token] for token in DECORATIVE_COLORS}

    drawn = set(HEX_COLOR.findall(stylesheet()))

    unaudited = sorted(drawn - audited)
    assert not unaudited, f"colour(s) drawn but never checked: {unaudited}"


def test_the_formula_matches_known_values() -> None:
    """Without this, a broken formula would pass every pair above."""
    assert contrast_ratio("#ffffff", "#000000") == pytest.approx(21.0)
    assert contrast_ratio("#ffffff", "#ffffff") == pytest.approx(1.0)
