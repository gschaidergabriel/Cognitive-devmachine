# ClayCode Trigger Run — Lexical Closure at the BASE Parser Boundary

Run: `claycode_20260809T1655p0700_chatgpt_lexical_closure`  
Trigger: `claycode`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE / IN_PROGRESS`  
Promotion: **NONE**

## Executive result

This run did not redesign ClayCode. It found and isolated two parser/lexer closure problems at the current G9 source-to-canonical-IR boundary and turned them into executable negative evidence.

1. **Reference-token closure:** the admitted EBNF says a `ref` is `@` followed by a non-whitespace resource path. Under the literal maximal-munch interpretation this token consumes adjacent structural delimiters. A deterministic 10,000-case adjacent-reference probe overconsumed **10,000/10,000** cases. A delimiter-aware candidate failed **0/10,000** matched cases.
2. **Hyphen/minus collision:** bare identifiers currently allow `-` while `-` is also an operator. Under longest-match lexing, **10,000/10,000** generated unspaced `a-b` forms were also valid single identifiers. Removing hyphen from bare identifiers resolves this tested ambiguity but rejected **10,000/10,000** generated hyphenated names accepted by the current grammar, so that repair is **not promoted**.

The narrow architecture consequence is:

> ClayCode BASE needs an explicit, versioned lexer/parser contract before semantic hashing, canonicalization and compiler receipts can be trusted. `ProgramSemanticId` should be derived from canonical typed IR after deterministic parsing, while grammar/lexer/compiler versions remain separate provenance/contract identity.

No FRANK-specific syntax primitive is added. No stage advances.

## Canonical and program grounding

Verified immediately before durable writes:

- Research Entity / Clay canonical: RAE-8.8, revision 2, state hash `04234efd...f489346`;
- worker provenance: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol;
- current stage: `BASE_CLAYCODE_RELEASE`, `IN_PROGRESS`;
- current admitted ClayCode stack: G9 V3 research candidate plus `grammar.ebnf`;
- BASE law: `less change, more compile`;
- Frank v0.1 target: Ubuntu Linux developer system; Android/mobile/edge is outside the v0.1 release gate.

## Fusion 1 — current mesh and concurrent evidence

The run assimilated the current Clay/FRANK/ClayGraph/UnifiedDB/GWT/Hyperposition/Emergenz/Harness/ClayCode context through the same branch set required by the ClayCode trigger protocol. The official repository-local interconnection preflight could not be executed because this hosted ChatGPT session has GitHub connector access but no repository checkout; the run therefore records a manual fail-closed manifest rather than claiming validator success.

Concurrent repository work materially narrowed the new contribution:

- an immediately preceding ClayCode run already preserved the G9 self-conformance failures for missing `>`, `>=` and `if` grammar coverage;
- a concurrent grammar coverage probe also flagged `projection`, `experiment`, `hypothesis` and typed method-signature constructs not represented by the checked EBNF;
- concurrent loop/runtime work established that current recurrence demands do not justify a FRANK-specific syntax primitive and that behavior-changing schedule/commit/halting dimensions belong in typed semantic identity;
- concurrent transactional-loop work further separated static `ProgramSemanticId` from dynamic snapshot/transaction/effect replay identity and showed guarded snapshot+retry removed all tested stale-decision mismatches in its synthetic class.

Therefore this run deliberately did **not** re-file the already-known control/operator grammar gaps. It tested a different boundary: lexical closure and token identity.

## Executable experiment

Experiment: `EXP-CC-LEXICAL-CLOSURE-20260809-01`  
Artifact: `LEXICAL_CLOSURE_PROBE.py`  
SHA-256: `d62977c934bee3cbfe3b90c380c1407c52aa1048c2c656086fb666db1b8d5345`  
Runtime: ChatGPT local Python container  
Seed: `20260809`  
Cases per family: `10,000`

### Test A — adjacent references

Generated forms equivalent to:

```text
[@path/A.clay,@path/B.clay]
```

Literal current matcher modeled from the EBNF: `@\S+`.

Observed:

- current overconsumption: **10,000 / 10,000**;
- delimiter-aware candidate failure: **0 / 10,000**.

This is `NR-CC-REF-LEXICAL-CLOSURE-20260809`.

### Test B — unspaced minus

Generated forms equivalent to:

```text
a-b
```

Current bare identifier model: `[A-Za-z_][A-Za-z0-9_-]*`.

Observed:

- entire expression also accepted as one current identifier: **10,000 / 10,000**;
- candidate bare identifier excluding hyphen allowed deterministic `identifier - identifier`: **0 / 10,000** failures in that test family.

But the same candidate rejected every generated hyphenated name that the present grammar admits: **10,000 / 10,000**. Therefore the test establishes ambiguity, not the correct migration.

This is `NR-CC-HYPHEN-MINUS-AMBIGUITY-20260809`.

## External triangulation / Fusion 2

Only primary/official technical documentation was used for external architecture comparison.

### Tree-sitter

Official Tree-sitter grammar documentation makes lexical conflict resolution explicit: lexical precedence, match length, specificity and rule order can affect token selection. This supports treating ClayCode lexer policy as a real compiler contract rather than assuming the EBNF alone determines ambiguous tokenization.

Sources:
- https://tree-sitter.github.io/tree-sitter/creating-parsers/3-writing-the-grammar.html
- https://tree-sitter.github.io/tree-sitter/creating-parsers/2-the-grammar-dsl.html

### MLIR

MLIR's official language reference deliberately uses a restricted bare-identifier grammar and separate sigil/string forms for symbols, while its dialect/ODS infrastructure treats parsing, printing and verification as part of the typed IR contract. This is useful independent design evidence for splitting human-friendly symbol spelling from an unambiguous parser surface instead of overloading one bare identifier class.

Sources:
- https://mlir.llvm.org/docs/LangRef/
- https://mlir.llvm.org/docs/DefiningDialects/
- https://mlir.llvm.org/docs/DefiningDialects/Operations/

### Component/FFI boundary

The Bytecode Alliance component model/WIT provides a separate reinforcing pattern for the later BASE ABI/FFI stage: typed interfaces and resources describe what crosses a component boundary, while Wasmtime/WASI capability exposure remains explicit. This does not decide ClayCode syntax, but it supports keeping typed interface identity distinct from ambient execution authority.

Sources:
- https://component-model.bytecodealliance.org/design/wit.html
- https://docs.wasmtime.dev/security.html

## Hypotheses and counterhypotheses

### H-CC-LEXREF-018 — OPEN_SUPPORTED_FOR_TESTED_CLASS

ClayCode refs should be delimiter-aware or contextually parsed so structural delimiters cannot silently enter Ref identity.

Counterhypothesis: the real production parser already terminates refs contextually and only the public EBNF is stale.

Falsifier: execute the admitted canonical parser and prove lossless delimiter-safe roundtrip across the full source corpus without changing the grammar contract.

### H-CC-IDCLASS-019 — OPEN

Separating bare identifiers from escaped/sigil/quoted symbols is likely safer than globally forbidding hyphens.

Counterhypothesis: contextual/precedence-aware lexing can preserve current hyphenated bare names with lower migration cost.

Falsifier: corpus-wide parser differential shows the current naming/operator scheme is deterministic and low-repair-cost under all admitted no-space arithmetic and symbol forms.

### H-CC-LEXER-RECEIPT-020 — OPEN_SUPPORTED_ARCHITECTURE_CANDIDATE

Lexer/parser policy and compiler version belong in contract/provenance identity; `ProgramSemanticId` belongs after deterministic parse/canonicalization.

Counterhypothesis: one monolithic raw-source/contract hash is sufficient for semantic caching, migration and replay.

Falsifier: matched equivalence/replay tests show the monolithic identity has no false distinctions, unsafe reuse or collision across source formatting, parser versions, runtime schedules and transaction roots.

## Goodman anti-echo result

The new lexical evidence is not FRANK-derived and therefore does not gain support merely because FRANK needs ClayCode. The prior FRANK loop requirement remains **REFINED** toward generic structured control plus typed schedule identity, not special syntax.

- delimiter-aware Ref repair: `REFINED/SUPPORTED_FOR_TESTED_CLASS`;
- global removal of hyphens from bare identifiers: `UNRESOLVED`, not promoted;
- separate static semantic versus parser/compiler versus execution/replay identity: `REFINED`, with this run adding the lexical pre-canonicalization layer.

The repository-local Goodman validator was not executable in this hosted session; the artifact explicitly records that absence.

## ClayGraph and UnifiedDB findings

### ClayGraph

No new graph semantic primitive is required. The new constraint is upstream: graph Ref identity must derive from deterministic canonical parsing, not arbitrary raw token slices. Graph activation/relevance remains non-authoritative.

### UnifiedDB

No physical or logical database redesign follows. UnifiedDB should receive canonical parsed semantic IDs and preserve parser/compiler version in provenance where needed. This aligns with the concurrently refined split between static program semantics and dynamic execution/replay roots.

## Architecture delta

Minimal current candidate:

```text
SourceText
  -> LexerPolicy(version/hash)
  -> Parser(version/hash)
  -> TypedCanonicalIR
  -> ProgramSemanticId(hash(canonical typed meaning))
  -> Lowering/Compiler(version/hash)
  -> ExecutableArtifact
  -> ExecutionReplayId(snapshot/txn/effect/runtime roots)
