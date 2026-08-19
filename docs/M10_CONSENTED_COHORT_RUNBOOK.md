# M10 consented cohort runner

Use this runner only for a private cohort whose labels are backed by consented or independently reviewed evidence. Synthetic regression fixtures already live in the repository; this path exists so real identifiers do not have to.

The input JSON stays on the operator machine. PersonaLattice reads it, evaluates the current graph policy against the existing depth-3 diagnostic candidate, and prints aggregate counts plus cryptographic replay/provenance digests. It does not print seed values, lead values, source locators or the external evidence record.

## Before you create a cohort

Keep the supporting consent/review record outside Git. Each fixture needs a lowercase SHA-256 digest that refers to that external record. Do not use a bare hash of an email address, phone number, name or other low-entropy identifier as the evidence record.

Use opaque fixture and cohort names. Do not put a person's name, email address or phone number in those labels because the cohort name is included in the aggregate output for operator bookkeeping.

## File shape

```json
{
  "schema_version": 1,
  "cohort_name": "reviewed-cohort-001",
  "fixtures": [
    {
      "name": "case-001",
      "evidence_digest": "<64 lowercase hex characters>",
      "seed": {
        "id": "seed",
        "kind": "username",
        "value": "example-handle"
      },
      "nodes": [
        {
          "id": "profile",
          "parent_id": "seed",
          "kind": "url",
          "value": "https://example.invalid/profile/example-handle",
          "reason": "public_url",
          "disposition": "auto_pivot",
          "source": "reviewed-evidence",
          "source_locator": "https://example.invalid/evidence/1",
          "field_name": "profile_url",
          "relevance": "relevant"
        }
      ]
    }
  ]
}
```

`id` and `parent_id` are local aliases inside one fixture. A child may reference only the seed or an earlier automatic lead whose simulated provider did not fail. This prevents a file from claiming traversal through a lead that the frontier could never execute.

For an automatic lead, `relevance` must be `relevant` or `wrong` if that lead can be admitted by either evaluated scenario. The consented-analysis boundary fails closed when an admitted pivot is unlabelled.

Optional fixture fields:

- `provider_fails: true` models an attempted provider failure and cannot be combined with `actual_value` or `relevance`.
- `actual_value` models a provider returning a canonical value different from the emitted candidate; it must have the same lead kind.

The runner uses the existing `LeadKind`, `LeadReason` and `LeadDisposition` values. Identifiers are normalized through the same M1-backed path used by PersonaLattice, not by a separate evaluation-only normalizer.

## Run it

From the repository root with the API environment installed:

```bash
cd services/api
python -m app.intelligence.m10_consented_runner /absolute/path/to/private-cohort.json
```

The command writes one compact JSON object to stdout. Store that aggregate result wherever you keep experiment records; do not copy the private input file into the repository.

## What the output means

The output contains:

- the SHA-256 digest of the exact local input bytes;
- the existing deterministic replay input/result digests;
- the label-provenance manifest digest;
- the consented-analysis digest;
- aggregate scenario counts and exact numerator/denominator fractions.

Those values prove which experiment definition produced the result. They do **not** prove calibration, identity probability, population false-positive rates or representative performance.

Production remains depth 2 / 12 nodes unless broader defensible evidence supports a change. The depth-3 result is diagnostic only.
