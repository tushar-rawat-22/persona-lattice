export type IdentifierKind =
  | "name"
  | "phone"
  | "email"
  | "username"
  | "url"
  | "organization";

export type ObservationSourceKind =
  | "user_supplied"
  | "public_web"
  | "public_profile"
  | "public_document"
  | "provider"
  | "registry"
  | "upload";

export type FreshnessState = "fresh" | "stale" | "unknown";
export type ClaimOrigin = "human" | "rule" | "ai";
export type EvidenceRelation = "supports" | "contradicts" | "unresolved";

export type CorrelationOutcome =
  | "insufficient_evidence"
  | "possible_match"
  | "strong_candidate"
  | "contradicted";

export type FactorKind =
  | "same_username"
  | "exact_confirmed_identifier_overlap"
  | "independent_cross_link"
  | "compatible_profile_metadata"
  | "temporal_compatibility"
  | "hard_contradiction";

export type FactorStatus =
  | "applied"
  | "applied_unknown_freshness"
  | "not_applicable"
  | "excluded_stale"
  | "suppressed_same_independence_group";

export type IdentifierView = {
  id: string;
  kind: IdentifierKind;
  value: string;
};

export type ProvenanceView = {
  source_kind: ObservationSourceKind;
  source_name: string;
  source_locator: string;
};

export type ObservationView = {
  id: string;
  identifier_id: string | null;
  provenance: ProvenanceView;
  retrieved_at: string;
  observed_at: string | null;
  expires_at: string | null;
  freshness: FreshnessState;
  summary: string;
  account_candidate: boolean;
  identity_claim: boolean | null;
  candidate_observation_id: string | null;
};

export type EvidenceLinkView = {
  observation_id: string;
  relation: EvidenceRelation;
  rationale: string | null;
};

export type ClaimView = {
  id: string;
  statement: string;
  confidence: number;
  origin: ClaimOrigin;
  evidence_links: EvidenceLinkView[];
};

export type CorrelationFactorView = {
  kind: FactorKind;
  independence_group: string;
  base_weight: number;
  applied_weight: number;
  status: FactorStatus;
  observation_ids: string[];
  identifier_ids: string[];
  rationale: string;
  veto: boolean;
};

export type CorrelationView = {
  run_id: string;
  policy_version: string;
  candidate_observation_id: string;
  evaluated_at: string;
  outcome: CorrelationOutcome;
  evidence_score: number;
  calibration_status: "uncalibrated";
  positive_independence_groups: number;
  factors: CorrelationFactorView[];
  is_identity_claim: false;
};

export type AccountCandidateView = {
  observation_id: string;
  identifier_id: string;
  source_name: string;
  site: string | null;
  profile_url: string;
  correlation: CorrelationView | null;
};

export type CaseReadModel = {
  schema_version: "m6-case-read-model-v1";
  generated_at: string;
  subject_id: string;
  display_name: string | null;
  identifiers: IdentifierView[];
  observations: ObservationView[];
  claims: ClaimView[];
  account_candidates: AccountCandidateView[];
};
