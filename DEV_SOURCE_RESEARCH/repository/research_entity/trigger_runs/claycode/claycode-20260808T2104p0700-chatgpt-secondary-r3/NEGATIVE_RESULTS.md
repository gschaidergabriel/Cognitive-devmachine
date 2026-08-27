# CC12 negative results

## N-CC12-001 — type-erased DISTINCT lowering is unsound
In 30,000 E2B/SQLite generated query cases, a lowerer treating every result as a set mismatched the typed reference in 16,947 cases. It destroyed ORDERED order/multiplicity and MULTISET multiplicity.

## N-CC12-002 — type-erased bag/order lowering is unsound
Treating every result as raw ordered rows mismatched the typed reference in 16,609/30,000 cases, especially SET duplicate semantics and MULTISET count semantics.

## N-CC12-003 — collection kind cannot be omitted from semantic identity
In the constructed E2B identity corpus, removing collection kind yielded 27,155/100,000 SET-vs-ORDERED cross-kind aliases, including 5,038 multi-element cases. Typed hashes yielded zero aliases in that corpus.

## N-CC12-004 — one universal collection canonicalizer is rejected
The same normalization cannot simultaneously satisfy SET duplicate-idempotence, ORDERED sequence identity and MULTISET multiplicity. Collection semantics must be explicit and operation/type-specific.

## N-CC12-005 — triple binding is not free
The current JSON proxy grows from 163 bytes for contract+view identity to 332 bytes when semantic identity and receipt metadata are included (+169 bytes). This does not reject triple binding; it rejects repeatedly shipping verbose hashes when compact cached handles can preserve the same identities.

## N-CC12-006 — packed ABI performance remains unresolved
C7/CC12 CPython proxies support avoiding repeated JSON on cognition-hot paths, but they are not Rust/C/Arrow/Android evidence. No target ABI speedup is promoted.

## N-CC12-007 — current WEIGHTED duplicate behavior is deliberately narrow
CC12 rejects duplicate weighted keys rather than guessing SUM/MAX/LAST-WRITE or another aggregation. Domains needing duplicate aggregation require an explicit policy type; rejection is safer than silent semantics.

## N-GOV-CC12-001 — ClayCode protocol count drift
The current ClayCode protocol text retained seven-branch wording after UnifiedDB became the eighth branch. CC12 followed the authoritative registry/interconnect protocol, materialized an eight-branch preflight and wrote `CLAYCODE_EIGHT_BRANCH_UNIFIEDDB_ADDENDUM.md`. No scientific conclusion is inferred from this governance repair.
