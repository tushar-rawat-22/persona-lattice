import Link from "next/link";

import { syntheticCase } from "./dashboard/fixture";
import styles from "./public.module.css";

const capabilities = [
  ["Clue", "Start with bounded identifiers", "Normalize phones, emails, usernames, domains, public URLs and reviewed files without assuming every clue belongs to the same person."],
  ["Source", "Show what was actually checked", "Keep executed, unavailable, no-match and review-required source states visible so missing coverage is never mistaken for negative evidence."],
  ["Evidence", "Retain the native trail", "Preserve source locator, retrieval time, freshness, query context and the research pivot that produced each observation."],
  ["Conflict", "Keep disagreement visible", "Stale observations, hard contradictions and unresolved links remain part of the case instead of being buried by positive signals."],
  ["Decision", "Leave identity judgment to the analyst", "Correlation is deterministic evidence-strength triage, not an identity probability. The operator records the decision and rationale."],
] as const;

export default function Home() {
  const sourceCount = new Set(syntheticCase.observations.map((item) => item.provenance.source_name)).size;
  const conflictCount = syntheticCase.account_candidates.filter(
    (candidate) => candidate.correlation?.outcome === "contradicted",
  ).length;
  const snapshotRows = syntheticCase.observations.slice(0, 3);

  return (
    <main className={styles.shell}>
      <header className={styles.topbar}>
        <Link className={styles.brand} href="/" aria-label="PersonaLattice home">
          <span className={styles.brandMark}>PL</span>
          <span>
            <strong>PersonaLattice</strong>
            <small>evidence casebook</small>
          </span>
        </Link>
        <nav className={styles.nav} aria-label="Public navigation">
          <Link className={styles.navLink} href="#method">Method</Link>
          <Link className={styles.navLink} href="/demo">Synthetic case</Link>
          <Link className={styles.adminLink} href="/admin">Private operator</Link>
        </nav>
      </header>

      <section className={styles.hero}>
        <div className={styles.heroCopy}>
          <p className={styles.kicker}>Public-source research, kept inspectable</p>
          <h1>Follow the evidence without forcing the identity.</h1>
          <p className={styles.lead}>
            PersonaLattice turns sparse clues into an analyst casebook: what was checked, what was
            observed, where it came from, what conflicts, what remains unknown, and why a human made
            the final decision.
          </p>
          <div className={styles.heroActions}>
            <Link className={styles.primaryLink} href="/demo">Inspect the synthetic case</Link>
            <span className={styles.boundaryText}>Read-only fixture · no live research or private case access</span>
          </div>
        </div>

        <aside className={styles.caseBrief} aria-label="Synthetic case file preview">
          <div className={styles.caseBriefHead}>
            <span>Case file / synthetic fixture</span>
            <strong>Read only</strong>
          </div>
          <div className={styles.caseIdentity}>
            <span className={styles.avatar} aria-hidden="true">SM</span>
            <div>
              <strong>{syntheticCase.display_name}</strong>
              <span>demonstration investigation</span>
            </div>
          </div>
          <dl className={styles.metrics}>
            <div><dt>Sources</dt><dd>{sourceCount}</dd></div>
            <div><dt>Observations</dt><dd>{syntheticCase.observations.length}</dd></div>
            <div><dt>Conflicts</dt><dd>{conflictCount}</dd></div>
            <div><dt>Candidates</dt><dd>{syntheticCase.account_candidates.length}</dd></div>
          </dl>
          <div className={styles.evidencePath} aria-label="Evidence path preview">
            <span>clue</span><i />
            <span>source</span><i />
            <span>observation</span><i />
            <span>human review</span>
          </div>
          <div className={styles.caseRows}>
            {snapshotRows.map((observation) => (
              <div key={observation.id}>
                <span>{observation.provenance.source_name}</span>
                <strong className={observation.freshness === "stale" ? styles.warn : styles.good}>
                  {observation.freshness}
                </strong>
              </div>
            ))}
          </div>
          <Link className={styles.caseLink} href="/demo">Open the evidence record →</Link>
        </aside>
      </section>

      <section className={styles.boundary} aria-label="Public demo boundary">
        <div>
          <span className={styles.boundaryLabel}>Public observer</span>
          <strong>Synthetic evidence, real product semantics.</strong>
        </div>
        <p>
          Visitors can inspect source states, provenance, contradictions and correlation behavior.
          They cannot submit identifiers, execute providers, mutate retained cases or access private authority.
        </p>
      </section>

      <section className={styles.method} id="method">
        <div className={styles.methodIntro}>
          <p className={styles.kicker}>The casebook method</p>
          <h2>A research trail that survives scrutiny.</h2>
          <p>
            The useful outcome is an inspectable case, not a single score. Each step keeps enough
            context for another analyst to understand how the conclusion was reached—or why it was withheld.
          </p>
        </div>
        <ol className={styles.capabilityList}>
          {capabilities.map(([label, title, description], index) => (
            <li className={styles.capabilityRow} key={label}>
              <span className={styles.stepNumber}>{String(index + 1).padStart(2, "0")}</span>
              <div>
                <small>{label}</small>
                <h3>{title}</h3>
              </div>
              <p>{description}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className={styles.provenance}>
        <div className={styles.provenanceCopy}>
          <p className={styles.kicker}>Why provenance matters</p>
          <h2>A finding is only as defensible as its path back to the source.</h2>
          <p>
            PersonaLattice keeps source-native locators, retrieval timing, freshness and source state beside
            the observation. Failed or unavailable sources stay visible as coverage limits; they do not become evidence.
          </p>
        </div>
        <div className={styles.provenanceCard} aria-label="Synthetic provenance example">
          <span className={styles.marginNote}>synthetic example</span>
          <div>
            <small>Observation</small>
            <strong>{snapshotRows[0]?.summary ?? "Public observation"}</strong>
          </div>
          <div>
            <small>Source</small>
            <strong>{snapshotRows[0]?.provenance.source_name ?? "Synthetic source"}</strong>
          </div>
          <div>
            <small>Locator</small>
            <code>{snapshotRows[0]?.provenance.source_locator ?? "synthetic://fixture"}</code>
          </div>
          <div className={styles.provenanceDecision}>
            <small>Analyst boundary</small>
            <strong>Evidence informs the decision; it does not impersonate one.</strong>
          </div>
        </div>
      </section>

      <footer className={styles.footer}>
        <span>PersonaLattice · evidence casebook</span>
        <div>
          <Link href="/demo">Synthetic case</Link>
          <Link href="/admin">Private operator</Link>
        </div>
      </footer>
    </main>
  );
}
