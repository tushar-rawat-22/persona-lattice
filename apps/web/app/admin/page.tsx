"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { QuickResearch } from "./quick-research";
import { UploadReviewWorkflow } from "./upload-review-workflow";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type AuthState = "checking" | "anonymous" | "authenticated";

type AuthSession = {
  authenticated: true;
  session_record_id: string;
  expires_at: string;
  csrf_token: string;
};

type ProviderPlan = {
  provider: string;
  capability: string;
  status: string;
  contact_risk: string;
  reason: string;
};

type Preview = {
  case_id: string;
  status: string;
  normalized: Record<string, unknown>;
  provider_plan: ProviderPlan[];
  warnings: string[];
};

type ReviewCandidate = {
  candidate_id: string;
  candidate_type: string;
  origin: string;
  identifier_kind: string | null;
  value: string;
  review_status: string;
  external_research_authorized: boolean;
};

type FilePreview = {
  status: "review_required";
  artifacts: Array<{
    artifact_id: string;
    original_name: string;
    detected_media_type: string;
    extraction_method: string;
    extracted_text: string;
    extracted_chars: number;
    trust_boundary: string;
    candidates: ReviewCandidate[];
  }>;
  warnings: string[];
};

function splitValues(value: string) {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

async function api(path: string, init?: RequestInit, csrfToken?: string) {
  const method = (init?.method ?? "GET").toUpperCase();
  const unsafe = !["GET", "HEAD", "OPTIONS"].includes(method);
  return fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(init?.headers ?? {}),
      ...(unsafe && csrfToken ? { "X-PersonaLattice-CSRF": csrfToken } : {}),
    },
  });
}

