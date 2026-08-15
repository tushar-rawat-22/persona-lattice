# SPDX-License-Identifier: Apache-2.0
from io import BytesIO

import pytest
from pypdf import PdfWriter

from app.uploads import ExtractionError, ExtractionLimits, extract_text_safely


def _blank_pdf(page_count: int = 1) -> bytes:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=72, height=72)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_text_extraction_runs_inside_bounded_worker() -> None:
    result = extract_text_safely(b"Synthetic document text", ".txt")
    assert result.text == "Synthetic document text"
    assert result.method == "utf8_text"


def test_extracted_text_output_limit_is_enforced() -> None:
    limits = ExtractionLimits(max_chars=8)

    with pytest.raises(ExtractionError) as exc:
        extract_text_safely(b"123456789", ".txt", limits)

    assert exc.value.code == "text_output_limit"


def test_pdf_page_limit_is_enforced() -> None:
    limits = ExtractionLimits(max_pdf_pages=1)

    with pytest.raises(ExtractionError) as exc:
        extract_text_safely(_blank_pdf(page_count=2), ".pdf", limits)

    assert exc.value.code == "pdf_page_limit"


def test_blank_pdf_can_be_parsed_without_ocr() -> None:
    result = extract_text_safely(_blank_pdf(), ".pdf")
    assert result.method == "pypdf_text"
    assert result.text == ""
