import Link from "next/link";

import { syntheticCase } from "../dashboard/fixture";
import styles from "./demo.module.css";
import { ReviewedDocumentSimulation } from "./reviewed-document-simulation";

const simulatedSourceRuns = [
  {
    source_name: "Synthetic profile API",
    state: "executed",
    reason: "results_returned",
    observation_count: 2,
    attempted: true,
  },
  {
    source_name: "Synthetic exact registry",
    state: "not_found",
    reason: "no_match",
    observation_count: 0,
    attempted: true,
  },
  {
    source_name: "Synthetic metered source",
    state: "unavailable",
    reason: "optional_not_configured",
    observation_count: 0,
    attempted: false,
  },
  {
    source_name: "Synthetic reviewed source",
    state: "review_required",
    reason: "review_gate",
    observation_count: 0,
    attempted: false,
  },
  {
    source_name: "Synthetic remote source",
    state: "unavailable",
    reason: "remote_rate_limit",
    observation_count: 0,
    attempted: true,
  },
] as const;

const simulatedLifecycleStates = [
  {
    step: "Case intake",
    private_action: "Create a retained case from reviewed clues",
    public_state: "simulated only",
    detail: "The observer shows accepted clue concepts but never accepts a real-person submission or creates storage.",
  },
  {
    step: "Reviewed document",
    private_action: "Preview, review and explicitly admit extracted clues",
    public_state: "interactive fixture",
    detail: "The safe simulation above mirrors confirm, reject, re-review, promotion and case-start boundaries without a file input, upload endpoint or document retention.",
  },
  {
    step: "Retained cases",
    private_action: "Search, switch and reopen retained investigations",
    public_state: "synthetic navigation",
    detail: "Case-switching semantics are represented with fixed labels; the visitor cannot list or read private retained cases.",
  },
  {
    step: "Delete case",
    private_action: "Confirm destructive deletion of a retained case",
    public_state: "disabled demo",
    detail: "The destructive boundary is visible but cannot mutate the fixture or call a deletion endpoint.",
  },
  {
    step: "Session boundary",
    private_action: "Expire or end the authenticated operator session",
    public_state: "not authenticated",
    detail: "Logout and expiry concepts are shown as product states; this static observer never creates an admin session.",
  },
] as const;

const simulatedWorkspaceStates = [
  {
    state: "Case loading",
    tone: "loading",
    private_state: "Retained-case history is still being fetched",
    detail: "The private workbench marks the case list busy and locks remote actions while loading. This observer demonstrates that state without making a request.",
  },
  {
    state: "Case index unavailable",
    tone: "error",
    private_state: "Retained-case history failed to load",
    detail: "A failed index is not an empty workspace. The operator must refresh before concluding that no retained cases exist.",
  },
  {
    state: "Research completed with limits",
    tone: "partial",
    private_state: "One or more provider attempts failed or source states remain unresolved",
    detail: "Usable evidence stays visible while incomplete source coverage remains explicit. Review source states before treating the case as complete.",
  },
  {
    state: "Some source paths were not attempted",
    tone: "limited",
    private_state: "Configuration, routing, review, budget or policy stopped provider contact",
    detail: "Missing observations from an unattempted path are a coverage limit, not negative evidence about the subject or claim.",
  },
  {
    state: "No retained match from attempted sources",
    tone: "quiet",
    private_state: "Every attempted source returned no match",
    detail: "Source silence is not evidence that the subject or claim does not exist elsewhere.",
  },
  {
    state: "Attempted sources completed",
    tone: "complete",
    private_state: "Every attempted source reached a terminal result",
    detail: "Completion applies only to the bounded configured source set; it does not imply exhaustive coverage.",
  },
] as const;

function words(value: string) {
  return value.replaceAll("_", " ");
}

function timestamp(value: string | null) {
  return value ? value.replace("T", " ").replace("Z", " UTC") : "not recorded";
}

