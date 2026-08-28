"use client";

import { useMemo, useState } from "react";

export type CaseNavigationKind = "username" | "phone" | "email" | "url" | "domain";

export type CaseNavigationItem = {
  id: string;
  created_at: string;
  expires_at: string;
  seed_kind: CaseNavigationKind;
  seed_value: string;
};

type SortOrder = "newest" | "oldest";
type KindFilter = "all" | CaseNavigationKind;

type CaseNavigationProps = {
  cases: CaseNavigationItem[];
  activeCaseId?: string;
  hasMore: boolean;
  loadingMore: boolean;
  onOpenCase: (caseId: string) => void;
  onLoadMore: () => void;
  onRefresh: () => void;
  onDeleteCase: (caseId: string) => void;
  onDeleteAll: () => void;
};

const KIND_LABELS: Record<CaseNavigationKind, string> = {
  username: "Username",
  phone: "Phone",
  email: "Email",
  url: "URL",
  domain: "Domain",
};

function normalizedSearch(value: string): string {
  return value.trim().toLocaleLowerCase();
}

export function filterAndSortLoadedCases(
  cases: CaseNavigationItem[],
  query: string,
  kind: KindFilter,
  sortOrder: SortOrder,
): CaseNavigationItem[] {
  const needle = normalizedSearch(query);
  return cases
    .filter((item) => {
      if (kind !== "all" && item.seed_kind !== kind) return false;
      if (!needle) return true;
      return [item.seed_kind, item.seed_value, item.id]
        .some((candidate) => candidate.toLocaleLowerCase().includes(needle));
    })
    .sort((left, right) => {
      const createdDelta = Date.parse(left.created_at) - Date.parse(right.created_at);
      if (createdDelta !== 0) return sortOrder === "newest" ? -createdDelta : createdDelta;
      return left.id.localeCompare(right.id);
    });
}

export function CaseNavigation({
  cases,
  activeCaseId,
  hasMore,
  loadingMore,
  onOpenCase,
  onLoadMore,
  onRefresh,
  onDeleteCase,
  onDeleteAll,
}: CaseNavigationProps) {
  const [query, setQuery] = useState("");
  const [kindFilter, setKindFilter] = useState<KindFilter>("all");
  const [sortOrder, setSortOrder] = useState<SortOrder>("newest");
  const [pendingDeleteCaseId, setPendingDeleteCaseId] = useState<string | null>(null);

  const visibleCases = useMemo(
    () => filterAndSortLoadedCases(cases, query, kindFilter, sortOrder),
    [cases, query, kindFilter, sortOrder],
  );

  function confirmDeleteCase(caseId: string) {
    onDeleteCase(caseId);
    setPendingDeleteCaseId(null);
  }

  return (
    <div className="recentCases" aria-label="Stored case navigation">
      <div className="panelHeader compactPanelHeader">
        <div>
          <span className="index">RECENT</span>
          <h2>Stored cases</h2>
          <small className="muted">Search and sort the cases already loaded in this session.</small>
        </div>
        <button className="secondaryButton" type="button" onClick={onRefresh}>Refresh</button>
      </div>

      {cases.length === 0 ? (
        <p className="muted">No retained research cases yet.</p>
      ) : (
        <>
          <div className="caseNavigationControls">
            <label>
              Search loaded cases
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Identifier or case ID"
              />
            </label>
            <label>
              Filter by kind
              <select value={kindFilter} onChange={(event) => setKindFilter(event.target.value as KindFilter)}>
                <option value="all">All kinds</option>
                {Object.entries(KIND_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </label>
            <label>
              Sort loaded cases
              <select value={sortOrder} onChange={(event) => setSortOrder(event.target.value as SortOrder)}>
                <option value="newest">Newest first</option>
                <option value="oldest">Oldest first</option>
              </select>
            </label>
          </div>

          {visibleCases.length === 0 ? (
            <p className="muted">No loaded cases match the current search and kind filter.</p>
          ) : (
            <div className="providerList">
              {visibleCases.map((item) => (
                <div className="caseRow" key={item.id}>
                  <button
                    className="caseOpen"
                    type="button"
                    onClick={() => onOpenCase(item.id)}
                    aria-current={activeCaseId === item.id ? "true" : undefined}
                  >
                    <strong>{KIND_LABELS[item.seed_kind]}</strong>
                    <span>{item.seed_value}</span>
                    <small>Created {new Date(item.created_at).toLocaleString()} · {item.id.slice(0, 8)}</small>
                  </button>
                  <details className="caseActions">
                    <summary>Actions</summary>
                    {pendingDeleteCaseId === item.id ? (
                      <div className="caseDeleteConfirmation" role="group" aria-label={`Confirm deletion of ${item.seed_value}`}>
                        <p className="muted" aria-live="polite">Delete this retained case? This cannot be undone.</p>
                        <div className="caseDeleteConfirmationActions">
                          <button className="dangerButton" type="button" onClick={() => confirmDeleteCase(item.id)}>
                            Confirm delete
                          </button>
                          <button className="secondaryButton" type="button" onClick={() => setPendingDeleteCaseId(null)}>
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button className="dangerButton" type="button" onClick={() => setPendingDeleteCaseId(item.id)}>
                        Delete this case
                      </button>
                    )}
                  </details>
                </div>
              ))}
            </div>
          )}

          <div className="caseNavigationFooter">
            {hasMore && (
              <button className="secondaryButton" type="button" onClick={onLoadMore} disabled={loadingMore}>
                {loadingMore ? "Loading older cases…" : "Load older cases"}
              </button>
            )}
            <details className="caseActions destructiveCaseActions">
              <summary>Retention actions</summary>
              <p className="muted">Destructive actions affect retained private cases and cannot be undone.</p>
              <button className="dangerButton" type="button" onClick={onDeleteAll}>
                Delete all retained cases
              </button>
            </details>
          </div>
        </>
      )}
    </div>
  );
}