```

Rules:

1. `@Ref` tokens terminate at structural delimiters unless a quoted/escaped form explicitly includes them.
2. Identifier/operator ambiguity must be resolved by a documented deterministic lexer contract, not incidental whitespace or host-regex behavior.
3. Do not change bare-identifier compatibility until a repository-wide symbol inventory and parser differential are measured.
4. `ProgramSemanticId` is post-parse/post-canonicalization and should ignore source spelling proven semantically irrelevant.
5. Parser/compiler versions remain provenance/contract data even when two versions produce the same `ProgramSemanticId`.
6. Execution/replay identity stays separate and includes snapshot/transaction/effect/runtime roots when behaviorally relevant.

## Branch feedback

- **ClayCode:** implement delimiter-safe Ref lexing; inventory hyphen usage; then property-test full parse/canonical-print/parse closure.
- **FRANK:** no architecture semantic change; use frozen FRANK sources as downstream parser/compiler fixtures.
- **Harness:** add adjacent-ref and `a-b` vs `a - b` parser oracles before H2 differential replay.
- **UnifiedDB:** persist canonical parsed identities plus parser/compiler provenance; keep execution roots separate.
- **ClayGraph:** project canonical IDs, never raw token ambiguity.
- **GWT / Hyperposition / Emergenz:** no mechanism promotion; parser correctness is simply an upstream validity condition.
- **Clay:** BASE implementation direction reinforced; no stage advance.

## Highest-information next execution

1. Run a repository-wide inventory of hyphenated bare identifiers and every `@ref` delimiter context.
2. Implement the production lexer/parser branch with the already identified grammar-control repairs plus delimiter-safe refs.
3. Parse every admitted G9 V3, dialect registry and Dynamic Binding Lattice source; do not special-case failures silently.
4. Add `parse -> canonical print -> parse` property/fuzz tests and prove typed-IR semantic-hash stability.
5. Only after parser closure, progress CC-WP-02/03/04 toward APP-06 (compiler/tool) and then the broader BASE application suite.
6. Reopen core syntax only if a concrete executable application/FRANK counterexample survives parser/runtime/FFI implementation.

## Completion

Completed in this run:

- canonical join and final pre-write reread;
- all registered branch coverage via manual hosted-session interconnect assembly;
- concurrent ClayCode evidence assimilation;
- executable 30,000-family-case lexical probe (10,000 cases in each of three matched families);
- two scoped negative results;
- three falsifiable hypotheses/counterhypotheses;
- Goodman anti-echo review;
- Tool Execution Manifest;
- branch feedback across the full mesh;
- one atomic ClayCode knowledge micro-packet;
- durable GitHub run artifacts.

Not completed / intentionally not claimed:

- official local `research_interconnect_preflight.py` execution;
- official local `goodman_filter_check.py` execution;
- E2B execution by this worker;
- production parser implementation;
- repository-wide hyphen compatibility scan;
- ClayCode BASE gate progress or canonical promotion.
