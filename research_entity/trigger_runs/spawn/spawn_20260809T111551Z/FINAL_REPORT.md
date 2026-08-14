# SPAWN Research Run — ClayCode Atomic CAS / ABA Semantic Identity

**run_id:** `spawn_20260809T111551Z`  
**trigger:** `spawn`  
**origin branch:** `claycode`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**decision:** **RESEARCH DELTA MATERIALIZED · NO SCIENTIFIC PROMOTION · BASE GATE REMAINS NOT_PASS**

## 1. Stochastic selection

The branch was selected with `python.secrets.SystemRandom`: one-based ticket `33/100`, equivalent to canonical zero-based ticket `32`, selecting **ClayCode** in its 50% interval. Five evidence-derived microdirections were generated. The eligible microdirection draw selected **CC-SPAWN-C3-ATOMIC-CAS** with zero-based ticket `2`. No branch reroll and no microdirection reroll occurred.

Recent spawn/live-work duplication checks excluded async replay/cancellation, FRANK-loop lowering, callable identity, adaptive learner state, affine capability revocation, delta equivalence, effect-authority/foreign-effect closure, GWT adaptive recurrence, Emergenz lesion/rescue, ClayGraph reversal-aware binding and the live strict-LALR parser-conflict lane. A final live-head reread also saw new Unicode canonicalization, keyword partitioning, HTTP/SQLite, Harness visual-action and observer-effect spawn work; no duplicate CAS/ABA run appeared.

## 2. Research question

> What atomic compare-exchange contract is sufficient for ClayCode to preserve semantic state identity across lowering and replay when host CAS is atomic but the compared value may recur?

This is a BASE compiler/runtime question, not a request for new language surface syntax.

## 3. Existing-state fusion

Current ClayCode BASE explicitly requires executable async/concurrency/atomics/resource semantics. The current G9 candidate already separates semantic hashes, epochs, capabilities, effect intent and execution mechanics, but the inspected candidate does not yet define a general CAS identity/memory-order contract.

The immediately prior async-replay spawn established a useful separation between semantic task/effect identity and physical scheduling/retries, while explicitly leaving conflicting state accesses to synchronization/transaction semantics. Earlier ClayCode authority-budget work independently showed that merely monotone state is insufficient under concurrency: the reservation/consumption point must itself be atomic. Harness H-WP-01 now also distinguishes semantic architecture identity from exact source-contract identity.

Fusion result: ClayCode already has the surrounding identity/replay vocabulary. The missing question is narrower: **what exactly must an atomic state guard compare and what belongs to semantic identity versus execution trace?**

## 4. Primary-source triangulation

Primary/official specifications were used as architecture constraints, not as proof of ClayCode correctness:

- Rust `std::sync::atomic` exposes `Relaxed`, `Acquire`, `Release`, `AcqRel` and `SeqCst`; `compare_exchange` has separate success/failure ordering and explicitly warns that value equality may not imply identity, producing the ABA problem.
- LLVM `cmpxchg` is an atomic read-modify-write with explicit success/failure orderings; weak compare-exchange may fail spuriously and failure ordering has stricter constraints than successful read-modify-write ordering.
- ECMAScript 2026 defines SharedArrayBuffer atomic accesses as sequentially consistent, demonstrating that real backend atomic ordering surfaces are not identical.

Sources:
- https://doc.rust-lang.org/std/sync/atomic/enum.Ordering.html
- https://llvm.org/docs/LangRef.html#cmpxchg-instruction
- https://llvm.org/docs/Atomics.html
- https://tc39.es/ecma262/2026/multipage/memory-model.html

## 5. Executable discrimination

`EXPERIMENT_ATOMIC_CAS.py` combines three tests.

### 5.1 Deterministic ABA discriminator

For each of 200,000 cases, a stale reader observed `A@version0`. Another actor then executed one to four `A -> B -> A` cycles, returning the visible value to `A` but advancing the version. The stale actor then attempted to write `C`.

