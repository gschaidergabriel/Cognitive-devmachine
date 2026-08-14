# ClayCode Trigger Run — Concurrent Idempotency Commit-Envelope Boundary

Run: `claycode_20260809T1712p0700_chatgpt_idempotency_concurrency`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` — IN_PROGRESS  
Target host: Ubuntu Linux developer system  
Promotion: **NONE** · Gate advancement: **NONE**

## Executive result

This run closed one explicit falsifier left open by the immediately preceding ClayCode DB-transaction lowering work: **concurrency**.

A fresh Harness negative result showed that the current H-WP-02 pre-lock idempotency path can race: two writers can both observe the same key as absent, then the loser reaches a UNIQUE insert after the winner commits and receives `IntegrityError` rather than deterministic replay handling.

An independent local mechanism probe reproduced that failure and tested the smallest repair class. Across 80 deterministic duplicate-writer rounds:

- pre-lock lookup + later write transaction: **80/80** -> one `applied` + one `IntegrityError`;
- acquire write serialization first, then lookup same-payload key: **80/80** -> one `applied` + one `replay`;
- acquire write serialization first, then lookup same key with different payload: **80/80** -> one `applied` + one `conflict`.

A separate `INSERT OR IGNORE` control showed that a UNIQUE key by itself is not a semantic replay oracle: different-payload reuse was suppressed at the storage layer but was not explicitly classified as a conflict.

**ClayCode conclusion:** the evidence does not justify a new DB/idempotency-specific core-language primitive. It justifies a stricter compiler/runtime/Needle legality contract: idempotency identity and semantic operation/payload fingerprint must be revalidated inside the backend serialization/commit domain, alongside relevant dependency/base epoch and capability validity, before the effect is applied or classified as replay/conflict.

This is a compiler/runtime hardening delta under the existing project rule: **less change, more compile**.

## Current-state grounding

Verified canonical state at write time remained:
- entity version `RAE-8.8`;
- revision `2`;
- state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`.

Current program stage is `BASE_CLAYCODE_RELEASE`. The release workspace remains centered on parser/canonical IR/type-effect/compiler/lowering/runtime/FFI/stdlib/toolchain and real Ubuntu application execution. Frank v0.1 remains Ubuntu-only for the current release target.

The admitted moving stack points to ClayCode G9 V3. Its relevant existing semantic machinery already includes typed records, `EffectIntent`, capability-bearing effects, external Needle lowering, explicit lifecycle/receipts, provenance separation and deterministic state/effect boundaries. Nothing in this experiment demonstrated that those source-level semantics are structurally unable to represent the concurrency guarantee.

## Interconnected research mesh

All nine registered scientific branches were included; see `INTERCONNECT_MANIFEST.json`.

### ClayCode

The prior host-owned DB transaction experiment supported generic typed IR + runtime resource adapters in a bounded single-resource slice, while explicitly leaving concurrency, cancellation, nesting/savepoints and multi-resource atomicity as open falsifiers. This run directly tests the concurrency falsifier rather than repeating the previous result.

### Harness

Fresh direct input: `NR-HARNESS-HWP02-IDEMPOTENCY-PRELOCK-RACE-20260809`. The local probe independently reproduces its mechanism and supports the proposed post-lock recheck direction. This does not close H-WP-02; the actual reference-ledger implementation still requires a real patch and project-host regression.

### UnifiedDB

The result reinforces an existing architectural separation: physical DB uniqueness/locking is not semantic identity. UnifiedDB should persist enough identity to distinguish a valid idempotent replay from conflicting key reuse, while backend-specific transaction implementation remains physical/lowering detail.

### ClayGraph

Replay/conflict state can be projected for retrieval or diagnostics, but graph activation/salience remains non-authoritative. A graph edge or high activation cannot authorize an effect or establish replay equivalence.

### GWT / Hyperposition / Emergenz

Deterministic effect/replay receipts reduce a causal measurement confound. They do not prove workspace ignition, causal use, higher-order coupling, synergy or emergence. No claim promotion was performed.

### FRANK

FRANK can benefit from stronger effect/recovery receipts, but this is Research-Entity runtime evidence. It neither validates the loop-of-loops hypothesis nor changes the rule that Frank cannot directly or indirectly modify its own Harness under Frank authority.

### ClayResearch

A same-time transaction-envelope line already converged on dependency read-set + capability epoch/validity in the runtime commit envelope with no new source syntax. That shared-ancestry convergence was preserved but not counted as independent replication.

## Fusion 1 — discriminating question

The live evidence created a precise choice:

