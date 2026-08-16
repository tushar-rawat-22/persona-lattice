import type { CaseReadModel } from "./model";

const SUBJECT_ID = "00000000-0000-4000-8000-000000000601";
const USERNAME_ID = "00000000-0000-4000-8000-000000000602";
const EMAIL_ID = "00000000-0000-4000-8000-000000000603";
const GITHUB_CANDIDATE_ID = "00000000-0000-4000-8000-000000000611";
const REDDIT_CANDIDATE_ID = "00000000-0000-4000-8000-000000000612";
const EMAIL_PROOF_ID = "00000000-0000-4000-8000-000000000613";
const STALE_LINK_ID = "00000000-0000-4000-8000-000000000614";
const CONTRADICTION_ID = "00000000-0000-4000-8000-000000000615";

export const syntheticCase: CaseReadModel = {
  schema_version: "m6-case-read-model-v1",
  generated_at: "2026-08-16T10:00:00Z",
  subject_id: SUBJECT_ID,
  display_name: "Synthetic M6 Subject",
  identifiers: [
    {
      id: EMAIL_ID,
      kind: "email",
      value: "synthetic-m6@example.test",
    },
    {
      id: USERNAME_ID,
      kind: "username",
      value: "synthetic-m6",
    },
  ],
  observations: [
    {
      id: STALE_LINK_ID,
      identifier_id: null,
      provenance: {
        source_kind: "public_web",
        source_name: "synthetic-stale-cross-link",
        source_locator: "https://archive.example.test/profile",
      },
      retrieved_at: "2026-07-27T10:00:00Z",
      observed_at: null,
      expires_at: "2026-08-15T10:00:00Z",
      freshness: "stale",
      summary: "Expired synthetic cross-link.",
      account_candidate: false,
      identity_claim: null,
      candidate_observation_id: REDDIT_CANDIDATE_ID,
    },
    {
      id: EMAIL_PROOF_ID,
      identifier_id: null,
      provenance: {
        source_kind: "public_web",
        source_name: "synthetic-email-proof",
        source_locator: "https://portfolio.example.test/contact",
      },
      retrieved_at: "2026-08-15T10:00:00Z",
      observed_at: null,
      expires_at: "2026-08-21T10:00:00Z",
      freshness: "fresh",
      summary: "Synthetic portfolio repeats the confirmed email.",
      account_candidate: false,
      identity_claim: null,
      candidate_observation_id: REDDIT_CANDIDATE_ID,
    },
    {
      id: CONTRADICTION_ID,
      identifier_id: null,
      provenance: {
        source_kind: "public_web",
        source_name: "synthetic-contradiction",
        source_locator: "https://contradiction.example.test/fact",
      },
      retrieved_at: "2026-08-16T06:00:00Z",
      observed_at: null,
      expires_at: "2026-08-21T10:00:00Z",
      freshness: "fresh",
      summary: "Synthetic source establishes incompatible account ownership.",
      account_candidate: false,
      identity_claim: null,
      candidate_observation_id: REDDIT_CANDIDATE_ID,
    },
    {
      id: REDDIT_CANDIDATE_ID,
      identifier_id: USERNAME_ID,
      provenance: {
        source_kind: "provider",
        source_name: "sherlock",
        source_locator: "https://www.reddit.com/user/synthetic-m6",
      },
      retrieved_at: "2026-08-16T07:00:00Z",
      observed_at: null,
      expires_at: "2026-08-21T10:00:00Z",
      freshness: "fresh",
      summary: "Reddit",
      account_candidate: true,
      identity_claim: false,
      candidate_observation_id: null,
    },
    {
      id: GITHUB_CANDIDATE_ID,
      identifier_id: USERNAME_ID,
      provenance: {
        source_kind: "provider",
        source_name: "sherlock",
        source_locator: "https://github.com/synthetic-m6",
      },
      retrieved_at: "2026-08-16T08:00:00Z",
      observed_at: null,
      expires_at: "2026-08-21T10:00:00Z",
      freshness: "fresh",
      summary: "GitHub",
      account_candidate: true,
      identity_claim: false,
      candidate_observation_id: null,
    },
  ],
  claims: [
    {
      id: "00000000-0000-4000-8000-000000000621",
      statement: "Synthetic portfolio lists the confirmed email address.",
      confidence: 0.8,
      origin: "human",
      evidence_links: [
        {
          observation_id: EMAIL_PROOF_ID,
          relation: "supports",
          rationale: "Direct synthetic source text.",
        },
        {
          observation_id: CONTRADICTION_ID,
          relation: "unresolved",
          rationale: "Contradiction remains visible for operator review.",
        },
      ],
    },
  ],
  account_candidates: [
    {
      observation_id: GITHUB_CANDIDATE_ID,
      identifier_id: USERNAME_ID,
      source_name: "sherlock",
      site: "GitHub",
      profile_url: "https://github.com/synthetic-m6",
      correlation: {
        run_id: "00000000-0000-4000-8000-000000000631",
        policy_version: "m5-evidence-strength-v1",
        candidate_observation_id: GITHUB_CANDIDATE_ID,
        evaluated_at: "2026-08-16T10:00:00Z",
        outcome: "insufficient_evidence",
        evidence_score: 10,
        calibration_status: "uncalibrated",
        positive_independence_groups: 1,
        factors: [
          {
            kind: "same_username",
            independence_group: "provider:sherlock",
            base_weight: 10,
            applied_weight: 10,
            status: "applied",
            observation_ids: [GITHUB_CANDIDATE_ID],
            identifier_ids: [],
            rationale: "Same public handle only.",
            veto: false,
          },
        ],
        is_identity_claim: false,
      },
    },
    {
      observation_id: REDDIT_CANDIDATE_ID,
      identifier_id: USERNAME_ID,
      source_name: "sherlock",
      site: "Reddit",
      profile_url: "https://www.reddit.com/user/synthetic-m6",
      correlation: {
        run_id: "00000000-0000-4000-8000-000000000632",
        policy_version: "m5-evidence-strength-v1",
        candidate_observation_id: REDDIT_CANDIDATE_ID,
        evaluated_at: "2026-08-16T10:00:00Z",
        outcome: "contradicted",
        evidence_score: 0,
        calibration_status: "uncalibrated",
        positive_independence_groups: 1,
        factors: [
          {
            kind: "exact_confirmed_identifier_overlap",
            independence_group: "host:portfolio.example.test",
            base_weight: 55,
            applied_weight: 55,
            status: "applied",
            observation_ids: [EMAIL_PROOF_ID],
            identifier_ids: [EMAIL_ID],
            rationale: "Synthetic confirmed email overlap.",
            veto: false,
          },
          {
            kind: "hard_contradiction",
            independence_group: "host:contradiction.example.test",
            base_weight: -100,
            applied_weight: -100,
            status: "applied",
            observation_ids: [CONTRADICTION_ID],
            identifier_ids: [],
            rationale: "Synthetic hard contradiction.",
            veto: true,
          },
          {
            kind: "independent_cross_link",
            independence_group: "host:archive.example.test",
            base_weight: 35,
            applied_weight: 0,
            status: "excluded_stale",
            observation_ids: [STALE_LINK_ID],
            identifier_ids: [],
            rationale: "Synthetic cross-link is stale.",
            veto: false,
          },
        ],
        is_identity_claim: false,
      },
    },
  ],
};

export const noEvidenceCase: CaseReadModel = {
  ...syntheticCase,
  generated_at: "2026-08-16T10:00:00Z",
  display_name: "Synthetic M6 Subject — no evidence",
  observations: [],
  claims: [],
  account_candidates: [],
};

export function validateSyntheticFixture(caseData: CaseReadModel): CaseReadModel {
  if (caseData.schema_version !== "m6-case-read-model-v1") {
    throw new Error("Unexpected M6 fixture schema version.");
  }

  for (const candidate of caseData.account_candidates) {
    const correlation = candidate.correlation;
    if (!correlation) {
      continue;
    }
    if (correlation.calibration_status !== "uncalibrated") {
      throw new Error("M6 fixture correlation must remain uncalibrated.");
    }
    if (correlation.is_identity_claim !== false) {
      throw new Error("M6 fixture correlation must remain non-identity evidence.");
    }
  }
  return caseData;
}
