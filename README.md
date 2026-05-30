# PDF Toolkit

A modern desktop utility for managing and editing PDF files.

PDF Toolkit helps users merge documents, split PDFs by page ranges, extract selected pages, rotate documents with plain-language controls, and create optimized PDF copies. The app uses a clean olive-green interface with drag-and-drop support, page count previews, progress indicators, recent files, and light/dark mode.

## Features

- Merge multiple PDFs into one file
- Split PDFs by page ranges
- Extract selected pages
- Rotate PDFs with friendly turn-left, turn-right, and flip options
- Basic PDF optimization
- Drag-and-drop PDF selection
- PDF page count previews
- Recent files list
- Olive green light and dark mode
- Remembered last folder
- Progress indicators and status messages
- Background workers for long-running operations
- Friendly validation for invalid, encrypted, empty, or missing PDFs

## Author

Isaac Gazula

## Installation

1. Install Python 3.11 or newer.
2. Install the dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the application:

```powershell
python main.py
```

If you prefer a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Usage

1. Open the application.
2. Choose a tab for the PDF task you want to perform.
3. Click `Add PDFs` or drag PDF files into the file list.
4. Review the page count preview for selected files.
5. Enter page ranges when splitting or extracting pages.
6. Choose a friendly rotation option when rotating PDFs.
7. Select an output file or folder when prompted.
8. Wait for the progress bar to complete, then confirm the success message.

## Project Architecture

- `main.py` starts the PyQt6 application.
- `ui/main_window.py` builds the main tabbed desktop interface, toolbar, theme toggle, progress handling, operation workers, and footer branding.
- `ui/widgets.py` contains reusable PDF file list widgets with drag-and-drop support and page count previews.
- `services/common.py` contains shared validation, page counting, PDF reading, and page-range parsing helpers.
- `services/merger.py` merges multiple PDFs into one output file.
- `services/splitter.py` splits one PDF into multiple files by page ranges.
- `services/extractor.py` extracts selected pages into a new PDF.
- `services/rotator.py` rotates PDF pages.
- `services/compressor.py` performs best-effort PDF optimization using pypdf.

## Compression Notes

PDF Toolkit uses pypdf's available stream compression and PDF rewriting features. This can reduce some PDFs, but it does not downsample images, remove embedded fonts, or perform advanced object optimization. For stronger compression, a future version could integrate Ghostscript, qpdf, or another dedicated PDF engine.

## Future Upgrades

- PDF password protection
- OCR text extraction
- PDF to Word conversion
- PDF signing
- Batch processing queues
- Image downsampling options
- Per-page rotate, delete, and reorder tools
- Preview thumbnails

## Branding

Application: PDF Toolkit  
Created by: Isaac Gazula  
Version: 1.0

© PDF Toolkit. All Rights Reserved.
