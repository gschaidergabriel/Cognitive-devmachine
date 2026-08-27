# ATOMIC — SPL-001 Semantic Parity Lattice

## Executive result

This ATOMIC cycle did **not** promote a new Frank v0.1 architecture organ.

It found and measured a real translator-validation failure class, generated a radical ClayCode-first candidate, then refuted that candidate's unique-benefit claim against the strongest conventional control.

The durable result is a target implementation/test obligation, not SPL architecture:

> Frank v0.1 must never treat same-codec German -> ClayCode -> German roundtrip success as sufficient evidence of semantic fidelity for owner-hard fields. A source-independent or implementation-diverse hard-semantic validation path must exist, UNKNOWN must remain ambiguity, and the validator itself may not become a second cognitive agent.

Target issue: `gschaidergabriel/Dr.-Unterweger#162`.

## Why this problem was selected

At the live cutoff, token authentication, single-active execution, same-session continuation/idempotency, ClayCode WP04 effect-boundary work and several ATOMIC candidate families were all under active development. Selecting any of those would have duplicated current workers.

The unified Frank v0.1 workspace still identified F-V01-07 NEEDLE-TRANSLATOR as open. The owner-fixed language directive imposes unusually strong constraints:

- cognition/model-facing semantics are ClayCode only;
- German is a bounded bidirectional codec;
- the translator cannot become a second mind;
- ambiguity/loss must be explicit;
- hard fields such as identity, authority, negation, quantity and consequential intent may not drift;
- state-aware German expression must not change semantic truth/authority.

The live repository search did not find a current target `DE_TO_CLAY`/`CLAY_TO_DE` implementation at the run cutoff. This was used only as a frontier signal, not as proof of absence.

## Fusion 1: the real failure is common-mode self-consistency

An ordinary roundtrip check looks strong:

`German source -> Clay candidate -> German rendering`

and asks whether the result seems equivalent to the input.

But if both directions share the same wrong convention, the roundtrip can be stable while the canonical Clay meaning is wrong.

Examples of modeled systematic failures:

- source negation is ignored;
- MAY is consistently interpreted/rendered as MUST;
- Andreas is consistently mapped to Gabriel;
- quantity 10 is consistently mapped to 100;
- QUESTION is mapped to COMMAND;
- READ is mapped to WRITE;
- ALLOW is mapped to DENY;
- TOMORROW is mapped to NOW.

A self-consistent codec can normalize the wrong meaning and then reproduce that wrong normalized meaning perfectly. Therefore roundtrip consistency is not source semantic equivalence.

## Hypothesis field

Fourteen mechanisms from eight mechanism families were generated before external collision research. They included:

- deletion/control: deterministic hard-field renderer;
- topology: Semantic Parity Lattice;
- design diversity: independent translator/checker versions;
- temporal dynamics: semantic hysteresis across paraphrase/retry;
- topology/noninterference: orthogonal ExpressionState fiber;
- information/error coding: semantic syndrome code;
- causal validation: proof-carrying translation;
- experiment generation: metamorphic boundary adversary;
- uncertainty/Hyperposition: ambiguity polytope;
- information addressing: hard semantic fingerprint;
- IFC-like hard semantic labels;
- consequence-weighted clarification;
- triangulated partial-oracle validation;
- translator lesion/substitution witness lineage.

## External collision research

Fresh primary/author/institution sources sharply reduced novelty.

Translation validation already establishes generator-versus-validator separation and checking individual source/target translations. Bidirectional lens work already studies forward/backward consistency laws. Metamorphic machine-translation testing already uses controlled input transformations and output relations to expose translation defects. N-version programming already studies independently prepared implementations, and classic experiments show that supposed independence can still yield statistically correlated failures. Reduced products of abstract domains already combine separately analyzed components through iterative exchange/reduction of observations. Constrained decoding already provides a strong target-formal-language admissibility baseline.

The candidate therefore survived only as a project-specific composition, never as a world-first mechanism.

## SPL-001 semantics

The ClayCode candidate separates generation from admission.

The main translator emits an untrusted typed candidate. Narrow partial oracles inspect only specific German hard fields. They return one of:

