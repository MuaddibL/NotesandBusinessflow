"""CB-1, CB-6, CB-7 at the entry point: what the application does on startup, not what its
pieces would say if someone called them.

The boxes are recorded rather than shown, and ``QApplication.exec`` is replaced where a test
would otherwise sit in the event loop — the run stays headless and leaves nothing behind.
"""

import logging
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox
from pytestqt.qtbot import QtBot

from app.__main__ import main, unexpected_error_hook
from app.shared.errors import StorageError
from app.shared.paths import DATABASE_FILE_NAME, LOG_FILE_NAME
from app.ui.main_window import MainWindow


@pytest.fixture(autouse=True)
def _restore_log_handlers() -> Iterator[None]:
    """main() attaches a file handler to the application logger; it must not outlive the test."""
    logger = logging.getLogger("notes_mj")
    before = list(logger.handlers)
    try:
        yield
    finally:
        for handler in logger.handlers:
            if handler not in before:
                handler.close()
                logger.removeHandler(handler)


def test_unopenable_database_stops_startup_with_an_error_box(qtbot: QtBot, tmp_path: Path) -> None:
    unopenable = tmp_path / "data" / DATABASE_FILE_NAME
    unopenable.parent.mkdir(parents=True)
    unopenable.mkdir()
    shown: list[QMessageBox] = []

    exit_code = main([], database=unopenable, show_box=shown.append)

    assert exit_code == 1, "a database that cannot be opened must not reach the event loop"
    assert len(shown) == 1
    qtbot.addWidget(shown[0])
    assert shown[0].windowTitle() == StorageError.title
    assert not [w for w in QApplication.topLevelWidgets() if isinstance(w, MainWindow)]


def test_a_healthy_start_opens_the_window_and_installs_the_hook(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    open_windows: list[bool] = []

    def exec_instead_of_blocking(app: QApplication) -> int:
        # The one moment the window is observable: main() holds it only until it returns.
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, MainWindow):
                open_windows.append(widget.isVisible())
                widget.close()  # closing is what releases the connection (CB-8)
        return 0

    monkeypatch.setattr(QApplication, "exec", exec_instead_of_blocking)
    monkeypatch.setattr(sys, "excepthook", sys.__excepthook__)
    shown: list[QMessageBox] = []

    exit_code = main(
        [],
        database=tmp_path / "data" / DATABASE_FILE_NAME,
        log_file=tmp_path / "data" / LOG_FILE_NAME,
        show_box=shown.append,
    )

    assert exit_code == 0
    assert shown == [], "a healthy start shows no error box"
    assert sys.excepthook is not sys.__excepthook__, "an unexpected error must reach the dialog"
    assert open_windows == [True], "exactly one window, open, by the time the loop starts"
    assert (tmp_path / "data" / LOG_FILE_NAME).exists(), "the log is ready before the first error"


def test_the_installed_hook_shows_the_id_it_logged(
    qtbot: QtBot, caplog: pytest.LogCaptureFixture
) -> None:
    shown: list[QMessageBox] = []
    hook = unexpected_error_hook(shown.append)

    with caplog.at_level(logging.ERROR):
        hook(RuntimeError, RuntimeError("kaboom"), None)

    assert len(shown) == 1
    qtbot.addWidget(shown[0])
    logged_id = caplog.records[-1].correlation_id
    assert logged_id in shown[0].informativeText(), "one id, in the dialog and in the log (CB-7)"
