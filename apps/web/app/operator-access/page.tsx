import Link from "next/link";

import styles from "../public.module.css";

export default function OperatorAccessPage() {
  return (
    <main className={styles.shell}>
      <header className={styles.topbar}>
        <Link className={styles.brand} href="/" aria-label="PersonaLattice home">
          <span className={styles.brandMark}>PL</span>
          <span>PersonaLattice</span>
        </Link>
        <nav className={styles.nav} aria-label="Public navigation">
          <Link className={styles.navLink} href="/demo">Read-only product demo</Link>
          <Link className={styles.adminLink} href="/">Product overview</Link>
        </nav>
      </header>

      <section className={styles.hero}>
        <div className={styles.heroCopy}>
          <p className={styles.kicker}>OPERATOR ACCESS</p>
          <h1>The public demo does not expose research authority.</h1>
          <p className={styles.lead}>
            PersonaLattice keeps real-person intake, provider execution, retained cases and mutation
            controls behind a separately hosted authenticated operator boundary. Public visitors can
            inspect the synthetic evidence workspace without receiving admin credentials or API access.
          </p>
          <div className={styles.heroActions}>
            <Link className={styles.primaryLink} href="/demo">Return to the evidence demo</Link>
            <span className={styles.boundaryText}>No admin session is available from this deployment.</span>
          </div>
        </div>

        <aside className={styles.caseBrief} aria-label="Public and private boundary">
          <div className={styles.caseBriefHead}>
            <span className={styles.kicker}>BOUNDARY</span>
            <span className={styles.caseBriefState}>read only</span>
          </div>
          <div className={styles.caseRows}>
            <div><span>synthetic investigation</span><strong className={styles.good}>public</strong></div>
            <div><span>provenance + conflicts</span><strong className={styles.good}>public</strong></div>
            <div><span>provider execution</span><strong className={styles.warn}>private</strong></div>
            <div><span>retained case mutations</span><strong className={styles.warn}>private</strong></div>
          </div>
        </aside>
      </section>

      <footer className={styles.footer}>
        <span>PersonaLattice · public demonstration boundary</span>
        <div>
          <Link href="/">Product overview</Link>
          <Link href="/demo">Product demo</Link>
        </div>
      </footer>
    </main>
  );
}
