# ClayCode Trigger Run — Parser Alignment / BASE Compiler Gate

Run: `claycode_20260809T1539p0700_chatgpt_secondary_parser_alignment`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` (IN_PROGRESS)

## Executive result

This run found and executed a concrete current-language counterexample: the admitted G9 V3 source uses type-level unions and an `if` statement, while the admitted `grammar.ebnf` has neither a type-union production nor an explicit conditional statement. A local executable proxy parser reproduces both failures. A minimal grammar-only repair accepts those cases and preserves the existing generic `Delta<T>` baseline. No ClayCode semantic redesign is justified by this result.

## Evidence

- Current source: `research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay`
- Current grammar: `research_entity/claycode/g9/grammar.ebnf`
- Executable receipt: `EXECUTABLE_RESEARCH_RECEIPT.json`
- Candidate grammar repair: `CLAYCODE_G9_GRAMMAR_PATCH_CANDIDATE.ebnf`
- Probe: `grammar_probe.py`

Observed:

```text
old
  union_field: FAIL line=1 col=54 token=|
  if_cycle: FAIL line=1 col=74 token==
  baseline: PASS
repaired
  union_field: PASS
  if_cycle: PASS
  baseline: PASS
```

Evidence boundary: this proves a mismatch in the current research grammar and an executable proxy translation. It is not yet a full-file final-parser conformance receipt.

## Cross-branch fusion

The current ClayGraph, UnifiedDB, GWT/Emergenz, Hyperposition, FRANK/Harness and Clay directives all increase pressure for typed state, higher-order relations, explicit effect/authority boundaries, replay/provenance and coherent epochs. None supplies evidence that today's parser mismatch requires new semantic primitives. The correct immediate action is parser/canonical-IR realization under the existing semantic basis.

The owner-fixed adaptive visual learner requirement remains an explicit representability test: existing generic records/deltas/provenance may be enough, but this was not executed here, so no new learner-specific primitive is promoted.

## External research

Current WebAssembly Component Model documentation provides an independently developed typed boundary model: WIT defines interfaces/worlds/resources and WASI 0.3 adds native async/future/stream interface primitives. This makes Component Model/WIT a plausible WP-06/WP-07 lowering target. It does **not** replace Clay's dynamic capability/commit authority layer because WIT is an interface contract language, not Clay's authorization semantics. Candidate remains OPEN pending executable APP-02/APP-04 lowering benchmarks.

## Hypotheses / counterhypotheses

1. `H-CC-PARSER-ALIGN-001` — supported for a grammar patch candidate. Falsifier: a parser generated directly from the current EBNF accepts the cited constructs without extension.
2. `H-CC-WASI-COMPONENT-001` — OPEN. Falsifier: application lowerings show semantic gaps, excessive repair/adapter cost or worse latency than native/WASI alternatives.

## Goodman anti-echo

See `FRANK_CLAYCODE_GOODMAN_REVIEW.json`. The parser fix does not depend on FRANK agreement. One FRANK authority-boundary assumption is independently refined using Component Model evidence; the adaptive-visual representability question remains UNRESOLVED because no MVC program was compiled in this run.

## Negative result

`NR-CC-G9-GRAMMAR-SELFALIGN-001`: admitted current grammar is not self-aligned with admitted current source for union types and conditionals. This is a language-tooling negative result, not evidence against the underlying ClayCode semantic model.

## Release/workspace implication

- Do **not** mark `CC-WP-02-PARSER-CANON` complete.
- Promote this run only as a parser-alignment defect + repair candidate.
- Next highest-information executable step: run a real repository parser over the entire G9 V3 corpus, freeze a typed AST for unions/conditionals, then add roundtrip + mutation tests.
- After parser/IR alignment, compile an MVC state/promotion/rollback example to test the FRANK v0.1 visual-learning requirement before inventing any new primitives.

## Protocol limitations

The official `research_interconnect_preflight.py` could not be executed because this ChatGPT session has GitHub connector access but no repository checkout exposed to the local execution surface. A fail-closed manual interconnect manifest was materialized from verified GitHub files; therefore the official interconnect completion gate is **not** claimed. E2B is repository-marked `RUNTIME_VERIFIED` but not exposed as a tool in this session, so the mandated fallback path used the local container and records that evidence class explicitly.

## Research delta

Durable delta committed by this run:
- grammar self-alignment negative result;
- minimal grammar repair candidate;
- executable proxy receipt;
- OPEN WASI Component Model lowering hypothesis;
- Goodman review;
- cross-branch manifest with explicit preflight blocker.
