# SEC EDGAR exact CIK admission

Status: admission contract implemented; runtime provider activation intentionally deferred until the same source-specific branch proves transport, ProviderRuntime wiring and source-state regressions.

Reviewed against SEC primary documentation on 2026-08-27.

## Why this source

SEC EDGAR is a high-provenance public registry source with no API key requirement for the submissions API. The SEC documents exact submissions JSON at `https://data.sec.gov/submissions/CIK##########.json`, where the CIK is zero-padded to ten digits. SEC also publishes explicit automated-access guidance, including a declared User-Agent requirement and a current ceiling of ten requests per second across machines.

PersonaLattice does not need anything close to that ceiling. When transport is activated, the provider will use one process-owned conservative budget, one exact request per admitted seed and no retry fan-out.

## Admitted seed

The only seed admitted by this contract is the exact documented submissions endpoint:

`https://data.sec.gov/submissions/CIK##########.json`

The parser requires HTTPS, the exact `data.sec.gov` hostname, no credentials or explicit port, no query or fragment, and a non-zero ten-digit CIK. Company-name search, ticker search, CIK lookup, browse URLs, filing-detail URLs, XBRL endpoints and guessed identifiers are deliberately outside this source.

This narrower input contract avoids an important ambiguity: filing-detail paths can refer to a submission whose reporting entity differs from the legal entity an operator intended to research. The submissions endpoint binds the request directly to the supplied CIK.

## Retained metadata

The minimizer retains only:

- zero-padded CIK;
- current filer name;
- up to eight explicitly published ticker/exchange pairs;
- optional SIC, state of incorporation and fiscal-year-end values;
- at most one latest filing summary: accession number, form and filing date;
- SEC EDGAR attribution and explicit `identity_claim=false` / registry-evidence flags.

The contract intentionally drops addresses, phone/contact fields, former names, filing primary-document paths, filing bodies, exhibits and other response content. It emits no recursive person, company, ticker, address or filing-text leads.

## Failure semantics

The admission layer fails closed on malformed URLs, invalid/zero CIKs, response CIK mismatch, malformed ticker/exchange columns and malformed latest-filing metadata. Runtime activation must preserve the existing typed provider outcomes: 404/no filer as neutral not-found; 403/429 as remote access/rate-limit outcomes; transient transport failures, malformed JSON and oversized responses as their existing provider error classes.

## Automation and privacy boundary

SEC asks automated clients to identify themselves and moderate traffic. A future adapter must use a declared PersonaLattice User-Agent with a maintainable contact address, download only the single exact submissions object needed for the supplied CIK and keep the local rate budget far below the SEC ceiling.

This source is legal-entity/filer registry evidence, not proof that a researched person controls or is identical to an SEC filer. No identity probability is derived from it. No ownership-form person expansion, officer extraction, address/contact enrichment, full-text search, bulk submissions archive or reverse enumeration is authorized.

## Primary references

- SEC EDGAR Application Programming Interfaces: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC Developer Resources / Fair Access: https://www.sec.gov/about/developer-resources
- SEC Accessing EDGAR Data: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
