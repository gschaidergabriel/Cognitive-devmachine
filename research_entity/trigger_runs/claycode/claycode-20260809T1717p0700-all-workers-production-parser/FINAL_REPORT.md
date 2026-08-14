# ClayCode Trigger Continuation — All-Worker Executable Test Saturation

Run: `claycode-20260809T1717p0700-all-workers-production-parser`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**

## Owner directive applied

The user clarified that **all workers in the ClayCode research direction** must execute materially available tests rather than stop at proposals, and then continue to the next highest-information test.

This is now durable through:

- `research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md`;
- `research_entity/rooms/rooms/claycode/ROOM.json` mandatory directive loading;
- ClayCode room event `evt-20260809T0957Z-all-workers-execution-directive.json` with `INTERRUPT_NEXT_SAFE_POINT`;
- revised work item `WORK-CC-BASE-G9-PARSER-FREEZE-001`, now `READY` for the remaining target-specific tests.

The branch law is now:

`test -> receipt -> learn -> recompute -> next_test`

until experimentally saturated or genuinely blocked.

## Executable result

The prior current-G9 work established that the published grammar proxy accepts only **61/86** current G9 top-level units and that strict normalization candidate N can reach 86/86 in a permissive proxy. This continuation moved the question to a production-like deterministic parser and a matched N/S/D discriminator.

Three live source-surface candidates were tested:

- **N** — strict normalization to calls/punctuation/qualified fields;
- **S** — explicit `@relation` surface with typed semantic resolver;
- **D** — finite declared bare relation words with typed semantic resolver.

### 1. New Dialect grammar counterexample

The current published grammar proxy accepts **22/25** current `DIALECT_REGISTRY_V3.clay` top-level units. The failures are interface method signatures:

- `projection(reader:ReaderId)->Ref`;
- `verify(receipt:ReceiptRef)->Verification`;
- `delta(input:Delta)->Delta`.

Adding a typed `method_sig` production lifts the tested Dialect corpus to **25/25**. This is a frontend grammar requirement, not a new cognitive semantic primitive.

### 2. Production-like LALR closure

A shared parser repair was built with:

- typed declaration-specific blocks instead of one generic block;
- explicit newline/semicolon statement separators;
- `method_sig`;
- `if`;
- postfix optional values;
- comparisons `> < >= <=`;
- `or`;
- explicit lexical treatment of keyword-like identifier names.

Under LALR/contextual lexing, **N, S and D each parse the complete current G9 V3 and complete current Dialect corpus**.

S initially exposed a real `@relation` versus existing `@Ref` lexical collision. A lookahead-based relation token policy preserved all tested reference forms and relation forms. S therefore remains viable rather than refuted.

### 3. Matched relation semantic oracle

Twenty current problematic relation forms were lowered to one shared typed relation semantic oracle.

All candidates:

- intended AST: **20/20**;
- roundtrip: **20/20**;
- unknown-relation fuzz: **0 false accepts / 100,000**;
- whitespace semantic-hash preservation: **20,000/20,000**;
- relation mutation changed hash: **20,000/20,000**;
- operand swap changed hash: **20,000/20,000**.

Migration cost differs materially:

- N: 20 changed lines, Levenshtein total 485, +58 chars;
- S: 20 changed lines, Levenshtein total 202, +48 chars;
- D: **5 changed lines, Levenshtein total 31, +26 chars**.

N additionally needs two explicit semantic aliases for current digit-leading `4B_*` relation identities in the tested normalization.

### 4. Semantic identity and collection identity

The tested canonical semantic hash is identical across N/S/D:

`7e51322e2bfd54ce2b190738382e7be20bc05e2f327a7b5a81af73a46566993b`

Formatting fuzz:

- N: 200/200 parse + semantic hash preserved;
- S: 200/200;
- D: 200/200.

Ten semantic mutations per candidate all remained parseable and all changed semantic hash.

Typed collection replication over 50,000 randomized cases:

- Set permutation/duplicate normalization preserved semantic hash: **50,000/50,000**;
- ordered sequence reversal changed semantic hash: **50,000/50,000**;
- exact provenance-bound contract hash changed on 49,831/50,000 generated instance mutations; the remaining cases were generated no-op instance mutations.

This independently supports keeping `semantic_hash` distinct from exact `contract_hash`.

### 5. Fail-closed diagnostics

For each N/S/D candidate:

