# Harness Trigger Run — H-WP-11 TurnTraceEnvelope v1

Run: `harness-20260809T1656p0700-trace-replay-v1`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Harness package: `H-WP-11-TRACE-REPLAY`  
Promotion: **NONE**  
H1 gate advancement: **NONE**

## Executive result

This run converted the previously researched Trace/Replay idea into an executable BASE-compatible Harness foundation:

`research_entity/harness/trace_replay_v1.py`

The validator treats a FRANK turn as a **causal graph over explicit loop/recurrence episodes and state/graph epochs**, not as a falsely acyclic pipeline. It supplies a representation-normalized differential oracle intended for later H1 Reference Harness -> H2 ClayCode Harness -> H3 one-module comparisons.

Executed result on the hosted Linux sandbox:
- embedded self-test: **13/13 PASS**;
- targeted mutation/property sweep: **1400/1400 violations detected**;
- nested recurrence stress: **64-level re-entry PASS**;
- cross-implementation trace/stage ID normalization: **EQUIVALENT** for semantically identical traces;
- Python compile: **PASS**.

Evidence class: `LOCAL_SYNTHETIC_EXECUTION` only. This is not live Frank, not Andreas' Ubuntu target, and not H1 PASS.

## Why this package was selected

At run start `HARNESS_WORKSPACE.json` showed:
- H-WP-02 State/Ledger already CLAIMED by another/current worker;
- H-WP-11 Trace/Replay OPEN.

The run therefore avoided duplication and claimed H-WP-11.

Current program stage is still BASE ClayCode. The shared program explicitly allows Harness to build architecture-generic host foundations during BASE but forbids declaring H1 complete before the ClayCode release gate passes. This run stays within that boundary.

## Full-mesh integration

`INTERCONNECT_MANIFEST.json` covers all nine current registered branches and recent/live material.

Key retained constraints:
- **Clayresearch / Safe-Effect:** loop continuation authority != effect authority; recurrence cannot widen capabilities by itself.
- **FRANK:** P9 causal observability/replay, state/graph epochs, crash/restart/idempotency, functional distinctions survive physical consolidation.
- **GWT:** addressability != delivery != reconstruction != uptake != causal use != outcome != re-entry.
- **Emergenz:** stage-orthogonal intervention, mechanistic rescue, causal-basis validity; replay validity is not emergence evidence.
- **ClayCode:** recurrent loop/epoch semantics, explicit lowering legality, BASE remains NOT_PASS.
- **Hyperposition:** semantic/active/coordination/physical topologies remain distinct; gain/delay/timescale interventions.
- **ClayGraph:** retrieval != admissibility != consequential use; dynamic Run ClayGraph evidence required.
- **UnifiedDB:** semantic/logical/physical unification remain distinct; exact event/state history must be replayable.
- **Harness:** Golden Traces, counterfactual replay, ablation, recovery and differential localization remain release obligations.

A newer open FRANK architecture-lineage fusion overlay was explicitly assimilated. It is research input, not canonical promotion.

## Executable design

### 1. Loop-aware causal identity

The envelope contains explicit `loop_episodes` with:
- loop id;
- parent loop id;
- recurrence index;
- timescale;
- budgets;
- status.

Stage order is recorded as **observation order** while causal-parent edges preserve dependency. Cyclic FRANK dynamics therefore remain representable without pretending the architecture is a DAG.

### 2. State and graph basis

Every trace binds:
- source repository head;
- architecture freeze hash;
- semantic contract hash;
- pre/post semantic epoch + root hash;
- pre/post ClayGraph epoch + root hash;
- dynamic Run ClayGraph delta hash.

### 3. GWT causal closure

Per receiver the validator keeps separately addressable:

`addressable -> delivered -> reconstructed -> uptake -> causal_use -> outcome -> reentry`

A downstream stage cannot be true if an upstream prerequisite is not true, and every true causal-stage assertion requires a receipt reference.

