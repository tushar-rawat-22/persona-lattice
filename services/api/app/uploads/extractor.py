# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import json
from multiprocessing import get_context
from multiprocessing.connection import Connection
import warnings

from .policy import (
    EXTRACTION_CPU_SECONDS,
    EXTRACTION_MEMORY_BYTES,
    EXTRACTION_TIMEOUT_SECONDS,
    MAX_EXTRACTED_CHARS,
    MAX_IMAGE_PIXELS,
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
    max_image_pixels: int = MAX_IMAGE_PIXELS
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


def _safe_text(value: object, *, limit: int = 512) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    text = str(value).replace("\x00", "").strip()
    if not text:
        return None
    return text[:limit]


def _rational(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        raise ExtractionError("invalid_gps", "Embedded GPS metadata is malformed.") from exc


def _gps_decimal(parts: object, reference: object) -> float | None:
    if not isinstance(parts, (tuple, list)) or len(parts) != 3:
        return None
    degrees = _rational(parts[0])
    minutes = _rational(parts[1])
    seconds = _rational(parts[2])
    value = degrees + minutes / 60.0 + seconds / 3600.0
    ref = (_safe_text(reference, limit=8) or "").upper()
    if ref in {"S", "W"}:
        value = -value
    elif ref not in {"N", "E"}:
        return None
    return round(value, 7)


def _image_metadata(data: bytes, limits: ExtractionLimits) -> dict[str, object]:
    from PIL import ExifTags, Image, UnidentifiedImageError

    Image.MAX_IMAGE_PIXELS = limits.max_image_pixels
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as probe:
                width, height = probe.size
                if width <= 0 or height <= 0 or width * height > limits.max_image_pixels:
                    raise ExtractionError(
                        "image_pixel_limit",
                        "The image exceeds the configured pixel limit.",
                    )
                probe.verify()

            with Image.open(BytesIO(data)) as image:
                width, height = image.size
                metadata: dict[str, object] = {
                    "format": image.format,
                    "width": width,
                    "height": height,
                    "mode": image.mode,
                    "pixel_count": width * height,
                    "identity_claim": False,
                    "location_semantics": "embedded_metadata_only_not_current_location",
                }

                exif = image.getexif()
                if exif:
                    allowed = {
                        int(ExifTags.Base.ImageDescription): "image_description",
                        int(ExifTags.Base.Make): "camera_make",
                        int(ExifTags.Base.Model): "camera_model",
                        int(ExifTags.Base.Software): "software",
                        int(ExifTags.Base.DateTime): "datetime",
                        int(ExifTags.Base.DateTimeOriginal): "datetime_original",
                        int(ExifTags.Base.DateTimeDigitized): "datetime_digitized",
                        int(ExifTags.Base.Artist): "artist",
                        int(ExifTags.Base.Copyright): "copyright",
                    }
                    exif_fields: dict[str, str] = {}
                    for tag, name in allowed.items():
                        text = _safe_text(exif.get(tag))
                        if text is not None:
                            exif_fields[name] = text
                    if exif_fields:
                        metadata["exif"] = exif_fields

                    try:
                        gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
                    except (KeyError, TypeError, ValueError):
                        gps = {}
                    if gps:
                        latitude = _gps_decimal(
                            gps.get(ExifTags.GPS.GPSLatitude),
                            gps.get(ExifTags.GPS.GPSLatitudeRef),
                        )
                        longitude = _gps_decimal(
                            gps.get(ExifTags.GPS.GPSLongitude),
                            gps.get(ExifTags.GPS.GPSLongitudeRef),
                        )
                        gps_fields: dict[str, object] = {}
                        if latitude is not None and longitude is not None:
                            gps_fields["latitude"] = latitude
                            gps_fields["longitude"] = longitude
                        altitude = gps.get(ExifTags.GPS.GPSAltitude)
                        if altitude is not None:
                            try:
                                gps_fields["altitude_meters"] = round(_rational(altitude), 2)
                            except ExtractionError:
                                pass
                        date_stamp = _safe_text(gps.get(ExifTags.GPS.GPSDateStamp), limit=64)
                        if date_stamp:
                            gps_fields["date_stamp"] = date_stamp
                        if gps_fields:
                            metadata["embedded_gps"] = gps_fields

                return metadata
    except Image.DecompressionBombWarning as exc:
        raise ExtractionError(
            "image_decompression_bomb",
            "The image exceeds the safe decompression boundary.",
        ) from exc
    except Image.DecompressionBombError as exc:
        raise ExtractionError(
            "image_decompression_bomb",
            "The image exceeds the safe decompression boundary.",
        ) from exc
    except UnidentifiedImageError as exc:
        raise ExtractionError("image_parse_error", "The image could not be parsed safely.") from exc
    except OSError as exc:
        raise ExtractionError("image_parse_error", "The image could not be parsed safely.") from exc


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

    if extension in {".jpg", ".jpeg", ".png"}:
        metadata = _image_metadata(data, limits)
        text = json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if len(text) > min(limits.max_chars, 20_000):
            raise ExtractionError(
                "image_metadata_limit",
                "Embedded image metadata exceeds the configured output limit.",
            )
        return ExtractionResult(text=text, method="pillow_metadata")

    raise ExtractionError("unsupported_extension", "The evidence type is not supported.")


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
                    "message": "The evidence extractor rejected the file.",
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
                "Evidence extraction exceeded the configured time limit.",
            )

        try:
            worker_status, payload = parent_connection.recv()
        except EOFError as exc:
            process.join(timeout=1)
            raise ExtractionError(
                "extractor_failure",
                "The evidence extractor stopped before returning a result.",
            ) from exc

        process.join(timeout=1)

        if worker_status == "error":
            raise ExtractionError(payload["code"], payload["message"])
        if worker_status != "ok":
            raise ExtractionError(
                "extractor_failure",
                "The evidence extractor returned an invalid result.",
            )
        return ExtractionResult(text=payload["text"], method=payload["method"])
    finally:
        parent_connection.close()
        if process.is_alive():
            process.terminate()
            process.join(timeout=1)
