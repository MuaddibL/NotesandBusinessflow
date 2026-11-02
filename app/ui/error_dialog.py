"""What the user sees when something fails (CB-6, CB-7).

Both boxes are built, not shown, so the texts can be asserted without an event loop. Neither
carries an exception message, a SQL statement or a file path (docs/security.md).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QWidget

from app.shared.errors import AppError

UNEXPECTED_TITLE = "Beklenmeyen bir hata oluştu"
UNEXPECTED_TEXT = "İşlem tamamlanamadı. Sorun sürerse aşağıdaki numarayı bildirin."
CORRELATION_LABEL = "Hata numarası: {correlation_id}"


def _box(parent: QWidget | None, title: str, text: str, informative: str) -> QMessageBox:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Critical)
    box.setWindowTitle(title)
    box.setTextFormat(Qt.TextFormat.PlainText)
    box.setText(text)
    box.setInformativeText(informative)
    return box


def unexpected_error_box(parent: QWidget | None, correlation_id: str) -> QMessageBox:
    """CB-7: a general message plus the id that identifies the log record."""
    return _box(
        parent,
        UNEXPECTED_TITLE,
        UNEXPECTED_TEXT,
        CORRELATION_LABEL.format(correlation_id=correlation_id),
    )


def storage_error_box(parent: QWidget | None, error: AppError) -> QMessageBox:
    """CB-6: the data file could not be opened — say so instead of starting up empty."""
    return _box(parent, error.title, error.detail, "")
