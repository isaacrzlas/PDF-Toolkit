"""PDF split service."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from pypdf import PdfWriter

from services.common import PdfToolkitError, ensure_pdf, parse_page_ranges, read_pdf

ProgressCallback = Callable[[int, str], None]


class PdfSplitterService:
    def split(
        self,
        input_path: str | Path,
        range_specs: list[str],
        output_folder: str | Path,
        progress: ProgressCallback | None = None,
    ) -> list[Path]:
        if not range_specs:
            raise PdfToolkitError("Enter at least one range, such as 1-5.")

        try:
            source = ensure_pdf(input_path)
            reader = read_pdf(source)
            output_dir = Path(output_folder)
            output_dir.mkdir(parents=True, exist_ok=True)
            created: list[Path] = []

            for index, spec in enumerate(range_specs, start=1):
                pages = parse_page_ranges(spec, len(reader.pages))
                writer = PdfWriter()
                for page_index in pages:
                    writer.add_page(reader.pages[page_index])

                safe_spec = spec.replace(" ", "").replace(",", "_").replace("-", "to")
                output_path = output_dir / f"{source.stem}_pages_{safe_spec}.pdf"
                with output_path.open("wb") as handle:
                    writer.write(handle)
                created.append(output_path)

                if progress:
                    progress(round(index / len(range_specs) * 100), f"Created {output_path.name}")

            return created
        except Exception as exc:
            if isinstance(exc, PdfToolkitError):
                raise
            raise PdfToolkitError(f"Split failed: {exc}") from exc
