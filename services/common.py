"""Shared PDF service helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


class PdfToolkitError(Exception):
    """Raised when a PDF operation cannot be completed."""


def ensure_pdf(path: str | Path) -> Path:
    if not str(path).strip():
        raise PdfToolkitError("Select a PDF file first.")
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise PdfToolkitError(f"File does not exist: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise PdfToolkitError(f"Not a PDF file: {pdf_path.name}")
    return pdf_path


def get_page_count(path: str | Path) -> int:
    return len(read_pdf(path).pages)


def read_pdf(path: str | Path) -> PdfReader:
    try:
        reader = PdfReader(str(ensure_pdf(path)))
        if reader.is_encrypted:
            raise PdfToolkitError("Encrypted PDFs are not supported yet.")
        if len(reader.pages) < 1:
            raise PdfToolkitError("The PDF has no pages.")
        return reader
    except Exception as exc:  # pypdf raises several parser exceptions.
        if isinstance(exc, PdfToolkitError):
            raise
        raise PdfToolkitError(f"Could not read PDF: {exc}") from exc


def parse_page_ranges(spec: str, total_pages: int) -> list[int]:
    """Parse a one-based page/range string into zero-based page indexes."""

    if total_pages < 1:
        raise PdfToolkitError("The PDF has no pages.")

    pages: list[int] = []
    seen: set[int] = set()

    for raw_part in spec.replace(" ", "").split(","):
        if not raw_part:
            continue

        if "-" in raw_part:
            bounds = raw_part.split("-", 1)
            if len(bounds) != 2 or not bounds[0] or not bounds[1]:
                raise PdfToolkitError(f"Invalid page range: {raw_part}")
            start, end = (int(bounds[0]), int(bounds[1]))
            if start > end:
                raise PdfToolkitError(f"Range start is after end: {raw_part}")
            range_pages: Iterable[int] = range(start, end + 1)
        else:
            range_pages = (int(raw_part),)

        for page in range_pages:
            if page < 1 or page > total_pages:
                raise PdfToolkitError(
                    f"Page {page} is outside the valid range 1-{total_pages}."
                )
            index = page - 1
            if index not in seen:
                pages.append(index)
                seen.add(index)

    if not pages:
        raise PdfToolkitError("Enter at least one page number or range.")

    return pages
