"use client";

import { FormEvent, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type ResearchKind = "username" | "phone" | "email" | "url";

type QuickReport = {
  kind: ResearchKind;
  normalized_value: string;
  observations: Array<{
    source: string;
    source_locator: string;
    summary: string;
    details: Record<string, unknown>;
  }>;
  warnings: string[];
};

export function QuickResearch() {
  const [kind, setKind] = useState<ResearchKind>("username");
  const [value, setValue] = useState("");
  const [report, setReport] = useState<QuickReport | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setReport(null);
    setBusy(true);
    try {
      const response = await fetch(`${API_URL}/v1/research/quick`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind,
          value,
          purpose: "public_source_research",
          consent_acknowledged: false,
        }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(
          typeof body.detail === "string" ? body.detail : "Research request failed.",
        );
      }
      setReport(body as QuickReport);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Research request failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <div className="panelHeader">
        <div><span className="index">02</span><h2>Quick research</h2></div>
        <span className="count">admin only</span>
      </div>
      <form className="quickResearchForm" onSubmit={submit}>
        <div className="twoColumn">
          <label>
            Identifier type
            <select value={kind} onChange={(event) => setKind(event.target.value as ResearchKind)}>
              <option value="username">Username / handle</option>
              <option value="phone">Phone number</option>
              <option value="email">Email address</option>
              <option value="url">Public profile URL</option>
            </select>
          </label>
          <label>
            Value
            <input
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder={kind === "username" ? "@handle" : "Identifier to research"}
              required
            />
          </label>
        </div>
        <button type="submit" disabled={busy || !value.trim()}>
          {busy ? "Researching public sources…" : "Run quick research"}
        </button>
      </form>

      {error && <p className="error quickResult">{error}</p>}
      {report && (
        <div className="quickResult">
          <div className="caseId">{report.kind.toUpperCase()} · {report.normalized_value}</div>
          {report.warnings.map((warning) => <p className="muted" key={warning}>{warning}</p>)}
          <div className="providerList">
            {report.observations.map((observation, index) => (
              <article className="researchObservation" key={`${observation.source_locator}-${index}`}>
                <div className="provider">
                  <div>
                    <strong>{observation.source}</strong>
                    <span>{observation.summary}</span>
                    <span>{observation.source_locator}</span>
                  </div>
                </div>
                <pre>{JSON.stringify(observation.details, null, 2)}</pre>
              </article>
            ))}
          </div>
          <p className="muted">
            Public-account matches and metadata are evidence candidates, not automatic identity claims.
          </p>
        </div>
      )}
    </section>
  );
}
