# KMP — ClayCode Ref Lexical Closure

- packet_id: `KMP-CLAYCODE-REF-LEXICAL-CLOSURE-20260809`
- domains: `xeno_claycode`, `formal_methods_testing`, `tooling`
- epistemic_class: `EXECUTABLE_SYNTHETIC_GRAMMAR_COUNTEREXAMPLE`
- status_hint: `NEGATIVE_RESULT + OPEN_REPAIR`
- origin_actor: `chatgpt-secondary`
- provider/model: `OpenAI / GPT-5.6 Sol`
- run: `claycode_20260809T1655p0700_chatgpt_lexical_closure`
- evidence: `EXP-CC-LEXICAL-CLOSURE-20260809-01`
- source_hash: `d62977c934bee3cbfe3b90c380c1407c52aa1048c2c656086fb666db1b8d5345`

## Atomic claim

The admitted G9 grammar production `ref = "@", non-whitespace resource path` is not lexically closed for adjacent structural delimiters under a literal maximal-munch interpretation. In 10,000 generated two-reference list cases, the current matcher consumed the comma/following reference; a delimiter-aware candidate failed 0/10,000 matched cases.

## Constraint

This does not prove an unobserved production parser lacks a delimiter special case. It proves the published grammar is insufficiently precise as a standalone deterministic lexer contract for this tested form.

## Architecture implication

Reference lexing should terminate on structural delimiters unless escaped/quoted/contextually admitted. Canonical semantic identity should be formed after deterministic parsing/canonicalization; lexer/compiler identity remains provenance/contract metadata.

## Falsifier / next test

Execute the admitted production parser over the complete G9/dialect/Dynamic-Binding-Lattice corpus and property-test `parse -> canonical print -> parse` for stable typed IR. If the existing parser already provides delimiter-safe lossless behavior without a grammar delta, narrow this packet to documentation/grammar drift only.
