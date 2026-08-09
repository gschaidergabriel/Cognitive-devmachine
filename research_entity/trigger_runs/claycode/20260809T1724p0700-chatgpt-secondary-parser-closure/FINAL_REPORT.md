# ClayCode Trigger Run — Parser/Canonical Surface Closure

Run ID: `20260809T1724p0700-chatgpt-secondary-parser-closure`  
Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
Canonical parent: `r2` · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**  
Target implementation scope: Frank v0.1 on Ubuntu Linux developer system only.

## Executive result

The highest-value current ClayCode blocker is not lack of another cognitive concept. It is executable closure between the admitted G9 V3 source surface and its declared grammar.

The current G9 V3 source contains syntax that the current `grammar.ebnf` does not declare or leaves materially underspecified, including:

- `<` and `>` comparisons used by current rules;
- `if { ... }` conditional execution used in the current cycle;
- `//` comments;
- current legacy predicate-like rule forms such as `never_implies`, `returns`, and `is_explanation_of_derivation`;
- a flat expression rule that provides no explicit executable precedence/associativity contract.

A corrected local executable experiment compared a parser proxy faithful to the current declared EBNF against a minimal compatibility candidate on nine exact current-G9-V3 fragments.

Result:

- declared-grammar baseline proxy: **2/9 pass, 7/9 fail**;
- minimal candidate: **9/9 pass, 0/9 fail**.

This is a real counterexample to treating the current grammar as release-ready for the tested source surface. It is **not** whole-file parser completion and it does not close `CC-WP-02`.

## Why this matters to the current gate

`BASE_CLAYCODE_RELEASE` is still `NOT_PASS`; all 14 current ClayCode work packages remain open. The current release law is `less change, more compile`: preserve existing semantics unless a concrete executable counterexample forces a language correction.

This run found exactly such a counterexample, but the repair can remain narrow: fix parser/surface closure and canonicalization rather than inventing new cognitive semantics.

## Fusion 1 — internal evidence

### ClayCode

Current G9 V3 already carries substantial semantic machinery: delta calculus, provenance algebra, capability-bearing effects, dialect contracts, UnifiedDB/ClayGraph deltas, GWT readouts, effect intents, bounded equivalence search, reader/context accounting and native-cognition task structures.

The practical gap exposed here is that the executable source surface and formal grammar are not yet closed over one another.

### FRANK

No current `FRANK_ARCHITECTURE.claycode.json` was located. Repository search returned no artifact and the expected-path fetch returned 404. No artifact was fabricated. Current FRANK loop-of-loops and adaptive-visual-learning directives were therefore used only as provisional requirements.

### Harness

The Harness ClayCode adapter remains blocked on ClayCode release. Parser/canonicalizer closure is therefore a direct prerequisite for H2 rather than an isolated language-cleanup task.

### ClayGraph / UnifiedDB

Current graph and persistence substrates already require epoch identity, provenance, selection/projection receipts, hyperrelations, revisioned work/capability state and explicit execution receipts. These requirements strengthen the case for deterministic typed IR and canonicalization, but they do not require arbitrary new surface operators.

### GWT / Hyperposition / Emergenz

These branches require typed causal/readout/intervention structures and strict distinctions such as selection vs causal use, activation vs truth, recurrence vs emergence and semantic vs physical topology. Nothing found in this run requires new surface-language semantics to represent those distinctions.

## Hypotheses and counterhypotheses

### H-CC-PARSER-01 — current grammar is not closed over current G9 V3

Status: `SUPPORTED_FOR_TESTED_FRAGMENTS`.

Mechanism: current source constructs are absent or underspecified in the EBNF.

Counterhypothesis: the mismatch is cosmetic documentation drift and has no executable effect.

Falsifier: a parser generated from the current declared grammar parses the exact tested fragments and whole current G9 source without hidden extensions.

Observed: baseline proxy accepted 2/9 and rejected 7/9.

### H-CC-PARSER-02 — minimal compatibility repair is sufficient

Status: `SUPPORTED_FRAGMENT_LEVEL_ONLY`.

Candidate delta:

1. lex `//` comments as extras;
2. add `<`, `>`, `<=`, `>=` comparisons;
3. add explicit `if/else` statement form;
4. define executable expression precedence/associativity;
5. accept only a bounded legacy-predicate compatibility set and canonicalize it into typed IR rather than permitting arbitrary prose-like operators.

Observed: 9/9 targeted fragments parse in the candidate.

Falsifier: whole-file parse/canonical roundtrip reveals irreducible ambiguity or meaning changes.

### H-CC-RULE-RUNTIME-SPLIT-01 — separate rule language from executable expressions

Status: `OPEN`.

Candidate architecture: retain a compatibility-oriented `rule_expr` for declarative research/constraint statements, but lower executable runtime behavior through a stricter precedence-defined `runtime_expr`.

Counterhypothesis: one unified typed operator table is simpler and equally deterministic.

Next test: whole-file parse + canonical roundtrip + mutation/fuzz corpus.

### H-CC-FFI-01 — WIT-like typed host boundary is useful

Status: `OPEN`.

Independent primary implementation evidence shows WIT can define typed component imports/exports while WASI/Wasmtime provides explicit capability-scoped host resources. This is evidence for a **candidate interface pattern**, not evidence that WASM/WASI is the best first ClayCode backend.

