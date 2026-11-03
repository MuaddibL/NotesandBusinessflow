"""CB-1, CB-2, CB-8: the shell opens, lists the sections, and lets go when it closes.

Accessibility (spec 0002, User experience) lives here too: the sidebar is reachable with the
keyboard and the item the keyboard is on is visible. The second half is rendered and compared
rather than read off the stylesheet — Qt ignores ``::item:focus`` in a style sheet (measured),
so a rule that merely exists would prove nothing.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QListWidget
from pytestqt.qtbot import QtBot

from app.ui.main_window import EMPTY_STATE_DETAIL, SECTIONS, MainWindow
from app.ui.theme import stylesheet
from app.ui.tokens import PRODUCT_NAME


def _pixels(widget: QListWidget) -> bytes:
    return bytes(widget.grab().toImage().constBits())


def test_window_title_is_product_name_with_ampersand(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == "Notes&MJ"
    assert window.brand.text() == "Notes&MJ"
    # Plain text is what keeps the '&' on screen: a mnemonic-aware widget would swallow it.
    assert window.brand.textFormat() == Qt.TextFormat.PlainText


def test_sidebar_lists_the_five_sections(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    listed = [window.sections.item(row).text() for row in range(window.sections.count())]

    assert listed == [
        "Görev Panosu",
        "Notlarım & Belgeler",
        "Günlük Planlayıcı",
        "Projeler",
        "Etiketler & Arşiv",
    ]
    assert not any("enkron" in name for name in listed), "sync is out of scope (docs/design)"


def test_unbuilt_section_shows_shared_empty_state(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    for row, section in enumerate(SECTIONS):
        window.sections.setCurrentRow(row)
        page = window.pages.currentWidget()

        title = page.findChild(QLabel, "emptyStateTitle")
        detail = page.findChild(QLabel, "emptyStateDetail")

        assert title is not None and detail is not None
        assert title.text() == f"{section} henüz hazır değil"
        # One template, only the section name varies.
        assert detail.text() == EMPTY_STATE_DETAIL


def test_closing_window_leaves_nothing_running(qtbot: QtBot) -> None:
    released: list[str] = []
    window = MainWindow(on_close=lambda: released.append("connection"))
    qtbot.addWidget(window)
    window.show()

    window.close()

    assert released == ["connection"], "what the window owns is released when it closes"
    assert not window.isVisible()


def test_sidebar_takes_keyboard_focus_on_open(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    assert window.sections.focusPolicy() & Qt.FocusPolicy.TabFocus, "Tab must reach the sidebar"
    # focusWidget, not hasFocus: offscreen the window is never activated, but the widget that
    # holds the focus inside it is what decides where the first key press lands.
    assert window.focusWidget() is window.sections, "the arrow keys work without clicking first"


def test_arrow_keys_move_through_the_sections(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    qtbot.keyClick(window.sections, Qt.Key.Key_Down)

    assert window.sections.currentRow() == 1
    assert window.pages.currentIndex() == 1, "the page follows the keyboard, not only the mouse"

    qtbot.keyClick(window.sections, Qt.Key.Key_Up)

    assert window.sections.currentRow() == 0
    assert window.pages.currentIndex() == 0


def test_the_item_the_keyboard_is_on_looks_different(qtbot: QtBot) -> None:
    """Rendered and compared: moving the keyboard must change what the sidebar looks like."""
    window = MainWindow()
    window.setStyleSheet(stylesheet())
    qtbot.addWidget(window)
    window.show()

    window.sections.setCurrentRow(0)
    on_first = _pixels(window.sections)
    window.sections.setCurrentRow(1)
    on_second = _pixels(window.sections)

    assert on_first != on_second, "the current section is not visually distinguishable"


def test_product_name_is_the_one_in_the_tokens(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == PRODUCT_NAME
