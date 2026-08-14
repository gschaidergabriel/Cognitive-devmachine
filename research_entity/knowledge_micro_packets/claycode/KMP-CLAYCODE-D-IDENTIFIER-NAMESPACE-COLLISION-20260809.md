# KMP — ClayCode declared relation identifier-namespace collision

- packet_id: `KMP-CLAYCODE-D-IDENTIFIER-NAMESPACE-COLLISION-20260809`
- domains: `claycode`, `frank`, `claygraph`, `harness`
- epistemic_class: `EXECUTABLE_NEGATIVE_RESULT`
- status_hint: `NEGATIVE_RESULT`
- origin_actor: `chatgpt-secondary`
- provider/model: `OpenAI / GPT-5.6 Sol`
- run: `claycode_20260809T1615p0700_chatgpt_nsd_namespace`

## Atomic finding

In the tested Lark LALR implementation of ClayCode candidate D, compiling finite declared bare relation words into lexer terminals reserved those spellings against the ordinary identifier namespace: **0/15** legal current relation spellings remained parseable as plain identifier controls, versus **15/15** for the S and N proxy arms.

This refutes only the tested finite-terminal implementation strategy. It does **not** refute declared readable relations generally. D remains viable if a production parser can implement scoped soft-keyword/contextual declaration or an explicit escape mechanism while preserving deterministic AST, diagnostics and full-corpus closure.

A second source mismatch is preserved separately: `4B_emits` and `4B_need_not_learn` are current G9 relation spellings but are not legal under the current `ident` production because they begin with a digit.

## Evidence

- `research_entity/trigger_runs/claycode/claycode_20260809T1615p0700_chatgpt_nsd_namespace/EXECUTABLE_RESEARCH_RECEIPT.json`
- current source: `research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay`
- current grammar: `research_entity/claycode/g9/grammar.ebnf`

## Counterhypothesis / falsifier

A scoped D production parser may eliminate the collision with lower total migration/context cost than N or a redesigned S. Test full G9+dialects plus explicit relation/identifier shadowing, escaping, typo mutations, roundtrip semantic hash, diagnostics, compile latency and target-reader repair cost.

## Promotion boundary

No language, BASE-stage or canonical-state promotion follows from this packet.