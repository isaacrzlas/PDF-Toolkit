# PDF Toolkit

Made by Isaac Gazula.

PDF Toolkit copyright reserved.

PDF Toolkit is a modern Python 3.11+ desktop app for merging, splitting, extracting, rotating, and optimizing PDF files. Built with PyQt6 and pypdf, it features drag-and-drop support, page previews, recent files, olive green light and dark themes, progress indicators, and a clean tabbed interface.

## Features

- Merge multiple PDFs into one file
- Split a PDF into multiple PDFs by page ranges
- Extract selected pages into a new PDF
- Rotate all pages by 90, 180, or 270 degrees
- Optimize PDFs with pypdf's available stream compression
- Drag-and-drop PDF selection
- Page count previews
- Recent files list
- Olive green light and dark themes
- Remembered last folder
- Keyboard shortcut: `Ctrl+O` to add PDFs to the current tab
- Background workers for long-running operations
- Friendly validation for invalid, encrypted, empty, or missing PDFs
- Plain-language rotation choices such as turn right, turn left, and flip upside down

## Installation

```bash
cd pdf_toolkit
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

## Run

```bash
python main.py
```

## Project Structure

```text
pdf_toolkit/
|-- main.py
|-- ui/
|   |-- main_window.py
|   `-- widgets.py
|-- services/
|   |-- common.py
|   |-- merger.py
|   |-- splitter.py
|   |-- extractor.py
|   |-- rotator.py
|   `-- compressor.py
|-- assets/
|-- requirements.txt
`-- README.md
```

## Architecture

The application separates GUI logic from PDF operations:

- `main.py` creates the Qt application and opens the main window.
- `ui/main_window.py` defines the tabbed interface, toolbar, dialogs, status messages, settings, operation wiring, and footer branding.
- `ui/main_window.py` also runs PDF operations on a worker thread so the interface remains responsive.
- `ui/widgets.py` provides reusable drag-and-drop PDF list widgets with page count previews.
- `services/` contains focused classes for each PDF operation. These modules raise `PdfToolkitError` so the UI can show friendly error messages.

## Compression Notes

The compression tab performs best-effort optimization using pypdf. It compresses page content streams and rewrites the PDF, which can reduce some documents. It does not downsample images, remove embedded fonts, or perform advanced object optimization. For stronger compression, integrate Ghostscript, qpdf, or a dedicated commercial PDF engine.

## Future Upgrades

- Password protection and unlocking
- OCR text extraction
- PDF to Word conversion
- Digital signing
- Batch processing queues
- Image downsampling options
- Per-page rotate, delete, and reorder tools
- Preview thumbnails
