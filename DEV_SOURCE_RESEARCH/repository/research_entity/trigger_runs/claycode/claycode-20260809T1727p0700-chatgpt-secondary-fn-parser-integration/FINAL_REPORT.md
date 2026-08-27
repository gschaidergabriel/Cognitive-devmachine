# ClayCode Trigger Run — D + typed function integration and strict-parser discriminator

**run_id:** `claycode-20260809T1727p0700-chatgpt-secondary-fn-parser-integration`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**target host:** Ubuntu Linux developer system  
**decision:** **RESEARCH DELTA · NO SCIENTIFIC PROMOTION · BASE GATE REMAINS NOT_PASS**

## Executive result

This run did not invent another ClayCode architecture. It followed the current `less change, more compile` law and joined two already-existing non-promoted results:

1. the locally leading-but-unselected D production-parser candidate; and
2. the independently tested minimal typed `fn` definition surface that closes the current definition→call gap.

The integrated candidate passed the local non-strict parser→canonical-IR→type/binding→lowering chain:

- base D+`fn` program parsed, including contextual keyword compatibility (`fn` as a record field);
- 1,000 formatting/comment variants: 0 parse failures, 1,000/1,000 same `semantic_hash`, 1,000/1,000 changed provenance-bound `contract_hash`;
- 500 semantic mutations: 500/500 changed `semantic_hash`;
- 8/8 negative classes rejected (undefined callee, arity mismatch, undefined variable, duplicate function, duplicate parameter, return-type mismatch, unsupported recursion in this minimal surface, untyped parameter surface);
- 20,000 randomized calls lowered to separately executed Python: **0 differential mismatches**.

However, a new discriminating negative result blocks parser freeze: **the unmodified D candidate already fails strict LALR construction under Lark 1.3.1, and the D+`fn` extension also fails strict construction.** Therefore this run cannot claim a conflict-free parser, cannot select D, and cannot advance CC-WP-02.

## Fusion 1 — internal evidence

The current BASE gate requires executable realization, not more semantic invention. All 14 ClayCode BASE work packages remained OPEN in the workspace read, and the mandatory application suite still had no recorded passes. Prior evidence supports a universal-core proxy and capability/effect mechanisms, but the gate explicitly treats those as design evidence, not a finished compiler.

Immediately preceding ClayCode work narrowed two issues:

- current admitted calls lack a general reusable function-definition surface;
- N/S/D production-like parser candidates can all parse the current corpus after shared repairs, with D locally leading on migration cost but explicitly `LEADING_NOT_SELECTED`.

This run tested the next non-duplicative question: can the already-tested function-definition contract be integrated into D without a new cognitive/FRANK-specific semantic primitive?

## Nine-branch mesh synthesis

See `INTERCONNECT_MANIFEST.json`.

- **FRANK:** C9 lineage-fused requirements need reusable typed execution, replay/idempotency and external authority separation; they do not justify FRANK-specific function semantics.
- **ClayResearch:** current critical path is conformance → parser → canonical typed IR → type/effect → evaluator → legality-gated lowering → runtime/FFI/stdlib → app suite → FRANK.
- **Harness:** semantic retry identity must be exact and deterministic; fuzzy matching is not acceptable at consequential state boundaries.
- **ClayGraph:** exact/high-confidence identity queries may bypass graph propagation; function resolution is an even stricter exact-identity case.
- **UnifiedDB:** typed semantic identity and exact representation/contract identity remain distinct; replay and selection integrity are separate.
- **GWT:** latest R7 says current G9 appears representationally sufficient for its typed contract and still awaits compiler/runtime validation.
- **Hyperposition:** multiple frontend alternatives may remain OPEN, but a selected compiled artifact needs one explicit callee binding.
- **Emergenz:** function binding is orthogonal to emergence evidence; measurement receipts remain ordinary typed semantics.
- **ClayCode:** the result belongs in parser/canonical IR/symbol table/type checker/compiler work, not a new special-purpose branch.

## Deep ClayGraph finding

ClayGraph G3's self-use negative result rejected universal graph propagation for exact identity lookup. This transfers directly to compiler binding:

`ClayGraph activation/proximity != symbol resolution`.

A missing or ambiguous function target must fail closed or invoke an explicit compiler diagnostic/recovery path; it must never pick the nearest activated graph node.

## Deep UnifiedDB finding

UnifiedDB U2 separates typed semantic identity from exact emitted representation identity. The current experiment independently reproduced the value of that separation:

- source formatting/comments changed the provenance-bound `contract_hash`;
- canonical meaning stayed stable under those variants;
- semantic mutations changed the semantic identity.

Candidate compiler chain:

`source -> parser -> canonical typed symbol/signature identity -> ProgramSemanticId -> type/effect closure -> lowering identity -> emitted artifact hash -> execution receipt`.

No database record, vector proximity or work item mints the callee identity.

## Fusion 2 — independent primary-source triangulation

