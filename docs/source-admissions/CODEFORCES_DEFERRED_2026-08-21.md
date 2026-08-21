# Codeforces public API — deferred

**Decision:** do not execute Codeforces profile enrichment in the commercial-product baseline.

Review date: 2026-08-21.

Primary sources reviewed:

- Codeforces API help and `user.info` method documentation;
- current Codeforces Terms and Conditions.

The technical API boundary is clear: `user.info` can be requested anonymously for public data, and Codeforces limits API calls to one request per two seconds. That is not enough to approve commercial product use.

The current Terms expressly prohibit selling, sublicensing or otherwise commercializing Website material. The review found no Codeforces-authored API terms, data license or other primary statement that clearly grants a future commercial PersonaLattice SaaS the right to use public profile metadata despite that restriction. Public availability and anonymous access are not treated as commercial-use permission.

PersonaLattice therefore keeps the historical source name and provider implementation for retained-case/read compatibility, but current execution is quarantined:

- source catalog status is `review_required`;
- `source_policy_reviewed=false` and recursive eligibility is disabled;
- the source has no executable source binding;
- the provider descriptor is `review_required`, so central provider policy rejects execution before credentials or network I/O;
- attempted historical evidence remains readable and is not rewritten or deleted;
- no profile-URL expansion or field expansion is approved.

Reconsider only if materially clearer current Codeforces primary documentation establishes a commercial API/data-use basis. Any future reactivation requires a fresh terms/privacy review and its own reviewed implementation change; it must not be inferred from anonymous API availability alone.
