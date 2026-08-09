# G9 source normalization candidate

Status: OPEN parser-surface candidate, no semantic promotion.

The current source mixes strict ClayCode expressions with prose-like relation syntax. Do not add arbitrary identifier-as-infix parsing. Normalize representative constructs to explicit existing forms:

- `rule delegation returns narrower_or_equal(CapabilityToken)` -> `rule delegation -> narrower_or_equal(CapabilityToken)`
- `rule Needle.owns [tool_schema,api_wire,shell_wire,...]` -> `rule Needle.owns = [tool_schema,api_wire,shell_wire,...]`
- `rule 4B_emits EffectIntent` -> `rule model4B_emits -> EffectIntent`
- `rule 4B_need_not_learn Needle.owns` -> `rule model4B_need_not_learn = Needle.owns`
- `rule external_effect lifecycle=[...]` -> `rule external_effect.lifecycle = [...]`
- `rule Claude_only consumes latest stack + writes task receipts` -> two explicit rules: `rule Claude_only.consumes = latest_stack` and `rule Claude_only.writes = task_receipts`
- `rule NativeCognitionTask.forbidden_burden includes [...]` -> `rule includes(NativeCognitionTask.forbidden_burden,[...])`
- `outcome=verify(receipt? or residual)` -> `outcome=verify(coalesce(receipt,residual))`
- preserve `union` and `if` from the prior grammar patch candidate;
- add explicit numeric comparisons `>`, `<`, `>=`, `<=` to the operator set.

Counterhypothesis: generic prose-like infix identifiers may reduce authoring friction. Falsifier for this strict-normalization candidate: a generic-infix grammar demonstrates deterministic parse/canonical roundtrip, stable semantic hashes and lower repair cost across the G9 corpus without ambiguity or authority confusion.
