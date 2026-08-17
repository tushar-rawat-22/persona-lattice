# Documentation standard

PersonaLattice has two different documentation audiences. Mixing them produces bad public docs and unreliable handovers, so they are kept separate on purpose.

## Maintainer and operator documentation

README files, setup notes, operator guides, deployment notes and feature documentation are written for people who need to understand or run the project.

Use normal maintainer prose:

- say what the component does, what it needs and what can fail;
- prefer concrete names, commands, limits and examples over generic summaries;
- explain unusual decisions where they affect operation or maintenance;
- keep warnings close to the action they qualify;
- remove obsolete instructions when behavior changes;
- do not claim a provider, integration or deployment mode works until the repository actually supports it.

Avoid writing that sounds generated or ceremonial. In particular, avoid repeated project summaries, inflated adjectives, filler such as “comprehensive” or “robust” when a precise statement is possible, repetitive disclaimer blocks, and headings that exist only to make a document look complete.

A maintainer should be able to read the file without knowing the history of the ChatGPT conversation.

## Architecture decisions

Files under `docs/decisions/` record a decision, not a retrospective essay.

An ADR should normally contain:

- the problem or constraint that forced a decision;
- the chosen design;
- the important alternatives or rejected assumptions when they matter;
- security, privacy, cost or compatibility consequences;
- what deliberately remains out of scope;
- the next migration or review point when one exists.

Keep executable policy and ADR text aligned. If code and an ADR disagree, treat that as a defect.

## Continuity and assistant handover material

`docs/CONTINUITY.md` and any future assistant-oriented handover files exist to let a later engineering session resume without reconstructing old conversations.

These files should be dense and explicit rather than conversational. Record:

- authoritative branch and relevant merge/checkpoint SHAs;
- what is complete, active and intentionally deferred;
- current test/CI evidence;
- important invariants and security/privacy boundaries;
- known debt, open issues and the exact next gate;
- assumptions that were challenged or corrected;
- commands or paths only when they are still authoritative.

Do not copy assistant-oriented checkpoint language into the public README or operator documentation. Do not turn continuity files into marketing material.

## Roadmap discipline

`docs/ROADMAP.md` describes the current engineering sequence, not an aspirational feature list.

When a milestone materially changes:

1. update its status;
2. record the real remaining work;
3. remove or rewrite instructions that would now duplicate completed work;
4. keep permanent product/security rules visible;
5. avoid percentage-complete claims unless they are explicitly labelled as estimates.

A stale roadmap is a project bug because it can send the next implementation block in the wrong direction.

## Zero-spend baseline

The default PersonaLattice product must remain usable without paid APIs, paid hosting, paid databases, paid proxy networks or paid enrichment services.

Paid or metered integrations may be documented only as optional future enhancements. They must not become required dependencies of the baseline architecture. Before activating an external source, re-check its current official terms, authentication requirements, limits and pricing; do not rely on an old note in the repository.

Where a free source has quotas, record the quota assumptions and design the provider so exhaustion degrades to an explicit unavailable/budget-stopped state rather than breaking the investigation pipeline.

## Change checklist

For a meaningful implementation PR, ask:

- Did behavior, configuration, limits or source coverage change?
- Which maintainer/operator document now needs to change?
- Does an ADR need to be added or corrected?
- Do `CONTINUITY.md` or `ROADMAP.md` now contain stale state?
- Can a reader tell what actually executed versus what is planned or optional?
- Does the documentation still describe a zero-spend working baseline?

Documentation updates belong in the same engineering block whenever practical. A later cleanup pass is not a substitute for keeping the repository truthful as it evolves.
