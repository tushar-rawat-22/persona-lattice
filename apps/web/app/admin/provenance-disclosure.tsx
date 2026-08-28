"use client";

type ProvenanceRecord = {
  source: string;
  sourceLocator: string;
  sourceState?: string | null;
  leadKind?: string | null;
};

type ProvenanceDisclosureProps = {
  records: ProvenanceRecord[];
  label?: string;
};

function safeWebLocator(locator: string): string | null {
  if (!locator || locator !== locator.trim()) return null;
  try {
    const parsed = new URL(locator);
    if (!["http:", "https:"].includes(parsed.protocol)) return null;
    if (parsed.username || parsed.password || !parsed.hostname) return null;
    return locator;
  } catch {
    return null;
  }
}

export function ProvenanceDisclosure({
  records,
  label = "Inspect provenance",
}: ProvenanceDisclosureProps) {
  if (records.length === 0) return null;

  const unique = records.filter((record, index, all) =>
    all.findIndex((candidate) =>
      candidate.source === record.source && candidate.sourceLocator === record.sourceLocator,
    ) === index,
  );

  return (
    <details className="provenanceDisclosure">
      <summary>{label}</summary>
      <ul className="provenanceList">
        {unique.map((record) => {
          const href = safeWebLocator(record.sourceLocator);
          return (
            <li key={`${record.source}-${record.sourceLocator}`}>
              <div>
                <strong>{record.source}</strong>
                {(record.sourceState || record.leadKind) && (
                  <small>
                    {record.sourceState ?? "state unavailable"}
                    {record.leadKind ? ` · ${record.leadKind}` : ""}
                  </small>
                )}
              </div>
              {href ? (
                <a href={href} target="_blank" rel="noopener noreferrer">
                  Open canonical source
                </a>
              ) : (
                <span className="muted">Canonical locator is not a safe public web URL.</span>
              )}
            </li>
          );
        })}
      </ul>
    </details>
  );
}
