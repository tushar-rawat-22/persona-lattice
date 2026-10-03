import Link from "next/link";

import { InvestigationDesk } from "./investigation-desk";
import styles from "./public.module.css";

export default function Home() {
  return (
    <main className={styles.shell}>
      <header className={styles.topbar}>
        <Link className={styles.brand} href="/" aria-label="PersonaLattice home">
          <span className={styles.brandMark}>PL</span>
          <span>
            <strong>PersonaLattice</strong>
            <small>investigation desk</small>
          </span>
        </Link>
        <nav className={styles.nav} aria-label="Public navigation">
          <Link className={styles.navLink} href="#how-it-works">How it works</Link>
          <Link className={styles.navLink} href="/demo">Synthetic investigation</Link>
          <Link className={styles.operatorLink} href="/operator-access">Operator access</Link>
        </nav>
      </header>

      <section className={styles.intro}>
        <div>
          <p className={styles.kicker}>Public synthetic investigation · read only</p>
          <h1>Trace a clue to evidence, provenance, and the questions left open.</h1>
        </div>
        <div className={styles.introAside}>
          <p>
            PersonaLattice keeps public-source observations, contradictions, coverage gaps, and source context in one inspectable path. It refuses to turn correlation into an identity verdict.
          </p>
          <Link className={styles.primaryLink} href="/demo">Open the full synthetic investigation <span aria-hidden="true">→</span></Link>
        </div>
      </section>

      <InvestigationDesk />

      <section className={styles.method} id="how-it-works" aria-label="Investigation hierarchy">
        <div>
          <span>01</span>
          <strong>Start with a bounded clue</strong>
          <p>A username, email, phone, domain, public URL, or reviewed file becomes a lead—not an identity assumption.</p>
        </div>
        <div>
          <span>02</span>
          <strong>Keep evidence attached to provenance</strong>
          <p>Source locator, retrieval time, freshness, and execution state stay visible beside every retained observation.</p>
        </div>
        <div>
          <span>03</span>
          <strong>Expose conflict and unknowns</strong>
          <p>Contradictions, stale signals, source failure, and missing coverage remain visible before a person decides.</p>
        </div>
      </section>

      <section className={styles.boundary} aria-label="Public and private authority boundary">
        <div>
          <span>Public observer</span>
          <strong>Synthetic evidence. Real product semantics. No research authority.</strong>
        </div>
        <p>
          This page cannot submit identifiers, call providers, mutate retained cases, or access private investigations. The authenticated operator workspace is separately controlled.
        </p>
      </section>

      <footer className={styles.footer}>
        <span>PersonaLattice · evidence investigation workspace</span>
        <div>
          <Link href="/demo">Synthetic investigation</Link>
          <Link href="/operator-access">Operator boundary</Link>
        </div>
      </footer>
    </main>
  );
}
