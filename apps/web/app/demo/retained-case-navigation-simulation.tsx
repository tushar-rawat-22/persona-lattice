"use client";

import { useMemo, useState } from "react";

import styles from "./retained-case-navigation-simulation.module.css";

type CaseKind = "person" | "claim" | "document";

type SyntheticRetainedCase = {
  id: string;
  label: string;
  kind: CaseKind;
  updated: string;
  state: string;
  clue: string;
};

const retainedCases: SyntheticRetainedCase[] = [
  {
    id: "case-alex-rowan",
    label: "Alex Rowan",
    kind: "person",
    updated: "2026-08-30 18:42 UTC",
    state: "active · evidence retained",
    clue: "handle: alex-rowan",
  },
  {
    id: "case-domain-claim",
    label: "Northstar domain claim",
    kind: "claim",
    updated: "2026-08-29 11:05 UTC",
    state: "open questions",
    clue: "domain: northstar.example",
  },
  {
    id: "case-reviewed-brief",
    label: "Reviewed intake brief",
    kind: "document",
    updated: "2026-08-28 15:18 UTC",
    state: "reviewed clues admitted",
    clue: "document fixture: synthetic-intake-brief.pdf",
  },
] as const;

export function RetainedCaseNavigationSimulation() {
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<"all" | CaseKind>("all");
  const [activeCaseId, setActiveCaseId] = useState(retainedCases[0].id);

  const visibleCases = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return retainedCases.filter((item) => {
      const matchesKind = kind === "all" || item.kind === kind;
      const matchesQuery =
        !normalized ||
        item.label.toLowerCase().includes(normalized) ||
        item.clue.toLowerCase().includes(normalized);
      return matchesKind && matchesQuery;
    });
  }, [kind, query]);

  const activeCase = retainedCases.find((item) => item.id === activeCaseId) ?? retainedCases[0];
  const activeHidden = !visibleCases.some((item) => item.id === activeCase.id);

  function showActiveCase() {
    setQuery("");
    setKind("all");
  }

  return (
    <section className={styles.panel} aria-labelledby="retained-case-demo-title">
      <div className={styles.heading}>
        <div>
          <p>RETAINED CASES / SAFE SIMULATION</p>
          <h2 id="retained-case-demo-title">Search, filter and switch synthetic cases</h2>
        </div>
        <span>browser-memory fixture only</span>
      </div>

      <p className={styles.note}>
        This mirrors private retained-case navigation without listing private records, opening retained storage or making a network request.
      </p>

      <div className={styles.controls}>
        <label>
          <span>Search cases</span>
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="name or clue"
          />
        </label>
        <label>
          <span>Case kind</span>
          <select value={kind} onChange={(event) => setKind(event.target.value as "all" | CaseKind)}>
            <option value="all">All kinds</option>
            <option value="person">Person</option>
            <option value="claim">Claim</option>
            <option value="document">Document</option>
          </select>
        </label>
      </div>

      {activeHidden && (
        <div className={styles.hiddenActive} role="status">
          <div>
            <strong>Active synthetic case is hidden by filters.</strong>
            <span>{activeCase.label} remains the current workspace context.</span>
          </div>
          <button type="button" onClick={showActiveCase}>Show active case</button>
        </div>
      )}

      <div className={styles.caseList} aria-label="Synthetic retained case list">
        {visibleCases.length === 0 ? (
          <p className={styles.empty}>No synthetic cases match these filters. This is an empty filter result, not a failed case index.</p>
        ) : (
          visibleCases.map((item) => {
            const active = item.id === activeCase.id;
            return (
              <button
                className={active ? styles.activeCase : styles.caseRow}
                type="button"
                key={item.id}
                onClick={() => setActiveCaseId(item.id)}
                aria-pressed={active}
              >
                <span>
                  <strong>{item.label}</strong>
                  <small>{item.clue}</small>
                </span>
                <span>
                  <em>{item.kind}</em>
                  <small>{item.updated}</small>
                </span>
              </button>
            );
          })
        )}
      </div>

      <div className={styles.activeSummary}>
        <span>Current workspace context</span>
        <strong>{activeCase.label}</strong>
        <p>{activeCase.state} · {activeCase.kind} · {activeCase.updated}</p>
      </div>

      <div className={styles.boundary}>
        <button type="button" disabled>Delete retained case</button>
        <span>Destructive case mutation is intentionally disabled in the public observer.</span>
      </div>
    </section>
  );
}
