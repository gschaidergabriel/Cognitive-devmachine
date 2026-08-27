# Harness Deep Continuation — H-WP-10 Durable Effect Lifecycle

Run: `harness-20260810T2031p0700-chatgpt-secondary-hwp10-lifecycle`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 · 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Moving stack: epoch 23  
Result: `COMPLETE_DURABLE_H1_LIFECYCLE_COMPONENT / H-WP-10 PACKAGE REMAINS OPEN`

## 1. What materially changed

The previous H-WP-10 component established deterministic effect classification and exact confirmation binding, but still kept one-shot confirmation consumption in process-local memory. This run extended the H1 reference semantics across the next causal boundaries:

`EffectRequest -> EffectDecision -> Confirmation validation when required -> atomic durable EffectReservation -> external Attempt boundary -> verified/unknown Outcome -> provenance-bound Reentry -> RecoveryClass`

New/changed reference code:

- `research_entity/harness/reference/effect_authority.py`
- `research_entity/harness/reference/effect_lifecycle.py`
- `research_entity/harness/reference/test_effect_lifecycle.py`

The critical architecture correction is that **authority to attempt an effect, durable local reservation, external execution, verified outcome and re-entry are different facts**.

## 2. Strongest counterexample: local exactly-once is not external exactly-once

A one-shot confirmation nonce can be consumed atomically with a local reservation, but that does not make an arbitrary external tool/API/device effect exactly-once.

The dangerous interval is:

`local reservation durable -> external provider may act -> process/network fails before verified OutcomeReceipt becomes durable`

At that point the local system must not infer either success or failure merely from the transport failure. This run therefore introduces explicit `COMMITTING` and `OUTCOME_UNKNOWN` states.

Recovery classification is intentionally conservative:

- `RESERVED` -> `SAFE_TO_START`;
- `COMMITTING` or `OUTCOME_UNKNOWN` with a verified downstream idempotency contract and stable key -> `SAFE_TO_RETRY_SAME_IDEMPOTENCY_KEY`;
- the same states without that property -> `RECONCILE_REQUIRED`;
- verified success/failure without re-entry -> `REENTRY_PENDING`;
- provenance-bound re-entry -> `COMPLETE`.

This prevents the Harness from claiming exactly-once semantics that the downstream system cannot actually provide.

## 3. Durable local authority transaction

The H1 reference uses SQLite as a clear ordinary-code oracle, not as a final UnifiedDB physical-placement decision.

The reservation transaction binds:

- exact policy-relevant `request_hash`;
- exact `ConfirmationReceipt` hash where required;
- unique confirmation nonce;
- deterministic effect identity;
- optional downstream idempotency key;
- explicit downstream-idempotent capability flag;
- initial lifecycle state;
- append-only semantic lifecycle event.

`BEGIN IMMEDIATE` serializes the local write boundary and the reference config uses rollback journal + `synchronous=FULL`. A fault injected after confirmation-consumption insertion but before commit rolled back both the effect row and confirmation consumption.

## 4. Confirmation hardening

The confirmation validator was split into pure validation plus consumption so the durable store can validate first and consume inside the same atomic reservation transaction.

The validator now rejects:

- naive/non-timezone-aware timestamps;
- empty nonce;
- empty impact summary;
- future-dated confirmation;
- expiry before confirmation time;
- the exact expiry boundary (`now >= expiry`);
- request/effect/target/action mismatch;
- non-authenticated-user confirmation provenance.

`ConfirmationReceipt.receipt_hash()` binds request identity, actor, effect class, target, action, impact summary, confirmation time, expiry and nonce.

Policy-relevant `EffectRequest` fields remain part of `request_hash`; explicitly non-authoritative translator/model/GWT/ClayGraph signals remain excluded so salience/confidence cannot mint or downgrade effect authority by perturbing the authorization identity.

## 5. Executed test evidence

Final local suite: **40/40 PASS**.

Important executed families include:

- original default-allow/read/reversible-write/external-communication regressions;
- destructive/privileged/unknown effect gates;
- pure confirmation validation vs durable consumption;
- strict time/nonce/impact validation;
- durable replay rejection after restart;
- injected transaction failure with rollback;
- 24-thread same-confirmation race -> exactly one local reservation;
- 8-process same-confirmation race -> exactly one local reservation;
- duplicate downstream idempotency-key rejection even with a fresh confirmation;
- crash-state recovery classification;
- verified vs unverified outcome separation;
- verified-outcome-only re-entry;
- direct default-allow reservation without confirmation;
- SQLite physical integrity;
- semantic event-hash/state-chain integrity;
- 500 deterministic policy-field mutations -> 0 old-confirmation admissions;
- real Linux child process `os._exit(17)` during an uncommitted effect+confirmation transaction -> after restart no partial effect row, no confirmation consumption, SQLite integrity `ok`.

This is local H1 reference evidence, not target Hostinger/production evidence.

## 6. Physical integrity is not semantic integrity

A deliberately modified `effect_events.payload_json` row left SQLite `PRAGMA integrity_check` returning `ok`, while the independent canonical event-hash verifier detected `event hash mismatch`.

Therefore:

`database physical integrity != semantic trace integrity`

Both must remain explicit acceptance surfaces. A healthy B-tree/page structure is insufficient evidence that the causal effect history is trustworthy.

## 7. Test-system defects found and repaired

The run preserved two meta-level failures instead of hiding them:

