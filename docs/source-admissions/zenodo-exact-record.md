# Zenodo exact record source admission

Reviewed 2026-08-21 against current Zenodo/CERN primary documentation.

## Admitted use

PersonaLattice accepts only an explicit canonical `https://zenodo.org/records/<positive-id>` URL and performs one credentialless `GET https://zenodo.org/api/records/<id>`. Zenodo documents anonymous public record retrieval, publicly accessible record metadata, CC0 metadata reuse by default, and current guest limits of 60 requests per minute and 2,000 requests per hour.

PersonaLattice stays below those limits: one attempt, one concurrent request, four seconds, 30 requests per minute, and a 32 KiB raw-response ceiling. An oversized record fails closed rather than increasing the adapter ceiling.

The retained observation is deliberately smaller than the provider record:

- canonical Zenodo record ID;
- one title, capped at 512 characters;
- `data_license=CC0`;
- Zenodo/CERN attribution;
- canonical record locator;
- `identity_claim=false`.

Descriptions, creators, affiliations, ORCID identifiers, files, checksums, communities, grants, related identifiers, geolocation, uploader/account metadata and version links are discarded. The source emits no leads.

## Excluded use

No record search, DOI-to-record guessing, creator/community/keyword search, OAI harvesting, metadata dumps, file downloads, restricted-content access, access-request workflow, version traversal or bulk enumeration.
