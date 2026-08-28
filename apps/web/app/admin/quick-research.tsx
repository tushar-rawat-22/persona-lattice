"use client";

import {
  FormEvent,
  KeyboardEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { CaseNavigation } from "./case-navigation";
import { M5FactorSummary } from "./m5-factor-summary";
import { operatorSystemStateCountsFromSourceRuns } from "./operator-system-state-model";
import { OperatorSystemState } from "./operator-system-state";
import { ProvenanceDisclosure } from "./provenance-disclosure";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const CONNECTED_IDENTIFIER_FIELD_BY_KIND: Record<string, string> = {
  email: "email",
  username: "twitter_username",
  url: "blog",
  location_claim: "location",
  organization_claim: "company",
};

type ResearchKind = "username" | "phone" | "email" | "url" | "domain";
type WorkspaceView = "overview" | "accounts" | "sources" | "graph" | "raw";

const WORKSPACE_VIEWS: WorkspaceView[] = ["overview", "accounts", "sources", "graph", "raw"];
const WORKSPACE_VIEW_LABELS: Record<WorkspaceView, string> = {
  overview: "Overview",
  accounts: "Accounts & pivots",
  sources: "Sources",
  graph: "Graph",
  raw: "Raw",
};

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
  lead_graph?: { decisions: LeadDecision[] };
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
  onActiveCaseChange?: (active: boolean) => void;
};

type ResolvedProvenance = {
  source: string;
  source_locator: string;
};

type ResolvedPivotProvenance = ResolvedProvenance & {
  source_field: string | null;
  observation_summary: string | null;
};

type ResolvedConnectedIdentifier = ResolvedProvenance & { value: string };

type SourceOutcomeDetail = {
  label: string;
  count: number;
  note: string;
};

type ConvergedSourceRow = SourceRunRecord & {
  node_key: string;
  node_value: string;
};

type DecisionItem = {
  key: string;
  text: string;
  detail?: string;
  provenance?: Array<{
    source: string;
    sourceLocator: string;
  }>;
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

function safeWebSourceLocator(locator: string): string | null {
  if (!locator || locator !== locator.trim()) return null;
  try {
    const parsed = new URL(locator);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return null;
    if (parsed.username || parsed.password || !parsed.hostname) return null;
    return locator;
  } catch {
    return null;
  }
}

function SourceLocator({ locator }: { locator: string }) {
  const href = safeWebSourceLocator(locator);
  if (!href) return <>{locator}</>;
  return (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {locator}
    </a>
  );
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

function stableObservationValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stableObservationValue);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, nested]) => [key, stableObservationValue(nested)]),
    );
  }
  return value;
}

function renderObservationValue(value: unknown): string {
  if (typeof value === "string") return value;
  if (value === null) return "null";
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  const encoded = JSON.stringify(stableObservationValue(value));
  return encoded === undefined ? String(value) : encoded;
}

