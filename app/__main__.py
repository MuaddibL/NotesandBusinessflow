"""Starts the application locally: ``uv run python -m app`` (README)."""

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.shared.db import open_database
from app.shared.errors import StorageError
from app.shared.logging import configure_logging, report_unexpected
from app.shared.paths import database_path, log_path
from app.ui.error_dialog import storage_error_box, unexpected_error_box
from app.ui.main_window import MainWindow
from app.ui.theme import stylesheet


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet())

    try:
        connection = open_database(database_path(os.environ, Path.home()))
    except StorageError as error:
        # Starting up empty would look like a working app with no data (CB-6).
        storage_error_box(None, error).exec()
        return 1

    # After the database, not before: opening it is what proves the data directory is there and
    # writable, and a failure to open has its own screen rather than a correlation id (CB-6).
    configure_logging(log_path(os.environ, Path.home()))

    def _excepthook(kind: type[BaseException], error: BaseException, traceback: object) -> None:
        correlation_id = report_unexpected(error)
        unexpected_error_box(None, correlation_id).exec()

    sys.excepthook = _excepthook

    window = MainWindow(on_close=connection.close)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
