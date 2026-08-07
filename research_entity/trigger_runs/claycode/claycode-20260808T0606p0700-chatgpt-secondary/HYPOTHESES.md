# ClayCode CC8 Hypothesis Matrix

**run_id:** `claycode-20260808T0606p0700-chatgpt-secondary`  
**actor:** `chatgpt-secondary`  
**canonical parent:** r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Generation 1 — after mesh Fusion 1, before CC8 external fusion

| ID | Falsifiable hypothesis | Counterprediction / falsifier | Highest-information test |
|---|---|---|---|
| H-CC8-001 | CC7 object-version read/write witnesses are insufficient when semantic reads are predicates over absent or future objects. | Object-version OCC catches all invariant-relevant races in predicate workloads. | Concurrent create-if-absent/uniqueness phantom test. |
| H-CC8-002 | Predicate/range/invariant epochs can preserve scoped freshness without reverting to a whole-state root for every conflict. | Predicate witnesses either miss conflicts or reject as broadly as the global root. | Compare object-only, predicate-scoped and global-root validation. |
| H-CC8-003 | Trusted static operation semantics should compute a conservative dependency/effect upper bound. | Runtime observation alone is equally safe under reflection/dynamic access. | Inject accesses outside the declared envelope. |
| H-CC8-004 | A fully interposed runtime access trace can safely narrow commit revalidation below the static upper bound when the trace is proven to be a subset of it. | Narrowing produces misses even with complete interposition and a sound envelope. | Static-envelope vs observed-trace concurrency fuzz. |
| H-CC8-005 | Runtime traces must include semantic dependency classes beyond object reads: predicates, invariants, temporal/environment values and capabilities. | Object access trace alone predicts all stale/invalid proposals. | Volatile/regime dependency counterexample. |
| H-CC8-006 | Unknown reflection/FFI/dynamic dispatch must escalate to a broader conservative envelope unless the runtime can interpose it completely. | Unbounded dynamic access can be safely treated as ordinary scoped access. | Adversarial escape fuzz. |
| H-CC8-007 | `state_root` should remain basis-snapshot identity/provenance while commit freshness is evaluated from typed dependency witnesses. | Whole-state root is required as the only safe freshness mechanism. | Replay independent churn against scoped witnesses. |
| H-CC8-008 | Operation semantic version/hash belongs in every effectful TCC because unchanged syntax can acquire changed behavior after runtime evolution. | Runtime op upgrades cannot change proposal meaning in practice. | Replay old capsules across intentionally changed op semantics. |
| H-CC8-009 | `ADD/RETRACT/REPLACE/COMPENSATE` are semantic delta kinds independent of whether coordination or authority is required. | Delta polarity predicts coordination/authority class by itself. | Cross product of delta kinds × invariants × capabilities. |
| H-CC8-010 | Coordination scope must be derived from invariant interference, not merely read/write overlap. | Exact R/W overlap is sufficient for all declared FRANK invariants. | N-ary capacity/uniqueness invariant fuzz. |
| H-CC8-011 | GWT workspace freshness can be represented as typed channel-revision/regime dependencies rather than one workspace-global timestamp/root. | Per-channel scope misses causal stale reads or offers no rejection reduction. | FRANK shadow instrumentation of workspace reads. |
| H-CC8-012 | GWT re-entry validity needs episode/source-state/regime/value-at-use witnesses rather than fixed TTL. | Fixed TTL predicts safe/useful re-entry equally well. | Delay × regime persistence factorial on synchronized traces. |
| H-CC8-013 | Model-visible ClayCode projections should omit derivable safety metadata to reduce reader burden while the runtime reconstructs the same trusted TCC. | Model must emit dependency/effect metadata for correct execution. | Reader factorial with hidden vs visible derived metadata. |
| H-CC8-014 | Capability handles can remain opaque model-visible references while authority resolution remains host-side. | Model needs underlying credentials/secrets to use capabilities reliably. | Handle-only tool-use task with external gateway. |
| H-CC8-015 | Irreversible effects require pre-effect interposition; post-hoc access logging cannot be an authority boundary. | Post-hoc monitoring plus rollback is equivalent for external effects. | Unauthorized network/effect injection. |
| H-CC8-016 | State mutation plus external-effect intent should be committed atomically, then relayed idempotently after commit. | Direct dual-write is equally reliable under crash/retry. | Crash-at-each-boundary outbox factorial. |
| H-CC8-017 | A small trusted semantic kernel/registry can support reader-specific text/binary projections without making projection syntax authoritative. | Projection parser semantics necessarily become the runtime trust root. | Multi-projection semantic-hash roundtrip + mutation fuzz. |
| H-CC8-018 | Receipts used by GWT/emergence analysis should reuse the same causal episode/effect/outcome IDs but their presence must not count as independent evidence of emergence. | Shared representation alone strengthens causal/emergence evidence. | Ancestry-aware evidence graph audit. |

