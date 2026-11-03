"""Starts the application locally: ``uv run python -m app`` (README).

The paths and the way a box reaches the user are parameters with real defaults, so the startup
path itself can be tested instead of only the pieces it assembles (tests/ui/test_entry_point.py).
"""

import os
import sys
from collections.abc import Callable
from pathlib import Path
from types import TracebackType

from PySide6.QtWidgets import QApplication, QMessageBox

from app.shared.db import open_database
from app.shared.errors import StorageError
from app.shared.logging import configure_logging, report_unexpected
from app.shared.paths import database_path, log_path
from app.ui.error_dialog import storage_error_box, unexpected_error_box
from app.ui.main_window import MainWindow
from app.ui.theme import stylesheet

ShowBox = Callable[[QMessageBox], None]
ExceptHook = Callable[[type[BaseException], BaseException, TracebackType | None], None]


def show_modal(box: QMessageBox) -> None:
    """How a box reaches the user; a test passes its own recorder and keeps the run headless."""
    box.exec()


def unexpected_error_hook(show_box: ShowBox = show_modal) -> ExceptHook:
    """The hook ``sys.excepthook`` gets: log under an id, then show the user that same id (CB-7)."""

    def hook(
        kind: type[BaseException], error: BaseException, traceback: TracebackType | None
    ) -> None:
        correlation_id = report_unexpected(error)
        show_box(unexpected_error_box(None, correlation_id))

    return hook


def main(
    argv: list[str] | None = None,
    *,
    database: Path | None = None,
    log_file: Path | None = None,
    show_box: ShowBox = show_modal,
) -> int:
    # QApplication is a singleton: under pytest-qt one already exists and owns the run.
    existing = QApplication.instance()
    # `argv or sys.argv` would quietly swap an explicitly empty argv for pytest's own.
    arguments = sys.argv if argv is None else argv
    app = existing if isinstance(existing, QApplication) else QApplication(arguments)
    app.setStyleSheet(stylesheet())

    try:
        connection = open_database(database or database_path(os.environ, Path.home()))
    except StorageError as error:
        # Starting up empty would look like a working app with no data (CB-6).
        show_box(storage_error_box(None, error))
        return 1

    try:
        # After the database, not before: opening it is what proves the data directory is there
        # and writable, and a failure to open has its own screen rather than a correlation id.
        configure_logging(log_file or log_path(os.environ, Path.home()))
        sys.excepthook = unexpected_error_hook(show_box)

        window = MainWindow(on_close=connection.close)
        window.show()
    except Exception as error:
        # The excepthook only covers what happens once the loop is running, and nothing is on
        # screen yet: without this the process would exit in silence — in a windowed build
        # without even a stderr for the traceback to land in (CB-6).
        connection.close()
        show_box(unexpected_error_box(None, report_unexpected(error)))
        return 1

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
