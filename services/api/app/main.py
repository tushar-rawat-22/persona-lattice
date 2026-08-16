# SPDX-License-Identifier: Apache-2.0
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException as StarletteHTTPException

from .admin_auth import (
    authenticate_admin,
    require_admin,
    revoke_admin_session,
    set_admin_session_cookie,
)
from .authz import AuthenticatedPrincipal
from .evidence import IdentifierKind, InvalidIdentifier, normalize_collection, normalize_identifier
from .models import CaseIntake, IntakePreview, ProviderPlan, Purpose
from .policy import enforce_purpose
from .providers.errors import (
    ProviderExecutionError,
    ProviderPolicyError,
    ProviderRateBudgetExceeded,
)
from .providers.registry import PROVIDERS
from .research import ResearchKind, run_quick_research
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
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1, max_length=1024)


class AdminSessionResponse(BaseModel):
    authenticated: bool
    session_record_id: str
    expires_at: str


class QuickResearchRequest(BaseModel):
    kind: ResearchKind
    value: str = Field(min_length=1, max_length=2048)
    purpose: Purpose = Purpose.PUBLIC_SOURCE_RESEARCH
    consent_acknowledged: bool = False


class QuickObservationResponse(BaseModel):
    source: str
    source_locator: str
    summary: str
    details: dict[str, Any]


class QuickResearchResponse(BaseModel):
    kind: ResearchKind
    normalized_value: str
    observations: list[QuickObservationResponse]
    warnings: list[str]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "personalattice-api"}


@app.post("/v1/auth/login", response_model=AdminSessionResponse)
def admin_login(
    payload: AdminLoginRequest,
    request: Request,
    response: Response,
) -> AdminSessionResponse:
    source_key = request.client.host if request.client else "unknown"
    login = authenticate_admin(
        payload.username,
        payload.password,
        source_key=source_key,
    )
    if login is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials.",
            headers={"Cache-Control": "no-store"},
        )

    set_admin_session_cookie(response, login)
    return AdminSessionResponse(
        authenticated=True,
        session_record_id=str(login.principal.session_record_id),
        expires_at=login.principal.session_expires_at.isoformat(),
    )


@app.get("/v1/auth/session", response_model=AdminSessionResponse)
def admin_session(
    principal: AuthenticatedPrincipal = Depends(require_admin),
) -> AdminSessionResponse:
    return AdminSessionResponse(
        authenticated=True,
        session_record_id=str(principal.session_record_id),
        expires_at=principal.session_expires_at.isoformat(),
    )


@app.post("/v1/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def admin_logout(request: Request, response: Response) -> Response:
    revoke_admin_session(request, response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


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
def preview_intake(
    payload: CaseIntake,
    _principal: AuthenticatedPrincipal = Depends(require_admin),
) -> IntakePreview:
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


@app.post("/v1/research/quick", response_model=QuickResearchResponse)
async def quick_research(
    payload: QuickResearchRequest,
    _principal: AuthenticatedPrincipal = Depends(require_admin),
) -> QuickResearchResponse:
    enforce_purpose(payload.purpose, payload.consent_acknowledged)
    try:
        report = await run_quick_research(
            kind=payload.kind,
            value=payload.value,
            purpose=payload.purpose,
            consent_acknowledged=payload.consent_acknowledged,
        )
    except InvalidIdentifier as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except ProviderPolicyError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Research provider policy blocked this request.",
        ) from exc
    except ProviderRateBudgetExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Local research rate budget is exhausted. Try again shortly.",
        ) from exc
    except ProviderExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="A public-source provider failed to complete the request.",
        ) from exc

    return QuickResearchResponse(
        kind=report.kind,
        normalized_value=report.normalized_value,
        observations=[
            QuickObservationResponse(
                source=item.source,
                source_locator=item.source_locator,
                summary=item.summary,
                details=item.details,
            )
            for item in report.observations
        ],
        warnings=list(report.warnings),
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
async def preview_files(
    request: Request,
    _principal: AuthenticatedPrincipal = Depends(require_admin),
) -> FileBatchPreview:
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
