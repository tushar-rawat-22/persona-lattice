"use client";

import { useState } from "react";

import styles from "./demo.module.css";
import reviewStyles from "./reviewed-document-simulation.module.css";

type ReviewStatus = "pending" | "confirmed" | "rejected";

type Candidate = {
  id: string;
  kind: string;
  value: string;
  origin: string;
  initialStatus: ReviewStatus;
};

const candidates: Candidate[] = [
  {
    id: "candidate-username",
    kind: "username",
    value: "atlas_zero",
    origin: "synthetic page 2 · chars 418–428",
    initialStatus: "pending",
  },
  {
    id: "candidate-domain",
    kind: "domain",
    value: "atlas-labs.example",
    origin: "synthetic page 3 · chars 121–138",
    initialStatus: "rejected",
  },
] as const;

export function ReviewedDocumentSimulation() {
  const [statuses, setStatuses] = useState<Record<string, ReviewStatus>>(
    Object.fromEntries(candidates.map((candidate) => [candidate.id, candidate.initialStatus])),
  );
  const [previewedLead, setPreviewedLead] = useState<string | null>(null);
  const [caseSimulation, setCaseSimulation] = useState<string | null>(null);
  const [sessionExpired, setSessionExpired] = useState(false);

  function setStatus(candidateId: string, status: ReviewStatus) {
    setStatuses((current) => ({ ...current, [candidateId]: status }));
    setPreviewedLead(null);
    setCaseSimulation(null);
  }

  function resetFixture() {
    setStatuses(Object.fromEntries(candidates.map((candidate) => [candidate.id, candidate.initialStatus])));
    setPreviewedLead(null);
    setCaseSimulation(null);
    setSessionExpired(false);
  }

  return (
    <section className={styles.section}>
      <div className={styles.sectionHead}>
        <div>
          <p className={styles.kicker}>REVIEWED DOCUMENT / SAFE SIMULATION</p>
          <h2>Extracted clues stay inert until human review</h2>
        </div>
        <span>synthetic artifact · local state only</span>
      </div>
      <p className={styles.sectionNote}>
        This fixture mirrors the private reviewed-document workflow without accepting a file, retaining a document,
        creating an operator session or calling an API. Every control below changes browser-memory demo state only.
      </p>

      <div className={reviewStyles.artifact}>
        <div className={reviewStyles.artifactHead}>
          <div>
            <strong>synthetic-intake-brief.pdf</strong>
            <span>sanitized fixture · 2 extracted candidates</span>
          </div>
          <div className={reviewStyles.actions}>
            <button type="button" onClick={() => setSessionExpired(true)} disabled={sessionExpired}>
              Simulate session expiry
            </button>
            <button type="button" onClick={resetFixture}>Reset fixture</button>
          </div>
        </div>

        {sessionExpired && (
          <p className={reviewStyles.alert} role="alert">
            Operator session expired. The rejected private request would leave review state unchanged; demo review actions are locked until reset.
          </p>
        )}

        <div className={reviewStyles.candidateList}>
          {candidates.map((candidate) => {
            const status = statuses[candidate.id] ?? candidate.initialStatus;
            const canResearch = status === "confirmed";
            return (
              <article className={reviewStyles.candidate} key={candidate.id}>
                <div className={reviewStyles.candidateTop}>
                  <div>
                    <span>{candidate.kind}</span>
                    <strong>{candidate.value}</strong>
                    <small>{candidate.origin}</small>
                  </div>
                  <em>{status} · research {canResearch ? "authorized" : "not authorized"}</em>
                </div>

                <div className={reviewStyles.actions} aria-label={`${candidate.kind} simulated review actions`}>
                  {status === "pending" ? (
                    <>
                      <button type="button" disabled={sessionExpired} onClick={() => setStatus(candidate.id, "confirmed")}>
                        Confirm
                      </button>
                      <button type="button" disabled={sessionExpired} onClick={() => setStatus(candidate.id, "rejected")}>
                        Reject
                      </button>
                    </>
                  ) : (
                    <button type="button" disabled={sessionExpired} onClick={() => setStatus(candidate.id, "pending")}>
                      Re-review
                    </button>
                  )}
                  <button
                    type="button"
                    disabled={sessionExpired || !canResearch}
                    onClick={() => {
                      setPreviewedLead(candidate.id);
                      setCaseSimulation(null);
                    }}
                  >
                    Preview promoted lead
                  </button>
                  <button
                    type="button"
                    disabled={sessionExpired || !canResearch}
                    onClick={() => setCaseSimulation(candidate.id)}
                  >
                    Simulate converged case start
                  </button>
                </div>

                {previewedLead === candidate.id && (
                  <p className={reviewStyles.result}>
                    Lead preview: {candidate.kind} · eligible after explicit review. No provider was called by promotion and no retained lead was created.
                  </p>
                )}
                {caseSimulation === candidate.id && (
                  <p className={reviewStyles.result}>
                    Simulated case start stopped at the public boundary. No case was created, no provider ran and nothing was retained.
                  </p>
                )}
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
