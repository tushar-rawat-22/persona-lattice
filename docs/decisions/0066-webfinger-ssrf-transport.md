# ADR 0066 — WebFinger uses fresh DNS admission and IP-pinned HTTPS

Status: accepted as a pre-activation transport boundary

## Context

The WebFinger admission preflight deliberately stopped before network execution. RFC 7033 requires HTTPS and permits a WebFinger service to redirect a client to another HTTPS service URI. That makes two shortcuts unsafe:

- refusing every redirect would reject a standards-defined deployment pattern;
- resolving a hostname, checking the result, and then handing the hostname to a normal HTTP client would allow the client to resolve it again and reopen DNS-rebinding/SSRF risk.

The source is still planned. This decision establishes the network boundary before catalog/runtime activation.

## Decision

Add a WebFinger-specific HTTPS transport with these rules:

- profile seeds and every redirect target are parsed through the fail-closed WebFinger URL admission code;
- only HTTPS DNS hostnames on the default TLS port are accepted;
- credentials, fragments, IP literals, local-use hosts and control characters are rejected;
- redirect service URIs may contain query data because RFC 7033 permits hosted WebFinger service URIs outside the original well-known path;
- each hop resolves immediately before I/O;
- every resolved address is independently parsed and must be globally routable;
- TCP connects to the admitted IP address, while TLS certificate/SNI validation remains bound to the DNS hostname;
- redirects are followed manually and re-run the complete URL + DNS + TLS admission path;
- redirects are capped at three;
- 404 is the only no-match HTTP outcome at this layer;
- rate limits, transient failures, malformed redirects/media/JSON and oversized responses remain distinct provider errors;
- there is no HTTP downgrade.

The low-level request uses the Python standard library and adds no runtime dependency.

## Why IP pinning matters

A pre-resolution check followed by an ordinary hostname-based request is not an SSRF boundary: the HTTP stack may resolve the hostname again after the check. The transport therefore connects to the exact globally routable address admitted immediately before the request and separately verifies the TLS certificate for the original hostname.

A redirect repeats the same process. If the first server redirects to an unsafe or non-public target, that is treated as malformed returned provider behavior because provider contact has already occurred; it is not mislabeled as a pre-call local policy stop.

## Scope

This does not activate `webfinger_activitypub`. There is still no provider registry entry, source binding, shared-runtime owner or quick-research call for WebFinger. ActivityPub actor fetching remains outside scope.

The planned source catalog also still needs to be narrowed from URL + generic username + name output to the URL-only contract actually supported by the reviewed WebFinger boundary before activation.

## Consequences

Positive:

- legitimate RFC 7033 HTTPS redirects can be supported without delegating redirect safety to a generic HTTP client;
- DNS rebinding cannot switch the actual TCP connection to an address that was not admitted;
- redirect and DNS failures have an execution phase that later typed source-state mapping can classify truthfully;
- the zero-spend baseline remains unchanged.

Costs:

- the transport is intentionally stricter than a browser and may reject unusual WebFinger deployments using explicit ports or non-DNS targets;
- activation still requires the catalog correction, provider wrapper, runtime ownership, typed fixtures and report integration.

## Next gate

Correct the planned source capability to URL-only, then wrap this transport and the existing JRD admission logic in one governed provider. Activation must remain atomic across catalog, binding, registry, shared runtime, quick research and typed source-state reporting.