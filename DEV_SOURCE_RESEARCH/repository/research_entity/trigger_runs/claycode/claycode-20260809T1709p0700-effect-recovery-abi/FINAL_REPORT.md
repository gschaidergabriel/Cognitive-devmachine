# ClayCode — External Effect Recovery ABI

Run: `claycode-20260809T1709p0700-effect-recovery-abi`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**

## Result

A new executable counterexample isolates an external-effect recovery boundary. Two crash worlds leave the same durable local `PREPARED` state: crash before the remote effect, versus remote effect followed by crash before durable local `DONE`. Local-only recovery cannot distinguish them. Always RETRY is exactly-once in 1/2 worlds and duplicates the already-executed world; always ABSTAIN is exactly-once in 1/2 and loses the not-yet-executed world. Retrying against a remote endpoint that deduplicates one stable operation identity is exactly-once in 2/2 tested worlds.

Therefore G9's lifecycle `[REQUESTED,AUTHORIZED,CLAIMED,EXECUTED,VERIFIED,DONE]` must not itself be treated as a generic exactly-once guarantee. The production-bound ABI needs stable `effect_operation_id`, a semantic request fingerprint, an explicit delivery/recovery class, and `UNCERTAIN` when the external world cannot be reconciled. This is a runtime/type-effect candidate first, not a syntax promotion.

Evidence: `EXP-CC-EFFECT-RECOVERY-EXACTLY-ONCE-20260809-01`, class `LOCAL_SYNTHETIC_RUNTIME_ABI_COMPONENT_EVIDENCE`. It is not production compiler evidence, E2B evidence, or Andreas Ubuntu target-host evidence.

## Same-window assimilation

Current sibling work already shows: minimal G9 parser repair remains incomplete; typed Relation IR can separate source spelling from semantic identity/authority; generation-tagged resource handles defeat the bounded ABA reuse probe; Harness H-WP-02 has a pre-lock idempotency race and a new red probe requiring changed semantic payload under the same idempotency identity to fail closed. These are shared-current findings, not independent replication.

## External triangulation

AWS idempotent-API architecture independently describes timeout-after-request as an ambiguous side-effect case and uses caller request identity, semantic consistency and atomic handling for safe retries. Kafka distinguishes at-most-once, at-least-once and exactly-once and uses idempotence/transactions or destination coordination for stronger guarantees. The IETF HTTPAPI Idempotency-Key document is an expired draft, but its key/fingerprint model is an architecture analogue only.

## Goodman review

The FRANK/Harness-derived assumption that local lifecycle/idempotency is sufficient is `REFINED`. Its counterhypothesis fails in the two indistinguishable crash worlds. Whether new ClayCode surface semantics are necessary remains `UNRESOLVED`; first implement the mechanism in typed IR/runtime/effect ABI and try to compile a real effectful application.

## ClayGraph / UnifiedDB

ClayGraph already carries `effect_ref`/`outcome_ref` while remaining derived and non-authoritative. It must not resolve `UNCERTAIN` into truth or authority. UnifiedDB V9 already carries execution receipts and revisioned work/capability state, but the inspected slice lacks an explicit generic cross-system `effect_operation_id + semantic_fingerprint + delivery/recovery class + reconciliation/uncertainty` contract. This is a candidate integration, not a physical-monolith requirement.

## New state

Hypotheses:
- `H-CC-EFFECT-OPID-20260809-01` — stable operation identity bound to semantic fingerprint — `OPEN_SUPPORTED_RUN_LOCAL`.
- `H-CC-EFFECT-DELIVERY-CLASS-20260809-02` — delivery/recovery class must be explicit — `OPEN_SUPPORTED_RUN_LOCAL`.
- `H-CC-EFFECT-ABI-NOT-LANGUAGE-20260809-03` — runtime/type-effect ABI may suffice without syntax change — `OPEN`.

Negative results:
- `NR-CC-LOCAL-PREPARED-NOT-EXACTLY-ONCE-20260809` — local PREPARED + fixed local recovery is insufficient for generic exactly-once in the tested crash model.
- `NR-CC-LIFECYCLE-DONE-CANNOT-BE-INFERRED-20260809` — local lifecycle cannot always reconstruct truthful external DONE after crash.

## Next discriminating execution

Add the candidate effect identity/delivery contract to production-bound typed IR/runtime ABI without changing surface syntax. Compile one real effectful program end-to-end through source hash -> parser -> AST -> typed IR -> semantic hash -> lowering -> artifact -> execution receipt. Run idempotent and deliberately non-idempotent adapters; inject crashes before send, after remote mutation before local receipt, during retry and reconciliation; reject same operation id with changed semantic fingerprint; require `UNCERTAIN` when remote state is unknowable. Differential-test H1/H2 and require Ubuntu target evidence before BASE credit.

Durable artifacts: `RUN_MANIFEST.json`, `INTERCONNECT_MANIFEST.json`, `TOOL_EXECUTION_MANIFEST.json`, `FRANK_CLAYCODE_GOODMAN_REVIEW.json`, `HYPOTHESIS_MATRIX.json`, `NEGATIVE_RESULTS.json`, `BRANCH_FEEDBACK_MANIFEST.json`, `experiments/effect_exactly_once_probe.py`, `EXECUTABLE_RESEARCH_RECEIPT.json`, `FINAL_REPORT.md`.

No canonical revision, current G9 source, release gate, application PASS or ClayCode semantic authority was promoted.
