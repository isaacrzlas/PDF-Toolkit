"""Best-effort PDF optimization service."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from pypdf import PdfWriter

from services.common import PdfToolkitError, ensure_pdf, read_pdf

ProgressCallback = Callable[[int, str], None]


class PdfCompressorService:
    limitation_note = (
        "This uses pypdf's stream compression and metadata cleanup. It can reduce "
        "some PDFs, but it does not downsample images like dedicated tools such as "
        "Ghostscript or qpdf."
    )

    def compress(
        self,
        input_path: str | Path,
        output_path: str | Path,
        progress: ProgressCallback | None = None,
    ) -> tuple[int, int]:
        try:
            source = ensure_pdf(input_path)
            reader = read_pdf(source)
            writer = PdfWriter()

            for index, page in enumerate(reader.pages, start=1):
                page.compress_content_streams()
                writer.add_page(page)
                if progress:
                    progress(round(index / len(reader.pages) * 90), f"Optimized page {index}")

            if reader.metadata:
                writer.add_metadata({})

            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("wb") as handle:
                writer.write(handle)

            before = source.stat().st_size
            after = output.stat().st_size
            if progress:
                progress(100, f"Optimized PDF saved to {output.name}")
            return before, after
        except Exception as exc:
            if isinstance(exc, PdfToolkitError):
                raise
            raise PdfToolkitError(f"Compression failed: {exc}") from exc
