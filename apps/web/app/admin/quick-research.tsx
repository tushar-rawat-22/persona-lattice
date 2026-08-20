"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const CONNECTED_IDENTIFIER_FIELD_BY_KIND: Record<string, string> = {
  email: "email",
  username: "twitter_username",
  url: "blog",
  location_claim: "location",
  organization_claim: "company",
};

type ResearchKind = "username" | "phone" | "email" | "url" | "domain";

const PLACEHOLDER_BY_KIND: Record<ResearchKind, string> = {
  username: "@handle",
  phone: "+1 415 555 0123",
  email: "person@example.com",
  url: "https://example.com/profile",
  domain: "example.com",
};

type Observation = {
  source: string;
  source_locator: string;
  summary: string;
  details: Record<string, unknown>;
};

type SourceRunRecord = {
  source: string;
  lead_kind: string;
  state: string;
  reason: string;
  observation_count: number;
  execution_attempted: boolean;
  terminal: boolean;
};

type SourceEvaluationAggregate = {
  record_count: number;
  attempt_count: number;
  completed_attempt_count: number;
  failed_attempt_count: number;
  unclassified_attempt_count: number;
  result_record_count: number;
  no_match_count: number;
  withheld_count: number;
  observation_count: number;
  public_web_opt_out_count: number;
  account_unavailable_count: number;
  remote_rate_limit_count: number;
  execution_failure_count: number;
  malformed_result_count: number;
  routing_unavailable_count: number;
  local_budget_stop_count: number;
  optional_not_configured_count: number;
  missing_secret_config_count: number;
  provider_policy_block_count: number;
  queued_count: number;
  review_required_count: number;
  display_only_count: number;
  blocked_count: number;
};

type SourceRunReport = {
  record_count: number;
  execution_attempted_count: number;
  terminal_count: number;
  state_counts: Record<string, number>;
  reason_counts: Record<string, number>;
  records: SourceRunRecord[];
  evaluation?: {
    aggregate: SourceEvaluationAggregate;
    by_source: Record<string, SourceEvaluationAggregate>;
  };
};

type SeedProvenance = {
  source: string;
  source_locator: string;
  review_required: boolean;
  human_reviewed: boolean;
};

type ConnectedIdentifier = {
  kind: string;
  status: string;
  observation_index?: number;
  detail_field?: string;
  // Read-only compatibility for cases retained before ADR 0045.
  value?: string;
  source?: string;
  source_locator?: string;
};

type StructuredReport = {
  executive_summary: {
    observation_count: number;
    source_count: number;
    sources: string[];
    connected_identifier_count: number;
    public_account_candidate_count: number;
    identity_probability: null;
    identity_claim: false;
    interpretation: string;
  };
  connected_identifiers: ConnectedIdentifier[];
  coverage_gaps: string[];
  provenance_rule: string;
};

type M5Evaluation = {
  candidate_node: string;
  candidate_observation_index?: number;
  // Read-only compatibility for retained cases created before ADR 0043.
  candidate_source?: string;
  candidate_source_locator?: string;
  outcome: string;
  evidence_score: number;
  calibration_status: "uncalibrated";
  positive_independence_groups: number;
  is_identity_claim: false;
  policy_version: string;
  input_digest: string;
  output_digest: string;
  factors: Array<{
    kind: string;
    independence_group: string;
    base_weight: number;
    applied_weight: number;
    status: string;
    rationale: string;
    veto: boolean;
  }>;
};

type LeadDecision = {
  parent_key: string;
  child_key: string | null;
  reason: string;
  decision: string;
  source_observation_index?: number;
  source_field?: string;
};

type ConvergedEdge = {
  parent_key: string;
  child_key: string;
  reason: string;
  lead_decision_index?: number;
  // Read-only compatibility for cases retained before ADR 0044.
  source?: string;
  source_locator?: string;
};

