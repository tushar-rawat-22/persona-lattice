# SPDX-License-Identifier: Apache-2.0
from io import BytesIO

import pytest
from pypdf import PdfWriter

from app.uploads import ExtractionError, ExtractionLimits, extract_text_safely
from app.uploads.extractor import _flatten_pdf_page_texts


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
    assert result.page_spans == ()


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
    assert [item.model_dump() for item in result.page_spans] == [
        {"page_number": 1, "source_start": 0, "source_end": 0}
    ]


def test_multi_page_pdf_preserves_empty_page_boundaries() -> None:
    result = extract_text_safely(_blank_pdf(page_count=3), ".pdf")

    assert result.text == "\n\n"
    assert [item.model_dump() for item in result.page_spans] == [
        {"page_number": 1, "source_start": 0, "source_end": 0},
        {"page_number": 2, "source_start": 1, "source_end": 1},
        {"page_number": 3, "source_start": 2, "source_end": 2},
    ]


def test_page_flattening_keeps_global_offsets_exact() -> None:
    text, spans = _flatten_pdf_page_texts(
        ["first@example.test", "", "Profile @second_user"]
    )

    assert text == "first@example.test\n\nProfile @second_user"
    assert [item.model_dump() for item in spans] == [
        {"page_number": 1, "source_start": 0, "source_end": 18},
        {"page_number": 2, "source_start": 19, "source_end": 19},
        {"page_number": 3, "source_start": 20, "source_end": 40},
    ]


def test_pdf_separator_characters_count_toward_output_limit() -> None:
    with pytest.raises(ExtractionError) as exc:
        extract_text_safely(_blank_pdf(page_count=2), ".pdf", ExtractionLimits(max_chars=0))

    assert exc.value.code == "text_output_limit"
