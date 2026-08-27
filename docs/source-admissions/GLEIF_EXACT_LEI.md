# GLEIF exact LEI source admission

Reviewed: 2026-08-27

## Decision

Admit GLEIF only when the operator supplies an exact canonical Global LEI Index record URL in the form `https://search.gleif.org/#/record/<LEI>`.

The source is legal-entity verification, not a people-search source. It does not search by company name, address, person, BIC, ISIN or other mapped identifier, and it does not traverse parent/child ownership relationships.

## Why this source is acceptable

GLEIF provides the production API for the Global LEI Index and documents API access to LEI reference data. Its API can technically do broad search, fuzzy matching, mapped-identifier lookup and corporate-structure exploration. PersonaLattice deliberately does not use those capabilities.

GLEIF publishes LEI data for access and reuse and makes the LEI reference dataset available under CC0. LEIs are 20-character alphanumeric identifiers for legal entities. GLEIF's supporting material also requires correct ISO 17442 check digits, so PersonaLattice validates both the character format and MOD 97-10 checksum before any provider call.

Primary material reviewed:

- https://www.gleif.org/en/lei-data/gleif-api
- https://www.gleif.org/en/lei-data/access-and-use-lei-data/
- https://www.gleif.org/en/lei-data/access-and-use-lei-data/supporting-documents
- https://www.gleif.org/lei-data/access-and-use-lei-data/2022-02-22_cdf_questions_and_answers_v2.4.pdf

## Runtime boundary

Applicability is intentionally narrow:

- HTTPS only;
- host must be exactly `search.gleif.org`;
- no credentials, custom port or query string;
- path must be `/`;
- fragment must be exactly `/record/<LEI>`;
- the LEI must be uppercase, 20 characters, end in two numeric check digits and pass MOD 97-10 validation.

Only then does the adapter call the official `api.gleif.org` production API with an exact `filter[lei]` request and `page[size]=1`. A zero-row response is a completed no-match. More than one row is treated as malformed/ambiguous provider output rather than silently choosing a record.

The returned JSON:API record must identify the exact requested LEI both as the record ID and in the LEI attribute. Mismatches fail closed.

## Retained evidence

PersonaLattice retains only a small legal-entity verification surface:

- LEI;
- legal name;
- entity status;
- LEI registration status;
- legal jurisdiction when present;
- last update timestamp when present;
- GLEIF attribution;
- CC0 marker;
- canonical GLEIF record locator;
- `identity_claim=false`.

The adapter intentionally ignores legal/headquarters addresses, other names, mapped BIC/MIC/ISIN-like identifiers, registration-authority details, managing LOU metadata, relationships, parent/child ownership data and other expansion fields. Provider-specific field names are display-only and emit no recursive leads.

## Operational limits

The source is credentialless and has zero direct API cost. PersonaLattice still imposes one attempt, a four-second timeout, a 128 KiB response ceiling, one concurrent call and a local ten-request-per-minute budget.

HTTP 429 preserves a valid `Retry-After`. Network failures and 408/5xx responses remain typed transient attempted failures. Malformed JSON, unexpected record shapes, mismatched LEIs and invalid required fields are post-attempt validation failures.

## Privacy and product boundary

GLEIF's API supports broader entity discovery than PersonaLattice needs. Those broader capabilities stay disabled because they would turn an exact legal-entity verifier into a search/enumeration system and would add weak or unnecessary pivots to person-oriented research.

This admission does not justify searching for a legal entity from a person's name, resolving ownership networks, or inferring that a legal entity belongs to the subject. The exact record URL is evidence supplied by the operator; the GLEIF response only verifies bounded public legal-entity metadata for that record.
