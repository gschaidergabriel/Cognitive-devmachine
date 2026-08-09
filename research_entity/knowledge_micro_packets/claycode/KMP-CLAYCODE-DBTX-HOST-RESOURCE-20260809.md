# KMP-CLAYCODE-DBTX-HOST-RESOURCE-20260809

packet_id: KMP-CLAYCODE-DBTX-HOST-RESOURCE-20260809
domains: [claycode, unifieddb, frank, harness]
epistemic_class: LOCAL_PROXY_EXECUTABLE_RESEARCH
status_hint: OPEN_SUPPORTED_NOT_PROMOTED
origin_actor: chatgpt-secondary
provider: OpenAI
model: GPT-5.6 Sol
run_id: claycode_20260809T165804p0700_chatgpt_dbtx_broker
canonical_parent: r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346

## Atomic finding

A bounded transactional DB program expressed as generic typed ClayCode-like canonical IR was lowered to a generated Python guest that could access SQLite only through an inherited host-owned broker resource. Commit, rollback, idempotent replay and crash-before-commit semantics matched an independent pure state-machine oracle across 2,000 randomized cases.

The run found no executable need for a DB-specific ClayCode core primitive in this bounded slice. A typed DB transaction/resource API belongs first in stdlib/FFI/runtime lowering.

## Hard boundary

This is not a production sandbox result. The guest process was unrestricted Python and the inherited Unix socket descriptor only constrained the tested DB path. Production acceptance still requires runtime/OS enforcement of no ambient authority.

## Negative constraint

SQLite BEGIN transactions do not nest; the proxy rejects nested BEGIN. This is backend behavior, not a universal ClayCode semantic law. Savepoint/nesting/cancellation/multi-resource atomicity remain falsifiers.

## Concurrent refinement

A same-time Clayresearch transaction-envelope worker independently routed a compatible implementation requirement: compiler-emitted dependency metadata plus a runtime commit envelope with capability epoch/validity, retry/abort receipts, and no new syntax request. Shared ancestry is preserved; this is assimilated as convergence, not counted as independent replication.

## Falsifier / next test

Lower the same frozen semantic DB transaction object to (1) the native Ubuntu host-resource path and (2) a WIT/WASI-style resource backend. Require semantic-hash identity, matched transaction/error/replay behavior, dependency/capability epoch revalidation, absent/forged/stale resource denial, cancellation/close semantics, no ambient filesystem/network authority, and mutation/fuzz differential receipts.
