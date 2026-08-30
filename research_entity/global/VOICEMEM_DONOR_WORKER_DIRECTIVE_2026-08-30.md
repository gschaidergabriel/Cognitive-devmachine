# VoiceMem donor worker directive — 2026-08-30

Status: RESEARCH ROUTING DIRECTIVE / DONOR INPUT / NO AUTOMATIC PRODUCT CREDIT

Read first:

- `research_entity/architect/donor_packets/VOICEMEM_DONOR_FORENSICS_2026-08-30.md`
- `research_entity/architect/donor_packets/VOICEMEM_WORKER_INGEST_PACKET_2026-08-30.json`

## Purpose

Use the VoiceMem donor only where it can measurably improve Frankenstein 2.0 / EntityOS / HCU. Do not copy the donor architecture wholesale. Preserve canonical state, effect authority, exact causal lineage, generation fences and current workpackage ownership.

## Worker order

1. Refresh exact current Frankenstein 2.0 `main` and current active workpackage claims.
2. Do not use stale Architect G6 frontier as current truth; it is known to trail the current F2 head materially.
3. Check whether a current workpackage already implements the candidate mechanism before creating work.
4. Prefer the smallest bounded donor-derived primitive that removes a real bottleneck.
5. Build its falsifier/negative tests before claiming architectural benefit.
6. Keep donor projections and learned policies noncanonical until separately admitted at target scope.
7. Preserve exact source -> test -> runtime evidence scope.

## P0 candidates

### P0-A — Claim / Evidence / Cause / Policy separation

Use when current code conflates:
- world/project observation;
- hypothesis/trait;
- evidence;
- method lesson;
- next-action policy candidate.

Required invariant:

`METHOD_PRESENT != FACT_PRESENT`

and

`POLICY_CANDIDATE != EFFECT_AUTHORITY`

### P0-B — Prospective Open Loop

Use for deferred intentions that should become relevant when a future typed condition appears.

Required path:

`open-loop encode -> condition observation -> cue detection receipt -> intention retrieval -> Agency/HCU arbitration -> optional typed effect request -> EffectGate`

Never:

`cue -> direct external effect`

### P0-C — Derived Query Adapter

Use for relative time, aliases, versions, generations or other context-dependent query normalization.

Required:
- original query digest;
- adapter identity/version;
- reference context such as time/timezone/generation;
- derived query digest;
- `canonical_state_mutated=false`.

### P0-D — Demand-Shaped Noncanonical Projection

Only after a retrieval baseline exists.

Input must come from actual retrieval/workspace episodes. Promotion is a view/index/workspace candidate, never a world fact. Require anti-feedback controls and deterministic rebuild.

### P0-E — exact turn/session/event lineage for learned experience

No promoted claim, method lesson or policy candidate without exact origin evidence identities where available.

## P1 candidates

- adaptive multi-prototype representation with fail-closed unknown identity;
- fast/slow selective HCU routing with measured false-negative rate;
- reversible slack-time retrieval/binding/prefetch;
- typed place/routine/environment context instead of flattening every signal into prose.

## Required research questions

Workers should return evidence for or against:

1. Does retrieval-shaped clustering improve held-out retrieval after controlling for frequency and query order?
2. Can the projection be rebuilt deterministically from canonical evidence + retrieval receipts?
3. Can experience memory improve future actions without learning false causal rules from coincident outcomes?
4. Can prospective cue monitoring remain cheap without missing rare high-value cues?
5. When do adaptive prototypes split too aggressively or collapse distinct modes?
6. Which donor mechanisms are already present in F2 under different names and therefore should not be duplicated?

## Required negative cases

- dominant-query rich-get-richer loop;
- stale-generation projection;
- forged evidence link;
- single noisy outcome promoted to policy;
- outdated claim treated as current;
- relative-date expansion with wrong reference timezone;
- scene/state cue false positive;
- similarity-induced identity collapse;
- low-cost gate suppressing rare important event;
- prefetch result incorrectly treated as authorized action.

## Deliverables from any adopting worker

A worker adopting a donor primitive must produce:

- exact target source SHA;
- donor mechanism ID (`VMD-D1` ... `VMD-D9`);
- target mapping and why it is dependency-correct;
- source diff;
- unit/component tests including negative cases;
- evidence scope statement;
- counterhypothesis;
- rollback/rebuild behavior;
- runtime receipt if runtime credit is claimed;
- explicit statement of what remains unproven.

## Current routing note

At the time of this donor run:
- VoiceMem public donor head observed: `d587d424a02727d9ff3ef6f8e672a39a19ce64a7`.
- Research Architect donor branch started from `c634c6f35dcad9e83eec8575b98467a262a2d671`.
- Frankenstein 2.0 main was observed later than the cached Architect G6 frontier and must be refreshed by every implementation worker before action.

This directive deliberately does not nominate a new F2 workpackage number. Workpackage ownership must be resolved from current granular F2 state to avoid duplicate mutation authority.