### 4. Memory-use separation

The validator keeps:

`retrieved != admissibility != consequential_use`

Consequential use is rejected unless the memory is retrieved and explicitly `ADMIT` or `BYPASS_EXACT` with a receipt.

### 5. Four topology identities

The envelope keeps separate hashes for:
- semantic topology;
- active topology;
- coordination/invariant topology;
- physical topology.

This prevents later one-module consolidation from erasing the functional topology needed for causal tests.

### 6. Recurrence-aware Safe-Effect invariant

Each effect attempt may record loop id, attempt count, retry reason, cumulative resource cost and capability set before/after.

Hard validator rule:

`capabilities_after ⊆ capabilities_before`

unless an explicit **external authorization receipt** exists.

A repeated denial must remain visible; recurrence is allowed to reconsider intent but not mint permission.

### 7. Visual/adaptive-learning authority boundary

Visual familiarity/classifier state remains representable but the validator rejects any trace claiming the visual model itself granted execution authority. Learner promotion records can bind candidate/previous version, shadow-evaluation, atomic-promotion and rollback identities.

### 8. Atomic status snapshot

One immutable response-boundary `StatusSnapshot` is bound to the exact final semantic/graph basis and source repo head. It includes auditable node-group multiplicity and its own content hash.

This directly addresses the previously found status split-basis risk without modifying Frank's live status renderer in this run.

### 9. Replay classes

The reference distinguishes:
- `EXACT_DETERMINISTIC`;
- `DETERMINISTIC_UNDER_ENV_FINGERPRINT`;
- `RECEIPT_BOUNDARY_NONDETERMINISTIC`;
- `LIVE_EXTERNAL_NONREPLAYABLE_WITH_RECORDED_OUTCOME`.

Deterministic claims require an environment fingerprint. Exact deterministic traces cannot simultaneously carry unresolved nondeterministic boundaries.

### 10. Representation-normalized differential

`semantic_projection()` removes implementation-only identities such as trace/stage IDs and the harness build hash while preserving semantic stage hashes, causal parent sequence, loop identity, GWT state, memory-use decisions, topology, effect-capability state, state/graph basis and dynamic graph delta.

`compare_traces()` returns:
- `EQUIVALENT`, or
- `DIVERGENT` with the **first semantic divergence path**.

This is the core later H1/H2/H3 oracle behavior.

## Execution evidence

See `EXECUTION_RECEIPT.json`.

### Self-test

13/13 passed, including:
- GWT causal-chain violation rejection;
- future causal-parent rejection;
- status/final-epoch mismatch rejection;
- deterministic replay without environment fingerprint rejection;
- quarantined memory consequential-use rejection;
- visual-authority rejection;
- capability widening without external authorization rejection;
- repeated denial with fixed authority accepted;
- nested recurrence accepted;
- first semantic divergence localized.

### Mutation/property sweep

1400 constructed violations were injected across:
- GWT causal prerequisite violations;
- unauthorized effect-capability expansion.

Detected: 1400/1400.

This is intentionally a targeted mutation sweep, not proof of complete validator correctness.

### Deep recurrence

A 64-level nested re-entry structure passed validation, showing that the contract does not reject recurrence merely because it is deep/cyclic.

### Differential normalization

A candidate with different trace id, stage ids and harness build hash but identical normalized semantics compared `EQUIVALENT`.

## External engineering triangulation

Evidence classes remain separate from project-internal evidence.

### FoundationDB

Primary FoundationDB debugging guidance says deterministic simulation failures may depend on OS type and build environment, not seed alone. This supports including an environment/toolchain fingerprint in deterministic replay identity.

Source: `https://github.com/apple/foundationdb/wiki/Debugging-in-FDB`

### TigerBeetle

TigerBeetle documents both deterministic simulation testing and an intentionally nondeterministic full-system harness, Vortex, as defense-in-depth. Its simulator also separates safety and liveness modes rather than assuming one fault distribution covers both.

