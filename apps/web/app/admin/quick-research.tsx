"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

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

type StoredCase = {
  id: string;
  created_at: string;
  expires_at: string;
  seed_kind: ResearchKind;
  seed_value: string;
  report: QuickReport;
};

async function request(path: string, init?: RequestInit) {
  return fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
  });
}

export function QuickResearch() {
  const [kind, setKind] = useState<ResearchKind>("username");
  const [value, setValue] = useState("");
  const [activeCase, setActiveCase] = useState<StoredCase | null>(null);
  const [recentCases, setRecentCases] = useState<StoredCase[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const refreshCases = useCallback(async () => {
    const response = await request("/v1/cases?limit=8");
    if (!response.ok) return;
    setRecentCases((await response.json()) as StoredCase[]);
  }, []);

  useEffect(() => {
    let active = true;
    request("/v1/cases?limit=8")
      .then(async (response) => {
        if (!response.ok) return null;
        return (await response.json()) as StoredCase[];
      })
      .then((items) => {
        if (active && items) setRecentCases(items);
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setActiveCase(null);
    setBusy(true);
    try {
      const response = await request("/v1/cases/run", {
        method: "POST",
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
      const stored = body as StoredCase;
      setActiveCase(stored);
      setValue(stored.seed_value);
      await refreshCases();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Research request failed.");
    } finally {
      setBusy(false);
    }
  }

  async function openCase(caseId: string) {
    setError("");
    const response = await request(`/v1/cases/${caseId}`);
    if (!response.ok) {
      setError("Stored case could not be loaded.");
      return;
    }
    setActiveCase((await response.json()) as StoredCase);
  }

  async function deleteCase(caseId: string) {
    const response = await request(`/v1/cases/${caseId}`, { method: "DELETE" });
    if (!response.ok && response.status !== 404) {
      setError("Stored case could not be deleted.");
      return;
    }
    if (activeCase?.id === caseId) setActiveCase(null);
    await refreshCases();
  }

  const report = activeCase?.report ?? null;

  return (
    <section className="panel">
      <div className="panelHeader">
        <div><span className="index">02</span><h2>Live research</h2></div>
        <span className="count">private cases</span>
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
          {busy ? "Researching public sources…" : "Run and save research case"}
        </button>
      </form>

      {error && <p className="error quickResult">{error}</p>}
      {activeCase && report && (
        <div className="quickResult">
          <div className="caseId">CASE {activeCase.id.slice(0, 8)} · {report.kind.toUpperCase()} · {report.normalized_value}</div>
          <p className="muted">Stored until {new Date(activeCase.expires_at).toLocaleString()} unless deleted earlier.</p>
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

      <div className="recentCases">
        <div className="panelHeader compactPanelHeader">
          <div><span className="index">RECENT</span><h2>Stored cases</h2></div>
          <button className="secondaryButton" type="button" onClick={() => refreshCases()}>Refresh</button>
        </div>
        {recentCases.length === 0 ? (
          <p className="muted">No retained research cases yet.</p>
        ) : (
          <div className="providerList">
            {recentCases.map((item) => (
              <div className="caseRow" key={item.id}>
                <button className="caseOpen" type="button" onClick={() => openCase(item.id)}>
                  <strong>{item.seed_kind}</strong>
                  <span>{item.seed_value}</span>
                  <small>{item.id.slice(0, 8)}</small>
                </button>
                <button className="dangerButton" type="button" onClick={() => deleteCase(item.id)}>Delete</button>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