export default function PublicDemoPage() {
  const caseData = syntheticCase;
  const observations = new Map(caseData.observations.map((item) => [item.id, item]));
  const identifiers = new Map(caseData.identifiers.map((item) => [item.id, item]));
  const contradicted = caseData.account_candidates.filter(
    (candidate) => candidate.correlation?.outcome === "contradicted",
  );
  const incompleteSourceRuns = simulatedSourceRuns.filter((run) => run.state !== "executed").length;
  const unresolvedClaimQuestions = caseData.claims.flatMap((claim) =>
    claim.evidence_links
      .filter((link) => link.relation === "unresolved")
      .map((link) => ({
        key: `${claim.id}-${link.observation_id}`,
        heading: claim.statement,
        status: "unresolved claim link",
        detail: `${observations.get(link.observation_id)?.summary ?? "Retained observation"} · ${link.rationale}`,
      })),
  );
  const insufficientCandidateQuestions = caseData.account_candidates
    .filter((candidate) => candidate.correlation?.outcome === "insufficient_evidence")
    .map((candidate) => ({
      key: `candidate-${candidate.observation_id}`,
      heading: `${candidate.site} candidate`,
      status: "insufficient evidence",
      detail: "The retained M5 outcome does not support an identity conclusion; more independent evidence or human review is required.",
    }));
  const openQuestions = [...unresolvedClaimQuestions, ...insufficientCandidateQuestions];

  return (
    <main className={styles.shell}>
      <header className={styles.topbar}>
        <Link className={styles.brand} href="/">
          <span>PL</span>
          <strong>PersonaLattice</strong>
        </Link>
        <div className={styles.topActions}>
          <span>PUBLIC READ-ONLY DEMO</span>
          <Link href="/admin">Private admin</Link>
        </div>
      </header>

      <section className={styles.caseHeader}>
        <div>
          <p className={styles.kicker}>SYNTHETIC INVESTIGATION WORKSPACE</p>
          <h1>{caseData.display_name}</h1>
          <p>
            This mirrors the operator evidence hierarchy using fixed synthetic data. No provider
            requests are executed from this demo and no visitor can submit a real-person research job.
          </p>
        </div>
        <dl className={styles.summaryStats}>
          <div><dt>observations</dt><dd>{caseData.observations.length}</dd></div>
          <div><dt>candidates</dt><dd>{caseData.account_candidates.length}</dd></div>
          <div><dt>claims</dt><dd>{caseData.claims.length}</dd></div>
          <div><dt>hard conflicts</dt><dd>{contradicted.length}</dd></div>
        </dl>
      </section>

      <section className={styles.boundary}>
        <strong>Interpretation boundary</strong>
        <p>
          Candidate factors below are deterministic evidence-strength triage. They are grouped by evidentiary
          direction, remain uncalibrated and non-probabilistic, and a hard contradiction can veto positive evidence.
        </p>
      </section>

      <div className={styles.workspace}>
        <aside className={styles.rail}>
          <section>
            <p className={styles.kicker}>CASE SIGNALS</p>
            <div className={styles.identifiers}>
              {caseData.identifiers.map((identifier) => (
                <div key={identifier.id}>
                  <span>{identifier.kind}</span>
                  <strong>{identifier.value}</strong>
                </div>
              ))}
            </div>
          </section>

          <section>
            <p className={styles.kicker}>EVIDENCE SOURCES</p>
            <ul className={styles.sourceList}>
              {Array.from(new Set(caseData.observations.map((item) => item.provenance.source_name))).map(
                (source) => (
                  <li key={source}>
                    <span>{source}</span>
                    <strong>observed</strong>
                  </li>
                ),
              )}
            </ul>
          </section>

          <section className={styles.railNote}>
            <p className={styles.kicker}>PUBLIC BOUNDARY</p>
            <p>
              Fixed fixture only. No uploads, mutations, case retention or provider execution are exposed.
            </p>
          </section>
        </aside>

        <div className={styles.mainColumn}>
          <ReviewedDocumentSimulation />

          <section className={styles.section}>
            <div className={styles.sectionHead}>
              <div>
                <p className={styles.kicker}>01 / SOURCE EXECUTION</p>
                <h2>Typed source-run states</h2>
              </div>
              <span>{incompleteSourceRuns} non-result states · simulated</span>
            </div>
            <p className={styles.sectionNote}>
              These rows are deterministic demonstrations of the private operator state vocabulary.
              They do not describe live requests and do not add observations to this synthetic case.
            </p>
            <div className={styles.runTable} role="table" aria-label="Simulated source execution states">
              <div className={styles.runHeader} role="row">
                <span role="columnheader">source</span>
                <span role="columnheader">state</span>
                <span role="columnheader">reason</span>
                <span role="columnheader">attempted</span>
                <span role="columnheader">observations</span>
              </div>
              {simulatedSourceRuns.map((run) => (
                <div className={styles.runRow} role="row" key={`${run.source_name}-${run.reason}`}>
                  <strong role="cell">{run.source_name}</strong>
                  <span role="cell" className={run.state === "executed" ? styles.good : run.state === "unavailable" ? styles.warn : styles.neutral}>
                    {words(run.state)}
                  </span>
                  <span role="cell">{words(run.reason)}</span>
                  <span role="cell">{run.attempted ? "yes" : "no"}</span>
                  <span role="cell">{run.observation_count}</span>
                </div>
              ))}
            </div>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHead}>
              <div>
                <p className={styles.kicker}>02 / CORRELATION</p>
                <h2>Account candidates</h2>
              </div>
              <span>{caseData.account_candidates.length} reviewed</span>
            </div>
            <div className={styles.candidateGrid}>
              {caseData.account_candidates.map((candidate) => {
                const correlation = candidate.correlation;
                const factorGroups = correlation
                  ? [
                      {
                        label: "Supporting factors",
                        factors: correlation.factors.filter((factor) => !factor.veto && factor.applied_weight > 0),
                      },
                      {
                        label: "Conflicting factors",
                        factors: correlation.factors.filter((factor) => factor.veto || factor.applied_weight < 0),
                      },
                      {
                        label: "Neutral / withheld factors",
                        factors: correlation.factors.filter((factor) => !factor.veto && factor.applied_weight === 0),
                      },
                    ]
                  : [];
                return (
                  <article className={styles.candidate} key={candidate.observation_id}>
                    <div className={styles.candidateTop}>
                      <div>
                        <span>{candidate.source_name}</span>
                        <h3>{candidate.site}</h3>
                      </div>
                      <strong className={correlation?.outcome === "contradicted" ? styles.bad : styles.neutral}>
                        {correlation ? words(correlation.outcome) : "not evaluated"}
                      </strong>
                    </div>
                    <code>{candidate.profile_url}</code>
                    {correlation && (
                      <>
                        <p className={styles.sectionNote}>
                          Non-probabilistic factor assessment. Direction follows retained M5 weight/veto semantics;
                          rationale wording alone does not create negative evidence.
                        </p>
                        {factorGroups.map((group) => (
                          <div key={group.label}>
                            <p className={styles.sectionNote}>
                              <strong>{group.label}</strong> · {group.factors.length} retained
                            </p>
                            {group.factors.length === 0 ? (
                              <p className={styles.sectionNote}>No retained factors in this direction.</p>
                            ) : (
                              <ul className={styles.factorList}>
                                {group.factors.map((factor, index) => (
                                  <li key={`${group.label}-${factor.kind}-${index}`}>
                                    <div>
                                      <strong>{words(factor.kind)}</strong>
                                      <span>{factor.rationale}</span>
                                    </div>
                                    <em
                                      className={
                                        factor.veto || factor.applied_weight < 0
                                          ? styles.bad
                                          : factor.applied_weight === 0 || factor.status === "excluded_stale"
                                            ? styles.warn
                                            : styles.good
                                      }
                                    >
                                      {factor.veto
                                        ? "veto"
                                        : factor.status === "excluded_stale"
                                          ? "stale"
                                          : `${factor.applied_weight > 0 ? "+" : ""}${factor.applied_weight}`}
                                    </em>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        ))}
                        <details>
                          <summary>Inspect model mechanics</summary>
                          <div className={styles.scoreLine}>
                            <span>{correlation.evidence_score}</span>
                            <div>
                              <strong>internal evidence-strength index / 100</strong>
                              <small>uncalibrated · not an identity probability</small>
                              <small>
                                policy {correlation.policy_version} · evaluated {timestamp(correlation.evaluated_at)}
                              </small>
                            </div>
                          </div>
                        </details>
                      </>
                    )}
                  </article>
                );
              })}
            </div>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHead}>
              <div>
                <p className={styles.kicker}>03 / EVIDENCE</p>
                <h2>Observation timeline</h2>
              </div>
              <span>provenance retained</span>
            </div>
            <ol className={styles.timeline}>
              {caseData.observations.map((observation) => (
                <li key={observation.id}>
                  <span className={styles.marker} />
                  <div>
                    <strong>{observation.summary}</strong>
                    <p>
                      {observation.provenance.source_name} · {observation.provenance.source_kind} · {observation.freshness}
                    </p>
                    <p>
                      retrieved {timestamp(observation.retrieved_at)} · expires {timestamp(observation.expires_at)}
                    </p>
                    <code>{observation.provenance.source_locator}</code>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHead}>
              <div>
                <p className={styles.kicker}>04 / EVIDENCE PATH</p>
                <h2>Clue → evidence → operator decision</h2>
              </div>
              <span>fixture-derived graph</span>
            </div>
            <p className={styles.sectionNote}>
              This compact graph view traces how a retained clue reaches a candidate, which observations influence M5,
              where a contradiction enters, and which non-probabilistic outcome remains for human review.
            </p>
            <div className={styles.lifecycleList}>
              {caseData.account_candidates.map((candidate) => {
                const clue = identifiers.get(candidate.identifier_id);
                const correlation = candidate.correlation;
                const factorPath = correlation?.factors.flatMap((factor) =>
                  factor.observation_ids.map((observationId) => {
                    const observation = observations.get(observationId);
                    const evidence = observation?.summary ?? "Retained observation";
                    return `${words(factor.kind)} → ${evidence}${factor.veto ? " → contradiction veto" : ""}`;
                  }),
                ).join(" · ");

                return (
                  <article className={styles.lifecycleRow} key={`path-${candidate.observation_id}`}>
                    <div>
                      <strong>{clue ? `${clue.kind}: ${clue.value}` : "retained clue"}</strong>
                      <span>clue → {candidate.site} candidate</span>
                    </div>
                    <em>{correlation ? words(correlation.outcome) : "not evaluated"}</em>
                    <p>
                      {factorPath || "No retained M5 factors."} → decision {correlation ? words(correlation.outcome) : "not evaluated"}
                    </p>
                  </article>
                );
              })}
            </div>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHead}>
              <div>
                <p className={styles.kicker}>05 / CLAIM REVIEW</p>
                <h2>Claims, exceptions and open questions</h2>
              </div>
              <span>{openQuestions.length} unresolved · human review required</span>
            </div>
            <div className={styles.claimGrid}>
              {caseData.claims.map((claim) => (
                <article key={claim.id}>
                  <span>stored human claim</span>
                  <h3>{claim.statement}</h3>
                  <ul>
                    {claim.evidence_links.map((link) => (
                      <li key={`${link.observation_id}-${link.relation}`}>
                        <strong>{link.relation}</strong>
                        <span>{observations.get(link.observation_id)?.summary}</span>
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
              <article className={styles.exceptionCard}>
                <span>exception state</span>
                <h3>Positive signals do not erase the contradiction.</h3>
                <p>
                  The Reddit candidate remains contradicted because a hard conflict veto is present;
                  stale supporting evidence is still shown rather than silently removed.
                </p>
              </article>
            </div>
            <div className={styles.lifecycleList}>
              {openQuestions.map((question) => (
                <article className={styles.lifecycleRow} key={question.key}>
                  <div>
                    <strong>{question.heading}</strong>
                    <span>open question</span>
                  </div>
                  <em>{question.status}</em>
                  <p>{question.detail}</p>
                </article>
              ))}
            </div>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHead}>
              <div>
                <p className={styles.kicker}>06 / OPERATOR LIFECYCLE</p>
                <h2>Private actions, public-safe states</h2>
              </div>
              <span>read-only simulation</span>
            </div>
            <p className={styles.sectionNote}>
              The private workbench includes write-capable and authenticated lifecycle steps. This observer mirrors
              their meaning without creating a session, accepting an upload, retaining a case or exposing an enabled mutation path.
            </p>
            <div className={styles.lifecycleList}>
              {simulatedLifecycleStates.map((state) => (
                <article className={styles.lifecycleRow} key={state.step}>
                  <div>
                    <strong>{state.step}</strong>
                    <span>{state.private_action}</span>
                  </div>
                  <em>{state.public_state}</em>
                  <p>{state.detail}</p>
                </article>
              ))}
            </div>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHead}>
              <div>
                <p className={styles.kicker}>07 / WORKSPACE STATES</p>
                <h2>Loading, failure and coverage semantics</h2>
              </div>
              <span>deterministic simulation</span>
            </div>
            <p className={styles.sectionNote}>
              The private workbench keeps empty, error, partial and complete states distinct so missing evidence is not
              over-interpreted. These examples are fixed explanatory states and never trigger network activity.
            </p>
            <div className={styles.lifecycleList}>
              {simulatedWorkspaceStates.map((state) => (
                <article className={styles.lifecycleRow} key={state.state}>
                  <div>
                    <strong>{state.state}</strong>
                    <span>{state.private_state}</span>
                  </div>
                  <em>{state.tone}</em>
                  <p>{state.detail}</p>
                </article>
              ))}
            </div>
          </section>
        </div>
      </div>

      <footer className={styles.footer}>
        <span>Read-only synthetic product demonstration</span>
        <div>
          <Link href="/">Product overview</Link>
          <Link href="/admin">Private admin</Link>
        </div>
      </footer>
    </main>
  );
}
