"use client";

import Link from "next/link";
import { useState } from "react";

import { noEvidenceCase, syntheticCase, validateSyntheticFixture } from "./fixture";
import type {
  CaseReadModel,
  CorrelationFactorView,
  CorrelationOutcome,
  ObservationView,
} from "./model";
import styles from "./dashboard.module.css";

type PreviewState = "complete" | "no-evidence" | "empty" | "loading" | "error";

const completeCase = validateSyntheticFixture(syntheticCase);
const noEvidence = validateSyntheticFixture(noEvidenceCase);

const previewStates: Array<{ id: PreviewState; label: string }> = [
  { id: "complete", label: "Complete case" },
  { id: "no-evidence", label: "No evidence" },
  { id: "empty", label: "Empty" },
  { id: "loading", label: "Loading" },
  { id: "error", label: "Error" },
];

function words(value: string) {
  return value.replaceAll("_", " ");
}

function formatUtc(value: string) {
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(value));
}

function outcomeLabel(outcome: CorrelationOutcome) {
  if (outcome === "strong_candidate") return "Strong candidate";
  if (outcome === "possible_match") return "Possible match";
  if (outcome === "contradicted") return "Contradicted";
  return "Insufficient evidence";
}

function outcomeClass(outcome: CorrelationOutcome) {
  if (outcome === "contradicted") return styles.dangerTag;
  if (outcome === "strong_candidate") return styles.strongTag;
  if (outcome === "possible_match") return styles.possibleTag;
  return styles.neutralTag;
}

function FactorRow({
  factor,
  observations,
}: {
  factor: CorrelationFactorView;
  observations: Map<string, ObservationView>;
}) {
  const evidence = factor.observation_ids
    .map((id) => observations.get(id))
    .filter((item): item is ObservationView => Boolean(item));

  return (
    <li className={`${styles.factor} ${factor.veto ? styles.factorVeto : ""}`}>
      <div className={styles.factorTopline}>
        <div>
          <strong>{words(factor.kind)}</strong>
          <span className={styles.factorGroup}>{factor.independence_group}</span>
        </div>
        <div className={styles.weightStack}>
          <span>
            {factor.applied_weight > 0 ? "+" : ""}
            {factor.applied_weight}
          </span>
          <small>applied weight</small>
        </div>
      </div>
      <p>{factor.rationale}</p>
      <div className={styles.inlineTags}>
        <span>{words(factor.status)}</span>
        {factor.veto && <span className={styles.vetoBadge}>veto</span>}
      </div>
      {evidence.length > 0 && (
        <ul className={styles.factorEvidence} aria-label="Referenced source observations">
          {evidence.map((item) => (
            <li key={item.id}>
              <span>{item.summary}</span>
              <code>{item.provenance.source_name}</code>
              {item.freshness === "stale" && <strong>stale</strong>}
            </li>
          ))}
        </ul>
      )}
    </li>
  );
}