type ConvergedReport = {
  report_version: string;
  seed: { kind: ResearchKind; normalized_value: string };
  executive_summary: {
    research_node_count: number;
    pivot_edge_count: number;
    source_count: number;
    sources: string[];
    identity_probability: null;
    identity_claim: false;
    truncated: boolean;
    interpretation: string;
  };
  nodes: Array<{
    key: string;
    kind: ResearchKind;
    normalized_value: string;
    depth: number;
    parent_key: string | null;
    pivot_reason: string;
    warnings: string[];
    source_runs?: SourceRunReport;
    observations: Observation[];
  }>;
  edges: ConvergedEdge[];
  lead_graph?: {
    decisions: LeadDecision[];
  };
  warnings: string[];
  provenance_rule: string;
  m5: {
    engine: string;
    evaluated_at: string;
    identifier_count: number;
    observation_count: number;
    candidate_count: number;
    evaluations: M5Evaluation[];
    calibration_status: "uncalibrated";
    is_identity_claim: false;
    interpretation: string;
  };
};

type QuickReport = {
  kind: ResearchKind;
  normalized_value: string;
  observations?: Observation[];
  warnings?: string[];
  source_runs?: SourceRunReport;
  seed_provenance?: SeedProvenance;
  structured_report?: StructuredReport;
  converged_report?: ConvergedReport;
};

type StoredCaseSummary = {
  id: string;
  created_at: string;
  expires_at: string;
  seed_kind: ResearchKind;
  seed_value: string;
};

type StoredCase = StoredCaseSummary & {
  report: QuickReport;
};

type QuickResearchProps = {
  csrfToken: string;
};

type ResolvedProvenance = {
  source: string;
  source_locator: string;
};

type ResolvedPivotProvenance = ResolvedProvenance & {
  source_field: string | null;
  observation_summary: string | null;
};

type ResolvedConnectedIdentifier = ResolvedProvenance & {
  value: string;
};

type SourceOutcomeDetail = {
  label: string;
  count: number;
  note: string;
};

async function request(path: string, init?: RequestInit, csrfToken?: string) {
  const method = (init?.method ?? "GET").toUpperCase();
  const unsafe = !["GET", "HEAD", "OPTIONS"].includes(method);
  return fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(init?.headers ?? {}),
      ...(unsafe && csrfToken ? { "X-PersonaLattice-CSRF": csrfToken } : {}),
    },
  });
}

function nonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function sourceOutcomeDetails(aggregate: SourceEvaluationAggregate): SourceOutcomeDetail[] {
  return [
    { label: "Public-web opt-out", count: aggregate.public_web_opt_out_count, note: "neutral withheld result" },
    { label: "Account unavailable", count: aggregate.account_unavailable_count, note: "neutral withheld result" },
    { label: "Remote rate limit", count: aggregate.remote_rate_limit_count, note: "provider attempt failed" },
    { label: "Execution failure", count: aggregate.execution_failure_count, note: "provider attempt failed" },
    { label: "Malformed provider result", count: aggregate.malformed_result_count, note: "provider attempt failed" },
    { label: "Routing unavailable", count: aggregate.routing_unavailable_count, note: "routing authority unavailable · no provider attempt" },
    { label: "Local budget stop", count: aggregate.local_budget_stop_count, note: "no provider attempt" },
    { label: "Optional source not configured", count: aggregate.optional_not_configured_count, note: "no provider attempt" },
    { label: "Credential not configured", count: aggregate.missing_secret_config_count, note: "no provider attempt" },
    { label: "Provider policy block", count: aggregate.provider_policy_block_count, note: "no provider attempt" },
    { label: "Queued", count: aggregate.queued_count, note: "not executed in this scope" },
    { label: "Review required", count: aggregate.review_required_count, note: "not executed in this scope" },
    { label: "Display only", count: aggregate.display_only_count, note: "not executable by policy" },
    { label: "Blocked", count: aggregate.blocked_count, note: "not executed in this scope" },
  ].filter((item) => item.count > 0);
}