Counterhypothesis: native Ubuntu ABI/FFI is simpler/faster with equivalent safety behind the same Clay authority gateway.

Next test: native-vs-WASM/WASI Ubuntu application and authority-bypass benchmarks.

### H-CC-LOOP-REP-01 — current typed primitives can represent loop dynamics

Status: `OPEN`.

The loop-of-loops research requirement should first be attempted with existing records/tensors/interventions/receipts. No new loop syntax is justified yet.

Next test: compile a minimal `LoopDynamicsReadout` plus continue/halt/escalate, lesion/rescue and rollback contract after parser closure.

## Executable experiment

Experiment: `CC-G9-PARSER-DELTA-20260809`.

Runtime: local Linux x86_64 ChatGPT execution fallback; Python 3.13.5; Lark 1.3.1.

Preferred E2B surface was not exposed in this ChatGPT session, so no E2B evidence is claimed. SandboxAPI remains non-runtime evidence under the current protocol state.

Corpus: nine exact current-source fragments covering comparisons, conditionals, comments, legacy rule predicates and already-supported controls.

Hashes and full test details are preserved in `EXECUTABLE_RESEARCH_RECEIPT.json` and the committed experiment script.

A first quick probe was rejected during method audit because it was too coarse. That failed method is preserved as a negative result rather than hidden.

## External primary-source research

External research was used only to test design direction, not to replace the executable ClayCode result.

- Tree-sitter documentation independently supports explicit precedence/associativity, conflict handling, comment extras and parser test corpora for reliable grammar construction.
- The Rust Reference provides an independent mature example in which comparison operators and `if` forms are explicitly grammar-defined and operator precedence is explicit.
- WebAssembly Component Model WIT provides a typed interface/world contract model for imports and exports; it is an IDL rather than a general-purpose behavior language.
- Wasmtime/WASI documents filesystem/resource access through explicit preopened/capability-scoped interfaces, supporting the ClayCode principle that computational expressibility should remain separate from ambient authority.

These are mechanism/design analogues, not ClayCode replication.

## Goodman anti-echo results

- External capability/effect authority boundary: `SUPPORTED` at mechanism level; final ClayCode API remains unproven.
- FRANK loop-of-loops mechanism: `UNRESOLVED`; this run produced no independent loop-dynamics execution evidence.
- WASM/WASI as first backend: `REFINED`; viable candidate boundary/backend, not mandatory winner.
- Adaptive visual learner state representation: `UNRESOLVED` scientifically but remains an owner-fixed product requirement; first try existing typed state/version/provenance primitives.

Full review: `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

## Negative results

1. `N-CC-G9-GRAMMAR-CLOSURE-20260809`: current declared EBNF is not sufficient for the tested current G9 V3 source surface.
2. `N-CC-FIRST-PROBE-20260809`: the first quick checker was inadequate and was discarded/replaced.

No negative result was upgraded into a universal claim beyond its tested scope.

## Branch feedback

- `claycode`: parser/canonicalizer closure is now a concrete BASE blocker with a minimal repair candidate.
- `harness`: H2 dependency is sharpened; next evidence must be whole-file closure before ClayCode Harness work can rely on this grammar.
- `frank`: loop/adaptive-vision requirements preserved as representation targets; no independent mechanism promotion.
- `clayresearch`: compile/realize priority reinforced.
- `gwt`, `emergenz`, `hyperposition`, `claygraph`, `unifieddb`: `NO_CHANGE` to scientific semantics; their typed distinctions remain inputs to the eventual canonical IR.

## Architecture delta candidate

Do **not** promote yet. Candidate for the next compiler iteration:

```text
source surface
  -> lexer/comments
  -> statement split
       declarative rule_expr      // compatibility, canonicalized to typed predicates
       executable runtime_expr    // explicit precedence/associativity
  -> typed canonical IR
  -> deterministic semantic hash
  -> type/effect/authority validation
  -> lowering/runtime
```

Hard boundary retained:

`expressibility != authority`

and

`model output != execution authority`.

## Gate impact

`CC-WP-02-PARSER-CANON`: remains `OPEN`, but now has a concrete executable blocker and tested repair direction.

`CC-WP-01-SPEC-FREEZE`: cannot honestly freeze until whole-file grammar/source closure is tested.

`CC-WP-11-FUZZ-CONFORMANCE`: should inherit the exact counterexample corpus and expand it with precedence, keyword, malformed-rule and canonical-roundtrip mutations.

No application proof (`APP-01..APP-10`) passed in this run. `GENERAL_PURPOSE_GATE` remains `NOT_PASS`.

## Highest-information next step

1. implement a real whole-file parser for the full current G9 V3 source using the minimal repair;
2. deterministic parse -> canonical IR -> print -> parse roundtrip with semantic hash stability;
3. negative/mutation corpus for precedence, keywords, legacy predicate boundaries and comments;
4. then type/effect-check and execute a minimal `LoopDynamicsReadout` plus adaptive-visual learner state contract;
5. only after that begin backend/FFI application proofs on the Ubuntu target.

This sequence advances Frank v0.1 directly while honoring the current rule: **less language invention, more executable ClayCode**.
