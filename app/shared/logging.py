"""Unexpected errors: one correlation id, shown to the user and written to the log (PB-5).

The log message is a constant and the helper takes no free-form text, so user content (a note
body, a task title) has no channel into the log — only the id and the traceback
(docs/security.md, Veri ve gizlilik).
"""

import logging
import uuid

UNEXPECTED_ERROR_MESSAGE = "unexpected error"

_LOGGER = logging.getLogger("notes_mj")


def report_unexpected(error: BaseException, logger: logging.Logger | None = None) -> str:
    """Logs ``error`` under a fresh correlation id and returns that id for the user to quote."""
    correlation_id = str(uuid.uuid4())
    (logger or _LOGGER).error(
        UNEXPECTED_ERROR_MESSAGE,
        exc_info=error,
        extra={"correlation_id": correlation_id},
    )
    return correlation_id
