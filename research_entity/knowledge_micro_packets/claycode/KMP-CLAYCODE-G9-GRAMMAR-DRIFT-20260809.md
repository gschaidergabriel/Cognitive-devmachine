<!-- RAE_META
{"packet_id":"KMP-CLAYCODE-G9-GRAMMAR-DRIFT-20260809","title":"Admitted G9 grammar/source compatibility drift","domains":["claycode","tooling","formal_methods_testing"],"topics":["parser","grammar","canonicalization","BASE_CLAYCODE_RELEASE"],"epistemic_class":"EXECUTABLE_RESEARCH_RESULT","claim_status_hint":"OPEN","origin_class":"CHATGPT_LOCAL_EXECUTABLE_EXPERIMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-09T15:39:00+07:00","updated_at":"2026-08-09T15:39:00+07:00","source_refs":["research_entity/trigger_runs/claycode/claycode-20260809T1539p0700-chatgpt-parser-compat/FINAL_REPORT.md"],"evidence_refs":["research_entity/trigger_runs/claycode/claycode-20260809T1539p0700-chatgpt-parser-compat/EXECUTABLE_RESEARCH_RECEIPT.json","research_entity/trigger_runs/claycode/claycode-20260809T1539p0700-chatgpt-parser-compat/CANONICALIZATION_PROBE_RECEIPT.json"],"related_claim_ids":["H-CC-G9-PARSER-001","H-CC-G9-SURFACE-002","H-CC-G9-AMBIG-003"],"related_experiment_ids":["EXP-CC-G9-GRAMMAR-COMPAT-20260809","EXP-CC-G9-CANON-PROBE-20260809"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.93,"verification_required":true,"falsifier_or_next_test":"Locate the normative production parser, then parse the complete admitted G9 spec+dialects with intended AST/IR; if a richer admitted parser already handles all constructs, narrow this result to grammar.ebnf documentation drift.","search_terms":["G9 grammar drift","ClayCode parser","union type","if misparse","BASE parser canonicalizer"]}
RAE_META -->

### Core
The admitted G9 V3 source already uses constructs not faithfully represented by the admitted `grammar.ebnf`. In an executable local parser probe, five current constructs failed or semantically misparsed under the published grammar surface: union types, comparisons, interface method signatures, relation-word operations and explicit `if` control. A minimal compatibility candidate accepted all five while preserving rejection of a malformed generic negative control.

### Interpretation
This is a parser/toolchain counterexample, **not** a refutation of G9 semantic concepts. Current best action is `less change, more compile`: freeze intended semantics, repair/freeze parser and canonicalizer, parse the full admitted corpus, then test typed IR/type-effect/evaluator/lowering.

### Canonicalization probe
Three whitespace/comment variants produced the same normalized parse-tree probe hash, while a tested type-semantic change produced a different hash. This is only a deterministic canonicalization probe and must not be called the final ClayCode `semantic_hash`.

### Cross-branch consequence
Harness/FRANK readiness remains unresolved until a real frozen FRANK component compiles. ClayGraph and UnifiedDB deep inputs exposed no new semantic primitive requirement in this run; their existing concepts need executable IR/lowering coverage.