function CaseDashboard({ data }: { data: CaseReadModel }) {
  const observations = new Map(data.observations.map((item) => [item.id, item]));
  const exceptions = data.account_candidates.flatMap((candidate) =>
    (candidate.correlation?.factors ?? [])
      .filter((factor) => factor.veto || factor.status === "excluded_stale")
      .map((factor) => ({
        candidate: candidate.site ?? candidate.source_name,
        factor,
      })),
  );

  if (data.observations.length === 0) {
    return (
      <section className={styles.stateCard} aria-labelledby="no-evidence-title">
        <p className={styles.kicker}>Case read model</p>
        <h2 id="no-evidence-title">No evidence has been attached to this synthetic case.</h2>
        <p>
          The subject and normalized identifiers can exist without observations, claims, account
          candidates, or correlation results. The dashboard does not invent a conclusion.
        </p>
        <div className={styles.identifierRow}>
          {data.identifiers.map((identifier) => (
            <span key={identifier.id}>
              <strong>{identifier.kind}</strong> {identifier.value}
            </span>
          ))}
        </div>
      </section>
    );
  }

  return (
    <div className={styles.caseLayout}>
      <section className={styles.summaryPanel} aria-labelledby="case-summary-title">
        <div className={styles.sectionHeading}>
          <div>
            <p className={styles.kicker}>01 / case</p>
            <h2 id="case-summary-title">{data.display_name ?? "Synthetic subject"}</h2>
          </div>
          <span className={styles.schemaTag}>{data.schema_version}</span>
        </div>
        <p className={styles.muted}>
          Generated {formatUtc(data.generated_at)} UTC · synthetic fixture only · no stored-case
          network request
        </p>
        <div className={styles.identifierRow} aria-label="Normalized identifiers">
          {data.identifiers.map((identifier) => (
            <span key={identifier.id}>
              <strong>{identifier.kind}</strong> {identifier.value}
            </span>
          ))}
        </div>
      </section>

      <section className={styles.boundaryPanel} aria-labelledby="boundary-title">
        <div>
          <p className={styles.kicker}>Interpretation boundary</p>
          <h2 id="boundary-title">Evidence-strength triage, not identity probability.</h2>
        </div>
        <p>
          Every M5 score shown below is <strong>uncalibrated</strong>. A candidate is not an
          identity claim, and a score such as 10 / 100 does not mean “10% likely to be the same
          person.”
        </p>
      </section>

      <section className={styles.candidateSection} aria-labelledby="candidate-title">
        <div className={styles.sectionHeading}>
          <div>
            <p className={styles.kicker}>02 / correlation</p>
            <h2 id="candidate-title">Account candidates</h2>
          </div>
          <span className={styles.countTag}>{data.account_candidates.length} candidates</span>
        </div>

        <div className={styles.candidateGrid}>
          {data.account_candidates.map((candidate) => {
            const correlation = candidate.correlation;
            return (
              <article className={styles.candidateCard} key={candidate.observation_id}>
                <div className={styles.candidateHeader}>
                  <div>
                    <p className={styles.sourceLabel}>{candidate.source_name}</p>
                    <h3>{candidate.site ?? "Unnamed candidate"}</h3>
                  </div>
                  {correlation && (
                    <span className={`${styles.outcomeTag} ${outcomeClass(correlation.outcome)}`}>
                      {outcomeLabel(correlation.outcome)}
                    </span>
                  )}
                </div>

                <code className={styles.locator}>{candidate.profile_url}</code>

                {!correlation ? (
                  <p className={styles.muted}>No correlation run exists for this candidate.</p>
                ) : (
                  <>
                    <div className={styles.scoreRow}>
                      <div>
                        <span className={styles.scoreValue}>{correlation.evidence_score}</span>
                        <span className={styles.scoreScale}> / 100</span>
                      </div>
                      <div>
                        <strong>Evidence score</strong>
                        <span>Uncalibrated rule score · not a probability</span>
                      </div>
                    </div>

                    {correlation.outcome === "contradicted" && (
                      <div className={styles.contradictionBanner} role="note">
                        Hard contradiction veto is active. Positive evidence is retained for review,
                        but the M5 outcome remains contradicted and the displayed score is 0.
                      </div>
                    )}

                    <dl className={styles.metaGrid}>
                      <div>
                        <dt>Calibration</dt>
                        <dd>{correlation.calibration_status}</dd>
                      </div>
                      <div>
                        <dt>Identity claim</dt>
                        <dd>{correlation.is_identity_claim ? "yes" : "no"}</dd>
                      </div>
                      <div>
                        <dt>Independent groups</dt>
                        <dd>{correlation.positive_independence_groups}</dd>
                      </div>
                      <div>
                        <dt>Policy</dt>
                        <dd>{correlation.policy_version}</dd>
                      </div>
                    </dl>

                    <h4>Evidence factors</h4>
                    <ol className={styles.factorList}>
                      {correlation.factors.map((factor, index) => (
                        <FactorRow
                          factor={factor}
                          observations={observations}
                          key={`${factor.kind}-${factor.independence_group}-${index}`}
                        />
                      ))}
                    </ol>
                  </>
                )}
              </article>
            );
          })}
        </div>
      </section>

      <div className={styles.twoColumn}>
        <section className={styles.panel} aria-labelledby="evidence-title">
          <div className={styles.sectionHeading}>
            <div>
              <p className={styles.kicker}>03 / observations</p>
              <h2 id="evidence-title">Source evidence timeline</h2>
            </div>
            <span className={styles.countTag}>{data.observations.length} observations</span>
          </div>
          <ol className={styles.timeline}>
            {data.observations.map((observation) => (
              <li key={observation.id}>
                <div className={styles.timelineMarker} aria-hidden="true" />
                <div>
                  <div className={styles.timelineTopline}>
                    <strong>{observation.summary}</strong>
                    <span
                      className={
                        observation.freshness === "stale"
                          ? styles.staleTag
                          : styles.freshnessTag
                      }
                    >
                      {observation.freshness}
                    </span>
                  </div>
                  <p>
                    <span>{observation.provenance.source_kind}</span>
                    {" · "}
                    <strong>{observation.provenance.source_name}</strong>
                    {" · "}
                    {formatUtc(observation.retrieved_at)} UTC
                  </p>
                  <code>{observation.provenance.source_locator}</code>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className={styles.panel} aria-labelledby="claim-title">
          <div className={styles.sectionHeading}>
            <div>
              <p className={styles.kicker}>04 / claims</p>
              <h2 id="claim-title">Factual claims</h2>
            </div>
            <span className={styles.countTag}>{data.claims.length} claims</span>
          </div>
          {data.claims.length === 0 ? (
            <p className={styles.muted}>No factual claims are stored for this case.</p>
          ) : (
            <div className={styles.claimList}>
              {data.claims.map((claim) => (
                <article key={claim.id} className={styles.claimCard}>
                  <div className={styles.claimTopline}>
                    <span>{claim.origin} claim</span>
                    <span>stored claim confidence {claim.confidence.toFixed(2)}</span>
                  </div>
                  <h3>{claim.statement}</h3>
                  <p className={styles.claimBoundary}>
                    Claim confidence is a separate stored field. It is not the M5 evidence score.
                  </p>
                  <ul>
                    {claim.evidence_links.map((link, index) => {
                      const observation = observations.get(link.observation_id);
                      return (
                        <li key={`${link.observation_id}-${link.relation}-${index}`}>
                          <span className={styles.relationTag}>{link.relation}</span>
                          <div>
                            <strong>{observation?.summary ?? "Referenced observation"}</strong>
                            {link.rationale && <p>{link.rationale}</p>}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className={styles.panel} aria-labelledby="exceptions-title">
        <div className={styles.sectionHeading}>
          <div>
            <p className={styles.kicker}>05 / exceptions</p>
            <h2 id="exceptions-title">Contradictions and stale evidence</h2>
          </div>
          <span className={styles.countTag}>{exceptions.length} visible exceptions</span>
        </div>
        {exceptions.length === 0 ? (
          <p className={styles.muted}>No vetoes or excluded stale factors are present.</p>
        ) : (
          <ul className={styles.exceptionList}>
            {exceptions.map(({ candidate, factor }, index) => (
              <li key={`${candidate}-${factor.kind}-${index}`}>
                <span className={factor.veto ? styles.vetoBadge : styles.staleTag}>
                  {factor.veto ? "veto" : "stale"}
                </span>
                <div>
                  <strong>
                    {candidate} · {words(factor.kind)}
                  </strong>
                  <p>{factor.rationale}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

export default function DashboardPage() {
  const [previewState, setPreviewState] = useState<PreviewState>("complete");

  let content;
  if (previewState === "loading") {
    content = (
      <section className={styles.stateCard} role="status" aria-live="polite">
        <p className={styles.kicker}>Synthetic state</p>
        <h2>Loading the bounded case read model…</h2>
        <div className={styles.loadingBars} aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      </section>
    );
  } else if (previewState === "error") {
    content = (
      <section className={`${styles.stateCard} ${styles.errorState}`} role="alert">
        <p className={styles.kicker}>Synthetic state</p>
        <h2>The case read model failed validation.</h2>
        <p>
          A production UI must not guess around malformed evidence. M6 renders a clear error state
          and stops instead.
        </p>
      </section>
    );
  } else if (previewState === "empty") {
    content = (
      <section className={styles.stateCard} aria-labelledby="empty-title">
        <p className={styles.kicker}>Synthetic state</p>
        <h2 id="empty-title">No case is selected.</h2>
        <p>
          This is the intentional empty shell. It contains no default person, no hidden background
          request, and no fabricated evidence.
        </p>
      </section>
    );
  } else {
    content = <CaseDashboard data={previewState === "no-evidence" ? noEvidence : completeCase} />;
  }

  return (
    <main className={styles.dashboardShell}>
      <header className={styles.hero}>
        <div>
          <p className={styles.kicker}>PERSONALATTICE / M6 / LOCAL SYNTHETIC</p>
          <h1>Evidence intelligence without false certainty.</h1>
          <p>
            Inspect provenance, freshness, factual claims, account candidates, contradictions and
            deterministic M5 factors without turning the rule score into an identity probability.
          </p>
        </div>
        <div className={styles.heroMeta}>
          <span>local / development</span>
          <span>synthetic fixture</span>
          <Link href="/">Back to intake</Link>
        </div>
      </header>

      <nav className={styles.stateNav} aria-label="Synthetic dashboard state previews">
        <span>Preview state</span>
        <div>
          {previewStates.map((item) => (
            <button
              aria-controls="dashboard-state"
              aria-pressed={previewState === item.id}
              key={item.id}
              onClick={() => setPreviewState(item.id)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      <div id="dashboard-state">{content}</div>

      <footer className={styles.footer}>
        M6 has no stored-case HTTP read endpoint, export workflow, AI identity decision, or
        autonomous provider expansion. Authentication, object authorization, retention/deletion,
        audit and abuse controls remain M7 work.
      </footer>
    </main>
  );
}
