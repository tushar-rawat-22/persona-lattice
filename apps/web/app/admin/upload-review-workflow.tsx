"use client";

import { useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type ReviewCandidate = {
  candidate_id: string;
  candidate_type: string;
  origin: string;
  identifier_kind: string | null;
  value: string;
  review_status: string;
  external_research_authorized: boolean;
};

type ReviewArtifact = {
  artifact_id: string;
  original_name: string;
  candidates: ReviewCandidate[];
};

type ReviewState = {
  artifact_id: string;
  candidate_id: string;
  candidate_type: string;
  identifier_kind: string | null;
  review_status: string;
  external_research_authorized: boolean;
  source_page: number | null;
  source_start: number | null;
  source_end: number | null;
};

type PromotedLead = {
  artifact_id: string;
  candidate_id: string;
  kind: string;
  reason: string;
  disposition: string;
  source_locator: string;
};

type CreatedCase = {
  case_id: string;
  mode: "quick" | "converged";
  seed_kind: string;
  created_at: string;
  expires_at: string;
};

type UploadReviewWorkflowProps = {
  artifacts: ReviewArtifact[];
  csrfToken: string;
  purpose: string;
  consentAcknowledged: boolean;
};

type CandidateViewState = {
  review_status: string;
  external_research_authorized: boolean;
  promoted: PromotedLead | null;
  createdCase: CreatedCase | null;
  error: string;
  busyAction: string | null;
};

async function request(path: string, csrfToken: string, init: RequestInit = {}) {
  return fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(init.headers ?? {}),
      "X-PersonaLattice-CSRF": csrfToken,
    },
  });
}

function candidateKey(artifactId: string, candidateId: string) {
  return `${artifactId}:${candidateId}`;
}

function initialView(candidate: ReviewCandidate): CandidateViewState {
  return {
    review_status: candidate.review_status,
    external_research_authorized: candidate.external_research_authorized,
    promoted: null,
    createdCase: null,
    error: "",
    busyAction: null,
  };
}

function detailMessage(body: unknown, fallback: string) {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail.trim()) return detail;
  }
  return fallback;
}