function resolveConnectedIdentifier(
  report: QuickReport,
  item: ConnectedIdentifier,
): ResolvedConnectedIdentifier | null {
  const hasLegacy = item.value !== undefined || item.source !== undefined || item.source_locator !== undefined;
  const hasReference = item.observation_index !== undefined || item.detail_field !== undefined;

  if (hasLegacy && hasReference) return null;
  if (hasLegacy) {
    if (!nonEmptyString(item.value) || !nonEmptyString(item.source) || !nonEmptyString(item.source_locator)) {
      return null;
    }
    return { value: item.value, source: item.source, source_locator: item.source_locator };
  }

  if (!Number.isInteger(item.observation_index) || (item.observation_index ?? -1) < 0) return null;
  if (!nonEmptyString(item.detail_field)) return null;
  if (CONNECTED_IDENTIFIER_FIELD_BY_KIND[item.kind] !== item.detail_field) return null;

  const observation = (report.observations ?? [])[item.observation_index as number];
  if (!observation || !nonEmptyString(observation.source) || !nonEmptyString(observation.source_locator)) {
    return null;
  }
  const value = observation.details[item.detail_field];
  if (!nonEmptyString(value)) return null;

  return {
    value,
    source: observation.source,
    source_locator: observation.source_locator,
  };
}

function resolveM5Candidate(report: ConvergedReport, evaluation: M5Evaluation): Observation | null {
  if (!Number.isInteger(evaluation.candidate_observation_index) || (evaluation.candidate_observation_index ?? -1) < 0) {
    return null;
  }
  const node = report.nodes.find((item) => item.key === evaluation.candidate_node);
  if (!node) return null;
  return node.observations[evaluation.candidate_observation_index as number] ?? null;
}

function m5EvaluationKey(evaluation: M5Evaluation): string {
  if (Number.isInteger(evaluation.candidate_observation_index)) {
    return `${evaluation.candidate_node}-${evaluation.candidate_observation_index}`;
  }
  return `${evaluation.candidate_node}-${evaluation.candidate_source_locator ?? evaluation.candidate_source ?? "legacy"}`;
}

function resolveEdgeProvenance(report: ConvergedReport, edge: ConvergedEdge): ResolvedPivotProvenance | null {
  const hasLegacy = edge.source !== undefined || edge.source_locator !== undefined;
  const hasReference = edge.lead_decision_index !== undefined;

  if (hasLegacy && hasReference) return null;
  if (hasLegacy) {
    if (!nonEmptyString(edge.source) || !nonEmptyString(edge.source_locator)) return null;
    return {
      source: edge.source,
      source_locator: edge.source_locator,
      source_field: null,
      observation_summary: null,
    };
  }

  if (!Number.isInteger(edge.lead_decision_index) || (edge.lead_decision_index ?? -1) < 0) return null;
  const decision = report.lead_graph?.decisions[edge.lead_decision_index as number];
  if (!decision || decision.decision !== "admitted") return null;
  if (
    decision.parent_key !== edge.parent_key ||
    decision.child_key !== edge.child_key ||
    decision.reason !== edge.reason
  ) {
    return null;
  }
  if (!Number.isInteger(decision.source_observation_index) || (decision.source_observation_index ?? -1) < 0) {
    return null;
  }
  if (!nonEmptyString(decision.source_field)) return null;

  const parentMatches = report.nodes.filter((node) => node.key === decision.parent_key);
  if (parentMatches.length !== 1) return null;
  const observation = parentMatches[0].observations[decision.source_observation_index as number];
  if (!observation || !nonEmptyString(observation.source) || !nonEmptyString(observation.source_locator)) {
    return null;
  }
  if (!(decision.source_field in observation.details)) return null;

  return {
    source: observation.source,
    source_locator: observation.source_locator,
    source_field: decision.source_field,
    observation_summary: nonEmptyString(observation.summary) ? observation.summary : null,
  };
}

