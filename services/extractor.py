"""PDF page extraction service."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from pypdf import PdfWriter

from services.common import PdfToolkitError, ensure_pdf, parse_page_ranges, read_pdf

ProgressCallback = Callable[[int, str], None]


class PdfExtractorService:
    def extract(
        self,
        input_path: str | Path,
        page_spec: str,
        output_path: str | Path,
        progress: ProgressCallback | None = None,
    ) -> None:
        try:
            source = ensure_pdf(input_path)
            reader = read_pdf(source)
            pages = parse_page_ranges(page_spec, len(reader.pages))
            writer = PdfWriter()

            for index, page_index in enumerate(pages, start=1):
                writer.add_page(reader.pages[page_index])
                if progress:
                    progress(round(index / len(pages) * 90), f"Added page {page_index + 1}")

            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("wb") as handle:
                writer.write(handle)
            if progress:
                progress(100, f"Extracted PDF saved to {output.name}")
        except Exception as exc:
            if isinstance(exc, PdfToolkitError):
                raise
            raise PdfToolkitError(f"Extraction failed: {exc}") from exc