export function UploadReviewWorkflow({
  artifacts,
  csrfToken,
  purpose,
  consentAcknowledged,
}: UploadReviewWorkflowProps) {
  const initial = useMemo(() => {
    const state: Record<string, CandidateViewState> = {};
    for (const artifact of artifacts) {
      for (const candidate of artifact.candidates) {
        state[candidateKey(artifact.artifact_id, candidate.candidate_id)] = initialView(candidate);
      }
    }
    return state;
  }, [artifacts]);
  const [candidateState, setCandidateState] = useState(initial);

  function patchCandidate(key: string, patch: Partial<CandidateViewState>) {
    setCandidateState((current) => ({
      ...current,
      [key]: { ...(current[key] ?? initial[key]), ...patch },
    }));
  }

  async function mutateReview(
    artifactId: string,
    candidate: ReviewCandidate,
    action: "confirm" | "reject" | "reopen",
  ) {
    const key = candidateKey(artifactId, candidate.candidate_id);
    patchCandidate(key, { busyAction: action, error: "", promoted: null, createdCase: null });
    try {
      const response = await request(
        `/v1/files/review/${artifactId}/${candidate.candidate_id}/${action}`,
        csrfToken,
        { method: "POST" },
      );
      const body = (await response.json().catch(() => ({}))) as ReviewState | Record<string, unknown>;
      if (!response.ok) throw new Error(detailMessage(body, `Could not ${action} candidate.`));
      const state = body as ReviewState;
      patchCandidate(key, {
        review_status: state.review_status,
        external_research_authorized: state.external_research_authorized,
      });
    } catch (caught) {
      patchCandidate(key, {
        error: caught instanceof Error ? caught.message : `Could not ${action} candidate.`,
      });
    } finally {
      patchCandidate(key, { busyAction: null });
    }
  }

  async function promote(artifactId: string, candidate: ReviewCandidate) {
    const key = candidateKey(artifactId, candidate.candidate_id);
    patchCandidate(key, { busyAction: "promote", error: "", createdCase: null });
    try {
      const response = await request(
        `/v1/files/review/${artifactId}/${candidate.candidate_id}/promote`,
        csrfToken,
        { method: "POST" },
      );
      const body = (await response.json().catch(() => ({}))) as PromotedLead | Record<string, unknown>;
      if (!response.ok) throw new Error(detailMessage(body, "Could not promote candidate."));
      patchCandidate(key, { promoted: body as PromotedLead });
    } catch (caught) {
      patchCandidate(key, {
        error: caught instanceof Error ? caught.message : "Could not promote candidate.",
      });
    } finally {
      patchCandidate(key, { busyAction: null });
    }
  }

  async function runCase(artifactId: string, candidate: ReviewCandidate) {
    const key = candidateKey(artifactId, candidate.candidate_id);
    patchCandidate(key, { busyAction: "run-case", error: "", createdCase: null });
    try {
      const response = await request(
        `/v1/files/review/${artifactId}/${candidate.candidate_id}/run-case`,
        csrfToken,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            mode: "converged",
            purpose,
            consent_acknowledged: consentAcknowledged,
          }),
        },
      );
      const body = (await response.json().catch(() => ({}))) as CreatedCase | Record<string, unknown>;
      if (!response.ok) throw new Error(detailMessage(body, "Could not start reviewed-candidate case."));
      patchCandidate(key, { createdCase: body as CreatedCase });
    } catch (caught) {
      patchCandidate(key, {
        error: caught instanceof Error ? caught.message : "Could not start reviewed-candidate case.",
      });
    } finally {
      patchCandidate(key, { busyAction: null });
    }
  }

  return (
    <div className="reportSection">
      <h3>Uploaded evidence review</h3>
      <p className="muted">
        Extracted candidates are inert until you review them. These controls send only the artifact
        and candidate IDs; the API reloads the trusted server-owned candidate before every mutation
        or research run.
      </p>
      <div className="providerList">
        {artifacts.map((artifact) => (
          <article className="researchObservation" key={artifact.artifact_id}>
            <div className="provider">
              <div>
                <strong>{artifact.original_name}</strong>
                <span>{artifact.candidates.length} candidates awaiting or carrying review state</span>
              </div>
              <div className="tags"><em>server-owned review state</em></div>
            </div>
            {artifact.candidates.length === 0 ? (
              <p className="muted">No review candidates were extracted from this artifact.</p>
            ) : (
              artifact.candidates.map((candidate) => {
                const key = candidateKey(artifact.artifact_id, candidate.candidate_id);
                const state = candidateState[key] ?? initialView(candidate);
                const busy = state.busyAction !== null;
                const canResearch =
                  candidate.candidate_type === "identifier" &&
                  state.review_status === "confirmed" &&
                  state.external_research_authorized;
                return (
                  <div className="nestedObservation" key={candidate.candidate_id}>
                    <strong>{candidate.identifier_kind ?? candidate.candidate_type}</strong>
                    <span>{candidate.value}</span>
                    <small>
                      {candidate.origin} · {state.review_status} · research {state.external_research_authorized ? "authorized" : "not authorized"}
                    </small>
                    <div className="adminActions">
                      {state.review_status === "pending" && (
                        <>
                          <button type="button" disabled={busy} onClick={() => mutateReview(artifact.artifact_id, candidate, "confirm")}>
                            Confirm
                          </button>
                          <button className="secondaryButton" type="button" disabled={busy} onClick={() => mutateReview(artifact.artifact_id, candidate, "reject")}>
                            Reject
                          </button>
                        </>
                      )}
                      {state.review_status !== "pending" && (
                        <button className="secondaryButton" type="button" disabled={busy} onClick={() => mutateReview(artifact.artifact_id, candidate, "reopen")}>
                          Re-review
                        </button>
                      )}
                      {canResearch && (
                        <>
                          <button className="secondaryButton" type="button" disabled={busy} onClick={() => promote(artifact.artifact_id, candidate)}>
                            Preview promoted lead
                          </button>
                          <button type="button" disabled={busy || !csrfToken} onClick={() => runCase(artifact.artifact_id, candidate)}>
                            Start converged case
                          </button>
                        </>
                      )}
                    </div>
                    {state.promoted && (
                      <small>
                        Lead preview: {state.promoted.kind} · {state.promoted.disposition} · {state.promoted.reason}. No provider was called by promotion.
                      </small>
                    )}
                    {state.createdCase && (
                      <small>
                        Case {state.createdCase.case_id.slice(0, 8)} created as {state.createdCase.mode}; retained until {new Date(state.createdCase.expires_at).toLocaleString()}.
                      </small>
                    )}
                    {state.error && <p className="error">{state.error}</p>}
                  </div>
                );
              })
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
