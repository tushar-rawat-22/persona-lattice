# SPDX-License-Identifier: Apache-2.0
import pytest

from app.uploads.policy import (
    MAX_FILE_BYTES,
    UploadPolicyError,
    validate_claimed_media_type,
    validate_content,
    validate_filename,
    validate_size,
)


@pytest.mark.parametrize(
    "filename",
    [
        "../resume.pdf",
        r"folder\resume.txt",
        "payload.php.pdf",
        "notes.txt.pdf",
        "double..pdf",
    ],
)
def test_unsafe_or_ambiguous_filenames_are_rejected(filename: str) -> None:
    with pytest.raises(UploadPolicyError):
        validate_filename(filename)


def test_benign_dotted_filename_is_allowed() -> None:
    assert validate_filename("resume.final.pdf") == ".pdf"


def test_claimed_media_type_is_secondary_but_must_not_conflict() -> None:
    validate_claimed_media_type(".pdf", "application/pdf")
    validate_claimed_media_type(".pdf", "application/octet-stream")

    with pytest.raises(UploadPolicyError) as exc:
        validate_claimed_media_type(".pdf", "text/plain")
    assert exc.value.code == "media_type_mismatch"


def test_size_limits_cover_empty_and_oversized_files() -> None:
    with pytest.raises(UploadPolicyError, match="Empty"):
        validate_size(0)

    with pytest.raises(UploadPolicyError) as exc:
        validate_size(MAX_FILE_BYTES + 1)
    assert exc.value.code == "file_too_large"


def test_text_content_requires_utf8_and_rejects_binary_controls() -> None:
    validated = validate_content(".txt", "Synthetic résumé\n".encode())
    assert validated.detected_media_type == "text/plain"

    with pytest.raises(UploadPolicyError) as exc:
        validate_content(".txt", b"hello\x00world")
    assert exc.value.code == "binary_text"

    with pytest.raises(UploadPolicyError) as exc:
        validate_content(".txt", b"\xff\xfe\xfd")
    assert exc.value.code == "invalid_text_encoding"


def test_pdf_content_requires_signature_and_eof_marker() -> None:
    with pytest.raises(UploadPolicyError) as exc:
        validate_content(".pdf", b"not-a-pdf")
    assert exc.value.code == "signature_mismatch"

    with pytest.raises(UploadPolicyError) as exc:
        validate_content(".pdf", b"%PDF-1.7\nsynthetic")
    assert exc.value.code == "malformed_pdf"