- OBSERVED(value, evidence);
- UNKNOWN(reason);
- CONTRADICTION(evidence).

They may not translate the message, reason long-horizon, query memory autonomously, form goals, authorize tools/effects, mint identity, mint voice origin or modify the candidate.

The typed Clay candidate has a deterministic hard projection. SPL compares source observations against that projection.

Decision semantics:

- contradiction -> reject;
- observed mismatch -> reject;
- missing observation for an owner-hard field -> TRANSLATION_AMBIGUOUS;
- all required observed fields compatible -> ACCEPT.

For CLAY_TO_DE, source semantics are stronger because the source is already typed Clay. The rendered German is re-observed and must conserve all hard coordinates. ExpressionState is modeled as a soft realization fiber and may not change hard fields.

SPL never mints effect authority. A translated effect intent remains a proposal and still requires the normal authenticated actor/capability/Needle/effect reservation/attempt/outcome verification path.

## Executable proxy

A deterministic Python reference harness modeled a controlled German boundary with nine hard coordinates:

- person;
- negation;
- modality;
- quantity;
- unit;
- temporal marker;
- speech act;
- explicit permission;
- effect-intent class.

This corpus is intentionally not unrestricted German. Its purpose is to produce objectively known semantic ground truth and systematic common-mode defects.

### Main run

Seed: `20260810`

Cases: `100000`

- deliberately corrupted candidates: `56486`
- valid candidates: `43514`

Results:

| Mechanism | corrupt false allow | valid false deny | p50 us | p95 us |
|---|---:|---:|---:|---:|
| TYPE_ONLY | 100% | n/a | not isolated | not isolated |
| SAME_CODEC_ROUNDTRIP | 100% | 0 in measured path | 4.256 | 5.959 |
| independent full validator | 0% | 0% | 3.044 | 3.375 |
| SPL | 0% | 0% | 5.187 | 5.968 |

SPL witness size in this proxy:

- p50: 382 bytes;
- p95: 396 bytes;
- p99: 399 bytes.

The weak baselines are decisively falsified by construction. SPL succeeds against them. But the independent full validator ties SPL and is faster.

### Fault classes

Every activated fault was detected by both strong mechanisms:

- ALLOW_AS_DENY: 8,651 / 8,651;
- ANDREAS_AS_GABRIEL: 5,123 / 5,123;
- DROP_NEGATION: 14,055 / 14,055;
- MAY_AS_MUST: 6,211 / 6,211;
- QUESTION_AS_COMMAND: 6,356 / 6,356;
- READ_AS_WRITE: 4,121 / 4,121;
- TEN_AS_HUNDRED: 5,616 / 5,616;
- TOMORROW_AS_NOW: 6,353 / 6,353.

### Replication

Five independent 40,000-case runs were executed, seeds 20260811 through 20260815, adding 200,000 cases.

Every replication reproduced the qualitative result:

- TYPE_ONLY false-accepted all modeled corruptions;
- SAME_CODEC_ROUNDTRIP false-accepted all modeled corruptions;
- full independent validator had 0 false allow / 0 false deny;
- SPL had 0 false allow / 0 false deny;
- the full validator had lower p50 latency than SPL in every replication.

This makes the main conclusion insensitive to the first random seed within the tested synthetic distribution.

## Causal ablation

The most damaging result for SPL was the per-field lesion.

For each single-coordinate corruption, the oracle corresponding to that coordinate was removed. In every tested field class, false-accept rate became 100%:

- person 100%;
- negation 100%;
- modality 100%;
- quantity 100%;
- temporal 100%;
- speech act 100%;
- permission 100%;
- effect 100%.

This demonstrates that the oracle is causally necessary for its field, but also that the original 'parity lattice' did not contain actual redundant parity within a coordinate. It was a modular set of field validators.

## Redundancy rescue and second refutation

A second experiment deliberately gave one validation implementation the same systematic error as the translator.

Activated corrupted cases: `52053`.

Single checker results:

- one faulty full validator: 100% false allow;
- one faulty SPL oracle family: 100% false allow.

Redundant results:

- two full validators, one faulty + one exact: 0% false allow;
- dual SPL oracle families, one faulty + one exact: 0% false allow.

