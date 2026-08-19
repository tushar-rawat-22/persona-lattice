# M10 independently reviewed cohort runner

Use this runner only when each fixture label is backed by an external independent review record. This is not a substitute for consent, and it is not a way to promote synthetic fixtures into stronger evidence.

The private JSON stays on the operator machine. PersonaLattice materializes the existing M10 graph-fixture contract, evaluates the production depth-2 / 12-node policy against the existing depth-3 diagnostic candidate, and prints aggregate counts plus replay/provenance digests. Raw identifiers, fixture names, source locators and review records are not printed.

## Evidence record

Keep the review record outside Git. Each fixture needs a lowercase SHA-256 digest that refers to that external record. The record should explain what was reviewed, the basis for each relevance label and who or what process performed the review.

Do not use a bare hash of an email address, phone number, name or another low-entropy identifier as the review record. That does not establish review provenance.

The JSON cannot declare its own evidence basis. The runner fixes the basis to `independently_reviewed`; `basis` and `label_basis` fields are rejected.

## File shape

The structure matches the consented local cohort format so both paths share one bounded parser and normalization contract:

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
          "source": "review-evidence",
          "source_locator": "https://example.invalid/evidence/1",
          "field_name": "profile_url",
          "relevance": "relevant"
        }
      ]
    }
  ]
}
```

A child may reference only the seed or an earlier successful automatic pivot. Any automatic pivot that can be admitted by an evaluated scenario must have a `relevant` or `wrong` label. The reviewed-analysis boundary fails closed when an admitted pivot is unlabelled.

Optional node fields:

- `provider_fails: true` models an attempted provider failure and cannot be combined with `actual_value` or `relevance`.
- `actual_value` models a provider returning a canonical value different from the emitted candidate; it must use the same lead kind.

The shared materializer enforces the same file-size, fixture-count, node-count and M1-backed normalization limits as the consented runner.

## Run it

From the repository root with the API environment installed:

```bash
cd services/api
python -m app.intelligence.m10_reviewed_runner /absolute/path/to/private-reviewed-cohort.json
```

The command writes one compact JSON object to stdout. Validation failures return one generic message so parser details cannot echo private values into terminal logs.

## Interpreting the result

The output includes the local input digest, a digest of the cohort name, deterministic replay digests, the reviewed label-manifest digest, the reviewed-analysis digest and aggregate scenario accounting.

These counts describe this reviewed corpus only. They are not population false-positive/false-negative rates, calibration evidence, confidence or identity probability. A reviewed cohort also does not become consented because it passed this runner.

Production remains depth 2 / 12 nodes. The depth-3 scenario remains diagnostic.
