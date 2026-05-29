"""Main PyQt6 window for PDF Toolkit."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PyQt6.QtCore import QObject, QSettings, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QStyle,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from services.common import PdfToolkitError, get_page_count
from services.compressor import PdfCompressorService
from services.extractor import PdfExtractorService
from services.merger import PdfMergerService
from services.rotator import PdfRotatorService
from services.splitter import PdfSplitterService
from ui.widgets import PdfFileList

ProgressCallback = Callable[[int, str], None]
Operation = Callable[[ProgressCallback], object]
SuccessHandler = Callable[[object], str]


class OperationWorker(QObject):
    """Runs a PDF operation away from the UI thread."""

    progress = pyqtSignal(int, str)
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, operation: Operation) -> None:
        super().__init__()
        self.operation = operation

    def run(self) -> None:
        try:
            result = self.operation(self.progress.emit)
            self.succeeded.emit(result)
        except PdfToolkitError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"Unexpected error: {exc}")
        finally:
            self.finished.emit()


LIGHT_STYLE = """
QMainWindow, QWidget { background: #f6f8f1; color: #1f2a1f; font-size: 13px; }
QTabWidget::pane { border: 1px solid #cbd8bd; background: #ffffff; }
QTabBar::tab { padding: 10px 16px; border: 1px solid #cbd8bd; background: #e8efde; color: #33412d; }
QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; color: #1f3a20; font-weight: 600; }
QListWidget, QLineEdit, QPlainTextEdit, QComboBox {
    background: #ffffff; border: 1px solid #bacaa9; border-radius: 6px; padding: 6px;
}
QPushButton { background: #5f7f3a; color: white; border: 0; border-radius: 6px; padding: 8px 12px; font-weight: 600; }
QPushButton:hover { background: #4f6f2f; }
QPushButton:disabled { background: #9ba88d; }
QToolBar { background: #ffffff; border-bottom: 1px solid #cbd8bd; spacing: 8px; padding: 6px; }
QToolButton { color: #26361f; padding: 7px 9px; border-radius: 6px; }
QToolButton:hover { background: #e8efde; }
QProgressBar { border: 1px solid #bacaa9; border-radius: 5px; text-align: center; background: #ffffff; }
QProgressBar::chunk { background: #7fa650; border-radius: 5px; }
QLabel#SectionTitle { font-weight: 700; font-size: 15px; }
QLabel#FooterText { color: #5c6a50; padding: 8px 4px; }
QLabel#HelperText { color: #5c6a50; padding: 2px 0 6px 0; }
"""

DARK_STYLE = """
QMainWindow, QWidget { background: #11180f; color: #ecf2e5; font-size: 13px; }
QTabWidget::pane { border: 1px solid #3d4a34; background: #172114; }
QTabBar::tab { padding: 10px 16px; border: 1px solid #3d4a34; background: #202b1b; color: #d3dec7; }
QTabBar::tab:selected { background: #172114; border-bottom-color: #172114; color: #ffffff; font-weight: 600; }
QListWidget, QLineEdit, QPlainTextEdit, QComboBox {
    background: #0c120b; border: 1px solid #536347; border-radius: 6px; padding: 6px; color: #f7fbf1;
}
QPushButton { background: #789d4c; color: #071006; border: 0; border-radius: 6px; padding: 8px 12px; font-weight: 700; }
QPushButton:hover { background: #8fb85b; }
QPushButton:disabled { background: #46523d; color: #aeb9a6; }
QToolBar { background: #0c120b; border-bottom: 1px solid #3d4a34; spacing: 8px; padding: 6px; }
QToolButton { color: #ecf2e5; padding: 7px 9px; border-radius: 6px; }
QToolButton:hover { background: #202b1b; }
QProgressBar { border: 1px solid #536347; border-radius: 5px; text-align: center; background: #0c120b; color: #ffffff; }
QProgressBar::chunk { background: #8fb85b; border-radius: 5px; }
QLabel#SectionTitle { font-weight: 700; font-size: 15px; }
QLabel#FooterText { color: #b7c5ad; padding: 8px 4px; }
QLabel#HelperText { color: #b7c5ad; padding: 2px 0 6px 0; }
"""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings()
        self.recent_files: list[str] = self.settings.value("recentFiles", [], list)
        self.last_folder = self.settings.value("lastFolder", str(Path.home()), str)

        self.merger = PdfMergerService()
        self.splitter = PdfSplitterService()
        self.extractor = PdfExtractorService()
        self.rotator = PdfRotatorService()
        self.compressor = PdfCompressorService()
        self.worker_thread: QThread | None = None
        self.worker: OperationWorker | None = None

        self.setWindowTitle("PDF Toolkit")
        self.resize(980, 680)
        self._build_toolbar()
        self._build_tabs()
        self._build_status_bar()
        self._apply_theme(self.settings.value("darkMode", False, bool))

    def _build_toolbar(self) -> None:
        self.toolbar = QToolBar("Main")
        self.toolbar.setMovable(False)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(self.toolbar)

        style = self.style()
        open_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton), "Open PDF", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_pdf_for_current_tab)
        self.toolbar.addAction(open_action)

        self.recent_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "Recent Files", self)
        self.recent_action.triggered.connect(self._show_recent_files)
        self.toolbar.addAction(self.recent_action)

        self.toolbar.addSeparator()
        self.dark_action = QAction(style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), "Switch to Dark Mode", self)
        self.dark_action.setCheckable(True)
        self.dark_action.setToolTip("Switch between light mode and dark mode")
        self.dark_action.triggered.connect(self._apply_theme)
        self.toolbar.addAction(self.dark_action)

    def _build_tabs(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._merge_tab(), "Merge PDFs")
        self.tabs.addTab(self._split_tab(), "Split PDF")
        self.tabs.addTab(self._extract_tab(), "Extract Pages")
        self.tabs.addTab(self._rotate_tab(), "Rotate Pages")
        self.tabs.addTab(self._compress_tab(), "Compress PDF")

        footer = QLabel("Made by Isaac Gazula | PDF Toolkit copyright reserved")
        footer.setObjectName("FooterText")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.tabs, stretch=1)
        layout.addWidget(footer)
        self.setCentralWidget(central)

    def _build_status_bar(self) -> None:
        status = QStatusBar()
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(260)
        self.progress.setValue(0)
        status.addPermanentWidget(self.progress)
        self.setStatusBar(status)
        self.statusBar().showMessage("Ready")

    def _merge_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.merge_files = PdfFileList("Selected PDFs", allow_multiple=True)
        self.merge_files.add_button.clicked.connect(lambda: self._choose_pdfs(self.merge_files))
        run_button = QPushButton("Merge PDFs")
        run_button.clicked.connect(self._run_merge)
        layout.addWidget(self.merge_files)
        layout.addWidget(run_button, alignment=Qt.AlignmentFlag.AlignRight)
        return tab

    def _split_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.split_file = PdfFileList("Source PDF", allow_multiple=False)
        self.split_file.add_button.clicked.connect(lambda: self._choose_pdfs(self.split_file))
        self.split_ranges = QPlainTextEdit()
        self.split_ranges.setPlaceholderText("One output per line, for example:\n1-5\n6-10\n11-14")
        run_button = QPushButton("Split PDF")
        run_button.clicked.connect(self._run_split)
        layout.addWidget(self.split_file)
        layout.addWidget(QLabel("Page ranges"))
        layout.addWidget(self.split_ranges)
        layout.addWidget(run_button, alignment=Qt.AlignmentFlag.AlignRight)
        return tab

    def _extract_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.extract_file = PdfFileList("Source PDF", allow_multiple=False)
        self.extract_file.add_button.clicked.connect(lambda: self._choose_pdfs(self.extract_file))
        self.extract_pages = QLineEdit()
        self.extract_pages.setPlaceholderText("Example: 1, 3, 5-8")
        run_button = QPushButton("Extract Pages")
        run_button.clicked.connect(self._run_extract)
        layout.addWidget(self.extract_file)
        layout.addWidget(QLabel("Pages to extract"))
        layout.addWidget(self.extract_pages)
        layout.addWidget(run_button, alignment=Qt.AlignmentFlag.AlignRight)
        return tab

    def _rotate_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.rotate_file = PdfFileList("Source PDF", allow_multiple=False)
        self.rotate_file.add_button.clicked.connect(lambda: self._choose_pdfs(self.rotate_file))
        self.rotation_degrees = QComboBox()
        self.rotation_degrees.addItem("Turn right - 90 degrees clockwise", 90)
        self.rotation_degrees.addItem("Flip upside down - 180 degrees", 180)
        self.rotation_degrees.addItem("Turn left - 90 degrees counterclockwise", 270)
        helper = QLabel("Choose how the pages should look after rotation.")
        helper.setObjectName("HelperText")
        run_button = QPushButton("Rotate PDF")
        run_button.clicked.connect(self._run_rotate)
        layout.addWidget(self.rotate_file)
        layout.addWidget(QLabel("Rotation direction"))
        layout.addWidget(helper)
        layout.addWidget(self.rotation_degrees)
        layout.addWidget(run_button, alignment=Qt.AlignmentFlag.AlignRight)
        return tab

    def _compress_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.compress_file = PdfFileList("Source PDF", allow_multiple=False)
        self.compress_file.add_button.clicked.connect(lambda: self._choose_pdfs(self.compress_file))
        note = QLabel(PdfCompressorService.limitation_note)
        note.setWordWrap(True)
        run_button = QPushButton("Optimize PDF")
        run_button.clicked.connect(self._run_compress)
        layout.addWidget(self.compress_file)
        layout.addWidget(note)
        layout.addWidget(run_button, alignment=Qt.AlignmentFlag.AlignRight)
        return tab

    def _choose_pdfs(self, target: PdfFileList) -> None:
        mode = QFileDialog.FileMode.ExistingFiles if target.allow_multiple else QFileDialog.FileMode.ExistingFile
        dialog = QFileDialog(self, "Select PDF files", self.last_folder, "PDF files (*.pdf)")
        dialog.setFileMode(mode)
        if dialog.exec():
            paths = dialog.selectedFiles()
            target.add_files(paths)
            self._remember_folder(paths[0])
            for path in paths:
                self._add_recent_file(path)

    def _save_pdf_path(self, title: str, suggested_name: str) -> str:
        start = str(Path(self.last_folder) / suggested_name)
        path, _ = QFileDialog.getSaveFileName(self, title, start, "PDF files (*.pdf)")
        if path and not path.lower().endswith(".pdf"):
            path += ".pdf"
        if path:
            self._remember_folder(path)
        return path

    def _choose_folder(self, title: str) -> str:
        folder = QFileDialog.getExistingDirectory(self, title, self.last_folder)
        if folder:
            self._remember_folder(folder)
        return folder

    def _run_operation(
        self,
        operation: Operation,
        success_handler: SuccessHandler | str,
    ) -> None:
        if self.worker_thread is not None:
            QMessageBox.information(self, "PDF Toolkit", "An operation is already running.")
            return

        self.progress.setValue(0)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.centralWidget().setEnabled(False)
        self.toolbar.setEnabled(False)
        self.statusBar().showMessage("Working...")

        self.worker_thread = QThread(self)
        self.worker = OperationWorker(operation)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._progress)
        self.worker.succeeded.connect(lambda result: self._operation_success(result, success_handler))
        self.worker.failed.connect(self._operation_failed)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self._operation_finished)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def _operation_success(self, result: object, success_handler: SuccessHandler | str) -> None:
        message = success_handler(result) if callable(success_handler) else success_handler
        self.progress.setValue(100)
        self.statusBar().showMessage(message, 7000)
        QMessageBox.information(self, "Success", message)
        self.progress.setValue(0)

    def _operation_failed(self, message: str) -> None:
        self.statusBar().showMessage(message, 7000)
        QMessageBox.warning(self, "PDF Toolkit", message)
        self.progress.setValue(0)

    def _operation_finished(self) -> None:
        self.centralWidget().setEnabled(True)
        self.toolbar.setEnabled(True)
        QApplication.restoreOverrideCursor()
        self.worker_thread = None
        self.worker = None

    def _progress(self, value: int, message: str) -> None:
        self.progress.setValue(value)
        self.statusBar().showMessage(message)

    def _run_merge(self) -> None:
        files = self.merge_files.files()
        output = self._save_pdf_path("Save merged PDF", "merged.pdf")
        if not output:
            return
        self._run_operation(lambda progress: self.merger.merge(files, output, progress), "PDFs merged successfully.")

    def _run_split(self) -> None:
        source = self.split_file.first_file()
        ranges = [line.strip() for line in self.split_ranges.toPlainText().splitlines() if line.strip()]
        folder = self._choose_folder("Choose output folder")
        if not folder:
            return
        self._run_operation(
            lambda progress: self.splitter.split(source, ranges, folder, progress),
            lambda result: f"PDF split successfully. Created {len(result)} file(s).",
        )

    def _run_extract(self) -> None:
        source = self.extract_file.first_file()
        output = self._save_pdf_path("Save extracted PDF", "extracted_pages.pdf")
        if not output:
            return
        self._run_operation(
            lambda progress: self.extractor.extract(source, self.extract_pages.text(), output, progress),
            "Pages extracted successfully.",
        )

    def _run_rotate(self) -> None:
        source = self.rotate_file.first_file()
        output = self._save_pdf_path("Save rotated PDF", "rotated.pdf")
        if not output:
            return
        degrees = int(self.rotation_degrees.currentData())
        self._run_operation(lambda progress: self.rotator.rotate(source, degrees, output, progress), "PDF rotated successfully.")

    def _run_compress(self) -> None:
        source = self.compress_file.first_file()
        output = self._save_pdf_path("Save optimized PDF", "optimized.pdf")
        if not output:
            return

        def operation(progress: ProgressCallback) -> tuple[int, int]:
            return self.compressor.compress(source, output, progress)

        def success(result: object) -> str:
            before, after = result
            delta = before - after
            if delta > 0:
                return f"PDF optimization complete. Saved {delta / 1024:.1f} KB."
            return "Optimized copy created. File size did not shrink with pypdf-only compression."

        self._run_operation(operation, success)

    def _open_pdf_for_current_tab(self) -> None:
        current = self.tabs.currentIndex()
        targets = [self.merge_files, self.split_file, self.extract_file, self.rotate_file, self.compress_file]
        self._choose_pdfs(targets[current])

    def _show_recent_files(self) -> None:
        if not self.recent_files:
            QMessageBox.information(self, "Recent Files", "No recent files yet.")
            return
        lines = []
        for path in self.recent_files[:10]:
            try:
                lines.append(f"{Path(path).name} - {get_page_count(path)} pages\n{path}")
            except Exception:
                lines.append(path)
        QMessageBox.information(self, "Recent Files", "\n\n".join(lines))

    def _add_recent_file(self, path: str) -> None:
        normalized = str(Path(path))
        self.recent_files = [normalized] + [item for item in self.recent_files if item != normalized]
        self.recent_files = self.recent_files[:10]
        self.settings.setValue("recentFiles", self.recent_files)

    def _remember_folder(self, path: str) -> None:
        folder = Path(path)
        self.last_folder = str(folder if folder.is_dir() else folder.parent)
        self.settings.setValue("lastFolder", self.last_folder)

    def _apply_theme(self, dark: bool) -> None:
        self.dark_action.setChecked(dark)
        self.dark_action.setText("Switch to Light Mode" if dark else "Switch to Dark Mode")
        self.settings.setValue("darkMode", dark)
        self.setStyleSheet(DARK_STYLE if dark else LIGHT_STYLE)
