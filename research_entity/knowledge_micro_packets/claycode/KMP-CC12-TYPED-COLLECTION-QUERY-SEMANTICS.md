<!-- RAE_META
{"packet_id":"KMP-CC12-TCQS-001","title":"ClayCode collection kind is semantic and must survive query lowering","domains":["claycode","unifieddb","frank","claygraph"],"topics":["SET","ORDERED","MULTISET","WEIGHTED","query IR","semantic identity","E2B"],"epistemic_class":"EXECUTABLE_MECHANISM_RESULT_WITH_OPEN_ARCHITECTURE_TRANSFER","status_hint":"OPEN","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","source_refs":["research_entity/runtime/tool_results/cc12-e2b-typed-collections-20260808T2104p0700.json","research_entity/runtime/tool_results/cc12-e2b-query-semantics-20260808T2104p0700.json","research_entity/runtime/tool_results/cc12-e2b-cross-kind-alias-20260808T2104p0700.json"],"verification_required":true}
RAE_META -->

# Atomic result

**Collection kind is part of ClayCode executable meaning, not merely container or backend metadata.**

CC12 E2B evidence:
- `SET`: permutation-invariant, duplicate-idempotent;
- `ORDERED`: sequence order and multiplicity preserved;
- `MULTISET`: permutation-invariant, multiplicity preserved;
- `WEIGHTED`: key/weight semantic; duplicate keys rejected unless a future explicit aggregation policy is typed;
- 100,000 collection/property cases: 0 failures in the constructed families;
- omitting collection kind produced 27,155/100,000 SET-vs-ORDERED false aliases in the constructed identity corpus; typed hashes produced 0;
- typed SQLite query lowering produced 0/30,000 reference mismatches, while DISTINCT-everything produced 16,947 and raw bag/order-everything 16,609.

# Architecture transfer

`CC-RC1.7 TCQS` should make collection kind part of:
1. canonical `semantic_hash`;
2. query/result type;
3. legal rewrite/canonicalization rules;
4. explicit cast/loss receipts;
5. UnifiedDB physical lowering;
6. MOSAIC `selection_plan_hash` whenever query cardinality/order/weight semantics matter.

This extends rather than replaces CC11/MRSC and MOSAIC-G11. Semantic, contract/provenance, basis, selection-plan and projected-view identities remain separate.

# Falsifier / next test

Run the same typed query corpus across PostgreSQL/DuckDB/graph/vector lowerings and a Rust/C/Arrow-compatible packed ABI. The candidate is weakened if explicit collection typing cannot preserve results across engines or its target cost exceeds specialized explicit APIs without compensating safety/correctness benefit.