export default function AdminConsole() {
  const [authState, setAuthState] = useState<AuthState>("checking");
  const [csrfToken, setCsrfToken] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authBusy, setAuthBusy] = useState(false);

  const [purpose, setPurpose] = useState("self_audit");
  const [fullName, setFullName] = useState("");
  const [phones, setPhones] = useState("");
  const [emails, setEmails] = useState("");
  const [usernames, setUsernames] = useState("");
  const [urls, setUrls] = useState("");
  const [organizations, setOrganizations] = useState("");
  const [notes, setNotes] = useState("");
  const [consent, setConsent] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [result, setResult] = useState<Preview | null>(null);
  const [fileResult, setFileResult] = useState<FilePreview | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    api("/v1/auth/session")
      .then(async (response) => {
        if (!active) return;
        if (!response.ok) {
          setCsrfToken("");
          setAuthState("anonymous");
          return;
        }
        const session = (await response.json()) as AuthSession;
        setCsrfToken(session.csrf_token);
        setAuthState("authenticated");
      })
      .catch(() => {
        if (active) {
          setCsrfToken("");
          setAuthState("anonymous");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const signalCount = useMemo(
    () =>
      [fullName, phones, emails, usernames, urls, organizations, notes].filter((value) =>
        value.trim(),
      ).length + files.length,
    [fullName, phones, emails, usernames, urls, organizations, notes, files],
  );

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthBusy(true);
    setAuthError("");
    try {
      const formData = new FormData(event.currentTarget);
      const submittedUsername = String(formData.get("username") ?? "");
      const submittedPassword = String(formData.get("password") ?? "");

      const response = await api("/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: submittedUsername,
          password: submittedPassword,
        }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(typeof body.detail === "string" ? body.detail : "Login failed.");
      }
      const session = body as AuthSession;
      setCsrfToken(session.csrf_token);
      setPassword("");
      setAuthState("authenticated");
    } catch (caught) {
      setAuthError(caught instanceof Error ? caught.message : "Login failed.");
    } finally {
      setAuthBusy(false);
    }
  }

  async function logout() {
    await api("/v1/auth/logout", { method: "POST" }, csrfToken).catch(() => undefined);
    setResult(null);
    setFileResult(null);
    setCsrfToken("");
    setAuthState("anonymous");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);
    setFileResult(null);

    if (!consent && purpose !== "public_source_research") {
      setError("Acknowledge the consent or authorization requirement first.");
      return;
    }

    setLoading(true);
    try {
      const response = await api(
        "/v1/intake/preview",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            purpose,
            consent_acknowledged: consent,
            full_name: fullName || null,
            phones: splitValues(phones),
            emails: splitValues(emails),
            usernames: splitValues(usernames),
            urls: splitValues(urls),
            organizations: splitValues(organizations),
            notes: notes || null,
            files: files.map((file) => ({
              name: file.name,
              media_type: file.type || null,
              size_bytes: file.size,
            })),
          }),
        },
        csrfToken,
      );

      if (response.status === 401) {
        setCsrfToken("");
        setAuthState("anonymous");
        throw new Error("Admin session expired. Sign in again.");
      }

      const body = await response.json();
      if (!response.ok) {
        throw new Error(
          typeof body.detail === "string" ? body.detail : "The intake request was rejected.",
        );
      }

      let uploaded: FilePreview | null = null;
      if (files.length > 0) {
        const formData = new FormData();
        formData.append("purpose", purpose);
        formData.append("consent_acknowledged", String(consent));
        for (const file of files) formData.append("files", file);

        const fileResponse = await api(
          "/v1/files/preview",
          { method: "POST", body: formData },
          csrfToken,
        );
        if (fileResponse.status === 401) {
          setCsrfToken("");
          setAuthState("anonymous");
          throw new Error("Admin session expired. Sign in again.");
        }
        const fileBody = await fileResponse.json();
        if (!fileResponse.ok) {
          throw new Error(
            typeof fileBody.detail === "string"
              ? fileBody.detail
              : "The file intake request was rejected.",
          );
        }
        uploaded = fileBody as FilePreview;
      }

      setResult(body as Preview);
      setFileResult(uploaded);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not reach the API.");
    } finally {
      setLoading(false);
    }
  }

  if (authState === "checking") {
    return (
      <main className="shell">
        <section className="panel loginCard">
          <p className="eyebrow">PERSONALATTICE / PRIVATE</p>
          <h1 className="compactTitle">Checking admin session…</h1>
          <p className="muted">Real intake and case data are never loaded before authentication.</p>
        </section>
      </main>
    );
  }

  if (authState === "anonymous") {
    return (
      <main className="shell">
        <section className="panel loginCard">
          <p className="eyebrow">PERSONALATTICE / ADMIN</p>
          <h1 className="compactTitle">Private operator access.</h1>
          <p className="lede">
            Real-person intake, evidence collection and stored case data are server-side protected.
          </p>
          <form className="loginForm" onSubmit={login}>
            <label>
              Admin username
              <input name="username" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required />
            </label>
            <label>
              Password
              <input name="password" autoComplete="current-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
            </label>
            {authError && <p className="error">{authError}</p>}
            <button type="submit" disabled={authBusy}>{authBusy ? "Authenticating…" : "Unlock operator console"}</button>
          </form>
          <Link className="textLink" href="/">Return to public preview</Link>
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">PERSONALATTICE / PRIVATE OPERATOR</p>
          <h1>Build the case from evidence, not assumptions.</h1>
          <p className="lede">
            Submit identifiers and authorized evidence. The API normalizes inputs, enforces purpose
            boundaries, and keeps provider output separate from factual claims.
          </p>
        </div>
        <div className="adminActions">
          <span className="status"><span className="dot" /> authenticated</span>
          <button className="secondaryButton" type="button" onClick={logout}>Log out</button>
        </div>
      </header>

      <section className="workspace">
        <form className="panel intake" onSubmit={submit}>
          <div className="panelHeader">
            <div><span className="index">01</span><h2>Case intake</h2></div>
            <span className="count">{signalCount} signals</span>
          </div>

          <label>
            Purpose
            <select value={purpose} onChange={(event) => setPurpose(event.target.value)}>
              <option value="self_audit">Self audit</option>
              <option value="consented_due_diligence">Consented due diligence</option>
              <option value="public_source_research">Public-source research</option>
              <option value="professional_verification">Professional verification</option>
              <option value="employment_decision">Employment decision — blocked</option>
            </select>
          </label>

          <div className="twoColumn">
            <label>Name<input value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Known or claimed name" /></label>
            <label>Phone<textarea value={phones} onChange={(event) => setPhones(event.target.value)} placeholder={"+91…\n+1…"} rows={3} /></label>
          </div>
          <div className="twoColumn">
            <label>Email addresses<textarea value={emails} onChange={(event) => setEmails(event.target.value)} placeholder="one@example.com" rows={3} /></label>
            <label>Usernames<textarea value={usernames} onChange={(event) => setUsernames(event.target.value)} placeholder={"@handle\nanother_handle"} rows={3} /></label>
          </div>
          <label>URLs / profiles<textarea value={urls} onChange={(event) => setUrls(event.target.value)} placeholder="Public profile, portfolio or source URLs" rows={3} /></label>
          <label>Organizations<textarea value={organizations} onChange={(event) => setOrganizations(event.target.value)} placeholder="Employer, university, company or claimed affiliation" rows={2} /></label>
          <label>Notes / claims to cross-check<textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Paste claims or context to verify." rows={4} /></label>

          <label className="dropzone">
            <strong>Attach evidence</strong>
            <span>PDF, UTF-8 text, JPEG or PNG. Images are inspected for bounded file/EXIF metadata only; no face identification is performed.</span>
            <input
              type="file"
              accept=".pdf,.txt,.jpg,.jpeg,.png,application/pdf,text/plain,image/jpeg,image/png"
              multiple
              onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
            />
            {files.length > 0 && <small>{files.map((file) => file.name).join(" • ")}</small>}
          </label>

          <label className="check">
            <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
            <span>I have the required consent or authorization for this purpose, or I am auditing myself.</span>
          </label>

          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={loading}>{loading ? "Validating evidence…" : "Build research plan"}</button>
        </form>

        <aside className="sideStack">
          <QuickResearch csrfToken={csrfToken} />

          <section className="panel">
            <div className="panelHeader"><div><span className="index">03</span><h2>Research plan</h2></div></div>
            {!result ? (
              <p className="muted">Submit an authenticated intake to see normalization and provider policy decisions.</p>
            ) : (
              <>
                <div className="caseId">CASE {result.case_id.slice(0, 8)}</div>
                <pre>{JSON.stringify(result.normalized, null, 2)}</pre>
                <div className="providerList">
                  {result.provider_plan.map((provider) => (
                    <div className="provider" key={provider.provider}>
                      <div><strong>{provider.provider}</strong><span>{provider.capability}</span></div>
                      <div className="tags"><em>{provider.status}</em><em>{provider.contact_risk}</em></div>
                    </div>
                  ))}
                </div>
                {fileResult && (
                  <>
                    <div className="providerList">
                      {fileResult.artifacts.map((artifact) => (
                        <div className="provider" key={artifact.artifact_id}>
                          <div>
                            <strong>{artifact.original_name}</strong>
                            <span>{artifact.detected_media_type} · {artifact.extraction_method} · {artifact.extracted_chars} metadata/text chars · {artifact.candidates.length} review candidates</span>
                          </div>
                          <div className="tags"><em>untrusted content</em><em>no automatic external query</em></div>
                        </div>
                      ))}
                    </div>
                    <UploadReviewWorkflow
                      artifacts={fileResult.artifacts}
                      csrfToken={csrfToken}
                      purpose={purpose}
                      consentAcknowledged={consent}
                    />
                  </>
                )}
              </>
            )}
          </section>

          <section className="panel boundary">
            <p className="eyebrow">BOUNDARY</p>
            <p>Private-account bypass, credential abuse, covert IP discovery, live tracking and hidden KYC acquisition are not provider capabilities.</p>
          </section>
        </aside>
      </section>
    </main>
  );
}
