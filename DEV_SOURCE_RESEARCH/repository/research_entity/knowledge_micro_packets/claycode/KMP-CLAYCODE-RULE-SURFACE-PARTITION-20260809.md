# KMP — ClayCode Rule Surface Partition

- packet_id: `KMP-CLAYCODE-RULE-SURFACE-PARTITION-20260809`
- domains: `xeno_claycode`, `compiler_runtime`, `formal_methods_testing`, `frank_architecture`
- epistemic_class: `EXECUTABLE_SYNTHETIC_COMPILER_FRONTEND_RESULT`
- status_hint: `SUPPORTED_LOCAL_PROXY + OPEN_PRODUCTION_REPLICATION`
- origin_actor: `chatgpt-secondary`
- provider/model: `OpenAI / GPT-5.6 Sol`
- run: `claycode-20260809T1710p0700-chatgpt-rule-surface-partition`
- evidence: `EXECUTABLE_RESEARCH_RECEIPT.json`
- source_ancestry: `current G9 V3 + published grammar + current stack + live typed-RelationIR sibling`

## Atomic claim

The current ClayCode G9 rule surface should not be made parser-closed by continually widening the executable operator set. In an executable EBNF-shaped proxy, current expression syntax covered 29/53 G9 rule lines and a minimal relational-operator repair covered 33/53. A registry-gated declarative `PredicateIR` compatibility layer deterministically covered 17 additional lines, yielding 50/53, while preserving fail-closed behavior for three semantically ambiguous clauses.

## Adversarial evidence

- whitespace semantic-hash preservation: `20000/20000`;
- ordered binary operand swaps changed semantic hash: `10000/10000`;
- unknown relation mutations rejected by registry-gated normalizer: `5000/5000`;
- permissive arbitrary-word relation grammar accepted generated nonsense: `5000/5000`.

## Constraint

This is a local compiler-front-end proxy, not the production BASE parser or Ubuntu target receipt. The current stack may intentionally be a distinct control/protocol surface; its low expression-grammar closure is evidence for explicit surface ownership, not proof it must compile as G9 application code.

## Architecture implication

Freeze three compiler-visible surface classes: executable `ExprIR`, declarative typed `PredicateIR/ConstraintIR`, and explicitly owned protocol/research surfaces. Relation names need signatures/registry ownership; semantic relation resolution carries no execution authority. Ambiguous legacy rules require explicit authoritative rewrite or AST mapping before parser freeze.

## Falsifier / next test

Build the production parser/canonicalizer and run every current G9 source file plus dialect registry through `parse -> typed IR -> canonical print -> parse`. Require exact diagnostics for the three ambiguous rules, unknown-relation rejection, typed method signatures/comments, and stable semantic hashes. Then replicate on the Ubuntu developer target.