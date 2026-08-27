# Fusion 2 — after prior-art destruction and recombination

## What external research killed

The original wide idea "treat translation meaning like an error-correcting lattice" cannot be claimed as a new general mechanism.

- Per-output translation validation is established in compiler verification.
- Bidirectional round-trip consistency and laws are established in the lens literature.
- Metamorphic testing is established for machine translation.
- Independent N-version implementations are established, and classic experiments warn that independently produced versions can still fail in correlated ways.
- Combining partial abstract observations by reduction/intersection is closely analogous to the reduced product of abstract domains.
- Formal constrained decoding is established and provides a strong syntactic/type-validity baseline.

Therefore `Semantic Parity Lattice` must not mean "invented lattice validation" and must not be sold as general semantic error correction.

## Reconstructed Frank-specific bottleneck

Frank's boundary is unusually constrained in a way the generic techniques do not directly solve as a packaged product:

1. source side is unconstrained German;
2. destination side must be typed ClayCode;
3. the translator is explicitly forbidden from becoming a second cognitive agent;
4. owner-defined hard fields have a zero-drift acceptance requirement;
5. ambiguity must survive rather than be confidently guessed;
6. upstream caller/auth/voice provenance must not be converted into semantic authority by translation;
7. ExpressionState may color German while remaining non-authoritative;
8. accepted Clay can later reach memory, GWT, Needle and effects, so a first-hop translation error has downstream leverage.

The important engineering question is not whether an all-powerful second semantic parser can validate the first. It is whether **small, capability-bounded, independently testable partial oracles** can provide useful hard-field validation while obeying the codec-not-second-mind constraint.

## Selected mechanism after collision

### SPL-001 — Semantic Parity Lattice, narrowed

SPL is a reduced-product-like validation layer over independent **partial hard-field observations**.

Each partial oracle has a deliberately narrow observational contract, for example:

- negation;
- quantity + unit;
- named person / grammatical role;
- modality;
- temporal marker;
- speech-act class;
- effect/action lexeme;
- explicit permission/denial marker.

An oracle can return only:

- `OBSERVED(value, evidence)`;
- `UNKNOWN(reason)`;
- `CONTRADICTION(evidence)`.

It cannot fill an unknown with a guess, query long-horizon memory, infer authority, or produce a replacement translation.

The main DE_TO_CLAY translator produces an **untrusted typed candidate**. ClayCode canonicalization deterministically projects that candidate onto its hard fields. SPL combines source observations with that exact destination projection.

Acceptance is one-way conservative:

- any contradiction => reject;
- any observed source field that differs from Clay => reject;
- hard-field UNKNOWN remains explicit erasure/ambiguity rather than evidence of correctness;
- no sensor can mint user identity, ASVB origin, token authority, capability or effect authorization;
- only after parity validation may the Clay candidate become boundary-admitted semantic input.

For CLAY_TO_DE the situation is stronger: the source hard projection is exact because source is typed Clay. After rendering German, the same narrow oracles must recover compatible observations. This produces a direct noninterference test for `ExpressionState`: varying ExpressionState is permitted to change soft realization, never the hard projection recovered from German.

## Why keep the word "parity"

Not because arbitrary natural-language semantics has a mathematical parity code. The operational analogy is limited:

- `OBSERVED mismatch` behaves like a detected error;
- `UNKNOWN` behaves like an erasure;
- overlapping independent observations create redundancy;
- destination hard projection acts as the codeword-side typed reference;
- a witness records which coordinates were actually checked.

No correction of an unknown meaning is authorized. SPL is **error detection / erasure exposure**, not semantic error correction.

## Strongest counterhypothesis after Fusion 2

A conventional independent full semantic parser/validator plus typed Clay validation and explicit UNKNOWN handling will match or dominate SPL. SPL's decomposition into partial oracles may add overhead without unique detection power.

This counterhypothesis is now mandatory, not optional. A synthetic benchmark that only defeats ordinary round-trip is insufficient.

## Required experiment classes

1. correct canonical German inputs;
2. correlated DE_TO_CLAY + backtranslation bug where same-codec round-trip remains stable;
3. single hard-field corruptions;
4. multi-field corruptions;
5. sensor ablation, especially one critical field removed;
6. deliberately UNKNOWN/ambiguous source form;
7. stale source hash / stale schema version witness;
8. shuffled witness-to-request binding;
9. ExpressionState variation against fixed Clay source;
10. upstream provenance field carried through but never synthesized;
11. full independent parser baseline;
12. constrained typed-output baseline;
13. resource metadata and latency.

## Decision law

`roundtrip_beaten` is interesting but not enough.

Promotion requires at least one of:

- unique consequential error coverage versus the strongest conventional validator;
- materially lower bounded checker complexity/resource cost for matched coverage;
- static architecture compression or assurance property that the conventional validator cannot express;
- stronger failure containment under checker fault injection.

Otherwise classify SPL `NO_UNIQUE_BENEFIT` and keep only the resulting translator-test obligations.
