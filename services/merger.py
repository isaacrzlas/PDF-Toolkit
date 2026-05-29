"""PDF merge service."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from pypdf import PdfWriter

from services.common import PdfToolkitError, ensure_pdf, read_pdf

ProgressCallback = Callable[[int, str], None]


class PdfMergerService:
    def merge(
        self,
        input_paths: list[str | Path],
        output_path: str | Path,
        progress: ProgressCallback | None = None,
    ) -> None:
        if len(input_paths) < 2:
            raise PdfToolkitError("Select at least two PDF files to merge.")

        writer = PdfWriter()
        total = len(input_paths)

        try:
            for index, input_path in enumerate(input_paths, start=1):
                path = ensure_pdf(input_path)
                reader = read_pdf(path)
                for page in reader.pages:
                    writer.add_page(page)
                if progress:
                    progress(round(index / total * 90), f"Added {path.name}")

            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("wb") as handle:
                writer.write(handle)
            if progress:
                progress(100, f"Merged PDF saved to {output.name}")
        except Exception as exc:
            if isinstance(exc, PdfToolkitError):
                raise
            raise PdfToolkitError(f"Merge failed: {exc}") from exc
