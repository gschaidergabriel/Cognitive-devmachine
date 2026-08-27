# ClayCode Trigger Run — Transactional Loop Trace Identity

Run: `claycode_20260809T1655p0700_transactional_loop_trace_identity`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` — IN_PROGRESS  
Promotion: **NONE**  
Gate advancement: **NONE**

## Executive result

This run assimilated the new FRANK loop-of-loops work, the loop scheduler semantic-identity experiment, the epoch-coherent loop runtime result, the semantic-transaction-isolation field and the live Fusion replay/status refresh. It deliberately did not repeat parser surface-closure or generic recurrence experiments.

The new result is an identity/runtime refinement:

> ClayCode needs a separation between **static program semantic identity** and **dynamic execution/replay identity**. Static behavior-defining schedule/control/effect policy belongs in semantic identity. Dynamic snapshot/read-set/transaction/effect/root state belongs in execution/replay identity. Consequential effects must bind to the authoritative snapshot/read-set they were decided from or fail closed/retry.

An exact synthetic race experiment over 1,400 executions per variant tested `REVOKE` and `GRANT` transitions at seven writer positions across 100 starting epochs.

Naive per-field reads + unbound effect commit:
- decision mismatches: **700/1400**;
- unsafe effects: **300**;
- missed effects: **400**;
- fractured authoritative snapshots: **200**.

Atomic snapshot + root-bound effect commit + explicit serialization conflict + deterministic retry:
- decision mismatches: **0/1400**;
- unsafe effects: **0**;
- missed effects: **0**;
- fractured snapshots: **0**;
- conflicts detected and retried: **1000**.

This is exact synthetic mechanism evidence, not live FRANK or Ubuntu target evidence.

## Why this is new relative to concurrent work

Concurrent ClayCode work had already established:

1. generic structured recurrence is sufficient for tested loop-of-loops semantics;
2. scheduling/timescale/commit-mode changes can change behavior and therefore can belong in semantic identity;
3. same-epoch snapshot/set-like loop permutation can be nonsemantic when explicitly typed that way;
4. per-field atomics can admit fractured state and lost updates;
5. status/replay currently has a repository-level mixed-snapshot risk candidate.

This run connects those findings and adds the missing **two-plane identity discriminator**.

A single hash is wrong in both directions:

- **too weak:** a deliberately blind replay hash built only from `semantic_hash + input` collapsed all 1,400 executions to one identity despite hundreds of distinct runtime outcomes;
- **too strong in the wrong layer:** adding runtime snapshot roots directly to static program semantic identity fragmented one unchanged program into hundreds of identities across epochs.

The candidate architecture is therefore:

`ProgramSemanticId -> Contract/BuildId -> ExecutionTraceId -> EffectReceiptId`

The exact number of physical hashes remains implementation-gated; the semantic separation is the tested requirement.

## Internal fusion

### ClayCode

Route primarily to:
- `CC-WP-03-IR-TYPES` — identity/type separation;
- `CC-WP-07-RUNTIME-ABI-FFI` — snapshot/effect commit guard;
- `CC-WP-09-CONCURRENCY-MEMORY` — serialization conflict/retry semantics;
- `CC-WP-11-FUZZ-CONFORMANCE` — race/replay mutation tests.

No new FRANK-specific syntax is justified.

### FRANK

The loop-of-loops view survives, but authority closure becomes stricter: a cognitive decision based on state epoch/root X must not commit a consequential effect after capability/policy state has moved to Y unless the effect is revalidated against the current authoritative state or an equivalent serializable contract.

### Harness

The new minimal race oracle is:

`grant/revoke mutation x snapshot timing x recurrence x effect commit x serialization conflict x retry x exact replay`.

H1 should establish the reference behavior. H2 should reproduce the same state/effect/receipt transitions in ClayCode.

### UnifiedDB

Snapshot epoch/root/read-set/write-set/transaction/effect receipts belong in persistence and replay indexes, but they must not redefine static program semantics. Authoritative and rebuildable derived state remain distinct.

### ClayGraph / GWT / Hyperposition / Emergenz

Dynamic graph/workspace/alternative/readout identities should bind into the execution trace plane. None of them gain truth or effect authority from being trace-addressable. Mixed-epoch artifacts must be excluded before causal/emergence interpretation.

## External triangulation

PostgreSQL's current Serializable documentation independently defines the target of concurrent committed execution as equivalence to some serial order and requires applications to retry serialization failures. That is a strong implementation analogue for the guard+retry contract tested here. It is not FRANK-specific evidence and does not select a ClayCode syntax.

## Hypotheses

### H-CC-DUAL-IDENTITY-018 — OPEN_SUPPORTED_NOT_PROMOTED

Static program semantics and dynamic replay provenance require distinct identity layers.

Falsifier: a single identity definition can both preserve semantic equivalence across runtime epochs and distinguish every behaviorally relevant execution/effect state without false merge or false split.

### H-CC-EFFECT-SNAPSHOT-BINDING-019 — OPEN_SUPPORTED_NOT_PROMOTED

Consequential effect commits should bind to the authoritative snapshot/read-set on which the effect decision was made, with explicit conflict/retry when the binding is stale.

Falsifier: a weaker unbound design passes exhaustive/live concurrent grant/revoke/correction/rollback races with no stale or missed effect and exact replay.

### H-CC-NO-NEW-TXN-SYNTAX-020 — OPEN

The tested requirement can likely be implemented as typed IR/runtime/ABI/stdlib contracts without new ClayCode core syntax.

Falsifier: the production ClayCode compiler/runtime cannot express/lower the required transaction/effect/replay semantics without an opaque escape hatch or semantic loss.

## Negative results

- `N-CC-ONE-HASH-IDENTITY-20260809` — one undifferentiated identity is insufficient for semantic equivalence and exact replay provenance.
- `N-CC-UNBOUND-EFFECT-STATE-20260809` — unbound effect commit produced 300 unsafe effects and 400 missed effects in the exact mechanism corpus.
- `N-CC-RUNTIME-ROOT-IN-PROGRAM-HASH-20260809` — dynamic runtime roots embedded in static semantic identity over-fragment one program across epochs.

## BASE implication

No work package closes and `GENERAL_PURPOSE_GATE` remains NOT_PASS.

The implementation direction becomes more precise:

1. finish parser/control self-conformance;
2. freeze typed program semantic identity including behavior-changing schedule/commit policy;
3. add execution/replay identity carrying snapshot/txn/effect/root receipts;
4. implement serializable or equivalent effect commit guard + retry semantics;
5. execute DB-backed concurrent service + sandboxed system-effect proof on Ubuntu;
6. then carry the same oracle into the FRANK component and H1/H2 differential replay.

Only a real executable inadequacy should reopen language semantics.

## Artifacts

- `experiments/CC_TXN_LOOP_TRACE_IDENTITY.py`
- `EXECUTABLE_RESEARCH_RECEIPT.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `FINAL_REPORT.md`
- `research_entity/knowledge_micro_packets/claycode/KMP-CLAYCODE-DUAL-SEMANTIC-EXECUTION-IDENTITY-20260809.md`

## Completion boundary

Completed: current canonical/program re-verification, concurrency-aware assimilation, executable exact race discriminator, dual-identity synthesis, cross-branch routing and durable GitHub write-back.

Not completed/claimed: production compiler change, official repo-local interconnect-preflight PASS, live Ubuntu/FRANK evidence, H1/H2 replay, any BASE work-package PASS, BASE gate PASS or canonical scientific promotion.
