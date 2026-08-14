# ClayCode Trigger Run — Operator Identity + Function Integration

**run_id:** `claycode-20260809T1735p0700-operator-identity-fn-integration`  
**trigger:** `claycode`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**target:** Ubuntu Linux developer system for Frank v0.1  
**decision:** **RESEARCH DELTA COMMITTED · NO SCIENTIFIC/LANGUAGE PROMOTION · BASE REMAINS NOT_PASS**

## Executive result

The latest all-worker parser run made candidate D the local `LEADING_NOT_SELECTED` surface because it preserved the tested G9 semantics with substantially lower migration cost than N/S. This continuation found a new executable frontend counterexample inside that D candidate:

1. ordinary `NAME` permits `-`, so tight `x-y` and `x->y` can lex differently from spaced `x - y` and `x -> y`;
2. the current literal `operator` alternatives are filtered from Lark's default parse tree, so a naïve raw-tree semantic hash cannot distinguish symbolic operators with the same operands.

This does **not** refute the previous typed semantic oracle, because that oracle explicitly retained relation/operator identity. It shows that the production parser→canonicalizer boundary has not yet inherited that guarantee.

A minimal repair candidate was executed:

- remove `-` from ordinary `NAME`;
- alias operator alternatives into explicit parse-tree identities;
- integrate the prior contextual typed `fn_decl` candidate without globally reserving `fn`.

The repair closes the tested counterexample corpus without adding a new cognitive/FRANK semantic primitive.

## Internal grounding

Current inputs reread from GitHub:

- canonical RAE-8.8 r2;
- current BASE ClayCode release workspace, all 14 work packages still OPEN;
- G9 V3 candidate and Dialect Registry V3;
- D LALR candidate from the 17:17 all-worker parser-saturation run;
- parser executable receipt and interconnect manifest;
- prior typed function-definition closure run;
- current integrated ClayResearch report plus branch-sensitive ClayGraph/UnifiedDB boundaries.

The project law remains `less change, more compile`: semantics change only on a concrete executable inadequacy.

## Experiment A — D lexical spacing counterexample

Local isolated Linux / Python 3.13.5 / Lark LALR contextual parser.

For 20,000 randomized matched tight-vs-spaced symbolic operator cases, seed `202608091735`:

- both forms parsed: **20,000/20,000**;
- same default parse-tree hash: **17,520/20,000**;
- different: **2,480/20,000**;
- `->`: **1,241** differences;
- `-`: **1,239** differences.

Cause: the D `NAME` regex admits hyphen. Therefore whitespace that should be semantically irrelevant can change tokenization for subtraction/arrow-shaped text.

This is a real parser-surface counterexample and becomes a regression requirement for CC-WP-02.

## Experiment B — default operator identity loss

Using the current D literal `operator` rule, the 16 symbolic operators

`>= <= != == -> => > < = | + - * / && ||`

with identical operands produced **1 distinct default Lark tree hash**.

Official Lark documentation explains the mechanism: unnamed literal terminals are filtered from trees by default, while aliases/named terminals can preserve identity. This means a normative ClayCode canonicalizer must not naïvely hash the raw default Lark tree and assume operator spelling survived.

## Experiment C — minimal lexical/operator repair

Candidate repair:

- ordinary identifiers become `[A-Za-z_][A-Za-z0-9_]*` in this ASCII research candidate;
- each operator alternative receives an explicit rule alias such as `op_sub`, `op_arrow`, `op_eq`, etc.;
- declaration punctuation is left contextual rather than captured by a global operator terminal.

Results:

- matched spacing retest: **20,000/20,000 same tree-semantic hash**;
- operator identity retest: **16/16 distinct operator hashes**;
- repaired transformed-G9 proxy parses: **PASS**;
- repaired Dialect Registry proxy parses: **PASS**.

The restriction to underscore-style ordinary identifiers is not promoted as final syntax. It is a minimal executable candidate. Rust independently demonstrates a production-language identifier grammar that excludes hyphen from ordinary identifiers, while WebAssembly explicitly defines lexical token formation/longest-match behavior; these are comparison anchors, not proof that ClayCode must copy either language.

## Negative repair control

A single high-priority named `OPERATOR` terminal was tested as a simpler identity-preservation strategy.

Result: **FAIL**. It captured the declaration `=` in an import statement and caused an `UnexpectedToken OPERATOR '='` rejection.

Therefore the current best repair candidate preserves operator identity by rule alternatives/aliases rather than globally stealing declaration punctuation.

## Experiment D — contextual function-definition integration

Prior work showed call syntax without deterministic definition/signature binding is incomplete and tested a minimal typed function declaration. This run integrated that candidate on top of the lexical/operator repair:

`fn f(a:Int,b:Int)->Int = expr`

without globally reserving `fn`.

Results:

- adding `fn_decl` left repaired legacy G9 parse-tree hash unchanged: **PASS**;
- repaired Dialect Registry parse-tree hash unchanged: **PASS**;
- contextual controls `record fn {...}`, `rule fn==fn`, `interface fn {...}`: **PASS**;
- formatting variants: **5,000/5,000 parse + tree hash preserved**;
- function body `+ - * /` mutations: **4/4 distinct hashes**;
- exact static binding: **5,000/5,000 valid composed programs resolved**;
- invalid binding corpus: **3,000/3,000 rejected** across undefined target, arity mismatch and duplicate definition.