- 11/11 malformed/unknown cases rejected;
- 1/1 valid control accepted;
- 20,000 additional unknown-relation fuzz cases produced **0 false accepts**.

D rejects unknown bare relation words at parser level; N and S parse their open surface and reject unknown identities in the typed resolver. Both are valid fail-closed architectures if the parser/resolver boundary remains explicit.

### 6. Ambiguity and lexical identity counterexample

A first production-like parser version exposed a more important bug than simple parse failure:

- `false` was parsed as a `qid` instead of BOOLEAN;
- keyword-like field identifiers such as `status`, `dialect`, `version` and `requires` parsed but lost lexical identity in empty `ident` nodes.

A whole-program exhaustive Earley `dynamic_complete` ambiguity run exceeded the local sandbox resource envelope. The test was replaced by brace-balanced top-level execution across all **86 G9 + 25 Dialect** units.

The repair reserves declaration/operator keywords and booleans out of generic `NAME`, and gives keyword-like identifier use explicit `ident_<keyword>` aliases. After repair:

- N/S/D full G9 LALR: PASS;
- N/S/D full Dialect LALR: PASS;
- empty identifier nodes: **0**;
- G9 top-level ambiguity nodes: **0**;
- Dialect top-level ambiguity nodes: **0**;
- `true`/`false` retain BOOLEAN identity.

This is a concrete demonstration that **parse closure without lexical semantic identity is not sufficient for ClayCode canonicalization**.

## Local performance after lexical repair

20 parser builds and 200 combined G9+Dialect parses per candidate:

- N: build median 96.23 ms; parse median 12.23 ms; p95 15.45 ms; grammar 3473 chars;
- S: build median 109.15 ms; parse median 12.56 ms; p95 16.07 ms; grammar 3627 chars;
- D: build median 113.71 ms; parse median **12.20 ms**; p95 **14.23 ms**; grammar 4166 chars.

The timing differences are small and local. D wins migration cost clearly and parse latency marginally, but pays the largest grammar/registry cost.

## Current decision

**D = LEADING_NOT_SELECTED.**

D is the current measured leader because it:

- changes only 5 of the tested current relation lines;
- has the lowest measured migration edit distance;
- is the shortest transformed current-G9 source among N/S/D;
- remains fail-closed;
- is marginally fastest in the repaired local parse benchmark.

It is **not** selected or promoted because the decisive remaining measurements are unavailable in this hosted worker:

1. target Qwen-class 4B reader/repair accuracy and context cost;
2. normative repository parser/canonicalizer integration;
3. type/effect handoff through the real compiler path;
4. E2B replication when the E2B execution surface is actually exposed to the worker;
5. execution on Andreas' Ubuntu developer-system target.

## Tool boundary

- E2B is project-state `RUNTIME_VERIFIED`, but no E2B callable tool is exposed to this hosted worker; no E2B evidence is claimed here.
- SandboxAPI remains `BLOCKED_NOT_SUBSCRIBED`.
- The target Ubuntu developer machine is not connected to this worker.
- No callable target Qwen-class 4B reader is exposed here.
- Local isolated Linux execution was therefore used until the local parser/hash/fuzz/diagnostic discriminator was saturated.

## Goodman / anti-echo result

No FRANK-derived preference was treated as independent evidence. The parser surfaced its own counterexamples. No new FRANK, GWT, ClayGraph, UnifiedDB, Hyperposition or Emergenz primitive is justified by this run.

The strongest architecture conclusion is narrower:

**source spelling must remain below deterministic typed semantic identity, and parse acceptance must never mint relation truth or effect authority.**

## Stage impact

`BASE_CLAYCODE_RELEASE`: remains **IN_PROGRESS**.  
`GENERAL_PURPOSE_GATE`: remains **NOT_PASS**.  
`CC-WP-02-PARSER-CANON`: remains **OPEN** until real repository/target-reader integration.

The uncertainty in CC-WP-02 is materially reduced, but no work package is marked complete merely from this research proxy.

## Next execution already routed

`WORK-CC-BASE-G9-PARSER-FREEZE-001` is revised to `READY`.

Every ClayCode worker must now load the all-worker execution directive and, where its surfaces allow, execute:

`real repo parser/canonicalizer -> typed AST/hash -> target-reader N/S/D comparison -> type/effect handoff -> E2B/Ubuntu receipt`

Then continue directly toward evaluator/lowering rather than returning to open-ended syntax discussion unless a new executable semantic counterexample appears.
