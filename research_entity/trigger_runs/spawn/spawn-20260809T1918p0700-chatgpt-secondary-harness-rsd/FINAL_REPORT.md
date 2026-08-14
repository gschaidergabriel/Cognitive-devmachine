# SPAWN FINAL REPORT — Receipt-Sealed Determinism Boundary

Run: `spawn-20260809T1918p0700-chatgpt-secondary-harness-rsd`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent at boot: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Origin branch: **Harness**  
Evidence status: **architecture/research delta supported by current repository evidence + external primary engineering precedent + local synthetic mechanism experiments; NOT live FRANK evidence and NOT Ubuntu acceptance**

## 1. Executive result

The highest-value spawned question was whether FRANK's current H1/H2 replay target should attempt to make the whole physical runtime deterministic, or instead preserve a deterministic semantic transition contract around explicitly receipted nondeterministic boundaries.

The result strongly favors the second architecture:

> **FRANK should use a Receipt-Sealed Determinism Envelope: every value that can change authoritative semantic state must either be deterministically derived from the frozen semantic state/input or be captured as a typed, provenance-bound receipt. Physical execution may remain nondeterministic. Semantic identity and execution-trace identity must remain distinct.**

This is a logical contract, not necessarily a new runtime process/module.

Four discriminators drive the conclusion:

1. In a 5,000-trace synthetic transition model, complete receipt sealing yielded **0/5,000 replay divergences**. Omitting only one semantically active nondeterminism dimension yielded near-universal divergence: clock 4,999/5,000; RNG 4,999/5,000; peer 5,000/5,000; tool 5,000/5,000; schedule 4,990/5,000.
2. In 10,000 pairs with identical semantic state/outcome but different retry/latency/worker metadata, semantic identity remained equal while a full execution-trace hash differed in **10,000/10,000** pairs. Therefore byte-identical trace equality is too strict for H1↔H2 semantic differential equivalence.
3. Crash injection around an idempotency-keyed external effect recovered to one effect + re-entry at every toy crash point tested. But a two-world counterexample shows that after a non-idempotent external effect may have committed before its local durable outcome receipt, local `retry` or `skip` alone cannot guarantee exactly once: the two worlds have the same local durable state but require opposite actions.
4. External systems engineering supports the structural separation: deterministic replay/simulation is powerful when nondeterminism is captured or controlled, but real thread/race testing remains a separate evidence surface. Deterministic simulation must not be mistaken for complete production-concurrency coverage.

The primary architecture delta is therefore not “make FRANK single-threaded.” It is:

`semantic transition determinism + receipt closure + explicit ambiguity + separate physical concurrency validation`.

## 2. Why this direction now

The weighted `spawn` draw selected Harness (`draw=0.539641`, Harness interval `[0.50,0.60)`). The current Harness workspace already has H-WP-02 State Ledger actively claimed, so duplicating that package would violate live-worker coordination. At the same time, the repository has just advanced the ClayCode typed core/native differential, integrated effect pipeline, strict authority checks and current-target H1 refreeze candidate.

The program remains at `BASE_CLAYCODE_RELEASE`; H1 is blocked on BASE. Therefore the useful Harness role right now is to generate executable counterexamples/contracts that sharpen BASE and later transfer directly into H1/H2 — not to claim H1 release progress prematurely.

Six candidate microdirections were screened:

- C1 Receipt-Sealed Determinism Boundary — selected;
- C2 mixed-epoch ActiveAssembly barrier;
- C3 observer-effect trace budget;
- C4 semantic-vs-execution identity split;
- C5 external commit ambiguity fence;
- C6 derived-topology replay commutation.

C1 had the highest immediate cross-stage information gain because it touches ClayCode WP04/06/07/09/11/13, current H1 Golden Trace design, GWT MeasurementReceipts, UnifiedDB event/effect lineage, ClayGraph dynamic causal traces and recovery semantics, while avoiding the active H-WP-02 implementation claim. C4 and C5 emerged as necessary subconstraints during C1 execution.

## 3. Current project constraints that shaped the research

The current H1 refreeze candidate already separates semantic slices for unified semantic state, dependency fabric, transient topology, ActiveAssembly compilation, GWT loop control, local 4B adapter, peer cognitive fabric, Needle, Retina/MVC, effect authority and trace/replay/recovery. It explicitly requires semantic/version/trace identity separation, Golden Traces, crash/restart, rollback and interventions.

The current ClayCode BASE direction already has an executable typed-effect pipeline with transitive effect/capability closure, a host-rooted Gateway, semantic/artifact/translation hashes and reference-vs-lowered trace comparison. Current CI guards explicitly reject missing capability and textual capability as authority while refusing to count the proxy as a whole-package or target acceptance PASS.

