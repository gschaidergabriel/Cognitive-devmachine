# ATOMIC 20260817T1203P0700 — MCA-001

## Status

`MCA-001 / Monotone Causal Aperture` is a **synthetically tested research possibility**, not accepted ClayVerse architecture and not product PASS.

Canonical product authority at run start was current `CLAYVERSE_SINGLE_CONTAINER`: one OCI/Docker-compatible ClayVerse image from `the artefact/`, UnifiedDB as sole durable state/world/data/wiki authority, ClayGraph derived/rebuildable, Claude Code as runtime cognition, Clerk as web auth, and EntityOS only as internal execution/security/runtime substrate where useful.

Run base research SHA: `c01a23a0ba69c4c81edb6c171fc908744c64c1fb`.

## Fusion 1 — observed current mechanism gap

Current `TurnLifecycle.begin()` records a session generation and assembles bounded context from own turns, exact resource-ref collisions in the other session, and durable memory. The resource-ref extractor is intentionally conservative and lexical. Current effect execution rechecks session generation and uses a global label-independent automatic lease for `entityos.exec`, with verification/re-entry through the causal journal.

That is strong for admitted external effects, but it does not provide a semantic rule for which **durable knowledge-state updates** may safely commute across Gabriel/Andreas sessions and which must revalidate/serialize. A session generation is too coarse to express this distinction; resource refs are collision hints rather than semantic read predicates.

## Hypothesis field

The required 12-candidate field is machine-readable at `hypotheses/HYPOTHESIS_FIELD.json` and spans deletion, information/compression, SSI-style causal dependency graphs, pessimistic resource locking, temporal epochs, monotonic logic, claim-lattice topology, speculation, incremental computation, two-phase resolution, absence capabilities, and dual-perspective contest preservation.

`CCC-001 / Causal Context Capsule` was the first strong candidate. A deterministic synthetic experiment found that exact positive+negative context witnesses could eliminate modeled stale admissions while broad session-generation/resource baselines either missed cross-session semantic conflicts or over-aborted. It was rejected as the radical ATOMIC selection because its mechanism collapses strongly to ordinary optimistic/predicate validation and SSI-family prior art. It remains a strong conventional baseline.

## Fresh external collision / destruction search

Primary/authoritative prior art materially narrows the novelty claim:

- Kung & Robinson, *On Optimistic Methods for Concurrency Control* (ACM TODS, 1981): validate optimistic transactions rather than always locking. This strongly collides with CCC-001.
- PostgreSQL Serializable Snapshot Isolation documentation and Ports/Grittner lineage: rw-conflict/dangerous-structure monitoring can reject anomaly-producing executions without blocking all reads/writes; false-positive aborts remain possible. This collides with turn-level dependency-graph candidates.
- Bailis et al., *Coordination Avoidance in Database Systems* (arXiv:1402.2237 / PVLDB): invariant confluence formalizes when application operations can safely execute without coordination. This strongly collides with any broad claim that MCA invented selective coordination.
- Hellerstein & Alvaro, *Keeping CALM* (arXiv:1901.01930): monotonic logic characterizes coordination-free consistency in the CALM setting. This is the closest conceptual ancestor of MCA's polarity split.
- Laddad et al., *Keep CALM and CRDT On* (arXiv:2210.12605): CRDT update safety does not make all observations safe; monotonic query reasoning matters. This destroys any naive claim that append-only data alone closes the problem.
- Hellerstein, *The Coordination Criterion* (arXiv:2602.09435): a 2026 generalization states the coordination boundary over history extension and observable outcomes. This further reduces novelty at the theory level.

Therefore novelty status is **NOVEL_COMBINATION_CANDIDATE**, never WORLD_FIRST. The possible new value is the ClayVerse-specific composition: explicit ClayCode operation polarity + contradiction-preserving canonical claim atoms + an antimonotone aperture + current causal/session/context/lease receipts + the already-strict EntityOS effect boundary, all inside one UnifiedDB authority.

## Fusion 2 — selected candidate

### MCA-001: Monotone Causal Aperture

ClayCode semantic source: `candidate/CANDIDATE_MCA_001.clay`.

Core rule:

- `MONOTONE_APPEND`: immutable claim/evidence addition that preserves every prior claim and contradiction. It may commute with another monotone append to the same subject.
- `NONMONOTONE_RESOLVE`: collapses alternatives, selects a winner, assumes uniqueness or relies on absence. It must cross the aperture.
- `RETRACT`: removes/invalidates prior canonical information. It must cross the aperture.
- `EXTERNAL_EFFECT`: always crosses the existing ClayVerse EffectGate + canonical `effect:entityos.exec` lease; MCA cannot weaken or bypass it.
- `UNKNOWN`: fail closed into the aperture. No inference or LLM may silently relabel unknown behavior as monotone.

