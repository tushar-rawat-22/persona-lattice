import Link from "next/link";

import styles from "./public.module.css";

const capabilities = [
  ["01", "Identity clues", "Normalize phones, emails, usernames, domains, public URLs and reviewed files without pretending every clue belongs to one person."],
  ["02", "Source coverage", "Show which public sources ran, which were unavailable, and which exact checks were not applicable instead of silently dropping gaps."],
  ["03", "Evidence trail", "Keep the source locator, retrieval time, freshness and research pivot that produced each retained observation."],
  ["04", "Contradictions", "Preserve stale evidence and hard conflicts so positive signals cannot bury an important mismatch."],
  ["05", "Correlation", "Use deterministic evidence-strength factors for triage. The score is never presented as an identity probability."],
  ["06", "Case review", "Open retained investigations, inspect source state and provenance, and delete cases through the authenticated operator workflow."],
] as const;

export default function Home() {
  return (
    <main className={styles.shell}>
      <header className={styles.topbar}>
        <Link className={styles.brand} href="/" aria-label="PersonaLattice home">
          <span className={styles.brandMark}>PL</span>
          <span>PersonaLattice</span>
        </Link>
        <nav className={styles.nav} aria-label="Public navigation">
          <Link className={styles.navLink} href="#capabilities">Capabilities</Link>
          <Link className={styles.navLink} href="/demo">Read-only product demo</Link>
          <Link className={styles.adminLink} href="/admin">Private admin</Link>
        </nav>
      </header>

      <section className={styles.hero}>
        <div className={styles.heroCopy}>
          <p className={styles.kicker}>EVIDENCE-FIRST PUBLIC-SOURCE RESEARCH</p>
          <h1>See what the evidence says. Keep what it does not.</h1>
          <p className={styles.lead}>
            PersonaLattice turns scattered public clues into a structured investigation record with
            source state, provenance, freshness, contradictions and bounded correlation visible in
            one workspace.
          </p>
          <div className={styles.heroActions}>
            <Link className={styles.primaryLink} href="/demo">Open the evidence workspace</Link>
            <span className={styles.boundaryText}>Synthetic case only · No research runs from this page</span>
          </div>
        </div>

        <aside className={styles.caseBrief} aria-label="Synthetic case snapshot">
          <div className={styles.caseBriefHead}>
            <span className={styles.kicker}>READ-ONLY PRODUCT DEMO</span>
            <span className={styles.caseBriefState}>complete</span>
          </div>
          <div className={styles.caseIdentity}>
            <span className={styles.avatar} aria-hidden="true">AR</span>
            <div>
              <strong>Alex Rowan</strong>
              <span>synthetic investigation fixture</span>
            </div>
          </div>
          <dl className={styles.metrics}>
            <div><dt>Sources</dt><dd>8</dd></div>
            <div><dt>Observations</dt><dd>11</dd></div>
            <div><dt>Conflicts</dt><dd>1</dd></div>
            <div><dt>Candidates</dt><dd>3</dd></div>
          </dl>
          <div className={styles.caseRows}>
            <div><span>github_public_api</span><strong className={styles.good}>matched</strong></div>
            <div><span>public DNS</span><strong className={styles.good}>observed</strong></div>
            <div><span>stale profile claim</span><strong className={styles.warn}>conflict retained</strong></div>
          </div>
          <Link className={styles.caseLink} href="/demo">Inspect the full synthetic case →</Link>
        </aside>
      </section>

      <section className={styles.demoStrip} aria-label="Public demo boundary">
        <div>
          <span className={styles.kicker}>PUBLIC ACCESS</span>
          <strong>Visitors can inspect the product, not operate it.</strong>
        </div>
        <p>
          The public demo contains fixed synthetic evidence. It cannot submit identifiers, upload
          files, execute providers, change cases or access protected research data.
        </p>
      </section>

      <section className={styles.capabilities} id="capabilities">
        <div className={styles.capabilityIntro}>
          <p className={styles.kicker}>WHAT THE OPERATOR WORKSPACE DOES</p>
          <h2>A background-research workflow built around inspectable evidence.</h2>
          <p>
            The useful part is not a giant confidence number. It is knowing what was checked, what
            came back, where it came from, and which assumptions still need a human decision.
          </p>
        </div>
        <div className={styles.capabilityList}>
          {capabilities.map(([index, title, description]) => (
            <article className={styles.capabilityRow} key={index}>
              <span>{index}</span>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.architecture}>
        <div>
          <p className={styles.kicker}>PRODUCT BOUNDARY</p>
          <h2>Research is private. Demonstration is public.</h2>
        </div>
        <div className={styles.architectureFlow} aria-label="PersonaLattice evidence flow">
          <span>clue intake</span><i>→</i><span>source policy</span><i>→</i><span>public evidence</span><i>→</i><span>provenance graph</span><i>→</i><span>case review</span>
        </div>
        <p>
          Real-person intake and retained cases remain behind the admin session and CSRF boundary.
          Public visitors get the same information hierarchy through synthetic fixtures without the
          authority to run a background check themselves.
        </p>
      </section>

      <footer className={styles.footer}>
        <span>PersonaLattice · evidence intelligence</span>
        <div>
          <Link href="/demo">Product demo</Link>
          <Link href="/admin">Admin login</Link>
        </div>
      </footer>
    </main>
  );
}
