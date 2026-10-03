"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { syntheticCase } from "./dashboard/fixture";
import styles from "./public.module.css";
import { simulatedSourceRuns } from "./public-source-runs";

type EvidenceState = "support" | "conflict" | "unknown" | "retained";

function words(value: string) {
  return value.replaceAll("_", " ");
}

function sourceState(sourceRun: (typeof simulatedSourceRuns)[number]) {
  if (sourceRun.state === "not_found") {
    return { label: "attempted · no match", tone: styles.sourceNeutral };
  }
  if (sourceRun.state === "review_required") {
    return { label: "not attempted · review gated", tone: styles.sourceUnknown };
  }
  if (sourceRun.state === "executed") {
    return { label: `${sourceRun.observation_count} retained`, tone: styles.sourceSupport };
  }
  if (sourceRun.attempted) {
    return { label: "attempted · degraded", tone: styles.sourceConflict };
  }
  return { label: "not attempted · unavailable", tone: styles.sourceUnknown };
}

export function InvestigationDesk() {
  const evidenceItems = useMemo(() => {
    const supportingIds = new Set(
      syntheticCase.claims.flatMap((claim) =>
        claim.evidence_links
          .filter((link) => link.relation === "supports")
          .map((link) => link.observation_id),
      ),
    );
    const conflictIds = new Set(
      syntheticCase.account_candidates.flatMap((candidate) =>
        (candidate.correlation?.factors ?? [])
          .filter((factor) => factor.veto || factor.applied_weight < 0)
          .flatMap((factor) => factor.observation_ids),
      ),
    );
    const unknownIds = new Set(
      syntheticCase.account_candidates.flatMap((candidate) =>
        (candidate.correlation?.factors ?? [])
          .filter((factor) => factor.status !== "applied" || factor.applied_weight === 0)
          .flatMap((factor) => factor.observation_ids),
      ),
    );

    return syntheticCase.observations
      .filter((observation) => !observation.account_candidate)
      .map((observation) => {
        let state: EvidenceState = "retained";
        if (supportingIds.has(observation.id)) state = "support";
        if (unknownIds.has(observation.id)) state = "unknown";
        if (conflictIds.has(observation.id)) state = "conflict";
        return { observation, state };
      })
      .sort((left, right) => {
        const rank: Record<EvidenceState, number> = { support: 0, conflict: 1, unknown: 2, retained: 3 };
        return rank[left.state] - rank[right.state] || left.observation.id.localeCompare(right.observation.id);
      });
  }, []);

  const defaultItem = evidenceItems.find((item) => item.state === "support") ?? evidenceItems[0];
  const [selectedId, setSelectedId] = useState(defaultItem?.observation.id ?? "");
  const selected = evidenceItems.find((item) => item.observation.id === selectedId) ?? defaultItem;

  const inspectorCopy: Record<EvidenceState, string> = {
    support: "Supports a claim in this synthetic record. It does not prove that two accounts belong to the same person.",
    conflict: "Conflicts with the candidate relationship. Positive signals remain visible, but they cannot erase this retained veto.",
    unknown: "This stale signal remains inspectable for audit, but it is withheld from positive assessment.",
    retained: "This observation is retained with its source context. No identity conclusion is inferred from retention alone.",
  };

  return (
    <section className={styles.deskShell} aria-labelledby="desk-title">
      <aside className={styles.caseRail} aria-label="Case and clue rail">
        <div className={styles.paneHeading}>
          <span>01</span>
          <div>
            <small>Case & clues</small>
            <h2 id="desk-title">{syntheticCase.display_name}</h2>
          </div>
        </div>

        <div className={styles.railSection}>
          <span className={styles.sectionLabel}>Retained clues</span>
          <ul className={styles.clueList}>
            {syntheticCase.identifiers.map((identifier) => (
              <li key={identifier.id}>
                <span>{identifier.kind}</span>
                <strong>{identifier.value}</strong>
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.railSection}>
          <span className={styles.sectionLabel}>Source coverage</span>
          <ul className={styles.sourceRunList}>
            {simulatedSourceRuns.map((sourceRun) => {
              const state = sourceState(sourceRun);
              return (
                <li key={sourceRun.source_name}>
                  <span>{sourceRun.source_name}</span>
                  <strong className={state.tone}>{state.label}</strong>
                </li>
              );
            })}
          </ul>
          <p className={styles.railNote}>No-match, unavailable, and review-gated paths are coverage states—not evidence about identity.</p>
        </div>
      </aside>

      <section className={styles.evidenceCanvas} aria-label="Evidence path">
        <div className={styles.paneHeading}>
          <span>02</span>
          <div>
            <small>Evidence path</small>
            <h2>Inspect what changed the case</h2>
          </div>
        </div>
        <p className={styles.paneIntro}>Choose a retained observation. Its source, freshness, and effect stay connected in the inspector.</p>

        <div className={styles.pathGuide} aria-hidden="true">
          <span>clue</span><i />
          <span>evidence</span><i />
          <span>provenance</span><i />
          <span>decision</span>
        </div>

        <div className={styles.evidenceList}>
          {evidenceItems.map((item) => (
            <button
              type="button"
              key={item.observation.id}
              className={`${styles.deskEvidenceButton} ${styles[`evidence_${item.state}`]}`}
              aria-pressed={selectedId === item.observation.id}
              onClick={() => setSelectedId(item.observation.id)}
            >
              <span className={styles.evidenceMarker} aria-hidden="true" />
              <span>
                <small>{item.state === "support" ? "corroborating signal" : item.state === "conflict" ? "contradiction" : item.state === "unknown" ? "withheld signal" : "retained observation"}</small>
                <strong>{item.observation.summary}</strong>
                <em>{item.observation.provenance.source_name} · {words(item.observation.freshness)}</em>
              </span>
              <b aria-hidden="true">→</b>
            </button>
          ))}
        </div>

        <div className={styles.decisionStates}>
          <div className={styles.conflictState}>
            <span>Contradiction retained</span>
            <strong>Incompatible ownership blocks the positive path.</strong>
          </div>
          <div className={styles.unknownState}>
            <span>Unknown / coverage limit</span>
            <strong>Stale and unattempted paths prevent a complete conclusion.</strong>
          </div>
        </div>
      </section>

      <aside className={styles.deskInspector} aria-label="Provenance inspector" aria-live="polite">
        <div className={styles.paneHeading}>
          <span>03</span>
          <div>
            <small>Provenance inspector</small>
            <h2>Selected evidence</h2>
          </div>
        </div>

        {selected ? (
          <div className={styles.inspectorBody}>
            <div className={`${styles.inspectorState} ${styles[`evidence_${selected.state}`]}`}>
              <span>{selected.state === "support" ? "corroborating signal" : selected.state === "conflict" ? "contradiction" : selected.state === "unknown" ? "withheld / unknown" : "retained"}</span>
              <strong>{selected.observation.summary}</strong>
            </div>
            <dl className={styles.provenanceList}>
              <div><dt>Source</dt><dd>{selected.observation.provenance.source_name}</dd></div>
              <div><dt>Source type</dt><dd>{words(selected.observation.provenance.source_kind)}</dd></div>
              <div><dt>Retrieved</dt><dd>{new Date(selected.observation.retrieved_at).toISOString().replace("T", " · ").replace(".000Z", " UTC")}</dd></div>
              <div><dt>Freshness</dt><dd>{selected.observation.freshness}</dd></div>
              <div className={styles.locatorRow}><dt>Canonical locator</dt><dd><code>{selected.observation.provenance.source_locator}</code></dd></div>
            </dl>
            <div className={styles.decisionBoundary}>
              <span>Human decision required</span>
              <p>{inspectorCopy[selected.state]}</p>
            </div>
          </div>
        ) : null}

        <Link className={styles.inspectorLink} href="/demo">Open the full evidence record <span aria-hidden="true">→</span></Link>
      </aside>
    </section>
  );
}
