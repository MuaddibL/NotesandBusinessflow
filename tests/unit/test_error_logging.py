"""PB-5: an unexpected error is logged under a correlation id, and carries no user content."""

import logging

import pytest

from app.shared.logging import UNEXPECTED_ERROR_MESSAGE, report_unexpected


def _boom(note: str) -> BaseException:
    try:
        raise RuntimeError("kaboom: " + note)
    except RuntimeError as error:
        return error


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


def test_log_record_excludes_user_content(caplog: pytest.LogCaptureFixture) -> None:
    """The message is a constant with nothing interpolated into it — no channel for user text."""
    with caplog.at_level(logging.ERROR):
        report_unexpected(_boom("gizli not metni"))

    record = caplog.records[-1]
    assert record.getMessage() == UNEXPECTED_ERROR_MESSAGE
    assert not record.args
