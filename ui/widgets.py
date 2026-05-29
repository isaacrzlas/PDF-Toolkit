"""Reusable PyQt widgets for PDF Toolkit."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.common import get_page_count


class PdfListWidget(QListWidget):
    """List widget that accepts dragged PDF files."""

    filesDropped = pyqtSignal(list)

    def __init__(self, allow_multiple: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.allow_multiple = allow_multiple
        self.setAcceptDrops(True)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
            if allow_multiple
            else QListWidget.SelectionMode.SingleSelection
        )

    def dragEnterEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802 - Qt override
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile() and url.toLocalFile().lower().endswith(".pdf")
        ]
        if paths:
            self.filesDropped.emit(paths if self.allow_multiple else paths[:1])
            event.acceptProposedAction()


class PdfFileList(QWidget):
    """A PDF file list with add/remove/reorder controls and page previews."""

    filesChanged = pyqtSignal(list)

    def __init__(self, title: str, allow_multiple: bool = True) -> None:
        super().__init__()
        self.allow_multiple = allow_multiple
        self.list_widget = PdfListWidget(allow_multiple=allow_multiple)
        self.list_widget.filesDropped.connect(self.add_files)

        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")

        self.add_button = QPushButton("Add PDFs")
        self.remove_button = QPushButton("Remove")
        self.clear_button = QPushButton("Clear")
        self.up_button = QPushButton("Move Up")
        self.down_button = QPushButton("Move Down")

        button_row = QHBoxLayout()
        button_row.addWidget(self.add_button)
        button_row.addWidget(self.remove_button)
        if allow_multiple:
            button_row.addWidget(self.up_button)
            button_row.addWidget(self.down_button)
        button_row.addStretch()
        button_row.addWidget(self.clear_button)

        layout = QVBoxLayout(self)
        layout.addWidget(title_label)
        layout.addWidget(self.list_widget, stretch=1)
        layout.addLayout(button_row)

        self.remove_button.clicked.connect(self.remove_selected)
        self.clear_button.clicked.connect(self.clear)
        self.up_button.clicked.connect(lambda: self.move_selected(-1))
        self.down_button.clicked.connect(lambda: self.move_selected(1))

    def add_files(self, paths: list[str]) -> None:
        if not self.allow_multiple:
            self.clear()

        existing = set(self.files())
        for path in paths:
            pdf_path = Path(path)
            if pdf_path.suffix.lower() != ".pdf" or str(pdf_path) in existing:
                continue
            try:
                page_count = get_page_count(pdf_path)
                label = f"{pdf_path.name}  -  {page_count} page{'s' if page_count != 1 else ''}"
            except Exception:
                label = f"{pdf_path.name}  -  unable to preview"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, str(pdf_path))
            item.setToolTip(str(pdf_path))
            self.list_widget.addItem(item)
            existing.add(str(pdf_path))

        self.filesChanged.emit(self.files())

    def files(self) -> list[str]:
        return [
            self.list_widget.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(self.list_widget.count())
        ]

    def first_file(self) -> str:
        files = self.files()
        return files[0] if files else ""

    def remove_selected(self) -> None:
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))
        self.filesChanged.emit(self.files())

    def clear(self) -> None:
        self.list_widget.clear()
        self.filesChanged.emit([])

    def move_selected(self, direction: int) -> None:
        rows = sorted(
            [self.list_widget.row(item) for item in self.list_widget.selectedItems()],
            reverse=direction > 0,
        )
        for row in rows:
            new_row = row + direction
            if new_row < 0 or new_row >= self.list_widget.count():
                continue
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(new_row, item)
            item.setSelected(True)
        self.filesChanged.emit(self.files())
