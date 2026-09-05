"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type JsonObject = Record<string, unknown>;

type StoredCasePayload = {
  id: string;
  report: JsonObject;
};

type Finding = {
  summary: string;
  sources: string[];
};

type Brief = {
  observationCount: number;
  sourceCount: number;
  corroboratedFindingCount: number;
  corroboratedFindings: Finding[];
  contradictionCount: number;
  conflictingFindings: string[];
  warningCount: number;
  coverageGapCount: number | null;
  openQuestions: string[];
  traversalLimited: boolean;
  sourceStates: Array<[string, number]>;
};

type BriefRequestState = {
  caseId: string;
  payload: StoredCasePayload | null;
  failed: boolean;
};

type CaseDecisionDisposition =
  | "continue_research"
  | "await_more_evidence"
  | "ready_for_handoff"
  | "close_case";

type CaseDecision = {
  id: string;
  case_id: string;
  created_at: string;
  disposition: CaseDecisionDisposition;
  rationale: string;
};

type DecisionRequestState = {
  caseId: string;
  items: CaseDecision[];
  failed: boolean;
};

const DECISION_LABELS: Record<CaseDecisionDisposition, string> = {
  continue_research: "Continue research",
  await_more_evidence: "Await more evidence",
  ready_for_handoff: "Ready for handoff",
  close_case: "Close case",
};

function objectValue(value: unknown): JsonObject {
  return value && typeof value === "object" && !Array.isArray(value) ? value as JsonObject : {};
}

function objectList(value: unknown): JsonObject[] {
  return Array.isArray(value) ? value.filter((item): item is JsonObject => Boolean(item) && typeof item === "object" && !Array.isArray(item)) : [];
}

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function countEntries(value: unknown): Array<[string, number]> {
  return Object.entries(objectValue(value))
    .filter((entry): entry is [string, number] => Number.isInteger(entry[1]) && Number(entry[1]) >= 0)
    .sort(([left], [right]) => left.localeCompare(right));
}

function observationSummary(observation: JsonObject): string {
  return typeof observation.summary === "string" ? observation.summary.trim() : "";
}

function observationIsContradiction(observation: JsonObject): boolean {
  const details = objectValue(observation.details);
  return details.contradiction === true || details.account_state === "illegal";
}

function collectIndependentlyCorroboratedFindings(observations: JsonObject[]): Finding[] {
  const findingsBySummary = new Map<string, Finding>();
  for (const observation of observations) {
    const summary = observationSummary(observation);
    const source = typeof observation.source === "string" ? observation.source.trim() : "";
    if (!summary || !source) continue;
    const summaryKey = summary.toLocaleLowerCase();
    const finding = findingsBySummary.get(summaryKey) ?? { summary, sources: [] };
    if (!finding.sources.includes(source)) finding.sources.push(source);
    findingsBySummary.set(summaryKey, finding);
  }
  return [...findingsBySummary.values()]
    .filter((finding) => finding.sources.length >= 2)
    .map((finding) => ({ ...finding, sources: [...finding.sources].sort((left, right) => left.localeCompare(right)) }))
    .sort((left, right) => left.summary.localeCompare(right.summary));
}

function collectConflictingFindings(observations: JsonObject[], indexedContradictions?: Set<number>): string[] {
  const findings = new Set<string>();
  observations.forEach((observation, index) => {
    if (!observationIsContradiction(observation) && !indexedContradictions?.has(index)) return;
    const summary = observationSummary(observation);
    if (summary) findings.add(summary);
  });
  return [...findings].sort((left, right) => left.localeCompare(right));
}

