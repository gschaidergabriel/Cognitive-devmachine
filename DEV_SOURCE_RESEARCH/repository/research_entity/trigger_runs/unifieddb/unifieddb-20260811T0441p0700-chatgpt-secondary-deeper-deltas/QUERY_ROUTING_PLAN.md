# QUERY ROUTING PLAN — authority/freshness separated

## Authoritative semantic reads/writes
Route to UnifiedDB only after:
1. storage mode/build gate passes;
2. exact UnifiedDB schema certificate passes;
3. selected semantic head/recovery floor rules pass for consequential writes;
4. exact current or explicitly admitted recovery execution owns the operation.

ClayGraph presence never upgrades authority.

## Graph-assisted retrieval
Use ClayGraph only when:
- U12 schema/migration pair is compatible;
- Graph projection watermark is `CURRENT` for the relevant derivation contract;
- `source_semantic_epoch` is compatible with the admitted UnifiedDB head according to an explicit lag policy.

If stale/missing/divergent:
- bypass Graph for truth-critical routing;
- query canonical UnifiedDB;
- quarantine/rebuild Graph asynchronously or via a bounded atomic projection path;
- do not block unrelated authoritative UnifiedDB reads merely because derived Graph is stale unless that exact query requires Graph semantics.

## Effect/re-entry routing
Effect terminalization must not route through ClayGraph authority. Resolve from canonical UnifiedDB receipts:
- pre-action EffectIntent/DecisionReceipt;
- origin execution generation;
- current reconciler execution authority;
- verified exact effect outcome;
- post-outcome causal credit;
- immutable learning/no-learning closure receipt.

## Historical audit routing
After DONE, audit against immutable closure receipts and hashes. Do not require old semantic rows to remain `CURRENT`; historical validity and current belief state are separate questions.

## Storage profile routing
- system SQLite 3.45.1 path: DELETE + FULL candidate; allow a dedicated ATTACH atomic-projection experiment;
- private fixed SQLite 3.53.4 path: WAL candidate only after exact target loader/source-id/regression pass; dynamic Graph coherence remains explicit because WAL multi-file crash atomicity is not available.