Official compiler/runtime specifications supply independent comparison anchors:

- MLIR SymbolTable requires unique symbol names in a parent symbol table and explicit symbolic references (`SymbolRefAttr`); `func.func` / `func.call` are canonical examples.
- LLVM models function types as return type + formal parameter types; its call semantics bind arguments to a specified function and signature.
- WebAssembly function invocation assumes a validated function instance and function type before execution.

These sources support exact function/symbol/signature semantics. They **do not** establish that ClayCode must spell the construct `fn` or select D over N/S.

Primary sources:
- https://mlir.llvm.org/docs/SymbolsAndSymbolTables/
- https://llvm.org/docs/LangRef.html
- https://webassembly.github.io/spec/core/exec/instructions.html

## Executable experiment

Durable experiment evidence is in `EXECUTABLE_RESEARCH_RECEIPT.json`, which binds the exact prior D grammar candidate blob and function-surface candidate blob, the local runtime/evidence class, identity tests, negative checks, lowering hash and all release blockers. The executed script remained on the hosted local execution surface; this report does not pretend it was persisted to GitHub.

Evidence class: `LOCAL_ISOLATED_LINUX_EXECUTION_NOT_TARGET_UBUNTU_ACCEPTANCE`.

The only tested integration delta was top-level `fn_decl`, typed parameter productions and contextual handling for the new keyword.

### Strict-parser negative

Strict-LALR construction fails for the baseline D grammar and the extended grammar. Since strict construction stops after reporting a conflict and conflict report ordering can vary, this run does **not** claim the extension uniquely caused the conflict. The valid conclusion is narrower:

> conflict-free D parser status is not established, and D+`fn` cannot be frozen while that remains true.

This negative result is preserved in `NEGATIVE_RESULTS.json`.

## Goodman anti-echo review

Verdict: **REFINED**.

FRANK's requirement for general-purpose reusable typed execution survives independent checks, but the exact surface is narrowed:

- no FRANK-specific function primitive;
- no inference that `rule`/`needle`/`cycle` already provide a verified general function ABI;
- no claim that `fn` is canonical;
- exact symbol/signature binding belongs in compiler/typed IR;
- model text, GWT, ClayGraph and UnifiedDB never become function authority;
- target Ubuntu and production compiler evidence remain required.

See `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

## Hypotheses / counterhypotheses

Four explicit OPEN hypotheses are recorded in `HYPOTHESIS_MATRIX.json`. The highest-information discriminator is now:

1. make the admitted parser conflict surface explicit and conflict-free (or formally justify deterministic conflict resolution);
2. integrate canonical symbol/signature tables with `semantic_hash` vs `contract_hash` separation;
3. compare D+`fn` against N/S and any existing-equivalent executable surface using target Qwen-class reader repair/error cost;
4. lower the same canonical function corpus through the production compiler on the Ubuntu developer host;
5. only then attempt APP-01 CLI and APP-02 real HTTP/website.

## Branch feedback

`BRANCH_FEEDBACK_MANIFEST.json` returns explicit refinement/NO_CHANGE receipts to all nine current branches. The main cross-branch delta is not syntax: exact compiler identity joins the Harness/ClayGraph/UnifiedDB exactness family.

## Late live-worker assimilation

Two concurrent ClayCode results landed before durable write and were ingested rather than counted as independent replication:

- `20260809T1724p0700-chatgpt-secondary-parser-closure` preserves a separate declared-EBNF self-closure negative: a faithful proxy accepted only 2/9 tested current-source fragments, with missing/underspecified comparison, conditional, comment and legacy-predicate classes. This strengthens the need for grammar/parser closure but is distinct from this run's strict-LALR conflict result.
- `KMP-CC-CONTROL-EFFECT-CLOSURE-20260809` reports a local control/effect proxy with 50,000 semantic differential cases and 20,000 transitive-effect mutations. It supports the same implementation-first direction: canonical typed IR can carry control/effect closure without a new FRANK-specific primitive. Therefore this run's rejection of recursion is explicitly only a limitation of the minimal `fn` experiment, not a claim that recursion should be absent from ClayCode.

These arrivals do not select D, do not promote `fn`, and do not change the BASE gate.

## Decision

`RESEARCH_DELTA = YES`  
`SCIENTIFIC_PROMOTION = NONE`  
`CLAYCODE_CORE_CHANGE = NO`  
`FRONTEND_CANDIDATE = D + typed fn`  
`CANDIDATE_STATUS = OPEN / NOT_SELECTED`  
`STRICT_PARSER_STATUS = NEGATIVE_RESULT`  
`CC-WP-02 = OPEN`  
`GENERAL_PURPOSE_GATE = NOT_PASS`

The practical result is a narrower BASE path:

> **Function definition→call closure appears locally realizable without new FRANK-specific semantics, but parser-conflict debt must be resolved before any frontend freeze or release claim.**
