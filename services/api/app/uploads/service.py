# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from uuid import UUID, uuid4

from starlette.datastructures import UploadFile

from .candidates import extract_identifier_candidates
from .contracts import ArtifactPreview, FileBatchPreview
from .extractor import ExtractionError, extract_text_safely
from .policy import (
    MAX_FILE_BYTES,
    MAX_FILES,
    MAX_TOTAL_BYTES,
    UploadPolicyError,
    validate_claimed_media_type,
    validate_content,
    validate_filename,
    validate_size,
)
from .review_store import UPLOAD_REVIEW_STORE


READ_CHUNK_BYTES = 64 * 1024


class UploadBatchError(ValueError):
    def __init__(self, code: str, public_message: str, file_index: int | None = None):
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message
        self.file_index = file_index


def _storage_root() -> Path:
    configured = os.environ.get("PERSONALATTICE_UPLOAD_DIR")
    root = (
        Path(configured).expanduser()
        if configured
        else Path.home() / ".personalattice" / "uploads"
    )
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        root.chmod(0o700)
    except OSError:
        pass
    return root


async def _stage_upload(
    upload: UploadFile,
    *,
    artifact_id: UUID,
    extension: str,
    file_index: int,
) -> tuple[Path, int, str]:
    root = _storage_root()
    path = root / f"{artifact_id}{extension}"
    digest = hashlib.sha256()
    size = 0

    try:
        with path.open("xb") as handle:
            try:
                path.chmod(0o600)
            except OSError:
                pass

            while True:
                chunk = await upload.read(READ_CHUNK_BYTES)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_FILE_BYTES:
                    raise UploadBatchError(
                        "file_too_large",
                        f"File {file_index} exceeds the per-file size limit.",
                        file_index=file_index,
                    )
                digest.update(chunk)
                handle.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        await upload.seek(0)

    try:
        validate_size(size)
    except UploadPolicyError as exc:
        path.unlink(missing_ok=True)
        raise UploadBatchError(
            exc.code,
            f"File {file_index} was rejected: {exc.public_message}",
            file_index,
        ) from exc

    return path, size, digest.hexdigest()


async def process_upload_batch(files: list[UploadFile]) -> FileBatchPreview:
    if not files:
        raise UploadBatchError("empty_batch", "At least one file is required.")
    if len(files) > MAX_FILES:
        raise UploadBatchError(
            "too_many_files",
            f"At most {MAX_FILES} files can be processed in one request.",
        )

    artifacts: list[ArtifactPreview] = []
    total_bytes = 0

    for index, upload in enumerate(files, start=1):
        try:
            extension = validate_filename(upload.filename)
            validate_claimed_media_type(extension, upload.content_type)
        except UploadPolicyError as exc:
            raise UploadBatchError(
                exc.code,
                f"File {index} was rejected: {exc.public_message}",
                file_index=index,
            ) from exc

        artifact_id = uuid4()
        staged_path, size_bytes, sha256 = await _stage_upload(
            upload,
            artifact_id=artifact_id,
            extension=extension,
            file_index=index,
        )
        total_bytes += size_bytes

        if total_bytes > MAX_TOTAL_BYTES:
            staged_path.unlink(missing_ok=True)
            raise UploadBatchError(
                "batch_too_large",
                "The combined upload size exceeds the batch limit.",
            )

        try:
            data = staged_path.read_bytes()
            try:
                validated = validate_content(extension, data)
            except UploadPolicyError as exc:
                raise UploadBatchError(
                    exc.code,
                    f"File {index} was rejected: {exc.public_message}",
                    file_index=index,
                ) from exc

            try:
                extracted = extract_text_safely(data, extension)
            except ExtractionError as exc:
                raise UploadBatchError(
                    exc.code,
                    f"File {index} was rejected: {exc.public_message}",
                    file_index=index,
                ) from exc

            candidates = extract_identifier_candidates(
                extracted.text,
                artifact_id,
                page_spans=extracted.page_spans,
            )
            artifacts.append(
                ArtifactPreview(
                    artifact_id=artifact_id,
                    original_name=upload.filename or f"file-{index}{extension}",
                    size_bytes=size_bytes,
                    sha256=sha256,
                    detected_media_type=validated.detected_media_type,
                    extraction_method=extracted.method,
                    extracted_text=extracted.text,
                    extracted_chars=len(extracted.text),
                    page_spans=list(extracted.page_spans),
                    candidates=candidates,
                )
            )
        finally:
            staged_path.unlink(missing_ok=True)

    preview = FileBatchPreview(artifacts=artifacts)
    UPLOAD_REVIEW_STORE.save_preview(preview)
    return preview