This supports integration testing; it does not select/promote `fn_decl`. The production type/effect checker, evaluator, lowering pipeline, target reader and Ubuntu execution remain missing.

## Performance

100 combined transformed-G9 + Dialect parses per candidate in the local sandbox:

- current D: median **9.6185 ms**, p95 **11.8039 ms**;
- strict operator repair: median **9.7146 ms**, p95 **10.5412 ms**;
- repair + contextual `fn_decl`: median **9.6754 ms**, p95 **10.2131 ms**.

Differences are small and local; they are **not** selection evidence.

## External primary-source triangulation

### Lark

Official Lark tree-construction documentation states that unnamed literal terminals are filtered from generated trees by default, while aliases affect tree construction. This independently explains the observed raw-tree operator collapse and supports explicit AST/operator identity handling.

### Rust Reference

Rust ordinary identifiers use `XID_Start/_` followed by `XID_Continue*`, with no medial hyphen class. This supports the engineering plausibility of separating subtraction punctuation from ordinary identifiers, but does not establish ClayCode's final lexical design.

### WebAssembly 3.0 lexical format

WebAssembly defines tokens through an explicit lexical grammar and a longest-match rule, with whitespace separating tokens rather than being silently semantic. This supports making ClayCode's tokenization contract explicit and fuzzing tight/spaced equivalents.

## Goodman anti-echo

The key new evidence is independent of FRANK agreement: the parser itself generated the counterexample.

Verdicts:

- deterministic operator/symbol identity before FRANK reliance: **SUPPORTED**;
- adopt source-level typed `fn_decl` now: **REFINED / remains non-promoted**;
- parser acceptance can grant effect authority: **REFUTED**.

Parallel ClayCode/FRANK/Harness/Graph/DB agreement sharing project ancestry is not counted as independent replication.

## ClayGraph finding

No ClayGraph semantic change is justified. The parser counterexample reinforces an existing boundary:

`graph activation / associative proximity != compiler symbol or operator identity`.

A graph must never repair ambiguous source by guessing a callee or operator, and activation cannot mint truth/effect authority.

## UnifiedDB finding

No UnifiedDB schema/physical consolidation change is justified. The new frontend law is:

`source tokenization -> explicit AST identity -> canonical typed IR -> ProgramSemanticId`

before persistence/query identity can safely reference the program. Database/query proximity is not symbol resolution, and parser acceptance does not authorize transactions/effects.

## Cross-branch result

- ClayCode: **CHANGE** — add lexical-spacing/operator-identity regressions to CC-WP-02; test contextual fn integration in production path.
- ClayResearch: **CHANGE** — BASE path narrows to lexical identity → canonical typed IR → type/effect → lowering.
- Harness: **CHANGE** — H2 source-chain oracle should verify spacing equivalence/operator identity before semantic-ID minting.
- FRANK, ClayGraph, UnifiedDB, GWT, Hyperposition, Emergenz: **NO SEMANTIC CHANGE**.

## Hypotheses

Strongest current hypothesis:

> The lowest-risk CC-WP-02 repair is to make identifier/operator lexical identity explicit and whitespace-robust, then integrate the already-tested generic function-definition contract contextually, without altering cognitive/runtime semantics.

Strongest counterhypothesis:

> Hyphenated identifiers or an existing normative canonicalizer can retain the current surface without ambiguity, and/or existing rule/cycle constructs already provide equivalent function-definition closure.

Highest-information discriminator:

1. implement the repair in the normative repository parser/canonicalizer;
2. prove exact typed operator identity and full G9/Dialect roundtrip;
3. hand it into the real type/effect checker;
4. compare N/S/D on the same Qwen-class 4B reader/repair corpus;
5. replicate in E2B when callable;
6. execute on Andreas' Ubuntu developer target;
7. then proceed directly to evaluator/lowering and APP-01 rather than reopen syntax design without a new executable counterexample.

## Limitations / negative evidence

- no E2B tool was callable in this hosted session;
- SandboxAPI remains not subscribed;
- Andreas' Ubuntu target is not connected to this worker;
- no callable Qwen-class 4B target reader exists here;
- the connector-backed repository is not mounted into the local Python environment, so `research_interconnect_preflight.py` and `goodman_filter_check.py` were **not** executed; manifests/reviews were materialized without pretending those tools ran;
- local transformed-source reconstruction matches the prior D edit-count/+26-char migration signature but is not asserted byte-identical to an unpublished transformed artifact;
- no production compiler/type-effect/evaluator/lowering/app-suite gate passed.

## Decision

`RESEARCH_DELTA = COMMITTED`  
`LANGUAGE_PROMOTION = NONE`  
`D_STATUS = LEADING_NOT_SELECTED`  
`CANDIDATE_REPAIR = STRICT_ORDINARY_IDENTIFIER + EXPLICIT_OPERATOR_IDENTITY`  
`FUNCTION_SURFACE = CONTEXTUAL_NON_PROMOTED_CANDIDATE`  
`CC-WP-02 = OPEN`  
`BASE_CLAYCODE_RELEASE = IN_PROGRESS`  
`GENERAL_PURPOSE_GATE = NOT_PASS`

The useful result is not another language redesign. It is a concrete frontend invariant:

> **Harmless spacing must not change ClayCode meaning, and canonicalization must retain exact operator identity before semantic hashes are minted.**
