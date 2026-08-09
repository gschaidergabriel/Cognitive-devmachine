# KMP — ClayCode concurrent idempotency commit-envelope boundary

Packet ID: `KMP-CLAYCODE-IDEMPOTENCY-CONCURRENCY-20260809`  
Domains: ClayCode · Harness · UnifiedDB · ClayResearch  
Epistemic class: `LOCAL_EXECUTABLE_MECHANISM_RESULT_PLUS_PRIMARY_DOC_TRIANGULATION`  
Status hint: `OPEN_REFINED_WORKING_CONTRACT`  
Origin actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol

## Atomic claim

For an effect whose idempotency/replay state is persisted through a concurrent transactional backend, checking an idempotency key before entering the backend serialization/commit domain is not sufficient. The replay check must be revalidated within that domain and must bind the key to semantic operation/payload identity (or an equivalent fingerprint) so the runtime can distinguish valid replay from conflicting key reuse.

## Evidence

Local Python 3.13.5 / SQLite 3.46.1 mechanism probe:
- pre-lock same-payload duplicate writers: 80/80 -> one `applied` + one `IntegrityError`;
- post-lock same-payload: 80/80 -> one `applied` + one `replay`;
- post-lock different-payload: 80/80 -> one `applied` + one `conflict`;
- uniqueness-only different-payload control: duplicate insertion suppressed, but payload mismatch was not semantically classified.

Source SHA-256: `a13dce4d208f445ee90c88b254a9293117a266b0f67700aec183dd06b8db396a`  
Result SHA-256: `8ec9469b76ba11998821c699003107610337e28f55b668841dbd5534d546cae2`

## Language implication

No new DB/idempotency-specific ClayCode core syntax is justified by this bounded test. Prefer an existing typed-IR + runtime/Needle lowering contract:

`semantic effect intent + idempotency identity + payload/operation fingerprint + dependency/base epoch + capability validity -> backend commit envelope -> APPLY | IDEMPOTENT_REPLAY | CONFLICT | ABORT receipt`

Backend-specific locking/transaction mechanics remain lowering details and must not become universal source-language laws.

## Boundaries

- local hosted SQLite, not Andreas' Ubuntu target;
- no production G9 parser/compiler;
- no E2B;
- no second backend;
- no distributed/multi-resource atomicity/cancellation test;
- no BASE gate advancement;
- no FRANK/GWT/Hyperposition/Emergenz claim promotion.

## Falsifier / next test

Patch actual H-WP-02 reference-ledger implementation, rerun real concurrent project-host regressions, then lower the same frozen ClayCode transaction semantics through at least two backends on the Ubuntu target. Reopen ClayCode core semantics only if an executable counterexample proves the existing typed IR/runtime contract cannot represent or legalize the required guarantee.
