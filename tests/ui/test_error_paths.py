"""CB-6, CB-7: failures are shown plainly, and never leak what caused them."""

import logging
from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from app.shared.db import open_database
from app.shared.errors import StorageError
from app.shared.logging import report_unexpected
from app.shared.paths import DATABASE_FILE_NAME
from app.ui.error_dialog import storage_error_box, unexpected_error_box


def test_unopenable_database_shows_error_screen(qtbot: QtBot, tmp_path: Path) -> None:
    unopenable = tmp_path / "data" / DATABASE_FILE_NAME
    unopenable.parent.mkdir(parents=True)
    unopenable.mkdir()

    with pytest.raises(StorageError) as caught:
        open_database(unopenable)

    box = storage_error_box(None, caught.value)
    qtbot.addWidget(box)

    assert box.windowTitle() == StorageError.title
    assert box.text() == StorageError.detail
    assert str(unopenable) not in box.text() + box.informativeText()


def test_unexpected_error_dialog_shows_correlation_id(qtbot: QtBot) -> None:
    box = unexpected_error_box(None, "11111111-2222-3333-4444-555555555555")
    qtbot.addWidget(box)

    assert "11111111-2222-3333-4444-555555555555" in box.informativeText()
    assert box.text(), "a bare id is not a message"


def test_dialog_hides_exception_details(qtbot: QtBot, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        try:
            raise RuntimeError("gizli ayrıntı C:/Users/birisi/notlar.sqlite3")
        except RuntimeError as error:
            correlation_id = report_unexpected(error)

    box = unexpected_error_box(None, correlation_id)
    qtbot.addWidget(box)

    shown = box.windowTitle() + box.text() + box.informativeText()
    assert "gizli ayrıntı" not in shown
    assert "C:/Users/birisi/notlar.sqlite3" not in shown
    assert correlation_id in shown, "the id is the only bridge to the log record"
    # CB-7 promises the same id in both places; assert it here rather than leave it to the
    # transitivity of two separate tests.
    assert caplog.records[-1].correlation_id == correlation_id
