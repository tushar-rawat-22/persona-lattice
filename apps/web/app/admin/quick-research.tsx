"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type ResearchKind = "username" | "phone" | "email" | "url";

type Observation = {
  source: string;
  source_locator: string;
  summary: string;
  details: Record<string, unknown>;
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
  connected_identifiers: Array<{
    kind: string;
    value: string;
    source: string;
    source_locator: string;
    status: string;
  }>;
  coverage_gaps: string[];
  provenance_rule: string;
};

type M5Evaluation = {
  candidate_node: string;
  candidate_observation_index: number;
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
    observations: Observation[];
  }>;
  edges: Array<{
    parent_key: string;
    child_key: string;
    reason: string;
    source: string;
    source_locator: string;
  }>;
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
  structured_report?: StructuredReport;
  converged_report?: ConvergedReport;
};

type StoredCase = {
  id: string;
  created_at: string;
  expires_at: string;
  seed_kind: ResearchKind;
  seed_value: string;
  report: QuickReport;
};

type QuickResearchProps = {
  csrfToken: string;
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

function resolveM5Candidate(report: ConvergedReport, evaluation: M5Evaluation): Observation | null {
  const node = report.nodes.find((item) => item.key === evaluation.candidate_node);
  if (!node) return null;
  return node.observations[evaluation.candidate_observation_index] ?? null;
}

export function QuickResearch({ csrfToken }: QuickResearchProps) {
  const [kind, setKind] = useState<ResearchKind>("username");
  const [value, setValue] = useState("");
  const [activeCase, setActiveCase] = useState<StoredCase | null>(null);
  const [recentCases, setRecentCases] = useState<StoredCase[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const refreshCases = useCallback(async () => {
    const response = await request("/v1/cases?limit=8");
    if (!response.ok) return;
    setRecentCases((await response.json()) as StoredCase[]);
  }, []);

  useEffect(() => {
    let active = true;
    request("/v1/cases?limit=8")
      .then(async (response) => {
        if (!response.ok) return null;
        return (await response.json()) as StoredCase[];
      })
      .then((items) => {
        if (active && items) setRecentCases(items);
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
            </select>
          </label>
          <label>
            Value
            <input
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder={kind === "username" ? "@handle" : "Identifier to research"}
              required
            />
          </label>
        </div>
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
                      return (
                        <div className="connectedField" key={`${evaluation.candidate_node}-${evaluation.candidate_observation_index}`}>
                          <span>{evaluation.outcome}</span>
                          <strong>{evaluation.evidence_score} / 100</strong>
                          <small>{candidate?.source ?? "canonical observation unavailable"} · {evaluation.calibration_status} · not an identity probability</small>
                          {evaluation.factors.map((factor) => (
                            <small key={`${factor.kind}-${factor.independence_group}`}>
                              {factor.kind}: {factor.applied_weight >= 0 ? "+" : ""}{factor.applied_weight} · {factor.status}
                            </small>
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
                    {converged.edges.map((edge) => (
                      <div className="connectedField" key={`${edge.parent_key}-${edge.child_key}`}>
                        <span>{edge.reason}</span>
                        <strong>{edge.child_key}</strong>
                        <small>{edge.source} · {edge.source_locator}</small>
                      </div>
                    ))}
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
              {structured.connected_identifiers.length > 0 && (
                <div className="reportSection">
                  <h3>Connected public fields</h3>
                  <div className="connectedGrid">
                    {structured.connected_identifiers.map((item) => (
                      <div className="connectedField" key={`${item.kind}-${item.value}-${item.source}`}>
                        <span>{item.kind}</span>
                        <strong>{item.value}</strong>
                        <small>{item.source} · {item.source_locator}</small>
                      </div>
                    ))}
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
          </div>
        )}
      </div>
    </section>
  );
}