function ObservationDetails({ observation }: { observation: Observation }) {
  const entries = Object.entries(observation.details).sort(([left], [right]) => left.localeCompare(right));
  return (
    <div className="observationDetails">
      {entries.length === 0 ? (
        <p className="muted">No retained fields were returned by this observation.</p>
      ) : (
        <div className="fieldTableWrap">
          <table className="compactTable fieldTable">
            <thead><tr><th>Field</th><th>Retained value</th></tr></thead>
            <tbody>
              {entries.map(([field, fieldValue]) => (
                <tr key={field}><td>{field}</td><td>{renderObservationValue(fieldValue)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <details>
        <summary>Raw retained JSON</summary>
        <pre>{JSON.stringify(observation.details, null, 2)}</pre>
      </details>
    </div>
  );
}

function resolveConnectedIdentifier(report: QuickReport, item: ConnectedIdentifier): ResolvedConnectedIdentifier | null {
  const hasLegacy = item.value !== undefined || item.source !== undefined || item.source_locator !== undefined;
  const hasReference = item.observation_index !== undefined || item.detail_field !== undefined;
  if (hasLegacy && hasReference) return null;
  if (hasLegacy) {
    if (!nonEmptyString(item.value) || !nonEmptyString(item.source) || !nonEmptyString(item.source_locator)) return null;
    return { value: item.value, source: item.source, source_locator: item.source_locator };
  }
  if (!Number.isInteger(item.observation_index) || (item.observation_index ?? -1) < 0) return null;
  if (!nonEmptyString(item.detail_field)) return null;
  if (CONNECTED_IDENTIFIER_FIELD_BY_KIND[item.kind] !== item.detail_field) return null;
  const observation = (report.observations ?? [])[item.observation_index as number];
  if (!observation || !nonEmptyString(observation.source) || !nonEmptyString(observation.source_locator)) return null;
  const value = observation.details[item.detail_field];
  if (!nonEmptyString(value)) return null;
  return { value, source: observation.source, source_locator: observation.source_locator };
}

function resolveM5Candidate(report: ConvergedReport, evaluation: M5Evaluation): Observation | null {
  if (!Number.isInteger(evaluation.candidate_observation_index) || (evaluation.candidate_observation_index ?? -1) < 0) return null;
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
    return { source: edge.source, source_locator: edge.source_locator, source_field: null, observation_summary: null };
  }
  if (!Number.isInteger(edge.lead_decision_index) || (edge.lead_decision_index ?? -1) < 0) return null;
  const decision = report.lead_graph?.decisions[edge.lead_decision_index as number];
  if (!decision || decision.decision !== "admitted") return null;
  if (decision.parent_key !== edge.parent_key || decision.child_key !== edge.child_key || decision.reason !== edge.reason) return null;
  if (!Number.isInteger(decision.source_observation_index) || (decision.source_observation_index ?? -1) < 0) return null;
  if (!nonEmptyString(decision.source_field)) return null;
  const parentMatches = report.nodes.filter((node) => node.key === decision.parent_key);
  if (parentMatches.length !== 1) return null;
  const observation = parentMatches[0].observations[decision.source_observation_index as number];
  if (!observation || !nonEmptyString(observation.source) || !nonEmptyString(observation.source_locator)) return null;
  if (!(decision.source_field in observation.details)) return null;
  return {
    source: observation.source,
    source_locator: observation.source_locator,
    source_field: decision.source_field,
    observation_summary: nonEmptyString(observation.summary) ? observation.summary : null,
  };
}

function reportObservations(report: QuickReport): Observation[] {
  if (report.converged_report) return report.converged_report.nodes.flatMap((node) => node.observations);
  return report.observations ?? [];
}

function uniqueDecisionItems(items: DecisionItem[]): DecisionItem[] {
  const seen = new Set<string>();
  return items.filter((item) => {
    if (seen.has(item.key)) return false;
    seen.add(item.key);
    return true;
  });
}

function deriveCorroboratedEvidence(report: QuickReport): DecisionItem[] {
  const groups = new Map<string, { summary: string; sources: Set<string>; provenance: Array<{ source: string; sourceLocator: string }> }>();
  for (const observation of reportObservations(report)) {
    if (!nonEmptyString(observation.summary) || !nonEmptyString(observation.source) || !nonEmptyString(observation.source_locator)) continue;
    const key = observation.summary.trim().toLocaleLowerCase();
    const current = groups.get(key) ?? { summary: observation.summary.trim(), sources: new Set<string>(), provenance: [] };
    current.sources.add(observation.source.trim());
    current.provenance.push({ source: observation.source.trim(), sourceLocator: observation.source_locator.trim() });
    groups.set(key, current);
  }
  return [...groups.entries()]
    .filter(([, value]) => value.sources.size >= 2)
    .map(([key, value]) => ({ key: `corroborated-${key}`, text: value.summary, detail: `${value.sources.size} distinct retained sources report this observation: ${[...value.sources].sort().join(", ")}.`, provenance: value.provenance }));
}

function deriveUncertaintyItems(report: QuickReport): DecisionItem[] {
  const items: DecisionItem[] = [];
  for (const warning of report.warnings ?? []) if (nonEmptyString(warning)) items.push({ key: `report-warning-${warning}`, text: warning });
  const converged = report.converged_report;
  if (converged) {
    for (const warning of converged.warnings) if (nonEmptyString(warning)) items.push({ key: `converged-warning-${warning}`, text: warning });
    for (const node of converged.nodes) for (const warning of node.warnings) if (nonEmptyString(warning)) items.push({ key: `node-warning-${warning}`, text: warning, detail: `Node: ${node.normalized_value}` });
    if (converged.m5.evaluations.length > 0) items.push({ key: "m5-uncalibrated", text: "M5 is uncalibrated; its score is evidence-strength triage, not an identity probability." });
    for (const evaluation of converged.m5.evaluations) {
      for (const factor of evaluation.factors) {
        const factorText = `${factor.status} ${factor.rationale}`;
        const isConflict = factor.veto || factor.applied_weight < 0 || /conflict|contradict|mismatch|negative|unsupported/i.test(factorText);
        if (!isConflict) continue;
        items.push({ key: `m5-${m5EvaluationKey(evaluation)}-${factor.kind}-${factor.independence_group}`, text: factor.rationale, detail: `${evaluation.candidate_node} · ${factor.kind}${factor.veto ? " · veto" : ""}` });
      }
    }
  }
  return uniqueDecisionItems(items);
}

function unresolvedSourceItems(sourceRuns: SourceRunReport | undefined, scope: string): DecisionItem[] {
  if (!sourceRuns) return [];
  return sourceRuns.records
    .filter((record) => !["executed", "not_found"].includes(record.state))
    .map((record, index) => ({ key: `source-${scope}-${record.source}-${record.lead_kind}-${record.state}-${index}`, text: `${record.source}: ${record.reason}`, detail: `${record.lead_kind} · ${record.state} · ${record.execution_attempted ? "attempted" : "not attempted"}` }));
}

function deriveOpenQuestions(report: QuickReport): DecisionItem[] {
  const items: DecisionItem[] = [];
  for (const gap of report.structured_report?.coverage_gaps ?? []) if (nonEmptyString(gap)) items.push({ key: `coverage-${gap}`, text: gap });
  items.push(...unresolvedSourceItems(report.source_runs, "single"));
  const converged = report.converged_report;
  if (converged) {
    if (converged.executive_summary.truncated) items.push({ key: "research-truncated", text: "The bounded research budget stopped before every eligible lead was explored." });
    for (const node of converged.nodes) {
      items.push(...unresolvedSourceItems(node.source_runs, node.key));
      if (node.observations.length === 0) items.push({ key: `no-observation-${node.key}`, text: `No attributable observation was retained for ${node.kind} ${node.normalized_value}.`, detail: node.pivot_reason });
    }
  }
  return uniqueDecisionItems(items);
}

function DecisionList({ items, empty }: { items: DecisionItem[]; empty: string }) {
  if (items.length === 0) return <p className="muted">{empty}</p>;
  return (
    <ul className="coverageList">
      {items.slice(0, 8).map((item) => (
        <li key={item.key}>
          {item.text}
          {item.detail && <small> · {item.detail}</small>}
          {item.provenance && item.provenance.length > 0 && <ProvenanceDisclosure records={item.provenance} label="Inspect retained provenance" />}
        </li>
      ))}
    </ul>
  );
}

function DecisionSurface({ report }: { report: QuickReport }) {
  const corroborated = deriveCorroboratedEvidence(report);
  const uncertainty = deriveUncertaintyItems(report);
  const openQuestions = deriveOpenQuestions(report);
  return (
    <div className="decisionSurface reportSection" aria-label="Case decision surface">
      <section><h3>Corroborated evidence</h3><DecisionList items={corroborated} empty="No retained observation is independently corroborated by two distinct sources yet. Single-source observations remain evidence, not corroboration." /></section>
      <section><h3>Conflicts & uncertainty</h3><DecisionList items={uncertainty} empty="No explicit contradiction is retained. Source limits and missing coverage still prevent treating silence as confirmation." /></section>
      <section><h3>Open questions</h3><DecisionList items={openQuestions} empty="No explicit coverage gap is retained for this case. Review Sources before treating the investigation as complete." /></section>
    </div>
  );
}

function SourceRunSummary({ sourceRuns, title }: { sourceRuns?: SourceRunReport; title: string }) {
  if (!sourceRuns) return <div className="reportSection"><h3>{title}</h3><p className="muted">Source execution state is unavailable for this historical case.</p></div>;
  const aggregate = sourceRuns.evaluation?.aggregate;
  const missingEvidenceReasons = aggregate ? sourceOutcomeDetails(aggregate) : [];
  return (
    <div className="reportSection">
      <h3>{title}</h3>
      <div className="sourceSummaryLine"><span>{sourceRuns.record_count} records</span><span>{aggregate?.attempt_count ?? sourceRuns.execution_attempted_count} attempts</span><span>{aggregate?.completed_attempt_count ?? "—"} completed</span><span>{aggregate?.failed_attempt_count ?? "—"} failed</span>{aggregate && <span>{aggregate.withheld_count} withheld</span>}</div>
      {sourceRuns.records.length === 0 ? <p className="muted">No typed source-run records were retained for this scope.</p> : (
        <div className="tableScroll"><table className="compactTable sourceTable"><thead><tr><th>Source</th><th>State</th><th>Kind</th><th>Attempt</th><th>Obs.</th><th>Reason</th></tr></thead><tbody>{sourceRuns.records.map((item, index) => <tr key={`${item.source}-${item.lead_kind}-${index}`}><td>{item.source}</td><td><span className={`statePill state-${item.state}`}>{item.state}</span></td><td>{item.lead_kind}</td><td>{item.execution_attempted ? "yes" : "no"}</td><td>{item.observation_count}</td><td>{item.reason}</td></tr>)}</tbody></table></div>
      )}
      {missingEvidenceReasons.length > 0 && <details><summary>Why evidence may be missing</summary><ul className="coverageList">{missingEvidenceReasons.map((item) => <li key={item.label}>{item.count} {item.label.toLowerCase()} · {item.note}</li>)}</ul></details>}
    </div>
  );
}

function M5EvidenceTable({ report }: { report: ConvergedReport }) {
  if (report.m5.evaluations.length === 0) return <div className="reportSection"><h3>M5 evidence-strength triage</h3><p className="muted">No username-based account candidate reached the M5 candidate gate.</p></div>;
  return (
    <div className="reportSection">
      <h3>M5 evidence-strength triage</h3>
      <p className="reportBoundary">{report.m5.interpretation} The retained score is evidence-strength triage, not an identity probability.</p>
      <div className="evidenceAssessmentList">
        {report.m5.evaluations.map((evaluation) => {
          const candidate = resolveM5Candidate(report, evaluation);
          const candidateSource = candidate?.source ?? evaluation.candidate_source ?? "canonical observation unavailable";
          const candidateLocator = candidate?.source_locator ?? evaluation.candidate_source_locator ?? null;
          const factorRows = evaluation.factors.length > 0 ? evaluation.factors : [{ kind: "no retained factors", independence_group: "—", base_weight: 0, applied_weight: 0, status: evaluation.calibration_status, rationale: "Historical evaluation did not retain factor rows.", veto: false }];
          return (
            <article className="evidenceAssessment" data-outcome={evaluation.outcome} key={m5EvaluationKey(evaluation)}>
              <div className="evidenceAssessmentHeader"><div><span>Candidate</span><strong>{evaluation.candidate_node}</strong></div><div className="evidenceScore"><strong>{evaluation.evidence_score}</strong><span>/ 100 evidence strength</span></div></div>
              <div className="evidenceAssessmentBody"><div><span>Outcome</span><strong>{evaluation.outcome.replaceAll("_", " ")}</strong></div><div><span>Independent support</span><strong>{evaluation.positive_independence_groups} groups</strong></div><div><span>Source</span><strong>{candidateSource}</strong></div></div>
              {candidateLocator && <p className="evidenceLocator"><SourceLocator locator={candidateLocator} /></p>}
              {evaluation.factors.length > 0 && <M5FactorSummary factors={evaluation.factors} />}
              <details className="evidenceFactors"><summary>Inspect {factorRows.length} retained factor{factorRows.length === 1 ? "" : "s"} and caveats</summary><div className="tableScroll"><table className="compactTable m5Table"><thead><tr><th>Factor</th><th>Group</th><th>Weight</th><th>Status / caveat</th></tr></thead><tbody>{factorRows.map((factor, factorIndex) => <tr key={`${m5EvaluationKey(evaluation)}-${factorIndex}`}><td>{factor.kind}</td><td>{factor.independence_group}</td><td>{factor.base_weight} → {factor.applied_weight}</td><td>{factor.status}{factor.veto ? " · veto" : ""} · {factor.rationale}</td></tr>)}</tbody></table></div><small className="policyNote">Policy {evaluation.policy_version} · uncalibrated · never an identity probability</small></details>
            </article>
          );
        })}
      </div>
    </div>
  );
}

function ConvergedSources({ report }: { report: ConvergedReport }) {
  const rows: ConvergedSourceRow[] = report.nodes.flatMap((node) => (node.source_runs?.records ?? []).map((record) => ({ ...record, node_key: node.key, node_value: node.normalized_value })));
  if (rows.length === 0) return <p className="muted">Source execution state is unavailable for this historical case.</p>;
  return <div className="reportSection"><h3>Source execution</h3><div className="tableScroll"><table className="compactTable sourceTable"><thead><tr><th>Node</th><th>Source</th><th>State</th><th>Attempt</th><th>Obs.</th><th>Reason</th></tr></thead><tbody>{rows.map((row, index) => <tr key={`${row.node_key}-${row.source}-${index}`}><td>{row.node_value}</td><td>{row.source}</td><td><span className={`statePill state-${row.state}`}>{row.state}</span></td><td>{row.execution_attempted ? "yes" : "no"}</td><td>{row.observation_count}</td><td>{row.reason}</td></tr>)}</tbody></table></div></div>;
}

export function QuickResearch({ csrfToken, onActiveCaseChange }: QuickResearchProps) {
  const [kind, setKind] = useState<ResearchKind>("username");
  const [value, setValue] = useState("");
  const [activeCase, setActiveCase] = useState<StoredCase | null>(null);
  const [recentCases, setRecentCases] = useState<StoredCaseSummary[]>([]);
  const [initialCasesLoading, setInitialCasesLoading] = useState(true);
  const [nextCaseCursor, setNextCaseCursor] = useState<string | null>(null);
  const [loadingOlderCases, setLoadingOlderCases] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [sessionExpired, setSessionExpired] = useState(false);
  const [activeView, setActiveView] = useState<WorkspaceView>("overview");
  const [launcherOpen, setLauncherOpen] = useState(true);
  const caseContextGeneration = useRef(0);
  const caseListGeneration = useRef(0);

  const startCaseContextChange = useCallback(() => { caseContextGeneration.current += 1; return caseContextGeneration.current; }, []);
  const isCurrentCaseContext = useCallback((generation: number) => caseContextGeneration.current === generation, []);
  const advanceCaseListGeneration = useCallback(() => { caseListGeneration.current += 1; return caseListGeneration.current; }, []);
  const isCurrentCaseList = useCallback((generation: number) => caseListGeneration.current === generation, []);
  const expireSession = useCallback((message = "Your operator session expired. Sign in again to continue.") => { setSessionExpired(true); setError(message); }, []);

  useEffect(() => { onActiveCaseChange?.(Boolean(activeCase)); }, [activeCase, onActiveCaseChange]);

  const refreshCases = useCallback(async () => {
    if (sessionExpired) return;
    const generation = advanceCaseListGeneration();
    setLoadingOlderCases(false);
    setNextCaseCursor(null);
    try {
      const response = await request("/v1/cases?limit=8");
      if (response.status === 401) { if (isCurrentCaseList(generation)) expireSession(); return; }
      if (!response.ok || !isCurrentCaseList(generation)) return;
      const page = (await response.json()) as StoredCaseSummary[];
      if (!isCurrentCaseList(generation)) return;
      setRecentCases(page);
      setNextCaseCursor(response.headers.get("X-PersonaLattice-Next-Cursor"));
    } catch {
      if (isCurrentCaseList(generation)) setError("Stored case index could not be refreshed.");
    }
  }, [advanceCaseListGeneration, expireSession, isCurrentCaseList, sessionExpired]);

  useEffect(() => {
    let active = true;
    const generation = advanceCaseListGeneration();
    request("/v1/cases?limit=8")
      .then(async (response) => {
        if (response.status === 401) { if (active && isCurrentCaseList(generation)) expireSession(); return null; }
        if (!response.ok) return null;
        return { items: (await response.json()) as StoredCaseSummary[], cursor: response.headers.get("X-PersonaLattice-Next-Cursor") };
      })
      .then((page) => {
        if (active && page && isCurrentCaseList(generation)) {
          setRecentCases(page.items);
          setNextCaseCursor(page.cursor);
        }
      })
      .catch(() => undefined)
      .finally(() => {
        if (active && isCurrentCaseList(generation)) setInitialCasesLoading(false);
      });
    return () => { active = false; };
  }, [advanceCaseListGeneration, expireSession, isCurrentCaseList]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (sessionExpired) return;
    const generation = startCaseContextChange();
    setError(""); setActiveCase(null); setLauncherOpen(true); setActiveView("overview"); setBusy(true);
    try {
      const response = await request("/v1/cases/run-converged", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ kind, value, purpose: "public_source_research", consent_acknowledged: false }) }, csrfToken);
      if (response.status === 401) { if (isCurrentCaseContext(generation)) expireSession("Your operator session expired. Sign in again to continue. The rejected request did not start or change a research case."); return; }
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Research request failed.");
      if (!isCurrentCaseContext(generation)) return;
      const stored = body as StoredCase;
      setActiveCase(stored); setLauncherOpen(false); setValue(stored.seed_value); await refreshCases();
    } catch (caught) {
      if (isCurrentCaseContext(generation)) setError(caught instanceof Error ? caught.message : "Research request failed.");
    } finally { setBusy(false); }
  }

  async function openCase(caseId: string) {
    if (sessionExpired) return;
    const generation = startCaseContextChange(); setError("");
    try {
      const response = await request(`/v1/cases/${caseId}`);
      if (!isCurrentCaseContext(generation)) return;
      if (response.status === 401) { expireSession(); return; }
      if (!response.ok) { setError("Stored case could not be loaded."); return; }
      const stored = (await response.json()) as StoredCase;
      if (!isCurrentCaseContext(generation)) return;
      setActiveCase(stored); setLauncherOpen(false); setActiveView("overview");
    } catch { if (isCurrentCaseContext(generation)) setError("Stored case could not be loaded."); }
  }

  async function deleteCase(caseId: string) {
    if (sessionExpired) return;
    const generation = startCaseContextChange(); setError("");
    try {
      const response = await request(`/v1/cases/${caseId}`, { method: "DELETE" }, csrfToken);
      if (response.status === 401) { if (isCurrentCaseContext(generation)) expireSession("Your operator session expired. Sign in again to continue. The rejected request did not delete the retained case."); return; }
      if (!response.ok && response.status !== 404) { if (isCurrentCaseContext(generation)) setError("Stored case could not be deleted."); return; }
      if (activeCase?.id === caseId) setLauncherOpen(true);
      setActiveCase((current) => current?.id === caseId ? null : current);
      await refreshCases();
    } catch { if (isCurrentCaseContext(generation)) setError("Stored case could not be deleted."); }
  }

  async function loadOlderCases() {
    if (sessionExpired || !nextCaseCursor || loadingOlderCases) return;
    const generation = caseListGeneration.current; const cursor = nextCaseCursor; setError(""); setLoadingOlderCases(true);
    try {
      const response = await request(`/v1/cases?limit=8&cursor=${encodeURIComponent(cursor)}`);
      if (!isCurrentCaseList(generation)) return;
      if (response.status === 401) { expireSession(); return; }
      if (!response.ok) { setError("Older stored cases could not be loaded."); return; }
      const page = (await response.json()) as StoredCaseSummary[];
      if (!isCurrentCaseList(generation)) return;
      setRecentCases((current) => { const existingIds = new Set(current.map((item) => item.id)); return [...current, ...page.filter((item) => !existingIds.has(item.id))]; });
      setNextCaseCursor(response.headers.get("X-PersonaLattice-Next-Cursor"));
    } catch { if (isCurrentCaseList(generation)) setError("Older stored cases could not be loaded."); }
    finally { if (isCurrentCaseList(generation)) setLoadingOlderCases(false); }
  }

  async function deleteAllCases() {
    if (sessionExpired) return;
    const generation = startCaseContextChange(); setError("");
    try {
      const response = await request("/v1/cases", { method: "DELETE" }, csrfToken);
      if (response.status === 401) { if (isCurrentCaseContext(generation)) expireSession("Your operator session expired. Sign in again to continue. The rejected request did not delete retained cases."); return; }
      if (!response.ok) { if (isCurrentCaseContext(generation)) setError("Stored cases could not be deleted."); return; }
      if (isCurrentCaseContext(generation)) setActiveCase(null);
      if (isCurrentCaseContext(generation)) setLauncherOpen(true);
      await refreshCases();
    } catch { if (isCurrentCaseContext(generation)) setError("Stored cases could not be deleted."); }
  }

  const report = activeCase?.report ?? null;
  const structured = report?.structured_report;
  const converged = report?.converged_report;

  function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>, view: WorkspaceView) {
    const currentIndex = WORKSPACE_VIEWS.indexOf(view); let targetIndex = currentIndex;
    if (event.key === "ArrowRight") targetIndex = (currentIndex + 1) % WORKSPACE_VIEWS.length;
    else if (event.key === "ArrowLeft") targetIndex = (currentIndex - 1 + WORKSPACE_VIEWS.length) % WORKSPACE_VIEWS.length;
    else if (event.key === "Home") targetIndex = 0;
    else if (event.key === "End") targetIndex = WORKSPACE_VIEWS.length - 1;
    else return;
    event.preventDefault(); const target = WORKSPACE_VIEWS[targetIndex]; setActiveView(target); document.getElementById(`case-tab-${target}`)?.focus();
  }

  function renderOverview() {
    if (!report) return null;
    if (converged) {
      const retainedObservationCount = converged.nodes.reduce((total, node) => total + node.observations.length, 0);
      const unresolvedSourceCount = converged.nodes.reduce((total, node) => total + (node.source_runs?.records.filter((record) => ["unavailable", "blocked", "budget_stopped"].includes(record.state)).length ?? 0), 0);
      const systemStateCounts = operatorSystemStateCountsFromSourceRuns(converged.nodes.map((node) => node.source_runs));
      return <div className="reportSummary"><DecisionSurface report={report} /><OperatorSystemState {...systemStateCounts} /><div className="reportMetricGrid"><div><strong>{retainedObservationCount}</strong><span>attributable observations</span></div><div><strong>{converged.executive_summary.pivot_edge_count}</strong><span>public pivots</span></div><div><strong>{converged.executive_summary.source_count}</strong><span>sources</span></div><div><strong>{unresolvedSourceCount}</strong><span>unresolved source states</span></div></div><p className="reportBoundary">{converged.executive_summary.interpretation} {converged.executive_summary.truncated ? "The bounded research budget stopped before every eligible lead was explored." : "The bounded research budget completed without truncation."}</p>{report.seed_provenance && <div className="reportSection"><h3>Reviewed document seed</h3><p className="muted">{report.seed_provenance.human_reviewed ? "Human reviewed" : "Review state unavailable"} · {report.seed_provenance.source} · <SourceLocator locator={report.seed_provenance.source_locator} /></p></div>}<div className="reportSection"><h3>Discovered identifiers</h3><div className="tableScroll"><table className="compactTable"><thead><tr><th>Kind</th><th>Identifier</th><th>Depth</th><th>Reached by</th></tr></thead><tbody>{converged.nodes.map((node) => <tr key={node.key}><td>{node.kind}</td><td>{node.normalized_value}</td><td>{node.depth}</td><td>{node.pivot_reason}</td></tr>)}</tbody></table></div></div><M5EvidenceTable report={converged} />{converged.warnings.length > 0 && <details><summary>{converged.warnings.length} research warnings</summary><ul className="coverageList">{converged.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></details>}</div>;
    }
    if (structured) {
      const systemStateCounts = operatorSystemStateCountsFromSourceRuns([report.source_runs]);
      return <div className="reportSummary"><DecisionSurface report={report} /><OperatorSystemState {...systemStateCounts} /><div className="reportMetricGrid"><div><strong>{structured.executive_summary.observation_count}</strong><span>observations</span></div><div><strong>{structured.executive_summary.source_count}</strong><span>sources</span></div><div><strong>{structured.executive_summary.connected_identifier_count}</strong><span>connected fields</span></div><div><strong>{structured.executive_summary.public_account_candidate_count}</strong><span>account candidates</span></div></div><p className="reportBoundary">{structured.executive_summary.interpretation}</p>{structured.coverage_gaps.length > 0 && <ul className="coverageList">{structured.coverage_gaps.map((gap) => <li key={gap}>{gap}</li>)}</ul>}</div>;
    }
    return <p className="muted">Historical case summary is limited. Use Sources or Raw for the retained evidence that is available.</p>;
  }

  function renderAccounts() {
    if (!report) return null;
    if (converged) {
      if (converged.edges.length === 0) return <p className="muted">No public evidence pivots were admitted for this case.</p>;
      return <div className="reportSection"><h3>Evidence pivots</h3><div className="tableScroll"><table className="compactTable pivotTable"><thead><tr><th>From</th><th>To</th><th>Reason</th><th>Provenance</th></tr></thead><tbody>{converged.edges.map((edge, index) => { const provenance = resolveEdgeProvenance(converged, edge); return <tr key={`${edge.parent_key}-${edge.child_key}-${index}`}><td>{edge.parent_key}</td><td>{edge.child_key}</td><td>{edge.reason}</td><td>{provenance ? <>{provenance.source_field ? `${provenance.source} · field ${provenance.source_field}` : `${provenance.source} · historical field unavailable`}{provenance.observation_summary && <><br />{provenance.observation_summary}</>}<br /><SourceLocator locator={provenance.source_locator} /></> : "Canonical pivot provenance could not be resolved safely."}</td></tr>; })}</tbody></table></div><p className="muted">A pivot is a lead to investigate, not proof that two identifiers belong to the same person.</p></div>;
    }
    if (structured) {
      if (structured.connected_identifiers.length === 0) return <p className="muted">No connected public fields were retained.</p>;
      return <div className="reportSection"><h3>Connected public fields</h3><div className="tableScroll"><table className="compactTable"><thead><tr><th>Kind</th><th>Value</th><th>Source</th><th>Locator</th></tr></thead><tbody>{structured.connected_identifiers.map((item, index) => { const resolved = resolveConnectedIdentifier(report, item); return <tr key={`${item.kind}-${index}`}><td>{item.kind}</td><td>{resolved?.value ?? "Reference unavailable"}</td><td>{resolved?.source ?? "—"}</td><td>{resolved ? <SourceLocator locator={resolved.source_locator} /> : "Stored connected-field reference could not be resolved safely."}</td></tr>; })}</tbody></table></div></div>;
    }
    return <p className="muted">Account and pivot references are unavailable for this historical case.</p>;
  }

  function renderSources() { if (!report) return null; if (converged) return <ConvergedSources report={converged} />; return <SourceRunSummary sourceRuns={report.source_runs} title="Source execution" />; }
  function renderGraph() { if (!converged) return <p className="muted">Graph topology is unavailable for this historical case.</p>; return <div className="reportSection"><h3>Research graph</h3><div className="tableScroll"><table className="compactTable graphTable"><thead><tr><th>Node</th><th>Kind</th><th>Depth</th><th>Parent</th><th>Pivot reason</th></tr></thead><tbody>{converged.nodes.map((node) => <tr key={node.key}><td>{node.normalized_value}</td><td>{node.kind}</td><td>{node.depth}</td><td>{node.parent_key ?? "seed"}</td><td>{node.pivot_reason}</td></tr>)}</tbody></table></div><p className="muted">{converged.provenance_rule}</p></div>; }
  function renderRaw() {
    if (!report) return null;
    if (converged) return <div className="rawNodeList">{converged.nodes.map((node) => <section className="rawNode" key={node.key}><div className="rawNodeHeader"><strong>{node.kind} · {node.normalized_value}</strong><span>depth {node.depth} · {node.pivot_reason}</span></div><SourceRunSummary sourceRuns={node.source_runs} title="Source execution" />{node.warnings.map((warning) => <p className="muted" key={warning}>{warning}</p>)}{node.observations.length === 0 ? <p className="muted">No attributable observations were retained for this node.</p> : <div className="rawObservationList">{node.observations.map((observation, index) => <article className="rawObservation" key={`${observation.source_locator}-${index}`}><div className="rawObservationHeader"><div><strong>{observation.source}</strong><span>{observation.summary}</span></div><small><SourceLocator locator={observation.source_locator} /></small></div><ObservationDetails observation={observation} /></article>)}</div>}</section>)}</div>;
    const observations = report.observations ?? [];
    return observations.length === 0 ? <p className="muted">No attributable observations were retained for this case.</p> : <div className="rawObservationList">{observations.map((observation, index) => <article className="rawObservation" key={`${observation.source_locator}-${index}`}><div className="rawObservationHeader"><div><strong>{observation.source}</strong><span>{observation.summary}</span></div><small><SourceLocator locator={observation.source_locator} /></small></div><ObservationDetails observation={observation} /></article>)}</div>;
  }
  function renderView(view: WorkspaceView) { if (view === "overview") return renderOverview(); if (view === "accounts") return renderAccounts(); if (view === "sources") return renderSources(); if (view === "graph") return renderGraph(); return renderRaw(); }

  return (
    <section className={activeCase ? "panel researchWorkbench activeResearch" : "panel researchWorkbench"}>
      <div className="panelHeader researchWorkbenchHeader"><div><span className="index">WORKSPACE</span><h2>{activeCase ? "Active investigation" : "Investigation workspace"}</h2></div><span className="count">private · retained</span></div>
      <details className="researchLauncher" open={launcherOpen} onToggle={(event) => setLauncherOpen(event.currentTarget.open)}>
        <summary><span><strong>{activeCase ? "Start another case" : "Start with a public identifier"}</strong><small>{activeCase ? "Keeps the current case until you run the next one" : "Exact, bounded research through approved sources"}</small></span><span className="summaryAction">{launcherOpen ? "Collapse" : "Open launcher"}</span></summary>
        <form className="quickResearchForm" onSubmit={submit}>
          <div className="twoColumn"><label>Starting identifier<select value={kind} onChange={(event) => setKind(event.target.value as ResearchKind)}><option value="username">Username / handle</option><option value="phone">Phone number</option><option value="email">Email address</option><option value="url">Public profile URL</option><option value="domain">Domain</option></select></label><label>Value<input value={value} onChange={(event) => setValue(event.target.value)} placeholder={PLACEHOLDER_BY_KIND[kind]} required /></label></div>
          {kind === "domain" && <p className="muted">Enter a bare domain such as example.com. Domain research is explicit-seed only; domain clues discovered during another case remain display-only.</p>}
          <button type="submit" disabled={busy || sessionExpired || !value.trim() || !csrfToken}>{busy ? "Following public evidence pivots…" : "Run converged research case"}</button>
          <p className="muted">Follows attributable public email, username and website fields through bounded approved providers. A pivot is evidence to investigate, not proof of identity.</p>
        </form>
      </details>
      {sessionExpired && <p className="error researchError" role="alert">Your operator session expired. Sign in again before loading, changing, deleting, or starting retained research cases.</p>}
      {!sessionExpired && error && <p className="error researchError" role="alert">{error}</p>}
      {activeCase && report && <div className="quickResult"><div className="caseContextBar"><div><span className="caseEyebrow">Active case</span><span className="caseId">CASE {activeCase.id.slice(0, 8)}</span><strong>{activeCase.seed_kind.toUpperCase()} · {activeCase.seed_value}</strong></div><span className="caseRetention">retained until {new Date(activeCase.expires_at).toLocaleString()}</span></div><div className="workspaceTabs" role="tablist" aria-label="Case workspace views">{WORKSPACE_VIEWS.map((view) => <button id={`case-tab-${view}`} key={view} type="button" role="tab" aria-selected={activeView === view} aria-controls={`case-panel-${view}`} tabIndex={activeView === view ? 0 : -1} className={activeView === view ? "workspaceTab active" : "workspaceTab"} onClick={() => setActiveView(view)} onKeyDown={(event) => handleTabKeyDown(event, view)}>{WORKSPACE_VIEW_LABELS[view]}</button>)}</div>{WORKSPACE_VIEWS.map((view) => <section id={`case-panel-${view}`} key={view} role="tabpanel" aria-labelledby={`case-tab-${view}`} tabIndex={activeView === view ? 0 : -1} hidden={activeView !== view} className="workspacePanel">{activeView === view ? renderView(view) : null}</section>)}</div>}
      <CaseNavigation cases={recentCases} activeCaseId={activeCase?.id} hasMore={Boolean(nextCaseCursor)} loadingMore={loadingOlderCases} initialLoading={initialCasesLoading} remoteActionsDisabled={sessionExpired} onOpenCase={openCase} onLoadMore={loadOlderCases} onRefresh={() => refreshCases()} onDeleteCase={deleteCase} onDeleteAll={deleteAllCases} />
    </section>
  );
}
