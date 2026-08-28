import Link from "next/link";

import { syntheticCase } from "../dashboard/fixture";
import styles from "./demo.module.css";

function words(value: string) {
  return value.replaceAll("_", " ");
}

export default function PublicDemoPage() {
  const caseData = syntheticCase;
  const observations = new Map(caseData.observations.map((item) => [item.id, item]));
  const contradicted = caseData.account_candidates.filter(
    (candidate) => candidate.correlation?.outcome === "contradicted",
  );

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
          Candidate scores below are deterministic evidence-strength triage. They are uncalibrated,
          they are not identity probabilities, and a hard contradiction can veto positive evidence.
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
            <p className={styles.kicker}>SOURCE COVERAGE</p>
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
          <section className={styles.section}>
            <div className={styles.sectionHead}>
              <div>
                <p className={styles.kicker}>01 / CORRELATION</p>
                <h2>Account candidates</h2>
              </div>
              <span>{caseData.account_candidates.length} reviewed</span>
            </div>
            <div className={styles.candidateGrid}>
              {caseData.account_candidates.map((candidate) => {
                const correlation = candidate.correlation;
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
                        <div className={styles.scoreLine}>
                          <span>{correlation.evidence_score}</span>
                          <div>
                            <strong>evidence score / 100</strong>
                            <small>uncalibrated · not probability</small>
                          </div>
                        </div>
                        <ul className={styles.factorList}>
                          {correlation.factors.map((factor, index) => (
                            <li key={`${factor.kind}-${index}`}>
                              <div>
                                <strong>{words(factor.kind)}</strong>
                                <span>{factor.rationale}</span>
                              </div>
                              <em className={factor.veto ? styles.bad : factor.status === "excluded_stale" ? styles.warn : styles.good}>
                                {factor.veto ? "veto" : factor.status === "excluded_stale" ? "stale" : `${factor.applied_weight > 0 ? "+" : ""}${factor.applied_weight}`}
                              </em>
                            </li>
                          ))}
                        </ul>
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
                <p className={styles.kicker}>02 / EVIDENCE</p>
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
                    <p>{observation.provenance.source_name} · {observation.freshness}</p>
                    <code>{observation.provenance.source_locator}</code>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHead}>
              <div>
                <p className={styles.kicker}>03 / CLAIM REVIEW</p>
                <h2>Claims and exceptions</h2>
              </div>
              <span>human review required</span>
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