The selected spawn direction therefore does not invent a competing architecture. It closes a missing contract between those existing pieces: **what exactly must be frozen to make replay scientifically meaningful, and what must be allowed to vary without producing false divergence?**

## 4. Proposed Receipt-Sealed Determinism Envelope

Define an authoritative semantic transition conceptually as:

`S[t+1] = F(contract_version, S[t], external_input, receipt_bundle, intervention)`

where `F` is deterministic with respect to its declared semantic inputs.

`receipt_bundle` should be a typed union of only those exogenous/nondeterministic observations that can influence semantics. Candidate receipt families include:

- `ClockReceipt` — logical/physical time sample when time is semantically observed;
- `RandomDrawReceipt` — random choice actually consumed by a semantic branch;
- `ModelOutputReceipt` — exact model/output identity when model output is not regenerated during replay;
- `PeerOutcomeReceipt` — peer result + provider/node/request identity + freshness/conflict state;
- `ToolOutcomeReceipt` — tool result/error + request/idempotency identity;
- `VisualPerceptReceipt` — external visual/percept input identity when fixture regeneration is not deterministic;
- `CapabilityObservationReceipt` — current reachable capability/resource observation if it changes routing;
- `SchedulerDecisionReceipt` — only when ordering among non-commuting semantic operations is observable;
- `EffectOutcomeReceipt` — confirmed external effect outcome and its evidence basis;
- `ExternalStatusReceipt` — remote reconciliation/status query where effect commit status is ambiguous.

This must not degenerate into “log everything.” The boundary rule is:

> **If changing a value while all other frozen inputs remain fixed can change authoritative semantic state, the value is semantic input and must be deterministic or receipted. If it cannot, it belongs to execution telemetry/provenance, not the semantic equivalence hash.**

That rule itself is falsifiable with mutation tests.

## 5. Identity hierarchy

The research supports a hash/identity hierarchy rather than one universal hash:

1. `semantic_contract_hash` — ClayCode/architecture semantics and version;
2. `pre_state_hash` — canonical authoritative semantic state before transition;
3. `receipt_bundle_hash` — semantic exogenous input bundle;
4. `intervention_hash` — lesion/shuffle/parameter change identity;
5. `post_state_hash` — authoritative semantic state after transition;
6. `semantic_transition_hash` — normalized identity over 1–5;
7. `execution_trace_hash` — timing, retries, worker/process identity, physical scheduler diagnostics, resource counters and other execution evidence;
8. `provenance_chain_hash` — lineage over source/evidence/adapter/version identities where needed.

H1↔H2 PASS should normally compare normalized semantic transition identity and declared causal/readout equivalence, while execution trace identity is analyzed for performance, race, resource and implementation differences.

A field may move from execution-only to semantic if a counterexample proves it affects observable semantics. This is why the distinction must be contract-versioned rather than hardcoded forever.

## 6. External-effect crash boundary

The most important negative result concerns external effects.

Recommended logical state family:

`PROPOSED`
`-> VALIDATED`
`-> RESERVED`
`-> COMMIT_REQUESTED`
`-> OUTCOME_CONFIRMED`
`-> REENTERED`

with failure/ambiguity branches such as:

`DENIED`
`ABORTED`
`COMMIT_UNKNOWN`
`RECONCILING`
`ROLLED_BACK` where the external effect is actually reversible.

### The ambiguity window

Suppose local durable state is `RESERVED`. The process sends an external non-idempotent effect. The external system applies it. The process crashes before writing `OUTCOME_CONFIRMED` locally.

After restart, local durable state alone cannot distinguish:

- World A: request never applied externally;
- World B: request applied externally, outcome receipt lost locally.

If recovery blindly retries, World B duplicates. If recovery skips, World A loses the requested effect. Therefore exactly-once cannot be created merely by local confidence or replay logic.

Allowed resolution families are:

- external idempotency/deduplication keyed by stable `effect_id`;
- queryable remote commit/outcome status;
- stronger transactional coupling that actually removes the ambiguity;
- explicit `COMMIT_UNKNOWN` plus reconciliation/escalation when none of the above exists.

This should become a typed adapter property, not an informal comment. For every external adapter the runtime should know at least:

`idempotency = NONE | KEYED_DEDUPE | NATURAL_IDEMPOTENT`

`outcome_query = NONE | QUERYABLE`

`transaction_coupling = NONE | LOCAL_ATOMIC | DISTRIBUTED/PROVIDER_SPECIFIC`

`ambiguous_recovery_policy = RECONCILE | ESCALATE | SAFE_RETRY | SAFE_SKIP` only when the preceding properties justify it.

Never infer `OUTCOME_CONFIRMED` from `COMMIT_REQUESTED`.