## Counterhypotheses retained

- C1: the additional predicate/invariant/volatile machinery costs more complexity than it saves; whole-root OCC may dominate at FRANK's actual mutation rate.
- C2: static effect envelopes for Python/dynamic FRANK code may become so broad that observed-trace narrowing rarely helps.
- C3: complete runtime interposition may be infeasible around native extensions, subprocesses or external services; safe fallback may frequently become global closure.
- C4: transactional outbox semantics may be excessive for reversible/local effects and should be reserved for externally consequential operations.
- C5: per-channel workspace versions may encode implementation detail rather than genuine causal freshness; live instrumentation must decide.

## Generation 2 — transformed after external research + experiments

### H-CC8-T01 — Observed Transition Closure Capsule (OTCC)

A ClayCode transition should combine a **trusted static semantic envelope** with a **runtime-observed trace**. The trace may narrow freshness validation only after `trace ⊆ envelope` is proven. Envelope escape fails closed and triggers wider validation/recompilation. This is stronger than CC7's derived object closure because it explicitly supports dynamic path sensitivity without trusting dynamic observation as the whole safety specification.

### H-CC8-T02 — typed dependency witnesses, not one read set

The closure certificate should distinguish at least:
- object/version witnesses;
- predicate/range/index witnesses;
- invariant-scope/epoch witnesses;
- temporal/environment/volatile receipts;
- capability/resource handles;
- causal episode/workspace revision witnesses.

Falsifier: one uniform object-version abstraction matches correctness and cost across predicate, temporal and capability workloads.

### H-CC8-T03 — hybrid static/dynamic effect semantics

Static inference provides the conservative **may-effect/may-depend** envelope; runtime interposition records the **did-effect/did-depend** trace. This parallels effect systems plus dynamic effect checking and self-adjusting computation's dynamic dependency graphs. Falsifier: target implementation cannot interpose enough dynamic accesses to maintain subset soundness without degenerating to a global envelope.

### H-CC8-T04 — predicate/invariant closure is mandatory for selective coordination

The G7 asymmetric coordination compiler should consume predicate/invariant witnesses derived by ClayCode semantics, not only object R/W sets. PostgreSQL Serializable/SSI is an implementation analogue showing why phantom/serialization dependencies require additional monitoring. Falsifier: real FRANK invariant corpus contains no meaningful predicate/cross-object constraints.

### H-CC8-T05 — external effects use prepare/commit/release

`STATE_PROPOSAL` may commit internal deterministic state directly after validation. `EFFECT_PROPOSAL` should first atomically commit state + durable effect intent, then release the real external effect through the capability gateway with an idempotency key and effect receipt. This is the ClayCode analogue of a transactional outbox. Falsifier: target effect substrate supplies stronger atomic cross-system transactions making the staging layer redundant.

### H-CC8-T06 — capability surface and semantic effect are distinct

A WIT-like interface/handle can expose what may be called, while ClayCode's trusted op semantics separately derive what the call can affect and which capability is required. Falsifier: interface typing alone proves application-level authority/freshness/invariant safety.

### H-CC8-T07 — temporal dependency is first-class Clay state semantics

Freshness is not metadata attached after execution: operations such as workspace read, re-entry consume, lease use or time-conditioned decision should declare temporal/environment dependencies in their semantic effect contract. Falsifier: live stale failures are fully predicted by ordinary object versions without temporal/regime witnesses.

### H-CC8-T08 — compression moves derived safety state away from the model

The more safety metadata can be reconstructed from `op_id + args + op_semantics_hash`, the less of it must occupy Qwen/LLM context. Reader projections should expose only semantics needed for cognition plus opaque handles/receipts. Falsifier: hiding derived metadata reduces target-reader task accuracy or repairability enough to erase token savings.

### H-CC8-T09 — OTCC becomes a shared semantic substrate across branches

FRANK freshness, GWT causal receipts, Hyperposition delta/invariant topology and Clay external-effect authority can all reference the same OTCC identifiers/witnesses without collapsing their distinct mechanisms. Falsifier: a shared capsule forces one branch's semantics to distort another branch's causal model.

### H-CC8-T10 — promotion gate moves from syntax fidelity to closure soundness

A ClayCode candidate should not be promoted primarily because it round-trips or is token-efficient. Minimum promotion evidence should include sound closure derivation, predicate/invariant coverage, envelope-escape detection, effect quarantine, replay and target-reader performance. Falsifier: a simpler contract provides equivalent target safety/utility with lower runtime cost.
