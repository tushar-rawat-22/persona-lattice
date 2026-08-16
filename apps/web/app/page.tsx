export default function Home() {
  return (
    <main className="shell publicShell">
      <header className="hero">
        <div>
          <p className="eyebrow">PERSONALATTICE / PUBLIC PREVIEW</p>
          <h1>Evidence intelligence without false certainty.</h1>
          <p className="lede">
            PersonaLattice structures public-source and authorized evidence into a defensible
            investigation record: identifiers, provenance, freshness, contradictions and bounded
            correlation stay visible instead of collapsing into a black-box identity score.
          </p>
        </div>
        <div className="publicNav">
          <a className="textLink" href="/dashboard">Synthetic evidence demo</a>
          <a className="textLink subtle" href="/admin">Operator access</a>
        </div>
      </header>

      <section className="publicGrid">
        <article className="panel publicPreviewCard">
          <div className="panelHeader">
            <div><span className="index">01</span><h2>Evidence workspace</h2></div>
            <span className="count">synthetic preview</span>
          </div>
          <div className="blurredPreview" aria-hidden="true">
            <div className="previewLine wide" />
            <div className="previewLine" />
            <div className="previewRow">
              <div className="previewBlock"><strong>Identifiers</strong><span>email · phone · handle</span></div>
              <div className="previewBlock"><strong>Sources</strong><span>public profiles · documents</span></div>
            </div>
            <div className="previewRow">
              <div className="previewBlock"><strong>Contradictions</strong><span>visible and unresolved</span></div>
              <div className="previewBlock"><strong>Correlation</strong><span>evidence triage, not probability</span></div>
            </div>
          </div>
          <div className="previewLock">
            <strong>Admin credentials required</strong>
            <span>Real intake and stored case data are never sent to an unauthenticated browser.</span>
          </div>
        </article>

        <aside className="sideStack">
          <section className="panel">
            <p className="eyebrow">PROVENANCE FIRST</p>
            <h2>Every conclusion keeps its source trail.</h2>
            <p className="muted">
              Observations, factual claims and correlation results remain separate so an analyst
              can see what was actually observed, what was asserted and what remains unresolved.
            </p>
          </section>
          <section className="panel">
            <p className="eyebrow">FAIL CLOSED</p>
            <h2>Uncertainty remains visible.</h2>
            <p className="muted">
              Stale evidence, contradictions and insufficient-source cases do not disappear behind
              a confidence percentage.
            </p>
          </section>
          <section className="panel boundary">
            <p className="eyebrow">PUBLIC BOUNDARY</p>
            <p>
              This surface is demo-only. It does not accept real-person research jobs or expose
              protected case data.
            </p>
          </section>
        </aside>
      </section>
    </main>
  );
}
