"use client";

export type M5FactorSummaryRow = {
  kind: string;
  independence_group: string;
  applied_weight: number;
  status: string;
  rationale: string;
  veto: boolean;
};

type FactorClass = "supporting" | "conflicting" | "neutral";

type ClassifiedFactor = M5FactorSummaryRow & {
  factorClass: FactorClass;
};

function classifyFactor(factor: M5FactorSummaryRow): FactorClass {
  const text = `${factor.status} ${factor.rationale}`;
  if (
    factor.veto ||
    factor.applied_weight < 0 ||
    /conflict|contradict|mismatch|negative|unsupported/i.test(text)
  ) return "conflicting";
  if (factor.applied_weight > 0) return "supporting";
  return "neutral";
}

function decisiveOrder(left: ClassifiedFactor, right: ClassifiedFactor): number {
  const weightDelta = Math.abs(right.applied_weight) - Math.abs(left.applied_weight);
  if (weightDelta !== 0) return weightDelta;
  const vetoDelta = Number(right.veto) - Number(left.veto);
  if (vetoDelta !== 0) return vetoDelta;
  return `${left.kind}:${left.independence_group}`.localeCompare(
    `${right.kind}:${right.independence_group}`,
  );
}

function FactorGroup({
  label,
  factorClass,
  rows,
  empty,
}: {
  label: string;
  factorClass: FactorClass;
  rows: ClassifiedFactor[];
  empty: string;
}) {
  const visibleRows = rows.slice(0, 3);
  const hiddenCount = Math.max(0, rows.length - visibleRows.length);

  return (
    <section className="m5FactorGroup" data-factor-class={factorClass}>
      <div className="m5FactorGroupHeader">
        <strong>{label}</strong>
        <span>{rows.length}</span>
      </div>
      {rows.length === 0 ? (
        <p className="muted">{empty}</p>
      ) : (
        <>
          <ul className="coverageList">
            {visibleRows.map((factor) => (
              <li key={`${factor.kind}-${factor.independence_group}`}>
                <strong>{factor.kind}</strong>
                <span> · {factor.rationale}</span>
                <small>
                  {` · ${factor.independence_group} · weight ${factor.applied_weight}`}
                  {factor.veto ? " · veto" : ""}
                </small>
              </li>
            ))}
          </ul>
          {hiddenCount > 0 ? (
            <p className="muted m5FactorOverflow">
              {hiddenCount} more retained {hiddenCount === 1 ? "factor" : "factors"} in the full ledger below.
            </p>
          ) : null}
        </>
      )}
    </section>
  );
}

export function M5FactorSummary({ factors }: { factors: M5FactorSummaryRow[] }) {
  const classified = factors
    .map((factor): ClassifiedFactor => ({ ...factor, factorClass: classifyFactor(factor) }))
    .sort(decisiveOrder);
  const supporting = classified.filter((factor) => factor.factorClass === "supporting");
  const conflicting = classified.filter((factor) => factor.factorClass === "conflicting");
  const neutral = classified.filter((factor) => factor.factorClass === "neutral");

  return (
    <div className="m5FactorSummary" aria-label="Decisive retained M5 factors">
      <p className="reportBoundary">
        Retained factors are grouped by evidentiary direction. They are not calibrated probabilities
        and do not establish identity.
      </p>
      <div className="m5FactorSummaryGrid">
        <FactorGroup
          label="Supporting"
          factorClass="supporting"
          rows={supporting}
          empty="No positive retained factor contributes weight to this candidate."
        />
        <FactorGroup
          label="Conflicting"
          factorClass="conflicting"
          rows={conflicting}
          empty="No retained negative or veto factor is present."
        />
        <FactorGroup
          label="Neutral / withheld"
          factorClass="neutral"
          rows={neutral}
          empty="No zero-weight or neutral retained factor is present."
        />
      </div>
    </div>
  );
}
