"""PB-5: an unexpected error is logged under a correlation id, and carries no user content."""

import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from app.shared.logging import (
    UNEXPECTED_ERROR_MESSAGE,
    configure_logging,
    report_unexpected,
)


def _boom(note: str) -> BaseException:
    try:
        raise RuntimeError("kaboom: " + note)
    except RuntimeError as error:
        return error


@pytest.fixture
def log_destination(tmp_path: Path) -> Iterator[tuple[logging.Logger, Path]]:
    """A logger of this test's own, with a real file handler, torn down afterwards."""
    path = tmp_path / "data" / "notes-mj.log"
    logger = logging.getLogger("notes_mj_test_destination")
    logger.propagate = False
    handler = configure_logging(path, logger)
    try:
        yield logger, path
    finally:
        handler.close()
        logger.removeHandler(handler)


def test_error_is_logged_with_correlation_id(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        correlation_id = report_unexpected(_boom("x"))

    record = caplog.records[-1]
    assert record.correlation_id == correlation_id
    assert record.exc_info is not None, "the detail belongs in the log, not on screen"


def test_two_errors_get_different_ids(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        first = report_unexpected(_boom("x"))
        second = report_unexpected(_boom("y"))

    assert first != second


def test_correlation_id_is_written_to_the_log_file(
    log_destination: tuple[logging.Logger, Path],
) -> None:
    """caplog proves the attribute; only a configured handler proves the id can be found again."""
    logger, path = log_destination

    correlation_id = report_unexpected(_boom("x"), logger)

    written = path.read_text(encoding="utf-8")
    assert correlation_id in written
    assert UNEXPECTED_ERROR_MESSAGE in written
    assert "Traceback" in written, "the detail belongs in the file, not on screen"


def test_a_record_without_an_id_still_formats(
    log_destination: tuple[logging.Logger, Path],
) -> None:
    """The format names the field, so an unrelated record must not break the log."""
    logger, path = log_destination

    logger.error("something else entirely")

    assert "something else entirely" in path.read_text(encoding="utf-8")


def test_log_message_has_no_interpolated_content(caplog: pytest.LogCaptureFixture) -> None:
    """The message is a constant with nothing interpolated into it — no channel for user text.

    Deliberately not named "excludes user content": PB-5 exempts the traceback, and the exception
    text does reach the record through ``exc_info``. What this pins is the only channel the spec
    does close — the message itself.
    """
    with caplog.at_level(logging.ERROR):
        report_unexpected(_boom("gizli not metni"))

    record = caplog.records[-1]
    assert record.getMessage() == UNEXPECTED_ERROR_MESSAGE
    assert not record.args
