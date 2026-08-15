# Product charter

## Problem

Background research is fragmented. One source may know a telecom carrier,
another may find a username, another may show a professional profile, and a
document may contradict all of them. Existing tools often dump links rather
than explain the relationship between the links.

PersonaLattice's job is to make the evidence legible.

## Product principle

**The evidence graph is the product. The AI is an analyst sitting on top of it.**

AI can:

- extract identifiers from user-provided material;
- propose candidate relationships;
- identify contradictions;
- rank research gaps;
- summarize verified evidence.

AI cannot:

- invent a source;
- silently turn a weak association into identity proof;
- bypass access controls;
- decide that a person's character is "good" or "bad";
- make regulated eligibility decisions in the bootstrap product.

## Initial users

The first useful version is for:

- people auditing their own digital footprint;
- researchers performing consented identity verification;
- founders or teams checking public-source identity signals with a legitimate purpose;
- professional credential research where the output remains evidence, not an automated employment decision.

## Success criteria for V1

A V1 case should be able to answer:

1. What identifiers did we start with?
2. What public/authorized sources were checked?
3. What did each source actually return?
4. Which observations support the same entity?
5. Which observations conflict?
6. How confident is each derived claim, and why?
7. What is still unknown?
8. Can another reviewer reproduce the reasoning from the evidence?