Results:

- raw value-only CAS stale accepts: **200,000 / 200,000**;
- version-bound `(value, version)` CAS stale accepts: **0 / 200,000**.

This falsifies the universal claim that atomic value comparison alone is a sufficient freshness/identity guard. The failure is not lack of atomicity: the compared representation returned to the same value while semantic state history/identity changed.

### 5.2 Weak-CAS retry identity discriminator

100,000 executions used one identical semantic CAS intent/outcome while injecting 0–15 modeled spurious physical failures before success.

Results:

- distinct semantic hashes: **1**;
- distinct physical execution-trace hashes: **16**.

Therefore physical retry count can vary without changing the default semantic operation identity. If a program intentionally observes retry count/timing, that observation must be an explicit semantic construct rather than leaking from backend retry mechanics.

### 5.3 Real cross-backend concurrent CAS counters

The hosted Linux x86_64 environment compiled a C11/GCC weak-CAS counter and executed a Node `SharedArrayBuffer` / `Atomics.compareExchange` counter. Each used 8 workers × 100,000 increments.

First captured run:

- C11/GCC: **800,000 / 800,000**, 408,145 failed/retry observations;
- Node Atomics: **800,000 / 800,000**, 345,461 failed/retry observations.

A later rerun again produced the exact 800,000 semantic result on both backends while retry counts changed substantially. This supports the semantic-vs-execution separation and preserves retry count as observational trace data.

## 6. Main result

The strongest supported narrow law is:

> **atomicity != freshness; value equality != semantic identity unless the type/resource contract proves it.**

For Clay semantic state whose identity can change while its visible value returns to a prior representation, a compare-exchange guard needs a version/epoch/identity component or an independently justified anti-ABA mechanism. Version tagging is the current simplest candidate, not the only theoretically possible defense.

A second law is:

> **semantic atomic operation identity != physical CAS attempt identity.**

Weak-CAS retries, worker/thread IDs and contention timing belong in execution trace. The stable semantic operation/outcome remains separately hashable and replay-comparable.

## 7. Candidate ClayCode IR/runtime contract

`ATOMIC_CAS_CONTRACT_CANDIDATE.clay` materializes an OPEN candidate with:

- `AtomicOrdering = RELAXED | ACQUIRE | RELEASE | ACQ_REL | SEQ_CST`;
- `AtomicIdentityMode = VALUE_ONLY | VERSION_BOUND`;
- stable `AtomicCell.cell_id` and `CompareExchangeIntent.op_id`;
- separate success and failure ordering;
- `VERSION_BOUND` expected `(value, version)` identity;
- checker rejection of release-style failure orderings;
- weak-CAS spurious failures recorded in execution trace, not default semantic hash;
- capability binding allowed but atomics never mint authority;
- **BASE portable candidate default = SeqCst**;
- weaker orderings remain explicit opt-ins requiring checker acceptance and backend support;
- `VALUE_ONLY` on semantic-state cells requires an `equality_is_identity` proof/contract.

No ClayCode surface-syntax change is proposed. Per the project invariant `less change, more compile`, this should first be implemented in canonical IR/typechecker/runtime metadata and lowered through existing syntax/constructs where possible.

## 8. Hypotheses and counterhypotheses

### Supported at proxy level

1. Value-only CAS is insufficient for versioned semantic-state identity under ABA.
2. Version/epoch binding rejects the tested stale ABA class.
3. Weak-CAS physical retries should not enter default semantic hash identity.

### Open

4. `SeqCst` is the best BASE-portable default while weaker orderings are explicit typed opt-ins.
5. Success/failure memory-order validity should be checked in ClayCode canonical semantics rather than silently inherited from the host.

### Refuted / not selected