export function summarizeRetainedCase(report: JsonObject): Brief {
  const converged = objectValue(report.converged_report);
  if (Object.keys(converged).length > 0) {
    const nodes = objectList(converged.nodes);
    const sources = new Set<string>();
    const retainedObservations: JsonObject[] = [];
    const sourceStateTotals = new Map<string, number>();

    for (const node of nodes) {
      const observations = objectList(node.observations);
      retainedObservations.push(...observations);
      for (const observation of observations) {
        if (typeof observation.source === "string" && observation.source) sources.add(observation.source);
      }
      const sourceRuns = objectValue(node.source_runs);
      for (const [state, count] of countEntries(sourceRuns.state_counts)) {
        sourceStateTotals.set(state, (sourceStateTotals.get(state) ?? 0) + count);
      }
    }

    const corroboratedFindings = collectIndependentlyCorroboratedFindings(retainedObservations);
    const conflictingFindings = collectConflictingFindings(retainedObservations);
    const executiveSummary = objectValue(converged.executive_summary);
    return {
      observationCount: retainedObservations.length,
      sourceCount: sources.size,
      corroboratedFindingCount: corroboratedFindings.length,
      corroboratedFindings,
      contradictionCount: retainedObservations.filter(observationIsContradiction).length,
      conflictingFindings,
      warningCount: stringList(converged.warnings).length,
      coverageGapCount: null,
      openQuestions: [],
      traversalLimited: executiveSummary.truncated === true,
      sourceStates: [...sourceStateTotals.entries()].sort(([left], [right]) => left.localeCompare(right)),
    };
  }

  const observations = objectList(report.observations);
  const sources = new Set(
    observations
      .map((observation) => observation.source)
      .filter((source): source is string => typeof source === "string" && source.length > 0),
  );
  const structured = objectValue(report.structured_report);
  const openQuestions = stringList(structured.coverage_gaps).map((gap) => gap.trim()).filter(Boolean);
  const indexedContradictions = new Set<number>();
  const contradictionIndexes = structured.contradiction_observation_indexes;
  if (Array.isArray(contradictionIndexes)) {
    for (const index of contradictionIndexes) {
      if (Number.isInteger(index) && Number(index) >= 0 && Number(index) < observations.length) indexedContradictions.add(Number(index));
    }
  }
  observations.forEach((observation, index) => {
    if (observationIsContradiction(observation)) indexedContradictions.add(index);
  });
  const corroboratedFindings = collectIndependentlyCorroboratedFindings(observations);
  const conflictingFindings = collectConflictingFindings(observations, indexedContradictions);
  const sourceRuns = objectValue(report.source_runs);

  return {
    observationCount: observations.length,
    sourceCount: sources.size,
    corroboratedFindingCount: corroboratedFindings.length,
    corroboratedFindings,
    contradictionCount: indexedContradictions.size,
    conflictingFindings,
    warningCount: stringList(report.warnings).length,
    coverageGapCount: openQuestions.length,
    openQuestions,
    traversalLimited: false,
    sourceStates: countEntries(sourceRuns.state_counts),
  };
}

