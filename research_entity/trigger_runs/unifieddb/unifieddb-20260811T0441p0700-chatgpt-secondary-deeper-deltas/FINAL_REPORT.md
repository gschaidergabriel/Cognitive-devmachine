# UnifiedDB — Deeper Delta Run

Run: `unifieddb-20260811T0441p0700-chatgpt-secondary-deeper-deltas`

Status: **COMPLETE / RESEARCH DELTAS COMMITTED / PROMOTION HOLD**

## Executive result

The previous UnifiedDB continuity model was directionally correct but still bundled several different properties. This deeper run separates them and finds a new confirmed design gap in the active V17 V3 lane.

The strongest new result is **temporal causal provenance**: a support graph can be perfectly referentially consistent and still be causally false if it is minted after the effect already happened. PR #280's current learning matrix does exactly that: it verifies the effect outcome first, then creates attention, receiver-use, prediction, prediction outcome, causal credit and exact-outcome support, and finally expects learning re-entry to succeed. The candidate therefore closes free-string/cross-row identity gaps but does not yet prove that GWT/receiver use preceded and contributed to the action.

This conflicts with the Frank causal-chain contract, whose semantic order is Workspace/receiver use/local effect -> verified outcome -> causal credit -> admitted learning -> provenance-bound re-entry.

## New delta A — EffectIntent before effect execution

Introduce an immutable pre-action `EffectIntent/DecisionReceipt` rather than trying to infer intent from post-hoc support rows. Preallocate the effect id and bind it to exact current execution generation, GWT cycle/episode, prediction, receiver-use/local-effect receipt, action/target/request hash and effect class. The effect reservation consumes this receipt.

Required negative: `POST_HOC_SUPPORT_MINT` — execute an effect without pre-action support, then mint otherwise valid exact-effect/exact-outcome support afterwards. Re-entry must reject with zero terminal mutation.

## New delta B — origin executor != recovery executor

Current V17 V3 correctly strengthens immutable origin execution-generation ancestry, but crash recovery creates a different authority question: who may reconcile/terminalize the effect *now*?

Required split:
- origin execution/epoch = immutable provenance of reservation/attempt;
- reconciler execution/epoch = exact current execution authorized to perform recovery/re-entry/DONE;
- successor reconciliation requires explicit recovery assignment/admission;
- stale origin and unrelated successor must fail closed.

This closes a gap that cannot be solved by simply demanding the original execution remain BUSY forever.

## New delta C — historical DONE must remain historically valid

PR #280 revalidates learning delta support using `semantic_records.status='CURRENT'`. That couples old terminal validity to later belief-state evolution. A later normal supersession can make a previously valid terminal chain fail verification.

Freeze validity-at-admission in an immutable closure receipt containing exact effect/attempt/outcome, pre-action decision receipt, origin and reconciler execution bindings, causal support, semantic record/epoch or typed NO_LEARNING mode, contract/schema identity and durable order references. Ordinary semantic supersession changes current truth state but must not silently rewrite historical effect completion.

Explicit corruption/revocation is separate quarantine evidence.

## New delta D — support retention must be bounded

If terminal verification forever joins live GWT/prediction/semantic rows, old DONE receipts become dependent on indefinite row retention and mutable projection status. The immutable closure receipt should be sufficient for stable historical audit, with compact hashes/identity references and explicit retention rules.

## New delta E — DELETE mode creates an atomic multi-file option

The target's safe current-system profile is SQLite rollback journal `DELETE` + `synchronous=FULL`. Official SQLite documentation states that transactions across ATTACHed databases are atomic when the main database is not memory and WAL is not used; SQLite uses a super-journal for multi-file rollback-journal commits.

Therefore safe DELETE mode creates a previously underused candidate: atomically commit one authoritative UnifiedDB semantic epoch together with a bounded ClayGraph projection batch/watermark. ClayGraph remains derived and cannot mint truth.

Local synthetic proxy (Python SQLite 3.46.1, N=300) observed application rollback across both attached files correctly and measured attached transaction p50/p95/p99 ~20.08/49.69/73.22 ms versus two separate commits ~13.56/34.05/48.35 ms. The attached path was ~1.48x slower at p50 in this environment. This is not target durability/performance evidence; it demonstrates why target A/B measurement is mandatory.

## New delta F — fixed WAL is not automatically a better UnifiedDB architecture

PR #288 tests a private fixed SQLite 3.53.4 WAL-capable runtime. That may improve reader/writer concurrency and remove the WAL-reset release blocker, but WAL does not provide crash-atomic transactions across multiple attached database files. If WAL wins, Graph must remain asynchronously projected with explicit freshness/quarantine/rebuild semantics.

Thus compare:

A. system SQLite + DELETE/FULL + bounded atomic ATTACH projection;
B. private fixed SQLite + WAL + asynchronous Graph freshness gate.

Choose by correctness first, then p50/p95/p99, concurrency, recovery time, write amplification, fsync/I/O, RSS/CPU and Graph lag.

## New delta G — Graph freshness is not schema-pair identity

The U12 scope correction is retained:
- schema/migration pair current;
- dynamic ClayGraph payload current;
- UnifiedDB semantic lineage current;
are distinct predicates.

External rollback authority may bind the canonical schema pair identity, but it must not make a particular dynamic Graph payload authoritative. A stale Graph should be rebuildable from admitted UnifiedDB.

## Current external/target state

- system SQLite patch provenance on the accepted target found no direct WAL-code/amalgamation backport evidence in Ubuntu `3.45.1-1ubuntu2.7`; system-WAL release blocker remains;
- current-system DELETE/FULL storage safety has component target evidence, but fused PR #286 still needs its exact current target run;
- private SQLite 3.53.4 PR #288 target preflight is queued at this run's observation point;
- V17 V3 PR #280 target causal-support gate is queued at this run's observation point;
- the persisted V17 bound-reentry target receipt proves the narrower simplified candidate only and must not be promoted into V3 causal-closure proof.

## Promotion boundary

`HOLD`.

F-V01-04 remains OPEN. No whole Frank v0.1 acceptance changes.

Highest-information next target work:
1. run/falsify PR #280 V3, adding `POST_HOC_SUPPORT_MINT` and origin-vs-reconciler recovery matrix before promotion;
2. add `DELTA_SUPERSEDED_AFTER_DONE` to prove terminal historical validity is monotonic;
3. finish PR #286 and PR #288 target gates;
4. A/B DELETE+ATTACH atomic projection vs fixed-WAL async Graph on exact current target;
5. compose selected semantic head + external rollback authority + schema/Graph freshness + current recovery execution + temporal effect closure into one crash/restart/replay receipt.

No canonical migration, external effect, Frank/self.root Harness mutation authority or final training authorization follows from this run.