- **“Atomicity alone prevents stale state transitions.”** Refuted for the versioned-identity class by the deterministic ABA counterexample.
- **“Every physical CAS retry is semantic state.”** Refuted as a default identity rule by stable semantic hashes across multiple retry traces and by cross-backend retry-count divergence.
- **“SeqCst only forever.”** Not selected; no cross-architecture production evidence justifies permanently forbidding weaker explicit ordering.
- **“Host order is an invisible implementation detail.”** Not selected; source models differ materially enough that silent inheritance would under-specify cross-backend behavior.

## 9. Research Center feedback

- **ClayCode:** implement candidate in canonical IR/typechecker/runtime before syntax change.
- **Harness:** add ABA schedule, weak-retry perturbation, semantic-vs-execution hash differential fixtures.
- **Frank:** compare-and-set style semantic state transitions should bind state version/epoch where values can recur; this grants Frank no self-Harness authority.
- **UnifiedDB:** semantic epoch is a natural candidate CAS identity component for optimistic publication/stale-write rejection.
- **ClayGraph:** graph mutations need version/identity-aware optimistic guards where relation/node representation can cycle back.
- **GWT/Emergenz:** separate contention/retry/state-version confounds from cognitive causal readouts.
- **Hyperposition:** preserve temporal/alternative identity across apparent value recurrence.
- **ClayResearch:** carry the mechanism distinction `atomicity != freshness` into whole-system convergence work.

## 10. Highest-information next experiment

Dynamic work item `WORK-SPAWN-CC-ATOMIC-CAS-UBUNTU-20260809` was created. It requests:

1. wait for / consume the current strict-LALR baseline without racing its grammar work;
2. implement the minimum atomic CAS IR/typechecker/runtime candidate;
3. execute ABA, invalid-order, retry-hash and concurrent-counter fixtures through the production ClayCode pipeline;
4. run on Andreas' Ubuntu developer target;
5. add at least one second backend differential;
6. record exact source/IR/compiler/backend hashes and mismatches;
7. keep capability/effect authority unchanged;
8. do not claim BASE PASS unless the independent compiler acceptance gate is actually satisfied.

## 11. Evidence boundary

This run does **not** prove the final ClayCode memory model, does not formally prove all linearizability properties, does not execute the production ClayCode frontend/compiler/runtime, and is not an Ubuntu target-host acceptance receipt. It establishes a reproducible counterexample against a too-weak value-only identity guard and supplies an implementable, falsifiable compiler/runtime candidate.

## 12. Durable artifacts

- `SPAWN_RECEIPT.json`
- `INTERCONNECT_MANIFEST.json`
- `HYPOTHESES.json`
- `EVIDENCE_MANIFEST.json`
- `EXPERIMENT_ATOMIC_CAS.py`
- `EXECUTION_RECEIPT.json`
- `ATOMIC_CAS_CONTRACT_CANDIDATE.clay`
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`
- `TOOL_EXECUTION_MANIFEST.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- dynamic work event `research_entity/state/work/events/20260809T1815p0700_spawn_cc_atomic_cas_ubuntu.json`

Two main-branch file writes were rejected with HTTP 409 while concurrent workers advanced `main`; no existing file was overwritten. The remaining run was materialized on the isolated append-only branch `spawn/spawn_20260809T111551Z-atomic-cas` before reintegration.

## Final decision

`RESEARCH_DELTA = MATERIALIZED`  
`SCIENTIFIC_PROMOTION = NONE`  
`CLAYCODE_SURFACE_CHANGE = NO`  
`ATOMICITY_LAW = ATOMICITY_DOES_NOT_IMPLY_FRESHNESS`  
`IDENTITY_DIRECTION = VERSION_OR_EQUIVALENT_ANTI_ABA_FOR_SEMANTIC_STATE`  
`RETRY_DIRECTION = PHYSICAL_ATTEMPTS_IN_EXECUTION_TRACE_NOT_DEFAULT_SEMANTIC_HASH`  
`ORDERING_DIRECTION = SEQCST_BASE_DEFAULT_CANDIDATE_WEAKER_EXPLICIT`  
`BASE_GATE = NOT_PASS`
