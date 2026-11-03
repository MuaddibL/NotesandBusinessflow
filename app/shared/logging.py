"""Unexpected errors: one correlation id, shown to the user and written to the log (PB-5).

The log message is a constant and the helper takes no free-form text, so user content (a note
body, a task title) has no channel into the log — only the id and the traceback
(docs/security.md, Veri ve gizlilik).

The id is only worth quoting if it can be found again, so the logger needs a destination of its
own: without a handler Python falls back to ``logging.lastResort``, which prints the bare message
to stderr and drops the ``extra`` fields — and a windowed build has no stderr at all.
``configure_logging`` is what makes the id on screen and the id in the file the same id (CB-7).
"""

import logging
import uuid
from pathlib import Path

UNEXPECTED_ERROR_MESSAGE = "unexpected error"
LOG_FORMAT = "%(asctime)s %(levelname)s %(correlation_id)s %(message)s"
NO_CORRELATION_ID = "-"

_LOGGER = logging.getLogger("notes_mj")


class _CorrelationIdField(logging.Filter):
    """Guarantees the field, so a record logged without one cannot break the format."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.__dict__.setdefault("correlation_id", NO_CORRELATION_ID)
        return True


def configure_logging(log_file: Path, logger: logging.Logger | None = None) -> logging.Handler:
    """Points the application log at ``log_file`` and returns the handler that owns it."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.addFilter(_CorrelationIdField())
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    target = logger or _LOGGER
    target.setLevel(logging.ERROR)
    target.addHandler(handler)
    return handler


def report_unexpected(error: BaseException, logger: logging.Logger | None = None) -> str:
    """Logs ``error`` under a fresh correlation id and returns that id for the user to quote."""
    correlation_id = str(uuid.uuid4())
    (logger or _LOGGER).error(
        UNEXPECTED_ERROR_MESSAGE,
        exc_info=error,
        extra={"correlation_id": correlation_id},
    )
    return correlation_id