function SourceRunSummary({ sourceRuns, title }: { sourceRuns?: SourceRunReport; title: string }) {
  if (!sourceRuns) {
    return (
      <div className="reportSection">
        <h3>{title}</h3>
        <p className="muted">Source execution state is unavailable for this historical case.</p>
      </div>
    );
  }

  const aggregate = sourceRuns.evaluation?.aggregate;
  const missingEvidenceReasons = aggregate ? sourceOutcomeDetails(aggregate) : [];
  return (
    <div className="reportSection">
      <h3>{title}</h3>
      <div className="reportMetricGrid">
        <div><strong>{sourceRuns.record_count}</strong><span>source records</span></div>
        <div><strong>{aggregate?.attempt_count ?? sourceRuns.execution_attempted_count}</strong><span>attempts</span></div>
        <div><strong>{aggregate?.completed_attempt_count ?? "—"}</strong><span>completed</span></div>
        <div><strong>{aggregate?.failed_attempt_count ?? "—"}</strong><span>failed attempts</span></div>
      </div>
      {aggregate && (
        <p className="muted">
          {aggregate.observation_count} observations · {aggregate.no_match_count} no-match results · {aggregate.withheld_count} withheld results
        </p>
      )}
      {missingEvidenceReasons.length > 0 && (
        <div>
          <strong>Why evidence may be missing</strong>
          <ul className="coverageList">
            {missingEvidenceReasons.map((item) => (
              <li key={item.label}>{item.count} {item.label.toLowerCase()} · {item.note}</li>
            ))}
          </ul>
        </div>
      )}
      {sourceRuns.records.length === 0 ? (
        <p className="muted">No typed source-run records were retained for this scope.</p>
      ) : (
        <div className="connectedGrid">
          {sourceRuns.records.map((item, index) => (
            <div className="connectedField" key={`${item.source}-${item.lead_kind}-${index}`}>
              <span>{item.state}</span>
              <strong>{item.source}</strong>
              <small>{item.lead_kind} · {item.reason}</small>
              <small>{item.execution_attempted ? "execution attempted" : "no execution attempt"} · {item.observation_count} observations</small>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function QuickResearch({ csrfToken }: QuickResearchProps) {
  const [kind, setKind] = useState<ResearchKind>("username");
  const [value, setValue] = useState("");
  const [activeCase, setActiveCase] = useState<StoredCase | null>(null);
  const [recentCases, setRecentCases] = useState<StoredCaseSummary[]>([]);
  const [nextCaseCursor, setNextCaseCursor] = useState<string | null>(null);
  const [loadingOlderCases, setLoadingOlderCases] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const refreshCases = useCallback(async () => {
    const response = await request("/v1/cases?limit=8");
    if (!response.ok) return;
    setRecentCases((await response.json()) as StoredCaseSummary[]);
    setNextCaseCursor(response.headers.get("X-PersonaLattice-Next-Cursor"));
  }, []);

  useEffect(() => {
    let active = true;
    request("/v1/cases?limit=8")
      .then(async (response) => {
        if (!response.ok) return null;
        return {
          items: (await response.json()) as StoredCaseSummary[],
          cursor: response.headers.get("X-PersonaLattice-Next-Cursor"),
        };
      })
      .then((page) => {
        if (active && page) {
          setRecentCases(page.items);
          setNextCaseCursor(page.cursor);
        }
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setActiveCase(null);
    setBusy(true);
    try {
      const response = await request(
        "/v1/cases/run-converged",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            kind,
            value,
            purpose: "public_source_research",
            consent_acknowledged: false,
          }),
        },
        csrfToken,
      );
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(
          typeof body.detail === "string" ? body.detail : "Research request failed.",
        );
      }
      const stored = body as StoredCase;
      setActiveCase(stored);
      setValue(stored.seed_value);
      await refreshCases();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Research request failed.");
    } finally {
      setBusy(false);
    }
  }

  async function openCase(caseId: string) {
    setError("");
    const response = await request(`/v1/cases/${caseId}`);
    if (!response.ok) {
      setError("Stored case could not be loaded.");
      return;
    }
    setActiveCase((await response.json()) as StoredCase);
  }

  async function deleteCase(caseId: string) {
    const response = await request(
      `/v1/cases/${caseId}`,
      { method: "DELETE" },
      csrfToken,
    );
    if (!response.ok && response.status !== 404) {
      setError("Stored case could not be deleted.");
      return;
    }
    if (activeCase?.id === caseId) setActiveCase(null);
    await refreshCases();
  }

  async function loadOlderCases() {
    if (!nextCaseCursor || loadingOlderCases) return;
    setError("");
    setLoadingOlderCases(true);
    try {
      const response = await request(
        `/v1/cases?limit=8&cursor=${encodeURIComponent(nextCaseCursor)}`,
      );
      if (!response.ok) {
        setError("Older stored cases could not be loaded.");
        return;
      }
      const page = (await response.json()) as StoredCaseSummary[];
      setRecentCases((current) => {
        const existingIds = new Set(current.map((item) => item.id));
        return [...current, ...page.filter((item) => !existingIds.has(item.id))];
      });
      setNextCaseCursor(response.headers.get("X-PersonaLattice-Next-Cursor"));
    } finally {
      setLoadingOlderCases(false);
    }
  }

  async function deleteAllCases() {
    if (!window.confirm("Delete every retained private research case?")) return;
    const response = await request("/v1/cases", { method: "DELETE" }, csrfToken);
    if (!response.ok) {
      setError("Stored cases could not be deleted.");
      return;
    }
    setActiveCase(null);
    await refreshCases();
  }

  const report = activeCase?.report ?? null;
  const structured = report?.structured_report;
  const converged = report?.converged_report;

  return (
    <section className="panel">
      <div className="panelHeader">
        <div><span className="index">02</span><h2>Converged live research</h2></div>
        <span className="count">private admin only</span>
      </div>
      <form className="quickResearchForm" onSubmit={submit}>
        <div className="twoColumn">
          <label>
            Starting identifier
            <select value={kind} onChange={(event) => setKind(event.target.value as ResearchKind)}>
              <option value="username">Username / handle</option>
              <option value="phone">Phone number</option>
              <option value="email">Email address</option>
              <option value="url">Public profile URL</option>
              <option value="domain">Domain</option>
            </select>
          </label>
          <label>
            Value
            <input
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder={PLACEHOLDER_BY_KIND[kind]}
              required
            />
          </label>
        </div>
        {kind === "domain" && (
          <p className="muted">
            Enter a bare domain such as example.com. Domain research is explicit-seed only; domain clues discovered during another case remain display-only.
          </p>
        )}
        <button type="submit" disabled={busy || !value.trim() || !csrfToken}>
          {busy ? "Following public evidence pivots…" : "Run converged research case"}
        </button>
        <p className="muted">
          Follows attributable public email, username and website fields through bounded approved providers. A pivot is evidence to investigate, not proof of identity.
        </p>
      </form>

      {error && <p className="error quickResult">{error}</p>}
      {activeCase && report && (
        <div className="quickResult">
          <div className="caseId">CASE {activeCase.id.slice(0, 8)} · {activeCase.seed_kind.toUpperCase()} · {activeCase.seed_value}</div>
          <p className="muted">Stored until {new Date(activeCase.expires_at).toLocaleString()} unless deleted earlier.</p>

          {report.seed_provenance && (
            <div className="reportSection">
              <h3>Reviewed document seed</h3>
              <div className="connectedField">
                <span>{report.seed_provenance.human_reviewed ? "human reviewed" : "review state unavailable"}</span>
                <strong>{report.seed_provenance.source}</strong>
                <small>{report.seed_provenance.source_locator}</small>
              </div>
            </div>
          )}

          {converged && (
            <div className="reportSummary">
              <div className="reportMetricGrid">
                <div><strong>{converged.executive_summary.research_node_count}</strong><span>research nodes</span></div>
                <div><strong>{converged.executive_summary.pivot_edge_count}</strong><span>public pivots</span></div>
                <div><strong>{converged.executive_summary.source_count}</strong><span>sources</span></div>
                <div><strong>{converged.executive_summary.truncated ? "yes" : "no"}</strong><span>budget truncated</span></div>
              </div>
              <p className="reportBoundary">{converged.executive_summary.interpretation}</p>

              <div className="reportSection">
                <h3>M5 evidence-strength triage</h3>
                <p className="muted">{converged.m5.interpretation}</p>
                {converged.m5.evaluations.length === 0 ? (
                  <p className="muted">No username-based account candidate reached the M5 candidate gate.</p>
                ) : (
                  <div className="connectedGrid">
                    {converged.m5.evaluations.map((evaluation) => {
                      const candidate = resolveM5Candidate(converged, evaluation);
                      const candidateSource = candidate?.source ?? evaluation.candidate_source ?? "canonical observation unavailable";
                      const candidateLocator = candidate?.source_locator ?? evaluation.candidate_source_locator ?? null;
                      return (
                        <div className="connectedField" key={m5EvaluationKey(evaluation)}>
                          <span>{evaluation.outcome}</span>
                          <strong>{evaluation.evidence_score} / 100</strong>
                          <small>{candidateSource} · {evaluation.calibration_status} · not an identity probability</small>
                          {candidateLocator && <small>{candidateLocator}</small>}
                          <small>
                            {evaluation.positive_independence_groups} positive independence groups · policy {evaluation.policy_version}
                          </small>
                          {evaluation.factors.map((factor) => (
                            <div className="nestedObservation" key={`${factor.kind}-${factor.independence_group}`}>
                              <strong>{factor.kind}</strong>
                              <span>{factor.status} · group {factor.independence_group}</span>
                              <small>
                                weight {factor.base_weight} → {factor.applied_weight}{factor.veto ? " · veto factor" : ""}
                              </small>
                              <small>{factor.rationale}</small>
                            </div>
                          ))}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {converged.edges.length > 0 && (
                <div className="reportSection">
                  <h3>Evidence pivots</h3>
                  <div className="connectedGrid">
                    {converged.edges.map((edge, index) => {
                      const provenance = resolveEdgeProvenance(converged, edge);
                      return (
                        <div className="connectedField" key={`${edge.parent_key}-${edge.child_key}-${index}`}>
                          <span>{edge.reason}</span>
                          <strong>{edge.child_key}</strong>
                          {provenance ? (
                            <>
                              <small>
                                {provenance.source_field
                                  ? `${provenance.source} · field ${provenance.source_field}`
                                  : `${provenance.source} · historical field unavailable`}
                              </small>
                              {provenance.observation_summary && <small>{provenance.observation_summary}</small>}
                              <small>{provenance.source_locator}</small>
                            </>
                          ) : (
                            <small>Canonical pivot provenance could not be resolved safely.</small>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="reportSection">
                <h3>Research graph</h3>
                <div className="providerList">
                  {converged.nodes.map((node) => (
                    <article className="researchObservation" key={node.key}>
                      <div className="provider">
                        <div>
                          <strong>{node.kind} · {node.normalized_value}</strong>
                          <span>depth {node.depth} · {node.pivot_reason}</span>
                          {node.parent_key && <span>from {node.parent_key}</span>}
                        </div>
                      </div>
                      <SourceRunSummary sourceRuns={node.source_runs} title="Source execution" />
                      {node.warnings.map((warning) => <p className="muted" key={warning}>{warning}</p>)}
                      {node.observations.length === 0 ? (
                        <p className="muted">No attributable observation returned for this pivot.</p>
                      ) : (
                        node.observations.map((observation, index) => (
                          <div className="nestedObservation" key={`${observation.source_locator}-${index}`}>
                            <strong>{observation.source}</strong>
                            <span>{observation.summary}</span>
                            <small>{observation.source_locator}</small>
                            <pre>{JSON.stringify(observation.details, null, 2)}</pre>
                          </div>
                        ))
                      )}
                    </article>
                  ))}
                </div>
              </div>
              <p className="muted">{converged.provenance_rule}</p>
            </div>
          )}

          {!converged && structured && (
            <div className="reportSummary">
              <div className="reportMetricGrid">
                <div><strong>{structured.executive_summary.observation_count}</strong><span>observations</span></div>
                <div><strong>{structured.executive_summary.source_count}</strong><span>sources</span></div>
                <div><strong>{structured.executive_summary.connected_identifier_count}</strong><span>connected fields</span></div>
                <div><strong>{structured.executive_summary.public_account_candidate_count}</strong><span>account candidates</span></div>
              </div>
              <p className="reportBoundary">{structured.executive_summary.interpretation}</p>
              <SourceRunSummary sourceRuns={report.source_runs} title="Source execution" />
              {structured.connected_identifiers.length > 0 && (
                <div className="reportSection">
                  <h3>Connected public fields</h3>
                  <div className="connectedGrid">
                    {structured.connected_identifiers.map((item, index) => {
                      const resolved = resolveConnectedIdentifier(report, item);
                      return (
                        <div className="connectedField" key={`${item.kind}-${index}`}>
                          <span>{item.kind}</span>
                          <strong>{resolved?.value ?? "Reference unavailable"}</strong>
                          <small>
                            {resolved
                              ? `${resolved.source} · ${resolved.source_locator}`
                              : "Stored connected-field reference could not be resolved safely."}
                          </small>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {structured.coverage_gaps.length > 0 && (
                <div className="reportSection">
                  <h3>Not established</h3>
                  <ul className="coverageList">
                    {structured.coverage_gaps.map((gap) => <li key={gap}>{gap}</li>)}
                  </ul>
                </div>
              )}
            </div>
          )}

          {!converged && !structured && <SourceRunSummary sourceRuns={report.source_runs} title="Source execution" />}
          {!converged && (report.warnings ?? []).map((warning) => <p className="muted" key={warning}>{warning}</p>)}
          {!converged && (report.observations ?? []).length > 0 && (
            <div className="providerList">
              {(report.observations ?? []).map((observation, index) => (
                <article className="researchObservation" key={`${observation.source_locator}-${index}`}>
                  <div className="provider">
                    <div>
                      <strong>{observation.source}</strong>
                      <span>{observation.summary}</span>
                      <span>{observation.source_locator}</span>
                    </div>
                  </div>
                  <pre>{JSON.stringify(observation.details, null, 2)}</pre>
                </article>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="recentCases">
        <div className="panelHeader compactPanelHeader">
          <div><span className="index">RECENT</span><h2>Stored cases</h2></div>
          <div className="buttonRow">
            <button className="secondaryButton" type="button" onClick={() => refreshCases()}>Refresh</button>
            <button className="dangerButton" type="button" onClick={deleteAllCases}>Delete all</button>
          </div>
        </div>
        {recentCases.length === 0 ? (
          <p className="muted">No retained research cases yet.</p>
        ) : (
          <div className="providerList">
            {recentCases.map((item) => (
              <div className="caseRow" key={item.id}>
                <button className="caseOpen" type="button" onClick={() => openCase(item.id)}>
                  <strong>{item.seed_kind}</strong>
                  <span>{item.seed_value}</span>
                  <small>{item.id.slice(0, 8)}</small>
                </button>
                <button className="dangerButton" type="button" onClick={() => deleteCase(item.id)}>Delete</button>
              </div>
            ))}
            {nextCaseCursor && (
              <button
                className="secondaryButton"
                type="button"
                onClick={loadOlderCases}
                disabled={loadingOlderCases}
              >
                {loadingOlderCases ? "Loading older cases…" : "Load older cases"}
              </button>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
