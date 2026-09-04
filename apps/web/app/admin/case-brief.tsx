"use client";

import { useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type JsonObject = Record<string, unknown>;

type StoredCasePayload = {
  id: string;
  report: JsonObject;
};

type Brief = {
  observationCount: number;
  sourceCount: number;
  corroboratedFindingCount: number;
  contradictionCount: number;
  warningCount: number;
  coverageGapCount: number | null;
  traversalLimited: boolean;
  sourceStates: Array<[string, number]>;
};

type BriefRequestState = {
  caseId: string;
  payload: StoredCasePayload | null;
  failed: boolean;
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

function observationIsContradiction(observation: JsonObject): boolean {
  const details = objectValue(observation.details);
  return details.contradiction === true || details.account_state === "illegal";
}

function countIndependentlyCorroboratedFindings(observations: JsonObject[]): number {
  const sourcesBySummary = new Map<string, Set<string>>();
  for (const observation of observations) {
    const summary = typeof observation.summary === "string" ? observation.summary.trim() : "";
    const source = typeof observation.source === "string" ? observation.source.trim() : "";
    if (!summary || !source) continue;
    const summaryKey = summary.toLocaleLowerCase();
    const sources = sourcesBySummary.get(summaryKey) ?? new Set<string>();
    sources.add(source);
    sourcesBySummary.set(summaryKey, sources);
  }
  return [...sourcesBySummary.values()].filter((sources) => sources.size >= 2).length;
}

export function summarizeRetainedCase(report: JsonObject): Brief {
  const converged = objectValue(report.converged_report);
  if (Object.keys(converged).length > 0) {
    const nodes = objectList(converged.nodes);
    const sources = new Set<string>();
    const retainedObservations: JsonObject[] = [];
    let contradictionCount = 0;
    const sourceStateTotals = new Map<string, number>();

    for (const node of nodes) {
      const observations = objectList(node.observations);
      retainedObservations.push(...observations);
      for (const observation of observations) {
        if (typeof observation.source === "string" && observation.source) sources.add(observation.source);
        if (observationIsContradiction(observation)) contradictionCount += 1;
      }
      const sourceRuns = objectValue(node.source_runs);
      for (const [state, count] of countEntries(sourceRuns.state_counts)) {
        sourceStateTotals.set(state, (sourceStateTotals.get(state) ?? 0) + count);
      }
    }

    const executiveSummary = objectValue(converged.executive_summary);
    return {
      observationCount: retainedObservations.length,
      sourceCount: sources.size,
      corroboratedFindingCount: countIndependentlyCorroboratedFindings(retainedObservations),
      contradictionCount,
      warningCount: stringList(converged.warnings).length,
      coverageGapCount: null,
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
  const sourceRuns = objectValue(report.source_runs);

  return {
    observationCount: observations.length,
    sourceCount: sources.size,
    corroboratedFindingCount: countIndependentlyCorroboratedFindings(observations),
    contradictionCount: indexedContradictions.size,
    warningCount: stringList(report.warnings).length,
    coverageGapCount: stringList(structured.coverage_gaps).length,
    traversalLimited: false,
    sourceStates: countEntries(sourceRuns.state_counts),
  };
}

export function CaseBrief({ caseId, disabled = false }: { caseId?: string; disabled?: boolean }) {
  const [requestState, setRequestState] = useState<BriefRequestState | null>(null);

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

  const currentRequest = requestState && requestState.caseId === caseId ? requestState : null;
  const currentPayload = currentRequest?.payload ?? null;
  const currentFailed = currentRequest?.failed ?? false;
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
        </div>
        <div className="provider">
          <div>
            <strong>Conflicting</strong>
            <span>{conflictSummary}</span>
          </div>
          <small className="muted">No recorded conflicts is not proof that the evidence is consistent.</small>
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
        </div>
      </div>

      {brief.sourceStates.length > 0 ? (
        <small className="muted">Source states: {brief.sourceStates.map(([state, count]) => `${state} ${count}`).join(" · ")}</small>
      ) : (
        <small className="muted">Source states were not recorded for this case.</small>
      )}
      <small className="muted">Read-only synopsis. No identity probability is calculated; same-handle overlap is not identity proof. Inspect canonical observations for evidence and provenance.</small>
    </div>
  );
}