## 7. Concurrency and scheduling

The result does **not** justify forcing global deterministic scheduling in production.

Instead:

- make transactions/state publication deterministic at the semantic contract level;
- use epochs/MVCC/serialized commit identity where appropriate;
- record a scheduler/conflict-winner receipt only where ordering of non-commuting operations changes semantics;
- allow timing, retry count, thread identity and physical interleaving to remain execution telemetry when they do not affect declared semantics;
- separately run real multithread/race/fault tests on Ubuntu.

This creates two complementary test worlds:

### Deterministic semantic oracle
Best for exact replay, mutation, ablation, lesion/rescue, H1↔H2 differential and ex-post instrumentation.

### Physical concurrency oracle
Best for data races, memory ordering, deadlocks/livelocks, starvation, unsafe FFI behavior, timing-dependent resource failures and hidden ambient state.

A PASS requires the correct oracle for the claim. A deterministic replay PASS cannot close a real-concurrency package by itself.

## 8. GWT and Emergence implications

The current GWT contract already requires each material measurement hook to emit deterministic or explicitly nondeterministic MeasurementReceipts bound to state epoch, episode id, intervention id, estimator/version, source hashes and result hash.

Receipt closure sharpens the causal experiment design:

- truthful re-entry vs shuffled re-entry must use the same exogenous receipt bundle where meaningful;
- receiver lesion vs baseline must not accidentally use a different peer/tool/model sample unless that difference is the intervention;
- model-output-frozen architecture ablations require exact model-output receipt identity;
- architecture-frozen model-output swaps require exact architecture/state/other-receipt identity;
- successful replay proves experimental control/reconstructability, **not** causal emergence.

Therefore the determinism envelope is measurement infrastructure. Emergence still requires interaction, lesion, rescue, shuffle/null, directed-flow and transfer evidence.

## 9. ClayGraph implications

Dynamic Run ClayGraph should bind:

- semantic pre/post state hashes;
- receipt ids/hashes for active causal inputs;
- edge activation/order when semantic;
- intervention identity;
- GWT delivery/reconstruction/uptake/causal-use/re-entry stages;
- effect-authority path and outcome identity.

But H1 and H2 dynamic graphs should not be required to be byte-identical if their execution telemetry differs. Differential should compare graph semantics under a declared normalization map.

This also helps H3: if final H3 has no mandatory persistent ClayGraph database, an H3 derived topology can still be tested by taking the same canonical state + receipt bundle and checking whether the derived semantic graph/causal path commutes with the H1/H2 oracle.

## 10. UnifiedDB implications

UnifiedDB should carry the authoritative event/effect lineage needed to reconstruct semantic transitions, but it should not conflate canonical semantic state with every derived telemetry field.

Recommended separation:

- canonical semantic event/state spine;
- typed receipt objects or references with immutable identity;
- effect lifecycle/outbox/reconciliation state;
- derived graph/vector/FTS/activation views;
- execution telemetry as auditable evidence that can be retained/queryable without contaminating semantic equality.

The physical storage decision remains open. Receipt sealing does not imply all bytes must live in one physical DB.

## 11. ClayCode implications

The most useful immediate BASE feedback is not a new surface syntax keyword. It is semantic/runtime capability:

- versioned receipt identity;
- typed effect outcome and ambiguity states;
- semantic hash normalization rules;
- execution trace hash as distinct evidence identity;
- adapter traits for idempotency/queryability/coupling;
- deterministic evaluator/lowering agreement over frozen receipt fixtures;
- race/replay primitives sufficient for the Ubuntu application suite and FRANK handoff.

This conforms to the current `less change, more compile` rule. Only an executable counterexample should force new syntax.

## 12. Experiments executed

### RSD-E1 — nondeterminism omission mutation
5,000 traces × 12 steps. Five external dimensions influence semantics. Full sealing: 0 divergent traces. Omit one dimension: 4,990–5,000 divergent traces depending on dimension. Omit all: 5,000/5,000 divergent.

Interpretation: validates the *test shape* and strongly rejects incomplete receipt closure in the toy system. The intentionally sensitivity-rich transition function means the exact rates must not be generalized to FRANK.

### RSD-E2 — semantic vs execution identity
10,000 pairs with identical semantic state/outcome and varying retries/latency/worker. Semantic identity: 0 divergences. Full trace identity: 10,000 divergences.

Interpretation: shows how a full-trace semantic oracle generates false positives by construction.

### RSD-E3 — idempotent crash recovery
Toy effect state machine with stable `effect_id` dedupe. Tested crashes before external apply, after external apply before local outcome, and after local outcome before re-entry. All recovered to one external effect and completed re-entry.

