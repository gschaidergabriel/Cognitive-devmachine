<!-- RAE_META
{"packet_id":"KMP-CLAYCODE-G9-GRAMMAR-EXECUTABLE-CONFORMANCE-20260809","title":"G9 grammar drift and minimal executable alignment","domains":["claycode"],"topics":["parser","grammar","compiler","BASE release","adaptive visual learner"],"epistemic_class":"EXECUTABLE_RESEARCH_RESULT","claim_status_hint":"OPEN_WITH_NEGATIVE_RESULT","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-09T15:57:34+07:00","source_refs":["research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay","research_entity/claycode/g9/grammar.ebnf","research_entity/trigger_runs/claycode/claycode-20260809T155134p0700-chatgpt-58f84b/EXECUTABLE_RESEARCH_RECEIPT.json"],"evidence_refs":["EXP-CC-G9-GRAMMAR-CONFORMANCE-20260809","EXP-CC-MVC-LOWERING-20260809"],"related_claim_ids":["H-CC-G9-GRAMMAR-01","H-CC-G9-GRAMMAR-02","H-CC-MVC-03"],"confidence":0.93,"verification_required":true,"falsifier_or_next_test":"Parse and canonical-roundtrip the complete current G9 spec with the production parser, then type/effect-check and lower a frozen real FRANK adaptive-learner component."}
RAE_META -->

### Core
The checked-in G9 EBNF is not a faithful parser contract for a sampled set of forms already used by `CLAYCODE_G9_FUSION_SPEC_V3.clay`. In a 10-case executable corpus the unmodified grammar accepted 2/10; a minimal parser-side alignment for already-used forms accepted 10/10.

A second prototype compiler/lowering fragment encoded trusted GOLD/SILVER admission, BRONZE rejection, candidate promotion, over-budget fallback, last-known-good rollback and external effect commit/deny rules, generated Python, executed the generated program in a separate process and passed 9/9 deterministic cases.

### Interpretation
This supports `less change, more compile`: fix grammar/parser drift and continue compiler/runtime realization. The run does **not** justify a new ClayCode semantic primitive and does not establish full compiler, H1/H2 parity, transaction/replay or atomic promotion correctness.

### Negative result
`research_interconnect_preflight.py` is currently fail-closed incompatible with the current registry rename `clay -> clayresearch`; strong promotion remains blocked until the governance tool is repaired and rerun.

### Next test
Production parser over the complete G9 spec -> canonical IR -> deterministic roundtrip -> type/effect checker -> real FRANK/MVC component lowering -> separate-process execution -> differential replay against H1 semantics.
