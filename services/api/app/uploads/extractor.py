# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from multiprocessing import get_context
from multiprocessing.connection import Connection

from .policy import (
    EXTRACTION_CPU_SECONDS,
    EXTRACTION_MEMORY_BYTES,
    EXTRACTION_TIMEOUT_SECONDS,
    MAX_EXTRACTED_CHARS,
    MAX_PDF_CONTENT_STREAM_BYTES,
    MAX_PDF_PAGES,
)


class ExtractionError(RuntimeError):
    def __init__(self, code: str, public_message: str):
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message


@dataclass(frozen=True, slots=True)
class ExtractionLimits:
    max_chars: int = MAX_EXTRACTED_CHARS
    max_pdf_pages: int = MAX_PDF_PAGES
    max_pdf_content_stream_bytes: int = MAX_PDF_CONTENT_STREAM_BYTES
    timeout_seconds: float = EXTRACTION_TIMEOUT_SECONDS
    memory_bytes: int = EXTRACTION_MEMORY_BYTES
    cpu_seconds: int = EXTRACTION_CPU_SECONDS


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    text: str
    method: str


def _apply_resource_limits(limits: ExtractionLimits) -> None:
    try:
        import resource
    except ImportError:
        return

    try:
        resource.setrlimit(resource.RLIMIT_AS, (limits.memory_bytes, limits.memory_bytes))
    except (OSError, ValueError):
        pass
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (limits.cpu_seconds, limits.cpu_seconds))
    except (OSError, ValueError):
        pass


def _extract_text(data: bytes, extension: str, limits: ExtractionLimits) -> ExtractionResult:
    if extension == ".txt":
        text = data.decode("utf-8-sig")
        if len(text) > limits.max_chars:
            raise ExtractionError(
                "text_output_limit",
                "Extracted text exceeds the configured output limit.",
            )
        return ExtractionResult(text=text, method="utf8_text")

    if extension == ".pdf":
        from pypdf import PdfReader
        from pypdf.errors import PdfReadError

        try:
            reader = PdfReader(BytesIO(data), strict=True)
        except PdfReadError as exc:
            raise ExtractionError("pdf_parse_error", "The PDF could not be parsed safely.") from exc

        if reader.is_encrypted:
            raise ExtractionError("encrypted_pdf", "Encrypted PDFs are not accepted.")
        if len(reader.pages) > limits.max_pdf_pages:
            raise ExtractionError(
                "pdf_page_limit",
                "The PDF has too many pages for this extraction boundary.",
            )

        pieces: list[str] = []
        total_chars = 0

        for page in reader.pages:
            contents = page.get_contents()
            if contents is not None:
                stream_data = contents.get_data()
                if len(stream_data) > limits.max_pdf_content_stream_bytes:
                    raise ExtractionError(
                        "pdf_stream_limit",
                        "A PDF page exceeds the configured content-stream limit.",
                    )

            page_text = page.extract_text() or ""
            total_chars += len(page_text)
            if total_chars > limits.max_chars:
                raise ExtractionError(
                    "text_output_limit",
                    "Extracted text exceeds the configured output limit.",
                )
            pieces.append(page_text)

        return ExtractionResult(text="\n".join(pieces), method="pypdf_text")

    raise ExtractionError("unsupported_extension", "The document type is not supported.")


def _worker(
    connection: Connection,
    data: bytes,
    extension: str,
    limits: ExtractionLimits,
) -> None:
    _apply_resource_limits(limits)
    try:
        result = _extract_text(data, extension, limits)
        connection.send(("ok", {"text": result.text, "method": result.method}))
    except ExtractionError as exc:
        connection.send(("error", {"code": exc.code, "message": exc.public_message}))
    except Exception:
        connection.send(
            (
                "error",
                {
                    "code": "extractor_failure",
                    "message": "The document extractor rejected the file.",
                },
            )
        )
    finally:
        connection.close()


def extract_text_safely(
    data: bytes,
    extension: str,
    limits: ExtractionLimits | None = None,
) -> ExtractionResult:
    active_limits = limits or ExtractionLimits()
    context = get_context("spawn")
    parent_connection, child_connection = context.Pipe(duplex=False)
    process = context.Process(
        target=_worker,
        args=(child_connection, data, extension, active_limits),
        daemon=True,
    )
    process.start()
    child_connection.close()

    try:
        if not parent_connection.poll(active_limits.timeout_seconds):
            process.terminate()
            process.join(timeout=1)
            raise ExtractionError(
                "extraction_timeout",
                "Document extraction exceeded the configured time limit.",
            )

        try:
            status, payload = parent_connection.recv()
        except EOFError as exc:
            process.join(timeout=1)
            raise ExtractionError(
                "extractor_failure",
                "The document extractor stopped before returning a result.",
            ) from exc

        process.join(timeout=1)

        if status == "error":
            raise ExtractionError(payload["code"], payload["message"])
        if status != "ok":
            raise ExtractionError(
                "extractor_failure",
                "The document extractor returned an invalid result.",
            )
        return ExtractionResult(text=payload["text"], method=payload["method"])
    finally:
        parent_connection.close()
        if process.is_alive():
            process.terminate()
            process.join(timeout=1)
