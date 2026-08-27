# SPDX-License-Identifier: Apache-2.0
import pytest

from app.intelligence.sec_edgar_admission import (
    SecEdgarAdmissionError,
    bounded_sec_submissions_metadata,
    sec_cik_from_submissions_url,
    sec_submissions_url,
)


CIK = "0000320193"
URL = "https://data.sec.gov/submissions/CIK0000320193.json"


def _payload() -> dict[str, object]:
    return {
        "cik": 320193,
        "name": "Apple Inc.",
        "sic": "3571",
        "stateOfIncorporation": "CA",
        "fiscalYearEnd": "0927",
        "tickers": ["AAPL"],
        "exchanges": ["Nasdaq"],
        "addresses": {
            "business": {"street1": "ONE APPLE PARK WAY"},
        },
        "phone": "(408) 996-1010",
        "formerNames": [{"name": "APPLE COMPUTER INC"}],
        "filings": {
            "recent": {
                "accessionNumber": ["0000320193-26-000100"],
                "filingDate": ["2026-08-01"],
                "form": ["10-Q"],
                "primaryDocument": ["aapl-20260627.htm"],
            }
        },
    }


def test_accepts_only_exact_documented_submissions_url() -> None:
    assert sec_cik_from_submissions_url(URL) == CIK
    assert sec_submissions_url(CIK) == URL


@pytest.mark.parametrize(
    "value",
    [
        "http://data.sec.gov/submissions/CIK0000320193.json",
        "https://www.sec.gov/submissions/CIK0000320193.json",
        "https://data.sec.gov/submissions/CIK320193.json",
        "https://data.sec.gov/submissions/CIK0000000000.json",
        "https://data.sec.gov/submissions/CIK0000320193.json?x=1",
        "https://data.sec.gov/submissions/CIK0000320193.json#fragment",
        "https://user@data.sec.gov/submissions/CIK0000320193.json",
        "https://data.sec.gov:443/submissions/CIK0000320193.json",
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json",
        "https://www.sec.gov/edgar/browse/?CIK=320193&owner=exclude&action=getcompany",
        "https://data.sec.gov/submissions/CIK0000320193.json/extra",
    ],
)
def test_rejects_noncanonical_or_broader_sec_urls(value: str) -> None:
    assert sec_cik_from_submissions_url(value) is None


@pytest.mark.parametrize("cik", ["320193", "0000000000", "000032019x", "00000320193"])
def test_canonical_url_builder_rejects_invalid_ciks(cik: str) -> None:
    with pytest.raises(SecEdgarAdmissionError):
        sec_submissions_url(cik)


def test_minimizes_response_to_admitted_registry_fields() -> None:
    details = bounded_sec_submissions_metadata(_payload(), expected_cik=CIK)

    assert details == {
        "sec_cik": CIK,
        "sec_filer_name": "Apple Inc.",
        "market_identifiers": [{"ticker": "AAPL", "exchange": "Nasdaq"}],
        "api_attribution": "U.S. Securities and Exchange Commission EDGAR",
        "registry_evidence": True,
        "identity_claim": False,
        "sic": "3571",
        "state_of_incorporation": "CA",
        "fiscal_year_end": "0927",
        "latest_filing": {
            "accession_number": "0000320193-26-000100",
            "form": "10-Q",
            "filing_date": "2026-08-01",
        },
    }
    serialized = repr(details)
    assert "ONE APPLE PARK WAY" not in serialized
    assert "996-1010" not in serialized
    assert "APPLE COMPUTER INC" not in serialized
    assert "primaryDocument" not in serialized


def test_caps_ticker_exchange_pairs_without_emitting_leads() -> None:
    payload = _payload()
    payload["tickers"] = [f"T{i}" for i in range(12)]
    payload["exchanges"] = [f"E{i}" for i in range(12)]

    details = bounded_sec_submissions_metadata(payload, expected_cik=CIK)

    pairs = details["market_identifiers"]
    assert isinstance(pairs, list)
    assert len(pairs) == 8
    assert details["identity_claim"] is False


def test_accepts_empty_recent_filings_as_no_latest_filing() -> None:
    payload = _payload()
    payload["filings"] = {
        "recent": {
            "accessionNumber": [],
            "filingDate": [],
            "form": [],
        }
    }

    details = bounded_sec_submissions_metadata(payload, expected_cik=CIK)

    assert "latest_filing" not in details


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("cik", 123456),
        ("name", ""),
        ("fiscalYearEnd", "927"),
        ("tickers", "AAPL"),
        ("exchanges", "Nasdaq"),
    ],
)
def test_rejects_malformed_or_mismatched_payload(field: str, value: object) -> None:
    payload = _payload()
    payload[field] = value

    with pytest.raises(SecEdgarAdmissionError):
        bounded_sec_submissions_metadata(payload, expected_cik=CIK)


def test_rejects_mismatched_market_columns() -> None:
    payload = _payload()
    payload["exchanges"] = []

    with pytest.raises(SecEdgarAdmissionError):
        bounded_sec_submissions_metadata(payload, expected_cik=CIK)


def test_rejects_incomplete_or_invalid_latest_filing() -> None:
    payload = _payload()
    payload["filings"] = {
        "recent": {
            "accessionNumber": ["bad"],
            "filingDate": ["2026-99-99"],
            "form": ["10-Q"],
        }
    }

    with pytest.raises(SecEdgarAdmissionError):
        bounded_sec_submissions_metadata(payload, expected_cik=CIK)


def test_expected_cik_is_itself_fail_closed() -> None:
    with pytest.raises(SecEdgarAdmissionError):
        bounded_sec_submissions_metadata(_payload(), expected_cik="320193")
