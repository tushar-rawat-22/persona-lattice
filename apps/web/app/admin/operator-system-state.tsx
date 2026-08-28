"use client";

type OperatorSystemStateProps = {
  attemptCount: number;
  completedAttemptCount: number;
  failedAttemptCount: number;
  noMatchCount: number;
  withheldCount: number;
  unresolvedCount: number;
};

type StateTone = "complete" | "partial" | "limited" | "quiet";

function statePresentation({
  attemptCount,
  completedAttemptCount,
  failedAttemptCount,
  noMatchCount,
  withheldCount,
  unresolvedCount,
}: OperatorSystemStateProps): { tone: StateTone; title: string; detail: string } {
  if (failedAttemptCount > 0 || unresolvedCount > 0) {
    return {
      tone: "partial",
      title: "Research completed with limits",
      detail: `${failedAttemptCount} provider attempt${failedAttemptCount === 1 ? "" : "s"} failed and ${unresolvedCount} source state${unresolvedCount === 1 ? " remains" : "s remain"} unresolved. Review Sources before treating the case as complete.`,
    };
  }
  if (attemptCount > 0 && noMatchCount === attemptCount) {
    return {
      tone: "quiet",
      title: "No retained match from attempted sources",
      detail: "This is source silence, not evidence that the subject or claim does not exist elsewhere.",
    };
  }
  if (withheldCount > 0) {
    return {
      tone: "limited",
      title: "Some evidence was withheld by source policy",
      detail: `${withheldCount} source outcome${withheldCount === 1 ? " was" : "s were"} withheld. Review Sources for the retained reason before drawing conclusions from missing evidence.`,
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
  return (
    <section
      className="operatorSystemState"
      data-state-tone={presentation.tone}
      aria-label="Research execution state"
      role="status"
    >
      <strong>{presentation.title}</strong>
      <p>{presentation.detail}</p>
    </section>
  );
}
