# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from pathlib import Path


MAX_FILES = 5
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 12 * 1024 * 1024
MAX_REQUEST_BYTES = MAX_TOTAL_BYTES + 1024 * 1024
MAX_EXTRACTED_CHARS = 200_000
MAX_PDF_PAGES = 40
MAX_PDF_CONTENT_STREAM_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
EXTRACTION_TIMEOUT_SECONDS = 6.0
EXTRACTION_MEMORY_BYTES = 512 * 1024 * 1024
EXTRACTION_CPU_SECONDS = 4

ALLOWED_MEDIA_TYPES = {
    ".txt": {"text/plain", "application/octet-stream"},
    ".pdf": {"application/pdf", "application/octet-stream"},
    ".jpg": {"image/jpeg", "application/octet-stream"},
    ".jpeg": {"image/jpeg", "application/octet-stream"},
    ".png": {"image/png", "application/octet-stream"},
}
DANGEROUS_INNER_SUFFIXES = {
    ".asp",
    ".aspx",
    ".bat",
    ".cgi",
    ".cmd",
    ".com",
    ".exe",
    ".hta",
    ".htm",
    ".html",
    ".jar",
    ".js",
    ".jsp",
    ".mjs",
    ".php",
    ".pl",
    ".ps1",
    ".py",
    ".rb",
    ".scr",
    ".sh",
    ".svg",
    ".vbs",
    ".xhtml",
}


class UploadPolicyError(ValueError):
    def __init__(self, code: str, public_message: str):
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message


@dataclass(frozen=True, slots=True)
class ValidatedContent:
    extension: str
    detected_media_type: str
    text_encoding: str | None = None


def validate_filename(filename: str | None) -> str:
    if filename is None or not filename:
        raise UploadPolicyError("missing_filename", "The upload has no usable filename.")
    if len(filename) > 200:
        raise UploadPolicyError("filename_too_long", "The upload filename is too long.")
    if filename != filename.strip():
        raise UploadPolicyError("unsafe_filename", "The upload filename is not accepted.")
    if any(character in filename for character in ("/", "\\", "\x00")):
        raise UploadPolicyError("path_in_filename", "The upload filename is not accepted.")
    if any(ord(character) < 32 for character in filename):
        raise UploadPolicyError("unsafe_filename", "The upload filename is not accepted.")
    if filename in {".", ".."} or ".." in filename:
        raise UploadPolicyError("path_in_filename", "The upload filename is not accepted.")

    path = Path(filename)
    extension = path.suffix.lower()
    if extension not in ALLOWED_MEDIA_TYPES:
        raise UploadPolicyError(
            "unsupported_extension",
            "Only PDF, UTF-8 text, JPEG and PNG evidence files are accepted.",
        )

    inner_suffixes = {suffix.lower() for suffix in path.suffixes[:-1]}
    if inner_suffixes & (DANGEROUS_INNER_SUFFIXES | set(ALLOWED_MEDIA_TYPES)):
        raise UploadPolicyError(
            "ambiguous_extension",
            "Ambiguous or executable-looking double extensions are not accepted.",
        )
    return extension


def validate_claimed_media_type(extension: str, content_type: str | None) -> None:
    if not content_type:
        return
    normalized = content_type.split(";", 1)[0].strip().lower()
    if normalized not in ALLOWED_MEDIA_TYPES[extension]:
        raise UploadPolicyError(
            "media_type_mismatch",
            "The supplied file type does not match the allowed evidence type.",
        )


def validate_size(size_bytes: int) -> None:
    if size_bytes <= 0:
        raise UploadPolicyError("empty_file", "Empty files are not accepted.")
    if size_bytes > MAX_FILE_BYTES:
        raise UploadPolicyError(
            "file_too_large",
            f"Each file must be {MAX_FILE_BYTES // (1024 * 1024)} MiB or smaller.",
        )


def validate_content(extension: str, data: bytes) -> ValidatedContent:
    validate_size(len(data))

    if extension == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise UploadPolicyError(
                "signature_mismatch",
                "The file content does not have a valid PDF signature.",
            )
        if b"%%EOF" not in data[-4096:]:
            raise UploadPolicyError(
                "malformed_pdf",
                "The PDF is incomplete or malformed.",
            )
        return ValidatedContent(extension=extension, detected_media_type="application/pdf")

    if extension == ".txt":
        if b"\x00" in data:
            raise UploadPolicyError(
                "binary_text",
                "The text file contains binary data and was rejected.",
            )
        try:
            decoded = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise UploadPolicyError(
                "invalid_text_encoding",
                "Text files must use UTF-8 encoding.",
            ) from exc

        controls = sum(
            1
            for character in decoded
            if ord(character) < 32 and character not in {"\n", "\r", "\t", "\f"}
        )
        if controls:
            raise UploadPolicyError(
                "unsafe_text_controls",
                "The text file contains unsupported control characters.",
            )
        return ValidatedContent(
            extension=extension,
            detected_media_type="text/plain",
            text_encoding="utf-8",
        )

    if extension in {".jpg", ".jpeg"}:
        if len(data) < 4 or not data.startswith(b"\xff\xd8\xff"):
            raise UploadPolicyError(
                "signature_mismatch",
                "The file content does not have a valid JPEG signature.",
            )
        return ValidatedContent(extension=extension, detected_media_type="image/jpeg")

    if extension == ".png":
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise UploadPolicyError(
                "signature_mismatch",
                "The file content does not have a valid PNG signature.",
            )
        return ValidatedContent(extension=extension, detected_media_type="image/png")

    raise UploadPolicyError("unsupported_extension", "The file type is not supported.")