Contradictions become explicit `ContestEdge`s between immutable `ClaimAtom`s. A single-winner/resolved representation is a derived projection, not an authority competing with UnifiedDB.

## Executable discriminator

Deterministic reference script: `experiments/mca_001_sim.py`.

Execution surface: OpenAI isolated container, non-VPS. This is a reference/synthetic mechanism experiment only; it is **not** exact ClayVerse runtime or OCI evidence. A direct Vercel Sandbox start/run interface was not exposed in the active tool surface for this run.

Script SHA-256: `f5561e7bd11de80b0325e1a200d3e863129ada617f40ec033a5498c2cc4ce86f`.

Raw observed result SHA-256: `5f6ba359d3d7275fd90f554ee2389a9b74e6f71713589a5117d973c84d542a5c`.

Seeds: 20. Pairs/seed: 10,000. Total concurrent operation pairs: 200,000.

Synthetic workload:
- 64 subjects;
- 35% deliberate same-subject pressure;
- 25% same-session probability;
- operation mix: 65% `claim_append`, 10% `retract`, 10% `resolve_single`, 10% `external_effect`, 5% `unknown`;
- model safety truth: same subject + at least one nonmonotone operation requires coordination.

### Result

| Baseline / candidate | Coordination rate | Unsafe violation rate | False coordination on safe pairs |
|---|---:|---:|---:|
| no coordination | 0.000000 | 1.000000 | 0.000000 |
| session generation proxy | 0.250285 | 0.747853 | 0.249795 |
| lock same resource | 0.361070 | 0.000000 | 0.192791 |
| OCC/context witness proxy | 0.361070 | 0.000000 | 0.192791 |
| **MCA typed aperture** | **0.208470** | **0.000000** | **0.000000** |
| randomized same-budget control | 0.202695 | 0.798388 | 0.202980 |

Within this constructed model, MCA coordinates 20.847% of pairs instead of 36.107% for same-resource/OCC-style coordination while producing zero modeled unsafe admissions. This result is not independent validation because the safety oracle is deliberately defined around operation monotonicity; it tests internal consequences and implementation sensitivity, not real-world truth.

### Adversarial ablation

Exactly one bounded classifier-corruption ablation was run: independently misclassify 1% of nonmonotone operations as monotone.

Result: coordination rate 20.6715%, but unsafe violation rate immediately rises to **0.8418%**. This supports a hard design requirement: polarity must be type-/contract-derived and unknown must fail closed. A probabilistic LLM classifier is not an acceptable authority boundary for MCA.

## Counter-realities that survive

1. **MCA is only CALM/I-confluence renamed.** Substantial theory-level collision is true. Promotion requires ClayVerse-specific measurable benefit over a conventional exact context-witness/OCC design.
2. **Natural-language knowledge operations cannot be typed safely enough.** If important resolve/retract/absence semantics can escape classification, MCA must be rejected.
3. **Claim accumulation explodes state size.** Contradiction preservation may trade coordination cost for write/storage/retrieval amplification.
4. **Resolution still needs exact context predicates.** MCA does not eliminate CCC/OCC; it may only reduce the operations that need those mechanisms.
5. **SQLite serialization already makes this unnecessary.** The candidate must show value at the application-semantic boundary, not merely reproduce database transaction safety.
6. **Derived resolved views become a shadow authority.** Any mutable authoritative winner table would violate the candidate and current product law.

## Strongest next falsifier

Do **not** integrate MCA into `the artefact/` yet.

First build an exact-current-head, isolated dual-session replay harness over real `UnifiedDB` operations that:

1. defines a small closed typed set of candidate durable operations;
2. mechanically proves/validates which operations are append-preserving versus destructive/absence-dependent;
3. runs contradictory Gabriel/Andreas claim appends concurrently and proves both claims + contest provenance survive restart;
4. runs resolve/retract with stale context and proves fail-closed behavior;
5. attempts `UNKNOWN -> MONOTONE_APPEND` and proves rejection;
6. attempts external effect execution and proves the existing global EntityOS effect lease/generation/journal path remains mandatory;
7. compares MCA against full same-resource lease and exact context-witness/OCC baselines for correctness, p50/p95 latency, retries, writes, DB growth and recovery integrity.

If MCA cannot beat the conventional context-witness baseline without weakening safety or state bounds, outcome = `NO_GAIN`/`REJECT`.

## Outcome

`MCA-001 = TESTED_SYNTHETIC / PROMISING_RESEARCH_POSSIBILITY`.

No architecture promotion. No effect-authority widening. No training authorization. No VPS test. No whole ClayVerse PASS.
