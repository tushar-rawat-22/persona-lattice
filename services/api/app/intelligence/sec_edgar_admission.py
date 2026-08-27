# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import date
import re
from urllib.parse import urlsplit


_SEC_SUBMISSIONS_RE = re.compile(r"^/submissions/CIK([0-9]{10})\.json$")
_ACCESSION_RE = re.compile(r"^[0-9]{10}-[0-9]{2}-[0-9]{6}$")
_FISCAL_YEAR_END_RE = re.compile(r"^[0-9]{4}$")
_MAX_NAME_LENGTH = 300
_MAX_SHORT_TEXT_LENGTH = 64
_MAX_MARKET_PAIRS = 8


class SecEdgarAdmissionError(ValueError):
    """Raised when an exact SEC seed or submissions payload violates the admission contract."""


def sec_cik_from_submissions_url(value: str) -> str | None:
    """Return a zero-padded CIK from an exact documented SEC submissions URL."""

    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return None
    if (
        parts.scheme != "https"
        or parts.hostname is None
        or parts.hostname.casefold() != "data.sec.gov"
        or parts.username is not None
        or parts.password is not None
        or port is not None
        or parts.query
        or parts.fragment
    ):
        return None
    match = _SEC_SUBMISSIONS_RE.fullmatch(parts.path)
    if match is None:
        return None
    cik = match.group(1)
    if int(cik) == 0:
        return None
    return cik


def sec_submissions_url(cik: str) -> str:
    """Return the canonical SEC submissions endpoint for one admitted CIK."""

    if not re.fullmatch(r"[0-9]{10}", cik) or int(cik) == 0:
        raise SecEdgarAdmissionError("SEC CIK must be a non-zero 10-digit identifier.")
    return f"https://data.sec.gov/submissions/CIK{cik}.json"


def _bounded_text(value: object, *, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise SecEdgarAdmissionError(f"SEC submissions payload has an invalid {field}.")
    text = value.strip()
    if not text or text != value or len(text) > maximum:
        raise SecEdgarAdmissionError(f"SEC submissions payload has an invalid {field}.")
    return text


def _payload_cik(value: object) -> str:
    if isinstance(value, int) and not isinstance(value, bool):
        digits = str(value)
    elif isinstance(value, str) and value.isdigit():
        digits = value
    else:
        raise SecEdgarAdmissionError("SEC submissions payload has an invalid CIK.")
    if len(digits) > 10 or int(digits) == 0:
        raise SecEdgarAdmissionError("SEC submissions payload has an invalid CIK.")
    return digits.zfill(10)


def _optional_short_text(
    payload: dict[str, object],
    key: str,
    *,
    field: str,
    pattern: re.Pattern[str] | None = None,
) -> str | None:
    value = payload.get(key)
    if value in {None, ""}:
        return None
    text = _bounded_text(value, field=field, maximum=_MAX_SHORT_TEXT_LENGTH)
    if pattern is not None and pattern.fullmatch(text) is None:
        raise SecEdgarAdmissionError(f"SEC submissions payload has an invalid {field}.")
    return text


def _market_pairs(payload: dict[str, object]) -> list[dict[str, str]]:
    tickers = payload.get("tickers", [])
    exchanges = payload.get("exchanges", [])
    if not isinstance(tickers, list) or not isinstance(exchanges, list):
        raise SecEdgarAdmissionError("SEC submissions payload has invalid ticker/exchange metadata.")
    if len(tickers) != len(exchanges):
        raise SecEdgarAdmissionError("SEC submissions payload has mismatched ticker/exchange metadata.")

    pairs: list[dict[str, str]] = []
    for ticker, exchange in zip(tickers[:_MAX_MARKET_PAIRS], exchanges[:_MAX_MARKET_PAIRS], strict=True):
        pairs.append(
            {
                "ticker": _bounded_text(
                    ticker,
                    field="ticker",
                    maximum=_MAX_SHORT_TEXT_LENGTH,
                ),
                "exchange": _bounded_text(
                    exchange,
                    field="exchange",
                    maximum=_MAX_SHORT_TEXT_LENGTH,
                ),
            }
        )
    return pairs


def _latest_filing(payload: dict[str, object]) -> dict[str, str] | None:
    filings = payload.get("filings")
    if not isinstance(filings, dict):
        raise SecEdgarAdmissionError("SEC submissions payload is missing filings metadata.")
    recent = filings.get("recent")
    if not isinstance(recent, dict):
        raise SecEdgarAdmissionError("SEC submissions payload is missing recent filings metadata.")

    accessions = recent.get("accessionNumber")
    forms = recent.get("form")
    dates = recent.get("filingDate")
    if not isinstance(accessions, list) or not isinstance(forms, list) or not isinstance(dates, list):
        raise SecEdgarAdmissionError("SEC submissions payload has invalid recent filing columns.")
    if not accessions and not forms and not dates:
        return None
    if not accessions or not forms or not dates:
        raise SecEdgarAdmissionError("SEC submissions payload has incomplete recent filing metadata.")

    accession = _bounded_text(
        accessions[0],
        field="latest accession number",
        maximum=20,
    )
    if _ACCESSION_RE.fullmatch(accession) is None:
        raise SecEdgarAdmissionError("SEC submissions payload has an invalid latest accession number.")
    form = _bounded_text(forms[0], field="latest filing form", maximum=32)
    filing_date = _bounded_text(dates[0], field="latest filing date", maximum=10)
    try:
        date.fromisoformat(filing_date)
    except ValueError as exc:
        raise SecEdgarAdmissionError("SEC submissions payload has an invalid latest filing date.") from exc
    return {
        "accession_number": accession,
        "form": form,
        "filing_date": filing_date,
    }


def bounded_sec_submissions_metadata(
    payload: dict[str, object],
    *,
    expected_cik: str,
) -> dict[str, object]:
    """Reduce an exact SEC submissions response to the admitted provenance-only fields."""

    if not isinstance(payload, dict):
        raise SecEdgarAdmissionError("SEC submissions response must be a JSON object.")
    if sec_submissions_url(expected_cik) != f"https://data.sec.gov/submissions/CIK{expected_cik}.json":
        raise AssertionError("unreachable")
    if _payload_cik(payload.get("cik")) != expected_cik:
        raise SecEdgarAdmissionError("SEC submissions payload CIK does not match the requested CIK.")

    details: dict[str, object] = {
        "sec_cik": expected_cik,
        "sec_filer_name": _bounded_text(
            payload.get("name"),
            field="filer name",
            maximum=_MAX_NAME_LENGTH,
        ),
        "market_identifiers": _market_pairs(payload),
        "api_attribution": "U.S. Securities and Exchange Commission EDGAR",
        "registry_evidence": True,
        "identity_claim": False,
    }

    sic = _optional_short_text(payload, "sic", field="SIC")
    if sic is not None:
        details["sic"] = sic
    state = _optional_short_text(payload, "stateOfIncorporation", field="state of incorporation")
    if state is not None:
        details["state_of_incorporation"] = state
    fiscal_year_end = _optional_short_text(
        payload,
        "fiscalYearEnd",
        field="fiscal year end",
        pattern=_FISCAL_YEAR_END_RE,
    )
    if fiscal_year_end is not None:
        details["fiscal_year_end"] = fiscal_year_end

    latest = _latest_filing(payload)
    if latest is not None:
        details["latest_filing"] = latest
    return details
