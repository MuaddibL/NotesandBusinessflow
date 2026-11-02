"""CB-1, CB-2, CB-8: the shell opens, lists the sections, and lets go when it closes."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from app.ui.main_window import EMPTY_STATE_DETAIL, SECTIONS, MainWindow
from app.ui.tokens import PRODUCT_NAME


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


def test_product_name_is_the_one_in_the_tokens(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == PRODUCT_NAME