1. **Core-language expansion:** add an idempotency/transaction primitive to ClayCode; or
2. **Lowering/runtime legality:** preserve ordinary typed semantic IR and require each backend to legalize the stronger atomic replay/commit contract.

The current-stage policy says semantics change only for executable counterexamples. Therefore the cheapest high-information test was whether the race can be closed without changing source-language semantics.

## External research

Primary SQLite transaction documentation supports the relevant backend fact pattern: transactions serialize writes according to SQLite's transaction/locking rules, and `BEGIN IMMEDIATE` starts a write transaction immediately. That supports using an in-transaction/post-serialization lookup for this SQLite mechanism probe; it does **not** make `BEGIN IMMEDIATE` a universal ClayCode semantic law.

An IETF Idempotency-Key Internet-Draft also describes the general distinction between unique request keys and different-payload key reuse, but the version discovered by this run is expired work-in-progress. It is retained only as contextual convergence, not normative authority.

## Executable experiment

Artifacts:
- `IDEMPOTENCY_CONCURRENCY_PROBE.py`
- `IDEMPOTENCY_CONCURRENCY_RESULT.json`
- `EXECUTABLE_RESEARCH_RECEIPT.json`

Runtime:
- Python 3.13.5;
- SQLite 3.46.1;
- local hosted container;
- not Andreas' Ubuntu target host.

Source SHA-256: `a13dce4d208f445ee90c88b254a9293117a266b0f67700aec183dd06b8db396a`  
Result SHA-256: `8ec9469b76ba11998821c699003107610337e28f55b668841dbd5534d546cae2`

### Arm A — pre-lock lookup

Both threads query key `K` before either enters the write transaction. A barrier forces both to see absence. Each then attempts `BEGIN IMMEDIATE` and insert.

Observed over 80/80 rounds:
- one writer commits;
- the second later attempts the same UNIQUE key;
- the second receives `IntegrityError`;
- one row remains.

This independently reproduces the fresh Harness TOCTOU failure mode.

### Arm B — serialize, then lookup; same payload

Both threads contend for `BEGIN IMMEDIATE`. Only after acquiring the write serialization domain does each query the idempotency record.

Observed over 80/80 rounds:
- one writer applies;
- the second sees the committed key + equal payload hash and returns `replay`;
- one row remains.

### Arm C — serialize, then lookup; different payload

Same mechanism, but the two writers use different payloads.

Observed over 80/80 rounds:
- one writer applies;
- the second sees the same key + different payload hash and returns `conflict`;
- one row remains.

### Arm D — uniqueness-only control

`INSERT OR IGNORE` was attempted with an already-used key but different payload.

Observed:
- insert was suppressed;
- original row remained;
- no explicit payload-mismatch/replay-conflict classification existed.

Therefore database uniqueness is a useful integrity guard but is insufficient as the semantic replay-equivalence contract in the tested design.

## Hypotheses and counterhypotheses

See `HYPOTHESIS_MATRIX.json`.

### H-CC-IDEMP-CONC-01 — SUPPORTED_LOCAL_EXECUTABLE

Idempotency identity + semantic payload/operation fingerprint checked inside the same backend serialization domain as commit closes the tested duplicate-writer TOCTOU failure and distinguishes replay from conflict.

### H-CC-IDEMP-CONC-02 — SUPPORTED_LOCAL_EXECUTABLE

UNIQUE-key behavior alone is not semantic proof of replay equivalence in the tested design.

### H-CC-IDEMP-CONC-03 — REFINED_NO_CORE_SYNTAX_CHANGE

Existing typed IR plus compiler/runtime/Needle legality is sufficient for the tested concurrency guarantee; no core source syntax change is currently justified.

Strongest counterhypothesis remains open: distributed retries, cancellation during commit, nested/savepoint semantics or multi-resource atomicity may expose a guarantee that cannot be represented/legalized by existing G9 semantics.

## Goodman anti-echo review

