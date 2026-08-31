"use client";

import type { OperatorSystemStateCounts } from "./operator-system-state-model";

type OperatorSystemStateProps = OperatorSystemStateCounts;

type StateTone = "complete" | "partial" | "limited" | "quiet";

type SourceStateLedgerItem = {
  key: string;
  label: string;
  count: number;
};

function countPhrase(count: number, singular: string, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}

function limitationSummary({
  failedAttemptCount,
  unresolvedCount,
  withheldCount,
  notAttemptedLimitCount,
}: OperatorSystemStateProps): string[] {
  const parts: string[] = [];
  if (failedAttemptCount > 0) {
    parts.push(`${countPhrase(failedAttemptCount, "provider attempt")} failed`);
  }
  if (unresolvedCount > 0) {
    parts.push(`${countPhrase(unresolvedCount, "source state")} ${unresolvedCount === 1 ? "remains" : "remain"} unresolved`);
  }
  if (withheldCount > 0) {
    parts.push(`${countPhrase(withheldCount, "source outcome")} withheld by source policy`);
  }
  if (notAttemptedLimitCount > 0) {
    parts.push(`${countPhrase(notAttemptedLimitCount, "source path")} not attempted because of configuration, routing, review, budget or policy limits before provider contact`);
  }
  return parts;
}

function sourceStateLedger({
  attemptCount,
  completedAttemptCount,
  failedAttemptCount,
  noMatchCount,
  withheldCount,
  unresolvedCount,
  notAttemptedLimitCount,
}: OperatorSystemStateProps): SourceStateLedgerItem[] {
  const items: SourceStateLedgerItem[] = [
    { key: "attempted", label: "attempted", count: attemptCount },
    { key: "completed", label: "completed", count: completedAttemptCount },
    { key: "failed", label: "failed", count: failedAttemptCount },
    { key: "no-match", label: "no retained match", count: noMatchCount },
    { key: "withheld", label: "withheld", count: withheldCount },
    { key: "unresolved", label: "unresolved", count: unresolvedCount },
    { key: "not-attempted", label: "not attempted", count: notAttemptedLimitCount },
  ];
  return items.filter((item) => item.key === "attempted" || item.count > 0);
}

function statePresentation({
  attemptCount,
  completedAttemptCount,
  failedAttemptCount,
  noMatchCount,
  withheldCount,
  unresolvedCount,
  notAttemptedLimitCount,
}: OperatorSystemStateProps): { tone: StateTone; title: string; detail: string } {
  const limitations = limitationSummary({
    attemptCount,
    completedAttemptCount,
    failedAttemptCount,
    noMatchCount,
    withheldCount,
    unresolvedCount,
    notAttemptedLimitCount,
  });
  if (failedAttemptCount > 0 || unresolvedCount > 0) {
    return {
      tone: "partial",
      title: "Research completed with limits",
      detail: `${limitations.join("; ")}. Review Sources before treating the case as complete.`,
    };
  }
  if (withheldCount > 0 && notAttemptedLimitCount > 0) {
    return {
      tone: "limited",
      title: "Research completed with coverage limits",
      detail: `${limitations.join("; ")}. Review Sources for the retained reason before drawing conclusions from missing evidence.`,
    };
  }
  if (withheldCount > 0) {
    return {
      tone: "limited",
      title: "Some evidence was withheld by source policy",
      detail: `${limitations.join("; ")}. Review Sources for the retained reason before drawing conclusions from missing evidence.`,
    };
  }
  if (notAttemptedLimitCount > 0) {
    return {
      tone: "limited",
      title: "Some source paths were not attempted",
      detail: `${limitations.join("; ")}. Review Sources for the exact reason.`,
    };
  }
  if (attemptCount > 0 && noMatchCount === attemptCount) {
    return {
      tone: "quiet",
      title: "No retained match from attempted sources",
      detail: "This is source silence, not evidence that the subject or claim does not exist elsewhere.",
    };
  }
  if (attemptCount > 0 && completedAttemptCount === attemptCount) {
    return {
      tone: "complete",
      title: "Attempted sources completed",
      detail: "All attempted sources reached a terminal result for this bounded run. This does not imply exhaustive coverage beyond the configured source set.",
    };
  }
  return {
    tone: "limited",
    title: "Source coverage is limited",
    detail: "The retained report does not prove that every eligible source was attempted. Review Sources for exact execution state.",
  };
}

export function OperatorSystemState(props: OperatorSystemStateProps) {
  const presentation = statePresentation(props);
  const ledger = sourceStateLedger(props);
  return (
    <section
      className="operatorSystemState"
      data-state-tone={presentation.tone}
      aria-label="Research execution state"
      role="status"
    >
      <strong>{presentation.title}</strong>
      <p>{presentation.detail}</p>
      <div className="sourceSummaryLine" aria-label="Source state counts">
        {ledger.map((item) => (
          <span key={item.key}>{item.count} {item.label}</span>
        ))}
      </div>
    </section>
  );
}
