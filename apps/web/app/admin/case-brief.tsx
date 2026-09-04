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
  contradictionCount: number;
  warningCount: number;
  coverageGapCount: number;
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

export function summarizeRetainedCase(report: JsonObject): Brief {
  const converged = objectValue(report.converged_report);
  if (Object.keys(converged).length > 0) {
    const nodes = objectList(converged.nodes);
    const sources = new Set<string>();
    let observationCount = 0;
    let contradictionCount = 0;
    const sourceStateTotals = new Map<string, number>();

    for (const node of nodes) {
      const observations = objectList(node.observations);
      observationCount += observations.length;
      for (const observation of observations) {
        if (typeof observation.source === "string" && observation.source) sources.add(observation.source);
        if (observationIsContradiction(observation)) contradictionCount += 1;
      }
      const sourceRuns = objectValue(node.source_runs);
      for (const [state, count] of countEntries(sourceRuns.state_counts)) {
        sourceStateTotals.set(state, (sourceStateTotals.get(state) ?? 0) + count);
      }
    }

    return {
      observationCount,
      sourceCount: sources.size,
      contradictionCount,
      warningCount: stringList(converged.warnings).length,
      coverageGapCount: 0,
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
    contradictionCount: indexedContradictions.size,
    warningCount: stringList(report.warnings).length,
    coverageGapCount: stringList(structured.coverage_gaps).length,
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

  const currentPayload = requestState?.caseId === caseId ? requestState.payload : null;
  const currentFailed = requestState?.caseId === caseId && requestState.failed;
  const brief = useMemo(() => currentPayload ? summarizeRetainedCase(currentPayload.report) : null, [currentPayload]);
  if (!caseId || disabled) return null;

  if (currentFailed) {
    return <p className="muted" role="status">Case brief unavailable. Use the reopened retained report as the source of truth.</p>;
  }
  if (!brief) return <p className="muted" role="status">Building case brief from the retained report…</p>;

  return (
    <div className="caseNavigationEmptyState" aria-label="Retained case brief">
      <p><strong>Case brief</strong></p>
      <p>{brief.observationCount} observations · {brief.sourceCount} sources · {brief.contradictionCount} conflicts · {brief.warningCount} warnings · {brief.coverageGapCount} gaps</p>
      {brief.sourceStates.length > 0 ? (
        <small className="muted">Source states: {brief.sourceStates.map(([state, count]) => `${state} ${count}`).join(" · ")}</small>
      ) : (
        <small className="muted">Source states were not recorded for this case.</small>
      )}
      <small className="muted">Read-only synopsis. No identity probability is calculated; same-handle overlap is not identity proof. Inspect canonical observations for evidence and provenance.</small>
    </div>
  );
}