Interpretation: supports idempotency-keyed retry as one valid recovery mechanism in the toy model.

### RSD-E4 — non-idempotent ambiguity counterexample
Exhaustive two-world construction with identical local post-crash state. `retry` fails one world by duplication; `skip` fails the other by omission.

Interpretation: local replay alone cannot manufacture knowledge of a remote side effect.

## 13. Negative results preserved

1. **Global deterministic runtime is NOT selected.** It risks hiding real races and imposing unnecessary serialization.
2. **One universal trace hash is NOT selected.** It creates false H1/H2 divergence from execution-only differences.
3. **Local journaling alone does NOT establish exactly-once external effects.** Ambiguous external commit needs stronger adapter semantics or an explicit unknown state.
4. **Replay success is NOT emergence evidence.** Intervention remains mandatory for causal claims.
5. **Current synthetic tests are NOT H1/H2/BASE acceptance.** Ubuntu target execution and actual FRANK/ClayCode integration remain required.

## 14. Proposed Golden Trace / test family additions

- `RSD-01 RECEIPT_CLOSURE_OMISSION_MUTATION` — remove each receipt class one at a time; expected mismatch/rejection when semantically necessary.
- `RSD-02 SEMANTIC_FIELD_CLASSIFICATION` — mutate declared execution-only fields; post-state must remain identical or field is reclassified semantic.
- `RSD-03 DUAL_HASH_DIFFERENTIAL` — H1/H2 identical semantic transition with allowed execution metadata divergence.
- `RSD-04 EFFECT_CRASH_WINDOW` — crash at every reserve/commit/outcome/re-entry boundary per adapter class.
- `RSD-05 AMBIGUOUS_REMOTE_COMMIT` — prove `COMMIT_UNKNOWN`/reconciliation rather than fabricated certainty.
- `RSD-06 SCHEDULER_COMMUTATION` — randomize order for operations declared commuting; preserve semantics; record order when non-commuting.
- `RSD-07 REAL_MULTITHREAD_RACE` — Ubuntu stress/TSAN-or-equivalent where available; separate from deterministic oracle.
- `RSD-08 OBSERVER_PERTURBATION` — no/low/full instrumentation paired traces to quantify measurement overhead/effect.
- `RSD-09 H1_H2_SAME_RECEIPT_REPLAY` — frozen H1 trace bundle replayed through ClayCode H2; classify every divergence.
- `RSD-10 OVERHEAD` — p50/p95/p99 latency, bytes/receipt, trace amplification, CPU, RAM, storage, and recovery time.

## 15. Architecture decision candidate

**Candidate: RSD-v1**

Adopt as a research/implementation constraint, not as a stage PASS:

1. `semantic nondeterminism -> deterministic derivation OR typed receipt`;
2. `semantic_transition_hash != execution_trace_hash`;
3. `external commit uncertainty is representable as UNKNOWN, never guessed`;
4. `idempotency/queryability are adapter capabilities with receipts`;
5. `deterministic replay + physical concurrency testing are both required`;
6. `GWT/emergence counterfactuals reuse frozen exogenous receipts`;
7. `H1/H2 differential compares normalized semantic causality, not byte-identical physical execution`.

This candidate should be falsified on Ubuntu before hard promotion.

## 16. Immediate implementation path

A dynamic work event was created at:

`research_entity/state/work/events/20260809T1918p0700_chatgpt_secondary_spawn_rsd_ubuntu.json`

It deliberately does not jump ahead of `BASE_CLAYCODE_RELEASE`. It asks the local build organ to integrate the smallest receipt/runtime semantics into current BASE work, execute omission/crash/hash/race/overhead tests on the Ubuntu developer target, and later reuse the exact receipt oracle for H1/H2 Golden Trace differential.

The highest-information next result is not another design document. It is an Ubuntu receipt showing whether the current ClayCode production path can represent and execute RSD-v1 without a semantic escape hatch and without unacceptable overhead.

## 17. Final synthesis

The spawned research changes the recommended shape of FRANK's replay/recovery boundary in a precise way.

The system should not strive for a physically deterministic organism. Frank's eventual one-binary runtime can remain concurrent, asynchronous and adaptive. What must be deterministic is the **meaning of a frozen semantic episode under a frozen set of exogenous receipts and interventions**.

That makes replay useful for science and implementation transfer without pretending that the world, the OS, the model, peers, tools or the scheduler are deterministic. It also forces uncertainty to remain explicit at the hardest boundary: external side effects whose outcomes cannot be reconstructed from local state.

The deepest invariant from this run is therefore:

`semantic determinism != physical determinism`

and

`unknown external outcome != failure != success`.

Those two distinctions should become first-class in the ClayCode/Harness handoff.
