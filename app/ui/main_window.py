"""The shell: a window, the section list, and one shared empty state (CB-1, CB-2, CB-8)."""

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.ui.tokens import PRODUCT_NAME, SPACING_PX

# The design's sidebar, minus what the product deliberately does not have: the sync items, and
# the screens that are not part of this spec (docs/design/README.md).
SECTIONS: tuple[str, ...] = (
    "Görev Panosu",
    "Notlarım & Belgeler",
    "Günlük Planlayıcı",
    "Projeler",
    "Etiketler & Arşiv",
)

EMPTY_STATE_TITLE = "{section} henüz hazır değil"
EMPTY_STATE_DETAIL = "Bu bölüm sonraki sürümlerde kullanıma açılacak."


class EmptyState(QWidget):
    """One template for every unbuilt section; only the section name varies (CB-2)."""

    def __init__(self, section: str) -> None:
        super().__init__()
        title = QLabel(EMPTY_STATE_TITLE.format(section=section))
        title.setObjectName("emptyStateTitle")
        detail = QLabel(EMPTY_STATE_DETAIL)
        detail.setObjectName("emptyStateDetail")
        for label in (title, detail):
            # Plain text, never rich text: a section name is not markup (docs/security.md).
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING_PX["sm"])
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(detail)
        layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self, on_close: Callable[[], None] | None = None) -> None:
        super().__init__()
        self._on_close = on_close
        self.setWindowTitle(PRODUCT_NAME)

        self.brand = QLabel(PRODUCT_NAME)
        self.brand.setObjectName("brand")
        # QLabel does not consume '&' as a mnemonic, so the product name keeps its ampersand
        # on screen (CB-1); PlainText makes that explicit rather than incidental.
        self.brand.setTextFormat(Qt.TextFormat.PlainText)

        self.sections = QListWidget()
        self.sections.setObjectName("sections")
        self.sections.addItems(SECTIONS)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        sidebar_layout.addWidget(self.brand)
        sidebar_layout.addWidget(self.sections)

        self.pages = QStackedWidget()
        for section in SECTIONS:
            self.pages.addWidget(EmptyState(section))

        self.sections.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.sections.setCurrentRow(0)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(sidebar, 0)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(central)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Closing the window releases what the window owns (CB-8)."""
        if self._on_close is not None:
            self._on_close()
        super().closeEvent(event)
