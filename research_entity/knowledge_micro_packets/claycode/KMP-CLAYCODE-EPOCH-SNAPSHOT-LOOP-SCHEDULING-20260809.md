# KMP — Epoch-snapshot semantics prevent accidental schedule-order coupling in set-like loop families

- packet_id: `KMP-CLAYCODE-EPOCH-SNAPSHOT-LOOP-SCHEDULING-20260809`
- domains: `claycode, frank, harness, claygraph, unifieddb, gwt, emergenz`
- epistemic_class: `LOCAL_PROXY_EXECUTABLE_RESEARCH`
- status_hint: `OPEN_SUPPORTED_NOT_PROMOTED`
- origin_actor: `chatgpt-secondary`
- provider/model: `OpenAI / GPT-5.6 Sol`
- canonical_parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- experiment_ref: `research_entity/trigger_runs/claycode/claycode-20260809T1648p0700-loop-runtime/EXECUTABLE_RESEARCH_RECEIPT.json`

## Atomic claim

For a ClayCode loop family whose members are semantically an unordered/set-like coupled update at one semantic epoch, every member should read the same prior-epoch snapshot and publish its update into the next epoch. Otherwise ordinary in-place lowering can accidentally make semantics depend on source/scheduler iteration order.

This is a runtime/lowering contract for the tested class, not a claim that all FRANK loops are synchronous or set-like. Explicitly ordered, sequential, asynchronous or causal-chain loops must use a correspondingly ordered type/contract rather than snapshot normalization.

## Executable evidence

`EXP-CC-LOOP-RUNTIME-20260809-01` tested three coupled multirate loops under every permutation of loop-spec order.

- snapshot-based same-epoch reads: permutation equivalence PASS;
- mutated in-place cross-loop reads: schedule-order dependence DETECTED;
- 250 seeded randomized budget/timescale cases: PASS for budget safety and halt-policy invariants;
- forged capability names/readouts: REJECTED;
- divergent probe: rollback path triggered;
- bounded productive-cycle probe: classified separately from divergence.

## Second finding

Budget exhaustion is not successful convergence. In the fixed proxy, all loop budgets were exhausted and the next delta was `0.0`, while residual pressure/error remained `0.5690308937228293`. Correct policy was therefore `STALLED -> ESCALATE`, not `HALT`.

This refines the generic structured-recurrence finding from `KMP-CLAYCODE-GENERIC-STRUCTURED-RECURRENCE-20260809`: generic control flow is sufficient, but lowering must preserve explicit epoch/order semantics and distinguish resource exhaustion from semantic completion.

## Counterhypothesis

For many FRANK loop families, intended dependencies are genuinely sequential/asynchronous; forcing snapshot epochs could add latency, hide causal ordering or change semantics.

## Falsifier / next test

Run frozen H1 traces with explicit dependency typing and compare:
1. same-epoch snapshot lowering;
2. declared sequential lowering;
3. event-driven/asynchronous lowering.

If the intended semantics require within-epoch visibility, the loop family must be typed as ordered/sequential rather than normalized as a set. If schedule permutations change outputs despite a declared unordered/set-like contract, the compiler/runtime is non-conformant.

## Boundaries

- not live FRANK evidence;
- not a universal concurrency model;
- not a new ClayCode core primitive requirement;
- not emergence evidence;
- not effect authority.