Sources:
- `https://tigerbeetle.com/blog/2023-07-06-simulation-testing-for-liveness/`
- `https://tigerbeetle.com/blog/2025-02-13-a-descent-into-the-vortex/`

FRANK implication: after the deterministic H1 replay lane exists, add an outside-in compiled/process fault lane and measure whether it finds distinct bug classes.

### OpenTelemetry

OpenTelemetry's tracing specification provides immutable trace/span context, parent relationships and links that propagate across process boundaries. This is a useful observability analogue for FRANK cross-node causal identity.

It is **not** an authority or truth model. FRANK trace context must remain non-authoritative metadata tied to canonical semantic receipts.

Source: `https://opentelemetry.io/docs/specs/otel/trace/api/`

## Hypotheses and counterhypotheses

See `HYPOTHESES.json`.

Strongest local result:
- `H-TR-004`: recurrence-aware capability non-expansion is executable and all 200 generated capability-expansion mutations in the targeted sweep were rejected.

Strongest architecture result:
- `H-TR-001`: semantic projection can ignore implementation identifiers while still localizing an actual semantic hash divergence in the synthetic fixtures.

Main counterrisk:
- a single envelope may become too large. The intended mitigation is content-addressed payloads/refs, then measurement of bytes/turn, latency and recovery cost rather than deleting semantic fields preemptively.

## Negative results

See `NEGATIVE_RESULTS.md`.

Important boundaries:
- reviewed current Frank surfaces do not yet establish one complete H-WP-11 replay oracle;
- this does not prove no replay code exists elsewhere;
- final-state equality alone is not accepted as the sole differential criterion;
- seed-only replay identity is not assumed sufficient;
- deterministic simulation alone is not yet accepted as complete fault coverage;
- BASE is still active, so H1 remains blocked.

## Branch feedback

See `BRANCH_FEEDBACK_MANIFEST.json`.

Material deltas were returned to every registered branch. No branch result was promoted merely because the Harness executable inherited the same contract.

## Architecture decision

**KEEP and extend TurnTraceEnvelope v1 as the H-WP-11 reference oracle foundation.**

Do not integrate it into live Frank from this hosted worker. The next implementation step belongs to the independent Research Entity/installer execution path on the frozen H1 target after BASE PASS.

## Highest-information next tests

1. **ClayCode representability test during BASE**  
   Parse/type/effect/canonicalize/lower a trace validation fixture. Fail if telemetry/readout values can become authority tokens or if recurrent/epoch semantics require opaque host escape hatches.

2. **H1 target-host adapter after BASE PASS**  
   Map existing Frank `prompt_cycles`, state epochs, query/injection receipts, GWT receipts, effects/outcomes, snapshots and ClayGraph deltas into TurnTraceEnvelope without semantic redesign.

3. **Golden replay roundtrip**  
   Freeze external inputs/model outputs/seeds/environment/external receipts and reproduce state + graph roots. Report first divergent stage on failure.

4. **Counterfactual replay**  
   Freeze model output while lesioning graph/GWT/re-entry/effect boundaries one at a time.

5. **Outside-in fault lane**  
   Run compiled/process-level crash, restart, network, file/state and partial-commit faults; compare bug classes with deterministic simulation.

6. **Status atomization regression**  
   Demonstrate that one snapshot cannot mix status fields from different semantic/graph basis epochs.

7. **Recurrence/authority test**  
   Replay compromised/stale intents at recurrence budgets {1,2,4,8}; authority must never increase absent an external authorization event.

## Completion assessment

Current run deliverables: **complete**.

H-WP-11 overall: **OPEN / FOUNDATION_IMPLEMENTED**, because live H1 integration, Golden traces, target-host replay, checkpoint/module/counterfactual replay and dynamic Run ClayGraph generation still remain.

No current stage or release gate advances from this run.
