"""PDF page rotation service."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from pypdf import PdfWriter

from services.common import PdfToolkitError, ensure_pdf, read_pdf

ProgressCallback = Callable[[int, str], None]


class PdfRotatorService:
    def rotate(
        self,
        input_path: str | Path,
        degrees: int,
        output_path: str | Path,
        progress: ProgressCallback | None = None,
    ) -> None:
        if degrees not in {90, 180, 270}:
            raise PdfToolkitError("Rotation must be 90, 180, or 270 degrees.")

        try:
            source = ensure_pdf(input_path)
            reader = read_pdf(source)
            writer = PdfWriter()

            for index, page in enumerate(reader.pages, start=1):
                writer.add_page(page.rotate(degrees))
                if progress:
                    progress(round(index / len(reader.pages) * 90), f"Rotated page {index}")

            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("wb") as handle:
                writer.write(handle)
            if progress:
                progress(100, f"Rotated PDF saved to {output.name}")
        except Exception as exc:
            if isinstance(exc, PdfToolkitError):
                raise
            raise PdfToolkitError(f"Rotation failed: {exc}") from exc
