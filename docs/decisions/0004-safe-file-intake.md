# ADR 0004 — safe file intake boundary

**Status:** accepted for M2

PersonaLattice needs document input, but a file upload is not just another form
field. The filename, claimed MIME type and file contents are all untrusted.

## Decision

M2 starts with a deliberately small allowlist:

- UTF-8 `.txt`;
- `.pdf` with PDF signature/trailer checks and text extraction through pypdf.

DOCX, ZIP and other archive-backed formats stay disabled until decompression,
embedded-content and parser limits have dedicated tests.

The API applies several independent controls:

1. multipart file/field/part limits and a request-size ceiling when
   `Content-Length` is available;
2. filename validation that rejects path separators, traversal-like names and
   dangerous or ambiguous double extensions;
3. a server-generated UUID for temporary storage rather than the original
   filename;
4. a client MIME check used only as a secondary signal;
5. content validation from the bytes themselves;
6. per-file and total-batch byte ceilings;
7. extraction in a separate process with time, output, PDF page/content-stream
   and best-effort process memory/CPU limits.

Raw bytes are staged under a private, non-webroot directory with restrictive
permissions, hashed, extracted, and deleted before the request completes. M2
does not retain raw uploads because production authentication, object storage
and retention/deletion policy do not exist yet.

## Evidence and AI boundary

Extracted text is labeled `untrusted_document_content`. Text such as
"ignore previous instructions" is evidence payload, not application authority.

The upload package can write extracted content to the M1 evidence store as an
`UPLOAD` observation with an `artifact://<uuid>` locator and SHA-256
provenance. The HTTP preview route remains stateless until a proper authenticated
case lifecycle exists.

Deterministic identifier extraction only creates review candidates. Candidate
identifiers cannot authorize later external research until a human explicitly
confirms them. A future model may propose claim candidates through the same
review contract, but model output is still not an observation.

## Why not retain files now?

Keeping uploaded identity documents without authentication, deletion controls
or a retention policy would create a larger privacy problem merely to make the
demo look more complete. Ephemeral raw storage is the safer M2 boundary.

## Deferred

M2 does not add:

- live model calls;
- live OSINT/provider queries;
- OCR or image vision;
- archive/ZIP extraction;
- antivirus/CDR services;
- production object storage;
- background job infrastructure;
- automatic research triggered by document content.
