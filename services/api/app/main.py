# SPDX-License-Identifier: Apache-2.0
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException as StarletteHTTPException

from .evidence import IdentifierKind, InvalidIdentifier, normalize_collection, normalize_identifier
from .models import CaseIntake, IntakePreview, ProviderPlan, Purpose
from .policy import enforce_purpose
from .providers.registry import PROVIDERS
from .uploads import (
    FileBatchPreview,
    MAX_FILE_BYTES,
    MAX_FILES,
    MAX_REQUEST_BYTES,
    UploadBatchError,
    process_upload_batch,
)

app = FastAPI(
    title="PersonaLattice API",
    version="0.0.1",
    description="Evidence-first identity intelligence API bootstrap.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "personalattice-api"}


def _normalize_scalar(kind: IdentifierKind, raw: str | None) -> tuple[str | None, list[str]]:
    if raw is None:
        return None, []

    try:
        normalized = normalize_identifier(kind, raw)
    except InvalidIdentifier as exc:
        return None, [f"{raw}: {exc}"]

    return normalized.normalized_value, []


def _normalize_values(kind: IdentifierKind, values: list[str]) -> tuple[list[str], list[str]]:
    normalized, warnings = normalize_collection(kind, values)
    return [item.normalized_value for item in normalized], warnings


@app.post("/v1/intake/preview", response_model=IntakePreview)
def preview_intake(payload: CaseIntake) -> IntakePreview:
    enforce_purpose(payload.purpose, payload.consent_acknowledged)

    warnings: list[str] = []

    full_name, scalar_warnings = _normalize_scalar(
        IdentifierKind.NAME,
        payload.full_name,
    )
    warnings.extend(scalar_warnings)

    phones, phone_warnings = _normalize_values(IdentifierKind.PHONE, payload.phones)
    warnings.extend(phone_warnings)

    emails, email_warnings = _normalize_values(IdentifierKind.EMAIL, payload.emails)
    warnings.extend(email_warnings)

    usernames, username_warnings = _normalize_values(
        IdentifierKind.USERNAME,
        payload.usernames,
    )
    warnings.extend(username_warnings)

    urls, url_warnings = _normalize_values(IdentifierKind.URL, payload.urls)
    warnings.extend(url_warnings)

    organizations, organization_warnings = _normalize_values(
        IdentifierKind.ORGANIZATION,
        payload.organizations,
    )
    warnings.extend(organization_warnings)

    normalized = {
        "full_name": full_name,
        "phones": phones,
        "emails": emails,
        "usernames": usernames,
        "urls": urls,
        "organizations": organizations,
        "file_count": len(payload.files),
        "note_present": bool(payload.notes),
    }

    plans = [
        ProviderPlan(
            provider=item.name,
            capability=item.capability,
            status=item.status,
            contact_risk=item.contact_risk.value,
            reason=item.reason,
        )
        for item in PROVIDERS
    ]

    return IntakePreview(
        case_id=uuid4(),
        status="planned_only",
        purpose=payload.purpose,
        normalized=normalized,
        provider_plan=plans,
        warnings=warnings,
    )


def _parse_consent(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="consent_acknowledged must be true or false.",
    )


def _parse_purpose(value: object) -> Purpose:
    if not isinstance(value, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="purpose is required.",
        )
    try:
        return Purpose(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="purpose is not recognized.",
        ) from exc


@app.post("/v1/files/preview", response_model=FileBatchPreview)
async def preview_files(request: Request) -> FileBatchPreview:
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            declared_length = int(content_length)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Content-Length header.",
            ) from exc
        if declared_length < 0 or declared_length > MAX_REQUEST_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="Upload request exceeds the request-size limit.",
            )

    try:
        async with request.form(
            max_files=MAX_FILES,
            max_fields=4,
            max_part_size=MAX_FILE_BYTES,
        ) as form:
            purpose = _parse_purpose(form.get("purpose"))
            consent_acknowledged = _parse_consent(form.get("consent_acknowledged"))
            enforce_purpose(purpose, consent_acknowledged)

            raw_files = form.getlist("files")
            if any(not isinstance(item, UploadFile) for item in raw_files):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Every files field must contain an uploaded file.",
                )

            try:
                return await process_upload_batch(raw_files)
            except UploadBatchError as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=exc.public_message,
                ) from exc
    except StarletteHTTPException as exc:
        if exc.status_code == status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="Upload request exceeded multipart parser safety limits.",
            ) from exc
        raise