1. The first deep prototype relied on the SQLite connection context manager for read paths. Under warnings-as-errors this exposed connection ResourceWarnings. Read paths were converted to explicit connection closing.
2. The first 500-case mutation test had a branch that could assign a Boolean its existing value, making that case a no-op rather than a mutation. The test generator was repaired to guarantee changed request hashes before checking old-confirmation rejection.

Neither failure is counted as a production defect after repair, but both remain durable negative engineering evidence.

## 8. Performance/resource shadow

Local environment:

- Python 3.13.5 / GCC 14.2.0;
- Linux 6.18.35 x86_64 / glibc 2.41;
- SQLite 3.46.1;
- Intel Xeon Platinum 8573C;
- 5 visible logical CPUs;
- ~6.2 GB MemTotal;
- ext4 root filesystem;
- VM/container classification not independently verified.

Primary local reference configuration, SQLite rollback journal + `synchronous=FULL`:

- pure gate/confirmation validation, 5000 iterations: p50 0.0155 ms, p95 0.0173 ms, p99 0.0613 ms;
- durable reservation, 300 iterations: p50 2.3978 ms, p95 8.3243 ms, p99 11.6994 ms;
- three persistent lifecycle transitions (`begin_attempt + verified outcome + reentry`), 200 iterations: p50 6.5558 ms, p95 13.4594 ms, p99 18.5098 ms;
- database size after primary benchmark: 790,528 bytes;
- SQLite integrity: `ok`.

A randomized three-run-per-mode DELETE rollback journal vs WAL comparison produced mixed/noisy results and one large WAL p99 outlier. Decision: **NO_CHANGE**. No backend is promoted from this local microbenchmark; target-VPS matched correctness/crash/performance testing is required.

## 9. External research/counterevidence integration

Current OWASP agentic-security guidance was used as an external engineering countercheck for independent execution gating, exact approval binding, short-lived authorization artifacts and replay protection.

Official SQLite documentation supports the use of transactions as a local ACID/crash-recovery mechanism and documents serialized write behavior and durability configuration.

AWS engineering guidance on idempotent APIs directly reinforces the discovered boundary: after a timeout, a client may not know whether a remote side effect occurred, and retry safety depends on service-level idempotency/client-token semantics rather than local optimism.

The IETF Idempotency-Key draft was treated only as expired historical design precedent, not as a current RFC or normative standard.

No external source changes the project-owner-fixed effect-authority policy; they refine implementation and falsification strategy.

## 10. Negative/null results preserved

`NEGATIVE_RESULTS.json` records six important results:

- in-memory nonce state is insufficient for restart-safe Harness authority;
- local atomicity does not imply external exactly-once;
- SQLite connection lifecycle defect found/fixed;
- fuzz-test no-op mutation defect found/fixed;
- no robust DELETE-vs-WAL backend winner;
- SQLite physical integrity alone cannot certify semantic effect-trace integrity.

## 11. Cross-branch architecture feedback

### Frank

The target architecture should represent authority, reservation, external attempt, outcome certainty and re-entry separately. `ALLOW` is permission to attempt, not proof of success. `OUTCOME_UNKNOWN` is a first-class state, not an error string to coerce into success/failure.

### ClayCode

H2 must be able to express and differentially reproduce at least:

- `ConfirmationReceipt` and deterministic semantic identity;
- atomic `ConfirmationConsumption + EffectReservation`;
- `AttemptIdentity`;
- `OutcomeCertainty` including UNKNOWN;
- downstream `IdempotencyCapability` and key;
- `RecoveryClass`;
- verified provenance-bound re-entry.

If lowering collapses these states, that is an H2/compiler/contract defect, not permission to simplify H1.

### UnifiedDB

The canonical persistence plane needs equivalent atomicity/uniqueness/trace semantics. The reference SQLite implementation is an executable oracle, not a mandate that final UnifiedDB physically use this exact schema/backend. H-WP-02 is actively owned by another worker, so this run intentionally does not overwrite the canonical state-ledger implementation.

### GWT / ClayGraph

GWT ignition and ClayGraph salience remain observational/selection signals only. They are excluded from the authority identity and cannot mint or downgrade effect authority. They may receive and route lifecycle evidence with provenance.

### Recovery / Trace / Fuzz / Performance Harness lanes

The new state machine creates direct reusable obligations for H-WP-11, H-WP-13, H-WP-14 and H-WP-15, but this worker did not claim or close those sibling packages.

## 12. What is still missing before H-WP-10 can close

H-WP-10 remains OPEN because local reference correctness is not the full package. Required next evidence includes:

- accepted Hostinger Ubuntu target execution and fault injection;
- integration with the current canonical H1 ledger/UnifiedDB by the owning work package;
- real tool/provider adapter evidence for capability-specific idempotency and reconciliation;
- explicit rollback implementation/receipts;
- exact resource/permit/reservation/commit/EffectReceipt/OutcomeReceipt integration across a full FRANK turn;
- H2 ClayCode implementation and differential oracle replay;
- E2E/golden-trace/recovery/release coverage.

## 13. Epistemic boundary

The strongest justified conclusion is:

> The H1 reference now has an executable, locally durable and crash-tested separation between authority, reservation, attempt, outcome certainty and re-entry, with conservative recovery semantics that avoid pretending arbitrary external effects are exactly-once.

Not justified from this run:

- production security;
- target-VPS performance;
- distributed exactly-once effects;
- universal prompt-injection immunity;
- correctness of every real provider's idempotency behavior;
- H1 release PASS;
- H2 equivalence;
- emergence/consciousness claims.

Those remain separate evidence gates.