export function CaseBrief({ caseId, disabled = false }: { caseId?: string; disabled?: boolean }) {
  const [requestState, setRequestState] = useState<BriefRequestState | null>(null);
  const [decisionState, setDecisionState] = useState<DecisionRequestState | null>(null);
  const [disposition, setDisposition] = useState<CaseDecisionDisposition>("await_more_evidence");
  const [rationale, setRationale] = useState("");
  const [decisionSaving, setDecisionSaving] = useState(false);
  const [decisionSaveError, setDecisionSaveError] = useState("");

  useEffect(() => {
    if (!caseId || disabled) return;

    const controller = new AbortController();
    void fetch(`${API_URL}/v1/cases/${encodeURIComponent(caseId)}`, {
      credentials: "include",
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error(`case brief failed with ${response.status}`);
        return await response.json() as StoredCasePayload;
      })
      .then((record) => {
        if (record.id !== caseId) throw new Error("case brief identity mismatch");
        if (!controller.signal.aborted) setRequestState({ caseId, payload: record, failed: false });
      })
      .catch(() => {
        if (!controller.signal.aborted) setRequestState({ caseId, payload: null, failed: true });
      });

    return () => controller.abort();
  }, [caseId, disabled]);

  useEffect(() => {
    setDecisionSaveError("");
    setRationale("");
    if (!caseId || disabled) return;

    const controller = new AbortController();
    void fetch(`${API_URL}/v1/cases/${encodeURIComponent(caseId)}/decisions`, {
      credentials: "include",
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error(`case decisions failed with ${response.status}`);
        return await response.json() as CaseDecision[];
      })
      .then((items) => {
        if (!controller.signal.aborted) setDecisionState({ caseId, items, failed: false });
      })
      .catch(() => {
        if (!controller.signal.aborted) setDecisionState({ caseId, items: [], failed: true });
      });

    return () => controller.abort();
  }, [caseId, disabled]);

  async function appendDecision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!caseId || disabled || decisionSaving) return;
    const trimmedRationale = rationale.trim();
    if (!trimmedRationale) {
      setDecisionSaveError("Add a rationale before recording the decision.");
      return;
    }

    setDecisionSaving(true);
    setDecisionSaveError("");
    try {
      const sessionResponse = await fetch(`${API_URL}/v1/auth/session`, { credentials: "include" });
      if (!sessionResponse.ok) throw new Error("Your operator session expired. Sign in again before recording a decision.");
      const session = await sessionResponse.json() as { csrf_token?: unknown };
      if (typeof session.csrf_token !== "string" || !session.csrf_token) {
        throw new Error("Decision write authority is unavailable. Sign in again before retrying.");
      }

      const response = await fetch(`${API_URL}/v1/cases/${encodeURIComponent(caseId)}/decisions`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-PersonaLattice-CSRF": session.csrf_token,
        },
        body: JSON.stringify({ disposition, rationale: trimmedRationale }),
      });
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          throw new Error("Decision write authority was rejected. Sign in again before retrying.");
        }
        throw new Error("Decision could not be recorded. The retained case was not changed.");
      }
      const created = await response.json() as CaseDecision;
      if (created.case_id !== caseId) throw new Error("Decision response did not match the active case.");
      setDecisionState((current) => ({
        caseId,
        items: [created, ...(current?.caseId === caseId ? current.items : [])],
        failed: false,
      }));
      setRationale("");
    } catch (error) {
      setDecisionSaveError(error instanceof Error ? error.message : "Decision could not be recorded.");
    } finally {
      setDecisionSaving(false);
    }
  }

  const currentRequest = requestState && requestState.caseId === caseId ? requestState : null;
  const currentPayload = currentRequest?.payload ?? null;
  const currentFailed = currentRequest?.failed ?? false;
  const currentDecisionState = decisionState && decisionState.caseId === caseId ? decisionState : null;
  const brief = useMemo(() => currentPayload ? summarizeRetainedCase(currentPayload.report) : null, [currentPayload]);
  if (!caseId || disabled) return null;

  if (currentFailed) {
    return <p className="muted" role="status">Case brief unavailable. Use the reopened retained report as the source of truth.</p>;
  }
  if (!brief) return <p className="muted" role="status">Building case brief from the retained report…</p>;

  const coverageSummary = brief.coverageGapCount === null
    ? "coverage gaps not recorded"
    : `${brief.coverageGapCount} coverage gaps`;
  const corroboratedSummary = brief.corroboratedFindingCount === 0
    ? "No independently corroborated retained findings"
    : `${brief.corroboratedFindingCount} independently corroborated retained finding${brief.corroboratedFindingCount === 1 ? "" : "s"}`;
  const conflictSummary = brief.contradictionCount === 0
    ? "No recorded conflicts"
    : `${brief.contradictionCount} recorded conflict${brief.contradictionCount === 1 ? "" : "s"}`;
  const unknownSummary = brief.traversalLimited
    ? "Traversal incomplete"
    : brief.coverageGapCount === null
      ? "Not classified"
      : brief.coverageGapCount === 0
        ? "No recorded coverage gaps"
        : `${brief.coverageGapCount} open coverage gap${brief.coverageGapCount === 1 ? "" : "s"}`;
  const visibleCorroboratedFindings = brief.corroboratedFindings.slice(0, 3);
  const hiddenCorroboratedCount = Math.max(0, brief.corroboratedFindings.length - visibleCorroboratedFindings.length);
  const visibleConflictingFindings = brief.conflictingFindings.slice(0, 3);
  const hiddenConflictingCount = Math.max(0, brief.conflictingFindings.length - visibleConflictingFindings.length);
  const visibleOpenQuestions = brief.openQuestions.slice(0, 3);
  const hiddenOpenQuestionCount = Math.max(0, brief.openQuestions.length - visibleOpenQuestions.length);
  const visibleDecisions = currentDecisionState?.items.slice(0, 5) ?? [];
  const hiddenDecisionCount = Math.max(0, (currentDecisionState?.items.length ?? 0) - visibleDecisions.length);

  return (
    <div className="caseNavigationEmptyState" aria-label="Retained case decision brief">
      <p><strong>Decision brief</strong></p>
      <p>{brief.observationCount} observations · {brief.sourceCount} sources · {brief.warningCount} warnings · {coverageSummary}</p>

      <div className="providerList" aria-label="Decision states">
        <div className="provider">
          <div>
            <strong>Corroborated</strong>
            <span>{corroboratedSummary}</span>
          </div>
          <small className="muted">Requires the same retained observation summary from at least two distinct retained sources. Observation volume alone never counts as corroboration.</small>
          {visibleCorroboratedFindings.length > 0 && (
            <div aria-label="Corroborated findings">
              <small><strong>Evidence</strong></small>
              <ul>
                {visibleCorroboratedFindings.map((finding) => (
                  <li key={finding.summary}>{finding.summary} <small className="muted">({finding.sources.join(" · ")})</small></li>
                ))}
              </ul>
              {hiddenCorroboratedCount > 0 && <small className="muted">+{hiddenCorroboratedCount} more corroborated finding{hiddenCorroboratedCount === 1 ? "" : "s"} in the retained report</small>}
            </div>
          )}
        </div>
        <div className="provider">
          <div>
            <strong>Conflicting</strong>
            <span>{conflictSummary}</span>
          </div>
          <small className="muted">No recorded conflicts is not proof that the evidence is consistent.</small>
          {visibleConflictingFindings.length > 0 && (
            <div aria-label="Conflicting findings">
              <small><strong>Evidence</strong></small>
              <ul>
                {visibleConflictingFindings.map((finding) => <li key={finding}>{finding}</li>)}
              </ul>
              {hiddenConflictingCount > 0 && <small className="muted">+{hiddenConflictingCount} more conflict{hiddenConflictingCount === 1 ? "" : "s"} in the retained report</small>}
            </div>
          )}
        </div>
        <div className="provider">
          <div>
            <strong>Unknown</strong>
            <span>{unknownSummary}</span>
          </div>
          <small className="muted">
            {brief.traversalLimited
              ? "Traversal limit reached. Treat unexplored leads as open questions rather than negative findings."
              : brief.coverageGapCount === null
                ? "Coverage gaps were not recorded for this report shape; unknown must not be presented as none."
                : "Coverage gaps are retained report findings, not evidence of absence."}
          </small>
          {visibleOpenQuestions.length > 0 && (
            <div aria-label="Open questions">
              <small><strong>Open questions</strong></small>
              <ul>
                {visibleOpenQuestions.map((question) => <li key={question}>{question}</li>)}
              </ul>
              {hiddenOpenQuestionCount > 0 && (
                <small className="muted">+{hiddenOpenQuestionCount} more in the retained report</small>
              )}
            </div>
          )}
        </div>
      </div>

      {brief.sourceStates.length > 0 ? (
        <small className="muted">Source states: {brief.sourceStates.map(([state, count]) => `${state} ${count}`).join(" · ")}</small>
      ) : (
        <small className="muted">Source states were not recorded for this case.</small>
      )}
      <small className="muted">Read-only evidence synopsis. No identity probability is calculated; same-handle overlap is not identity proof. Inspect canonical observations for evidence and provenance.</small>

      <div className="provider" aria-label="Analyst decision log">
        <div>
          <strong>Analyst decision log</strong>
          <span>Append-only rationale retained with this case</span>
        </div>
        <form onSubmit={appendDecision}>
          <label>
            Decision
            <select
              value={disposition}
              onChange={(event) => setDisposition(event.target.value as CaseDecisionDisposition)}
              disabled={decisionSaving}
            >
              {Object.entries(DECISION_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </label>
          <label>
            Rationale
            <textarea
              value={rationale}
              onChange={(event) => setRationale(event.target.value)}
              maxLength={1200}
              rows={3}
              placeholder="Record what the evidence supports, what remains unresolved, and why this is the next action."
              disabled={decisionSaving}
            />
          </label>
          <button type="submit" className="secondaryButton" disabled={decisionSaving || !rationale.trim()}>
            {decisionSaving ? "Recording…" : "Record decision"}
          </button>
          {decisionSaveError && <small className="errorText" role="alert">{decisionSaveError}</small>}
        </form>

        {currentDecisionState?.failed ? (
          <small className="muted" role="status">Decision history could not be loaded. Do not treat this case as having no prior analyst decisions.</small>
        ) : currentDecisionState === null ? (
          <small className="muted" role="status">Loading analyst decision history…</small>
        ) : visibleDecisions.length === 0 ? (
          <small className="muted">No analyst decision has been recorded for this retained case.</small>
        ) : (
          <div aria-label="Recorded analyst decisions">
            <ol>
              {visibleDecisions.map((decision) => (
                <li key={decision.id}>
                  <strong>{DECISION_LABELS[decision.disposition]}</strong>{" · "}
                  <time dateTime={decision.created_at}>{new Date(decision.created_at).toLocaleString()}</time>
                  <p>{decision.rationale}</p>
                </li>
              ))}
            </ol>
            {hiddenDecisionCount > 0 && <small className="muted">+{hiddenDecisionCount} older retained decision{hiddenDecisionCount === 1 ? "" : "s"}</small>}
          </div>
        )}
        <small className="muted">Decisions are analyst-authored workflow records, not evidence and not identity claims. Entries cannot be edited in place.</small>
      </div>
    </div>
  );
}
