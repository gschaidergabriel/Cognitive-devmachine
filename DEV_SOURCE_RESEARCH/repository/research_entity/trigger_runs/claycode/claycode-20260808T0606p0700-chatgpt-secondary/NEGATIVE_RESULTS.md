# ClayCode CC8 Negative Results / Non-Promotions

**run_id:** `claycode-20260808T0606p0700-chatgpt-secondary`

1. **N-CC8-001 — Object-version witnesses alone are not a sufficient universal freshness/serializability contract.** In `EXP-CC8-PREDICATE-001`, the constructed semantic read was a negative predicate (`no matching object exists`). Concurrent inserts used distinct object IDs, so ordinary object-only OCC missed every true predicate conflict. Scope: synthetic counterexample; it falsifies universality, not a measured claim about FRANK's current invariants.

2. **N-CC8-002 — Runtime-observed dependency traces are not safe as the sole specification when monitoring can be escaped.** Exact observed traces were safe in the fully interposed toy, but injected hidden accesses produced misses. The observed trace may narrow a trusted static envelope; it may not replace it without a proof of complete interposition.

3. **N-CC8-003 — Object access traces do not encode all semantic freshness dependencies.** Time, current workspace/regime, randomness, external snapshots and analogous volatile inputs require explicit witnesses/receipts when they influence meaning.

4. **N-CC8-004 — Post-hoc effect monitoring is not an authority boundary for irreversible effects.** Detection after a network/device/external call cannot generally undo the call. External effects require pre-effect capability/freshness/invariant validation or must remain quarantined as durable intent.

5. **N-CC8-005 — Whole-state root mismatch is not a minimally selective commit policy in the constructed independent-change workloads.** It safely rejected every second concurrent proposal after any state mutation, including semantically independent changes. This does not prove scoped validation will dominate on real FRANK; actual mutation/invariant distributions remain unmeasured.

6. **N-CC8-006 — A model's self-declared effect/read/write/purity metadata remains non-authoritative.** CC7 already replicated conflict misses from incomplete model-declared footprints; CC8 therefore treats any such fields as explanation/prediction only unless independently derived/verified by trusted semantics.

7. **N-CC8-007 — Cross-branch agreement is not independent replication.** Clay G7, GWT R2, Hyperposition H2 and CC7/CC8 share actor and source/experiment ancestry. Their convergence is useful architectural fusion but must not be counted as four independent confirmations.

8. **N-CC8-008 — No live Qwen3-4B reader result is available in CC8.** `huggingface_inference` is cached as `QUOTA_EXHAUSTED_CACHED` until 2026-09-01 UTC. CC8 does not retry paid inference or fabricate reader performance.

9. **N-CC8-009 — Transactional outbox semantics do not imply exactly-once external delivery.** The pattern converts atomic state+intent into at-least-once relay semantics; duplicates/order/retry still require idempotency and receipts. The CC8 proxy deliberately models duplicate delivery.

10. **N-CC8-010 — OTCC/CC-RC1.3 is not production security.** The current reference code and fuzzers test contract logic and counterexamples. They do not prove compiler effect completeness, native/FFI interposition, OS capability isolation, storage durability, or live FRANK correctness.
