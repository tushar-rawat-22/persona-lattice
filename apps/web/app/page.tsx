"use client";

import { FormEvent, useMemo, useState } from "react";

type ProviderPlan = {
  provider: string;
  capability: string;
  status: string;
  contact_risk: string;
  reason: string;
};

type Preview = {
  case_id: string;
  status: string;
  normalized: Record<string, unknown>;
  provider_plan: ProviderPlan[];
  warnings: string[];
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

function splitValues(value: string) {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function Home() {
  const [purpose, setPurpose] = useState("self_audit");
  const [fullName, setFullName] = useState("");
  const [phones, setPhones] = useState("");
  const [emails, setEmails] = useState("");
  const [usernames, setUsernames] = useState("");
  const [urls, setUrls] = useState("");
  const [organizations, setOrganizations] = useState("");
  const [notes, setNotes] = useState("");
  const [consent, setConsent] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [result, setResult] = useState<Preview | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const signalCount = useMemo(
    () =>
      [fullName, phones, emails, usernames, urls, organizations, notes].filter((value) =>
        value.trim(),
      ).length + files.length,
    [fullName, phones, emails, usernames, urls, organizations, notes, files],
  );

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!consent && purpose !== "public_source_research") {
      setError("Acknowledge the consent or authorization requirement first.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/v1/intake/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          purpose,
          consent_acknowledged: consent,
          full_name: fullName || null,
          phones: splitValues(phones),
          emails: splitValues(emails),
          usernames: splitValues(usernames),
          urls: splitValues(urls),
          organizations: splitValues(organizations),
          notes: notes || null,
          files: files.map((file) => ({
            name: file.name,
            media_type: file.type || null,
            size_bytes: file.size,
          })),
        }),
      });

      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail ?? "The intake request was rejected.");
      }
      setResult(body);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not reach the local API.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">PERSONALATTICE / M0</p>
          <h1>Build the case from evidence, not assumptions.</h1>
          <p className="lede">
            Bring the identifiers you already have. PersonaLattice normalizes the case,
            enforces source boundaries, and shows what would be checked before any provider runs.
          </p>
        </div>
        <div className="status"><span className="dot" /> local research shell</div>
      </header>

      <section className="workspace">
        <form className="panel intake" onSubmit={submit}>
          <div className="panelHeader">
            <div><span className="index">01</span><h2>Case intake</h2></div>
            <span className="count">{signalCount} signals</span>
          </div>

          <label>
            Purpose
            <select value={purpose} onChange={(event) => setPurpose(event.target.value)}>
              <option value="self_audit">Self audit</option>
              <option value="consented_due_diligence">Consented due diligence</option>
              <option value="public_source_research">Public-source research</option>
              <option value="professional_verification">Professional verification</option>
              <option value="employment_decision">Employment decision — blocked in M0</option>
            </select>
          </label>

          <div className="twoColumn">
            <label>Name<input value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Known or claimed name" /></label>
            <label>Phone<textarea value={phones} onChange={(e) => setPhones(e.target.value)} placeholder={"+91...\n+1..."} rows={3} /></label>
          </div>

          <div className="twoColumn">
            <label>Email addresses<textarea value={emails} onChange={(e) => setEmails(e.target.value)} placeholder="one@example.com" rows={3} /></label>
            <label>Usernames<textarea value={usernames} onChange={(e) => setUsernames(e.target.value)} placeholder={"@handle\nanother_handle"} rows={3} /></label>
          </div>

          <label>URLs / profiles<textarea value={urls} onChange={(e) => setUrls(e.target.value)} placeholder="Public profile, portfolio or source URLs" rows={3} /></label>
          <label>Organizations<textarea value={organizations} onChange={(e) => setOrganizations(e.target.value)} placeholder="Employer, university, company or claimed affiliation" rows={2} /></label>
          <label>Notes / claims to cross-check<textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Paste the claims or context you want the system to verify." rows={5} /></label>

          <label className="dropzone">
            <strong>Attach files</strong>
            <span>M0 records file metadata only. Content extraction arrives in M2.</span>
            <input type="file" multiple onChange={(e) => setFiles(Array.from(e.target.files ?? []))} />
            {files.length > 0 && <small>{files.map((file) => file.name).join(" • ")}</small>}
          </label>

          <label className="check">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
            <span>I have the required consent or authorization for this purpose, or I am auditing myself.</span>
          </label>

          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={loading}>{loading ? "Planning research…" : "Build research plan"}</button>
        </form>

        <aside className="sideStack">
          <section className="panel">
            <div className="panelHeader"><div><span className="index">02</span><h2>Evidence model</h2></div></div>
            <div className="graph">
              <div className="node primary">Subject</div><div className="connector" />
              <div className="nodeRow"><div className="node">Identifiers</div><div className="node">Sources</div><div className="node">Claims</div></div>
            </div>
            <p className="muted">AI analysis will sit above this graph. It will not be allowed to create evidence.</p>
          </section>

          <section className="panel">
            <div className="panelHeader"><div><span className="index">03</span><h2>Research plan</h2></div></div>
            {!result ? (
              <p className="muted">Submit an intake to see normalization, provider policy and contact-risk decisions.</p>
            ) : (
              <>
                <div className="caseId">CASE {result.case_id.slice(0, 8)}</div>
                <pre>{JSON.stringify(result.normalized, null, 2)}</pre>
                <div className="providerList">
                  {result.provider_plan.map((provider) => (
                    <div className="provider" key={provider.provider}>
                      <div><strong>{provider.provider}</strong><span>{provider.capability}</span></div>
                      <div className="tags"><em>{provider.status}</em><em>{provider.contact_risk}</em></div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </section>

          <section className="panel boundary">
            <p className="eyebrow">BOUNDARY</p>
            <p>Private-account access, OTP or recovery probing, live-location tracking and hidden KYC data are not product features.</p>
          </section>
        </aside>
      </section>
    </main>
  );
}
