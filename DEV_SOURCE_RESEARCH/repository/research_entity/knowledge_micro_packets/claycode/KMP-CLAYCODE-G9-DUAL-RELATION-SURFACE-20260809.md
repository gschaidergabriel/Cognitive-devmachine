<!-- RAE_META
{"packet_id":"KMP-CLAYCODE-G9-DUAL-RELATION-SURFACE-20260809","title":"Typed RelationId resolution separates semantic relation identity from parser surface","domains":["claycode","frank","claygraph","hyperposition","formal_methods_testing"],"topics":["parser","canonical IR","relation registry","generic surface","declared infix","BASE_CLAYCODE_RELEASE"],"epistemic_class":"EXECUTABLE_RESEARCH_SYNTHESIS","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-09T16:05:00+07:00","source_refs":["research_entity/trigger_runs/claycode/claycode_20260809T1600p0700_chatgpt_secondary_relation_generic/FINAL_REPORT.md","research_entity/trigger_runs/claycode/claycode-20260809T155804p0700-chatgpt-declared-relations/EXECUTABLE_RESEARCH_RECEIPT.json"],"evidence_refs":["research_entity/trigger_runs/claycode/claycode_20260809T1600p0700_chatgpt_secondary_relation_generic/EXECUTABLE_RESEARCH_RECEIPT.json","research_entity/trigger_runs/claycode/claycode-20260809T155804p0700-chatgpt-declared-relations/NEGATIVE_RESULTS.json"],"related_claim_ids":["H-CC-G9-RELATION-GENERIC-008","H-CC-G9-DUAL-SURFACE-009","H-CC-DECLREL-001"],"related_experiment_ids":["EXP-CC-G9-RELATION-GENERIC-20260809","EXP-CC-G9-DECLARED-RELATION-RESOLVER-20260809"],"confidence":0.91,"verification_required":true,"falsifier_or_next_test":"Implement generic quoted and declared-infix surfaces over one typed RelationId resolver in the real BASE parser and run full G9+dialect parse/roundtrip/unknown-symbol fuzz plus migration/diagnostic/reader cost benchmarks.","search_terms":["ClayCode relation surface","RelationId resolver","generic operation form","declared infix","G9 parser"]}
RAE_META -->

### Core
Two independently executed ClayCode parser-surface experiments converge on one deeper requirement: **syntax may recognize a relation form, but semantic relation identity must be admitted by a typed resolver/registry rather than by lexer acceptance alone**.

The generic quoted form `relation("id", lhs, rhs)` passed the sampled current binary relation set and 20k parser/identity fuzz cases; a typed resolver then accepted 10/10 known sampled RelationIds and rejected 50k/50k unknown IDs. A concurrent declared-infix resolver accepted 8/8 sampled current forms and likewise rejected 50k/50k unknown relation words.

### Synthesis
Do not prematurely choose between generic-call and readable declared-infix syntax as different semantic models. The evidence currently favors testing a **shared typed Relation IR/RelationId registry with two possible surfaces**:

- strict generic/canonical serialization form;
- optional declared custom/infix reader form lowering to the same IR.

This mirrors an independently developed compiler pattern in MLIR, where a generic operation syntax coexists with registered custom assembly forms. It is design triangulation, not proof for ClayCode.

### Hard boundary
This packet applies to ordinary **binary** relation/predicate surface handling. ClayGraph/Hyperposition explicit n-ary/higher-order relation identity and role bindings remain separate typed semantics until executable reduction evidence shows otherwise.

### Release implication
`CC-WP-02-PARSER-CANON` remains OPEN. No CURRENT G9 semantic promotion, BASE PASS, or application acceptance follows from these micro-oracles.