Latency p50 in this micro-harness:

- faulty full: 5.979 us;
- two full: 7.791 us;
- faulty SPL: 48.292 us;
- dual SPL: 22.944 us.

The rescue demonstrates the value of independent redundancy, but SPL does not own that property. Conventional redundant validation reproduced the containment with substantially lower cost in this proxy.

## UNKNOWN and ambiguity

2,526 deliberately unsupported hard-field forms were injected. SPL did not false-accept them. The full validator also did not accept them.

This supports the policy that UNKNOWN is an erasure/ambiguity state, not evidence of correctness. Again, the policy is useful but not unique to SPL.

## ExpressionState noninterference

5,000 typed frames were each rendered in four deterministic soft styles. The recovered hard projection did not drift in the controlled renderer.

This is only a mechanism check. It is not evidence that a learned/state-aware CLAY_TO_DE implementation will preserve hard semantics. Real ExpressionState noninterference remains a target test.

## Binding/replay controls

The proxy modeled source-hash/request/version binding:

- 10,000 shuffled source bindings rejected;
- 10,000 stale schema/version controls rejected.

These are deterministic proxy assertions, not target crash/restart evidence.

## Strongest counterhypothesis

> A conventional independent semantic parser/validator, composed with typed Clay validation and explicit UNKNOWN handling, matches SPL hard-field safety with less architecture; ordinary validator redundancy reproduces the checker-fault containment SPL claims.

The synthetic evidence supports this counterhypothesis.

Therefore SPL status is:

`NO_UNIQUE_BENEFIT_SYNTHETIC_TEST_OBLIGATION_CREATED`

not `SUPPORTED_ARCHITECTURE`.

## Durable Frank v0.1 delta

A target issue was created: `gschaidergabriel/Dr.-Unterweger#162`.

The obligation is conventional-first:

1. DE_TO_CLAY produces an untrusted candidate.
2. A separate semantic-validation path independently validates owner-hard fields before canonical admission.
3. Parser/type validity does not substitute for source fidelity.
4. UNKNOWN/unsupported hard semantics stays ambiguous.
5. CLAY_TO_DE must conserve exact typed source hard fields.
6. ExpressionState may affect soft realization only.
7. Upstream voice/auth provenance may be carried but never synthesized by the translator/validator.
8. Validation witnesses bind source/request/session/schema/implementation versions.
9. A release corpus must include common-mode roundtrip-stable errors.
10. Every hard field gets a lesion test.
11. Any SPL-like partial-oracle implementation must beat the smallest conventional validator on real German and target-VPS measurements before architecture adoption.

## Reopen condition

SPL is not permanently impossible. The synthetic proxy is intentionally simple and makes a full independent parser cheap.

A real German validator may require a second neural semantic model, while a set of deterministic narrow hard-field checkers might prove much cheaper. That is a plausible empirical hypothesis, but it has not been measured.

SPL may be reopened only if real German + target-VPS tests establish at least one of:

- unique consequential error coverage;
- materially lower bounded CPU/RAM/latency/token cost for matched hard-field safety;
- stronger static completeness over the declared hard-field set;
- stronger fault containment under realistic independent implementation faults.

Until then, building SPL as a separate Frank organ would be architecture inflation.

## Authority and safety

This ATOMIC run:

- did not train a model;
- did not authorize final training;
- did not mint effect authority;
- did not mutate the target Harness;
- did not promote SPL into accepted architecture;
- did not treat web research as runtime truth;
- did create a research possibility packet and a target implementation/test issue.

## Scientific value of the negative result

The most important result is not SPL itself. It is the removal of a dangerous future shortcut.

A developer could otherwise satisfy the owner directive by implementing one translator and showing good German->Clay->German roundtrips. The benchmark gives an executable counterexample to that acceptance logic: a deterministic translator can be wrong in a stable, self-consistent way.

The corrected acceptance logic is stronger:

`roundtrip consistency` is useful but insufficient.

`typed target validity` is useful but insufficient.

`independent source-semantic validation + explicit uncertainty + hard-field lesion tests` is the current minimal evidence direction.

That conclusion survives SPL's refutation and is now routed back into the real Frank v0.1 target as issue #162.
