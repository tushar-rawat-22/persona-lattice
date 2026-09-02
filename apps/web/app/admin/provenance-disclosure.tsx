"use client";

import { useState } from "react";

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

function isIpLiteral(hostname: string): boolean {
  if (/^\d{1,3}(?:\.\d{1,3}){3}$/.test(hostname)) return true;
  return hostname.includes(":");
}

function isSafePublicHostname(hostname: string): boolean {
  const normalized = hostname.toLowerCase().replace(/\.$/, "");
  if (!normalized || !normalized.includes(".")) return false;
  if (isIpLiteral(normalized)) return false;
  if (
    normalized === "localhost" ||
    normalized.endsWith(".localhost") ||
    normalized.endsWith(".local") ||
    normalized.endsWith(".internal")
  ) return false;
  return true;
}

function safeWebLocator(locator: string): string | null {
  if (!locator || locator !== locator.trim()) return null;
  try {
    const parsed = new URL(locator);
    if (!["http:", "https:"].includes(parsed.protocol)) return null;
    if (parsed.username || parsed.password || !parsed.hostname) return null;
    if (!isSafePublicHostname(parsed.hostname)) return null;
    return locator;
  } catch {
    return null;
  }
}

export function ProvenanceDisclosure({
  records,
  label = "Inspect provenance",
}: ProvenanceDisclosureProps) {
  const [copyStatus, setCopyStatus] = useState<string | null>(null);
  if (records.length === 0) return null;

  const unique = records.filter((record, index, all) =>
    all.findIndex((candidate) =>
      candidate.source === record.source &&
      candidate.sourceLocator === record.sourceLocator &&
      candidate.sourceState === record.sourceState &&
      candidate.leadKind === record.leadKind,
    ) === index,
  );

  async function copyCanonicalLocator(locator: string, source: string) {
    try {
      await navigator.clipboard.writeText(locator);
      setCopyStatus(`Copied canonical locator for ${source}.`);
    } catch {
      setCopyStatus(`Could not copy canonical locator for ${source}.`);
    }
  }

  return (
    <details className="provenanceDisclosure">
      <summary>{label}</summary>
      <ul className="provenanceList">
        {unique.map((record, index) => {
          const href = safeWebLocator(record.sourceLocator);
          return (
            <li key={`${record.source}-${record.sourceLocator}-${record.sourceState ?? "state-unavailable"}-${record.leadKind ?? "lead-unavailable"}-${index}`}>
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
                <>
                  <small
                    className="muted"
                    style={{ overflowWrap: "anywhere" }}
                    aria-label={`Canonical locator for ${record.source}`}
                  >
                    {href}
                  </small>
                  <div className="provenanceActions">
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label={`Open canonical source for ${record.source}`}
                    >
                      Open canonical source
                    </a>
                    <button
                      className="textButton"
                      type="button"
                      onClick={() => copyCanonicalLocator(href, record.source)}
                      aria-label={`Copy canonical locator for ${record.source}`}
                    >
                      Copy locator
                    </button>
                  </div>
                </>
              ) : (
                <span className="muted">Canonical locator is not a safe public web URL.</span>
              )}
            </li>
          );
        })}
      </ul>
      {copyStatus && <p className="muted" role="status" aria-live="polite">{copyStatus}</p>}
    </details>
  );
}