See `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

Shared FRANK/ClayCode/ClayResearch ancestry was explicitly collapsed. Independent discrimination came from the new local SQLite concurrency experiment plus primary SQLite documentation.

Verdicts:
- explicit commit/replay evidence boundary: **REFINED** by independent mechanism evidence;
- new DB/idempotency core syntax: **REFINED DOWNWARD / not justified by this test**;
- key collision always means valid replay: **REFUTED in the tested design**.

No architecture or scientific claim was promoted merely because multiple project branches agreed.

## Negative results

See `NEGATIVE_RESULTS.json`.

1. **Pre-lock-only idempotency lookup failed 80/80** deterministic duplicate-writer rounds in the tested SQLite interleaving.
2. **UNIQUE/INSERT-OR-IGNORE alone did not classify different-payload key reuse** and therefore cannot serve as the semantic replay oracle in this design.

These are preserved as scoped negative results, not silently overwritten by the repair candidate.

## ClayGraph and UnifiedDB findings that changed/refined ClayCode

### ClayGraph

No new graph primitive is needed. The result strengthens the authority boundary: replay identity/conflict may be graph-visible metadata, but graph activation/relevance cannot authorize or classify the underlying effect by itself.

### UnifiedDB

This run materially refines the runtime/persistence contract: idempotency identity should bind to semantic operation/payload identity and be checked in the relevant commit serialization domain. Physical index/UNIQUE behavior remains an implementation guard, not the definition of logical semantic equivalence.

This supports adding explicit replay/conflict receipt semantics to the lowering/runtime layer while preserving logical-vs-physical database separation.

## Architecture / BASE delta

### Change now justified

For effectful transactional lowerings, require a typed commit envelope containing, where relevant:

- idempotency key / operation identity;
- semantic operation/payload fingerprint;
- dependency/base epoch or read-set identity;
- capability identity + validity/revocation epoch;
- backend transaction/resource identity outside semantic program identity;
- explicit result class: `APPLIED | IDEMPOTENT_REPLAY | CONFLICT | ABORT/RETRY`;
- commit/rollback/crash receipt.

The backend must prove it can legalize this envelope atomically enough for its advertised semantics. For SQLite, the tested candidate acquires the write serialization domain before replay lookup. Other backends may use different mechanisms.

### Change not justified

- no magical `transaction` or `idempotency` ClayCode core primitive;
- no new G9 generation;
- no new FRANK cognition primitive;
- no physical UnifiedDB monolith mandate;
- no GWT/Hyperposition/Emergenz promotion.

## Stage impact

`BASE_CLAYCODE_RELEASE`: remains **IN_PROGRESS**.  
`CLAYCODE_RELEASE_GATE`: remains **NOT_PASS**.  
`GENERAL_PURPOSE_GATE`: remains **NOT_PASS**.

This run reduces uncertainty primarily in:
- CC-WP-04 TYPE/EFFECT;
- CC-WP-06 COMPILER/LOWERING;
- CC-WP-07 RUNTIME/ABI/FFI;
- CC-WP-08 STDLIB/SDK;
- CC-WP-11 FUZZ/CONFORMANCE.

No work package is marked complete by this run.

## Limitations

- production G9 parser/compiler not executed;
- E2B was not exposed in this hosted session;
- repo-local preflight/Goodman validator scripts were not executable on the connector-only surface;
- no second independent DB/backend;
- no distributed transaction, cancellation or multi-resource atomicity test;
- no execution on Andreas' Ubuntu developer-system target.

## Highest-information next test

1. Patch actual H-WP-02 reference-ledger implementation so idempotency key + event/operation fingerprint are rechecked after entering its serialization domain.
2. Run the real concurrent project-host regression plus all prior single-writer, snapshot/recovery and replay tests.
3. Freeze one canonical ClayCode DB/effect semantic IR and lower the exact same contract through two materially different backends.
4. On the Ubuntu target, test same-payload replay, different-payload conflict, stale dependency epoch, revoked capability, cancellation, crash/restart, resource close and unrelated-churn controls.
5. Require equal semantic outcomes with distinct backend/contract/trace identities and explicit receipts.
6. Reopen ClayCode core semantics only if an executable counterexample proves current typed IR + runtime legality cannot express the guarantee.

## Durable outputs

- `RUN_MANIFEST.json`
- `INTERCONNECT_MANIFEST.json`
- `TOOL_EXECUTION_MANIFEST.json`
- `IDEMPOTENCY_CONCURRENCY_PROBE.py`
- `IDEMPOTENCY_CONCURRENCY_RESULT.json`
- `EXECUTABLE_RESEARCH_RECEIPT.json`
- `HYPOTHESIS_MATRIX.json`
- `NEGATIVE_RESULTS.json`
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `research_entity/knowledge_micro_packets/claycode/KMP-CLAYCODE-IDEMPOTENCY-CONCURRENCY-20260809.md`
- `FINAL_REPORT.md`

## Final synthesis

The new concurrency evidence does **not** tell ClayCode to become more complicated. It tells the compiler/runtime boundary to become more exact.

The durable rule emerging from this run is:

`semantic effect identity + replay identity + fingerprint + authority/freshness -> backend commit serialization -> explicit applied/replay/conflict/abort receipt`

rather than:

`precheck key -> later write` or `UNIQUE collision == replay`.

That is a concrete BASE-stage hardening result, preserves the current external-authority boundary, and remains falsifiable by harder executable transaction semantics.
