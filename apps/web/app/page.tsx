import Link from "next/link";

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
    <main className="shell publicShell publicProduct">
      <header className="publicTopbar">
        <Link className="publicBrand" href="/" aria-label="PersonaLattice home">
          <span className="brandMark">PL</span>
          <span>PersonaLattice</span>
        </Link>
        <nav className="publicNav" aria-label="Public navigation">
          <Link className="textLink" href="#capabilities">Capabilities</Link>
          <Link className="textLink" href="/dashboard">Read-only product demo</Link>
          <Link className="adminLoginButton" href="/admin">Private admin</Link>
        </nav>
      </header>

      <section className="publicHero">
        <div className="publicHeroCopy">
          <p className="eyebrow">EVIDENCE-FIRST PUBLIC-SOURCE RESEARCH</p>
          <h1>See what the evidence says. Keep what it does not.</h1>
          <p className="publicLead">
            PersonaLattice turns scattered public clues into a structured investigation record with
            source state, provenance, freshness, contradictions and bounded correlation visible in
            one workspace.
          </p>
          <div className="publicHeroActions">
            <Link className="adminLoginButton" href="/dashboard">Open the evidence workspace</Link>
            <span className="publicBoundaryText">Synthetic case only · No research runs from this page</span>
          </div>
        </div>

        <aside className="publicCaseBrief" aria-label="Synthetic case snapshot">
          <div className="caseBriefHead">
            <span className="eyebrow">READ-ONLY PRODUCT DEMO</span>
            <span className="caseBriefState">complete</span>
          </div>
          <div className="caseBriefIdentity">
            <span className="caseBriefAvatar" aria-hidden="true">AR</span>
            <div>
              <strong>Alex Rowan</strong>
              <span>synthetic investigation fixture</span>
            </div>
          </div>
          <dl className="caseBriefMetrics">
            <div><dt>Sources</dt><dd>8</dd></div>
            <div><dt>Observations</dt><dd>11</dd></div>
            <div><dt>Conflicts</dt><dd>1</dd></div>
            <div><dt>Candidates</dt><dd>3</dd></div>
          </dl>
          <div className="caseBriefRows">
            <div><span>github_public_api</span><strong className="stateGood">matched</strong></div>
            <div><span>public DNS</span><strong className="stateGood">observed</strong></div>
            <div><span>stale profile claim</span><strong className="stateWarn">conflict retained</strong></div>
          </div>
          <Link className="caseBriefLink" href="/dashboard">Inspect the full synthetic case →</Link>
        </aside>
      </section>

      <section className="publicDemoStrip" aria-label="Public demo boundary">
        <div>
          <span className="eyebrow">PUBLIC ACCESS</span>
          <strong>Visitors can inspect the product, not operate it.</strong>
        </div>
        <p>
          The public demo contains fixed synthetic evidence. It cannot submit identifiers, upload
          files, execute providers, change cases or access protected research data.
        </p>
      </section>

      <section className="capabilitySection" id="capabilities">
        <div className="capabilityIntro">
          <p className="eyebrow">WHAT THE OPERATOR WORKSPACE DOES</p>
          <h2>A background-research workflow built around inspectable evidence.</h2>
          <p>
            The useful part is not a giant confidence number. It is knowing what was checked, what
            came back, where it came from, and which assumptions still need a human decision.
          </p>
        </div>
        <div className="capabilityList">
          {capabilities.map(([index, title, description]) => (
            <article className="capabilityRow" key={index}>
              <span className="index">{index}</span>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="publicArchitecture">
        <div>
          <p className="eyebrow">PRODUCT BOUNDARY</p>
          <h2>Research is private. Demonstration is public.</h2>
        </div>
        <div className="architectureFlow" aria-label="PersonaLattice evidence flow">
          <span>clue intake</span><i>→</i><span>source policy</span><i>→</i><span>public evidence</span><i>→</i><span>provenance graph</span><i>→</i><span>case review</span>
        </div>
        <p>
          Real-person intake and retained cases remain behind the admin session and CSRF boundary.
          Public visitors get the same information hierarchy through synthetic fixtures without the
          authority to run a background check themselves.
        </p>
      </section>

      <footer className="publicFooter">
        <span>PersonaLattice · evidence intelligence</span>
        <div>
          <Link href="/dashboard">Product demo</Link>
          <Link href="/admin">Admin login</Link>
        </div>
      </footer>
    </main>
  );
}
