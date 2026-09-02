"use client";

import { useEffect, useMemo, useRef, useState } from "react";

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
  initialLoading?: boolean;
  initialLoadFailed?: boolean;
  loadingMore: boolean;
  remoteActionsDisabled?: boolean;
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

function isEditableShortcutTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return target.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName);
}

export function caseRetentionStatus(expiresAt: string, nowMs = Date.now()): "active" | "elapsed" | "unknown" {
  const expiresMs = Date.parse(expiresAt);
  if (!Number.isFinite(expiresMs)) return "unknown";
  return expiresMs <= nowMs ? "elapsed" : "active";
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
  initialLoading = false,
  initialLoadFailed = false,
  loadingMore,
  remoteActionsDisabled = false,
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
  const [pendingDeleteAll, setPendingDeleteAll] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const visibleCases = useMemo(
    () => filterAndSortLoadedCases(cases, query, kindFilter, sortOrder),
    [cases, query, kindFilter, sortOrder],
  );
  const activeCase = useMemo(
    () => activeCaseId ? cases.find((item) => item.id === activeCaseId) : undefined,
    [activeCaseId, cases],
  );
  const activeCaseIsHidden = Boolean(
    activeCaseId &&
    cases.some((item) => item.id === activeCaseId) &&
    !visibleCases.some((item) => item.id === activeCaseId),
  );

  useEffect(() => {
    function focusCaseSearch(event: KeyboardEvent) {
      if (event.key !== "/" || event.metaKey || event.ctrlKey || event.altKey) return;
      if (isEditableShortcutTarget(event.target)) return;
      if (!searchInputRef.current) return;
      event.preventDefault();
      searchInputRef.current.focus();
    }

    window.addEventListener("keydown", focusCaseSearch);
    return () => window.removeEventListener("keydown", focusCaseSearch);
  }, []);

  function clearCaseFilters() {
    setQuery("");
    setKindFilter("all");
  }

  function confirmDeleteCase(caseId: string) {
    if (initialLoading || remoteActionsDisabled) return;
    onDeleteCase(caseId);
    setPendingDeleteCaseId(null);
  }

  function confirmDeleteAll() {
    if (initialLoading || remoteActionsDisabled) return;
    onDeleteAll();
    setPendingDeleteAll(false);
  }

  return (
    <div className="recentCases" aria-label="Stored case navigation" aria-busy={initialLoading}>
      <div className="panelHeader compactPanelHeader">
        <div>
          <span className="index">RECENT</span>
          <h2>Stored cases</h2>
          <small className="muted">Search and sort the cases already loaded in this session.</small>
        </div>
        <button className="secondaryButton" type="button" onClick={onRefresh} disabled={initialLoading || remoteActionsDisabled}>Refresh</button>
      </div>

      {activeCase && (
        <div className="caseNavigationEmptyState" role="status" aria-live="polite">
          <p><strong>Current workspace context</strong></p>
          <p>{KIND_LABELS[activeCase.seed_kind]} · {activeCase.seed_value}</p>
          <small className="muted">
            CASE {activeCase.id.slice(0, 8)} · {caseRetentionStatus(activeCase.expires_at) === "elapsed"
              ? "retention deadline passed — refresh before relying on this row"
              : caseRetentionStatus(activeCase.expires_at) === "active"
                ? `retained until ${new Date(activeCase.expires_at).toLocaleString()}`
                : "retention deadline unavailable — refresh before relying on this row"}
          </small>
        </div>
      )}

      {remoteActionsDisabled && (
        <p className="muted" role="status">
          Remote case actions are unavailable until you sign in again. Search, filter, and sort the cases already loaded in this browser remain available.
        </p>
      )}

      {initialLoading ? (
        <p className="muted" role="status" aria-live="polite">Loading retained cases…</p>
      ) : remoteActionsDisabled && cases.length === 0 ? (
        <p className="muted" role="status" aria-live="polite">Stored case history is unavailable until you sign in again. Do not treat this workspace as empty.</p>
      ) : initialLoadFailed && cases.length === 0 ? (
        <p className="muted" role="status" aria-live="polite">Stored case history could not be loaded. Refresh before treating this workspace as empty.</p>
      ) : cases.length === 0 ? (
        <p className="muted">No retained research cases yet.</p>
      ) : (
        <>
          <div className="caseNavigationControls">
            <label>
              Search loaded cases
              <input
                ref={searchInputRef}
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Identifier or case ID"
                aria-keyshortcuts="/"
              />
              <small className="muted">Press / to focus case search.</small>
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

          {activeCaseIsHidden && (
            <div className="caseNavigationEmptyState" role="status" aria-live="polite">
              <p className="muted">The active case is hidden by the current loaded-case search or kind filter.</p>
              <button className="secondaryButton" type="button" onClick={clearCaseFilters}>Show active case</button>
            </div>
          )}

          {visibleCases.length === 0 ? (
            <div className="caseNavigationEmptyState">
              <p className="muted">No loaded cases match the current search and kind filter.</p>
              {!activeCaseIsHidden && (
                <button className="secondaryButton" type="button" onClick={clearCaseFilters}>Clear filters</button>
              )}
            </div>
          ) : (
            <div className="providerList">
              {visibleCases.map((item) => {
                const retentionStatus = caseRetentionStatus(item.expires_at);
                return (
                  <div className="caseRow" key={item.id}>
                    <button
                      className="caseOpen"
                      type="button"
                      onClick={() => onOpenCase(item.id)}
                      aria-current={activeCaseId === item.id ? "true" : undefined}
                      disabled={remoteActionsDisabled}
                    >
                      <strong>{KIND_LABELS[item.seed_kind]}</strong>
                      <span>{item.seed_value}</span>
                      <small>Created {new Date(item.created_at).toLocaleString()} · {item.id.slice(0, 8)}</small>
                      <small className={retentionStatus === "elapsed" ? "caseRetentionElapsed" : "muted"}>
                        {retentionStatus === "elapsed"
                          ? `Retention deadline passed · ${new Date(item.expires_at).toLocaleString()} · refresh before relying on this row`
                          : retentionStatus === "active"
                            ? `Retained until ${new Date(item.expires_at).toLocaleString()}`
                            : "Retention deadline unavailable · refresh before relying on this row"}
                      </small>
                    </button>
                    <details className="caseActions">
                      <summary>Actions</summary>
                      {pendingDeleteCaseId === item.id ? (
                        <div className="caseDeleteConfirmation" role="group" aria-label={`Confirm deletion of ${item.seed_value}`}>
                          <p className="muted" aria-live="polite">Delete this retained case? This cannot be undone.</p>
                          <div className="caseDeleteConfirmationActions">
                            <button className="dangerButton" type="button" onClick={() => confirmDeleteCase(item.id)} disabled={remoteActionsDisabled}>
                              Confirm delete
                            </button>
                            <button className="secondaryButton" type="button" onClick={() => setPendingDeleteCaseId(null)}>
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button className="dangerButton" type="button" onClick={() => setPendingDeleteCaseId(item.id)} disabled={remoteActionsDisabled}>
                          Delete this case
                        </button>
                      )}
                    </details>
                  </div>
                );
              })}
            </div>
          )}

          <div className="caseNavigationFooter">
            {hasMore && (
              <button className="secondaryButton" type="button" onClick={onLoadMore} disabled={loadingMore || remoteActionsDisabled}>
                {loadingMore ? "Loading older cases…" : "Load older cases"}
              </button>
            )}
            <details className="caseActions destructiveCaseActions">
              <summary>Retention actions</summary>
              <p className="muted">Destructive actions affect retained private cases and cannot be undone.</p>
              {pendingDeleteAll ? (
                <div className="caseDeleteConfirmation" role="group" aria-label="Confirm deletion of all retained cases">
                  <p className="muted" aria-live="polite">Delete every retained private research case? This cannot be undone.</p>
                  <div className="caseDeleteConfirmationActions">
                    <button className="dangerButton" type="button" onClick={confirmDeleteAll} disabled={remoteActionsDisabled}>
                      Confirm delete all
                    </button>
                    <button className="secondaryButton" type="button" onClick={() => setPendingDeleteAll(false)}>
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button className="dangerButton" type="button" onClick={() => setPendingDeleteAll(true)} disabled={remoteActionsDisabled}>
                  Delete all retained cases
                </button>
              )}
            </details>
          </div>
        </>
      )}
    </div>
  );
}
