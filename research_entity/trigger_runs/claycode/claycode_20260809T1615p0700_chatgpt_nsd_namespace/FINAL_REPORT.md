# ClayCode Trigger Run — N/S/D Relation Surface Namespace Discriminator

Run: `claycode_20260809T1615p0700_chatgpt_nsd_namespace`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` — IN_PROGRESS  
Promotion: **NONE**

## Executive result

This run adds one narrow but decision-relevant negative result to the active BASE parser freeze.

Three current relation-source policies remain live over a shared typed canonical RelationId IR:

- **N** — strict generic/normalized relation representation;
- **S** — explicit relation sigil/custom reader surface;
- **D** — finite declared readable bare relation words.

A matched local Lark/LALR microbenchmark over 17 unambiguous relation-bearing forms from CURRENT G9 found that all three arms can preserve the same tested typed relation identities and can fail unknown semantic relation IDs closed when a typed resolver is mandatory.

However, the tested finite-terminal implementation of D created a new concrete namespace defect: all 15 relation spellings that are legal under the current identifier grammar ceased to parse as ordinary bare identifiers when compiled as declared relation terminals. The control was **0/15** for D versus **15/15** for S and N. Two additional current relation spellings, `4B_emits` and `4B_need_not_learn`, are digit-leading and therefore are not legal under the CURRENT `ident` grammar in the first place.

This does **not** refute D as a design family. It refutes the simple implementation strategy `declared relation word -> globally reserved lexer terminal` for the tested proxy. D now requires a production test of scoped soft-keyword/contextual declaration and/or explicit escaping.

During this run, concurrent evidence materially changed the comparison. A whole-current-G9 worker reported **61/86** chunks passing under the current checked grammar proxy and **86/86** under strict normalization N, without requiring a new cognitive/runtime semantic primitive. Separately, current S as written was challenged by the pre-existing `@ref` namespace: mixed tests were parser-backend sensitive, while a lexically disjoint sigil control and a quoted generic relation form remained stable. N was deliberately not promoted solely from parse closure, and neither is D or S promoted here.

The current strongest architecture therefore remains:

`source surface -> deterministic typed canonical IR -> semantic_hash -> type/effect verification -> lowering`

Surface recognition does not confer semantic identity, truth or execution authority.

## Internal grounding / Fusion 1

The current release workspace remains `BASE_CLAYCODE_RELEASE` with the release/general-purpose gates NOT_PASS and all 14 ClayCode work packages OPEN. The project law remains **less change, more compile**.

CURRENT G9 already contains the relevant semantic distinctions for this run: typed/provenance identity, capability-bearing effect intent separated from execution authority, ClayGraph relation/hyperrelation state, UnifiedDB semantic views and GWT use/re-entry distinctions. This run found no executable reason to add a new FRANK-specific cognitive primitive.

## Executable experiment

Experiment: `EXP-CC-G9-NSD-IDENTIFIER-NAMESPACE-20260809`.

Execution surface: local Python sandbox, Python 3.13.5, Lark 1.3.1, LALR contextual proxy. E2B was not exposed to this ChatGPT session, so no fresh E2B evidence is claimed.

Corpus: 17 manually extracted, unambiguous CURRENT-G9 relation-bearing forms: 12 binary, 2 prefix and 3 postfix relation families. This is deliberately smaller than the concurrent 86-chunk whole-G9 surface test and is used only for the namespace discriminator.

Observed:

- N typed relation identity: **17/17**;
- S typed relation identity: **17/17**;
- D typed relation identity: **17/17**;
- legal current bare relation IDs under current `ident`: **15/17**;
- D ordinary-identifier controls: **0/15**;
- S ordinary-identifier controls: **15/15**;
- N ordinary-identifier controls: **15/15**;
- unknown relation mutations: **50,000**; semantic admissions after resolver: **0** for all three arms;
- whitespace semantic-identity tests: **20,000/20,000** per arm;
- same-kind relation substitution changed semantic hash: **17/17**;
- binary operand swap changed semantic hash: **12/12**;
- source bytes across the 17 specimens: D **766**, S **787**, N **970**;
- mean surface overhead versus D: S **+1.235 bytes**, N **+12 bytes** per specimen.

The local parser throughput numbers are recorded in `EXECUTABLE_RESEARCH_RECEIPT.json`, but they are a toy proxy and are not interpreted as production compiler performance.

## Concurrent evidence assimilated before final write

### Whole-current-G9 closure

Concurrent report: strict normalization N closed **86/86** current top-level G9 chunks in its proxy versus **61/86** under the checked-in grammar. N used four general surface additions plus explicit source normalizations and required no new cognitive/runtime semantic primitive for parse closure. This strengthens N as a safe fallback but does not select it without matched migration/diagnostics/reader-cost evidence.

### S lexical namespace counterevidence

Concurrent mixed `@ref` + `@relation` evidence made the current S spelling backend-sensitive. Therefore this run does not treat the compact relation-only S result as a production-ready lexical policy. A lexically disjoint or quoted S remains an open redesign candidate.

### Typed canonical semantic-hash worker

A concurrent worker started a dedicated type-directed canonical semantic-hash lane. This run does not duplicate that worker's Set/Ordered/role canonicalization research; it contributes the separate relation/identifier namespace negative result.

## External triangulation

Primary documentation was used as architecture comparison, not as ClayCode-specific proof.

- MLIR's Language Reference exposes a generic operation syntax and optional registered custom assembly forms over one extensible IR, with round-trippable textual representation and verification-oriented semantics.
- MLIR ODS separates registered operation definition, custom parsing/printing and verification.
- Tree-sitter explicitly treats keyword/identifier overlap, lexical precedence and context-aware lexing as parser design concerns.

These sources support testing a separation between reader surface and typed semantic IR. They do not decide whether N, S or D is best for ClayCode.

## Fusion 2 — updated hypothesis map

### N — strict normalization / generic fallback

Status: `OPEN_SUPPORTED_NOT_SELECTED`.

Strength: current whole-G9 proxy closure 86/86; no identifier collision found in this run; generic explicit representation is a strong deterministic fallback.

Open cost: higher source/migration size in the tested relation sample, diagnostics and target-reader repair cost not yet matched.

### S — explicit sigil/custom surface

Status: `OPEN_CHALLENGED`.

Strength: compact relation-only reader form and typed resolver separation.

Counterevidence: current `@relation` spelling overlaps the existing `@ref` lexical namespace and became backend-sensitive in concurrent tests.

Required repair: lexically disjoint sigil/quoted design plus full production corpus verification.

### D — declared bare relation surface

Status: `OPEN_REFINED_BY_NEGATIVE_RESULT`.

Strength: minimal source overhead and readable current-like forms; unknown semantic relation IDs can be failed closed by declaration/resolution.

Counterevidence: finite global relation terminals captured the ordinary identifier namespace in this run; two current relation names also violate the current identifier lexical rule.

Required repair: scoped soft keywords/contextual relation declaration or escaping, then full corpus + shadowing/mutation tests.

## ClayGraph finding

No ClayGraph semantic change is justified. ClayGraph explicitly preserves typed edges, hyperrelations, role-bearing members, graph epochs, projection/selection/receiver receipts and authority class. A binary relation reader convenience must therefore lower into typed relation identity and must not flatten n-ary/higher-order graph semantics.

The new D namespace negative result reinforces that relation identity belongs in a typed semantic layer, not in accidental lexical reservation.

## UnifiedDB finding

No UnifiedDB physical or semantic consolidation change is justified. UnifiedDB V9 separately models resources, capability observations, revisioned work specs, scheduler receipts, leases and execution receipts. Source relation spelling cannot mint any of those identities or authority classes.

The parser/canonicalizer must preserve stable semantic identifiers and replayable transitions independently of reader syntax.

## FRANK / Harness finding

No new FRANK semantic primitive is justified by this parser issue. FRANK's Ubuntu v0.1 adaptive visual learner still requires versioned prototype/classifier state, trusted-example tiers, calibrated known/unknown/conflict outcomes, promotion/rollback, resource budgets and deterministic replay. The parser must carry those semantics rather than simplify them.

No Harness gate advances. The ClayCode adapter remains blocked on ClayCode release; parser success here is not H1/H2/H3 evidence.

## GWT / Hyperposition / Emergenz findings

No GWT causal distinction changes. Delivery, reconstruction, uptake, causal use, outcome and re-entry remain distinct typed evidence channels.

No Hyperposition relation reduction is authorized. N-ary/higher-order relation identity, role bindings and topology semantics remain first-class and must survive canonicalization.

No emergence claim changes. Parser closure, lexical disambiguation or semantic-hash stability are not evidence of causal emergence.

## Goodman anti-echo result

The run does not accept a parser policy because it resembles current FRANK/Clay prose. Shared ancestry was collapsed; competing N/S/D implementations and independent parser/IR documentation were used as discriminators.

- typed semantic admission separate from parser acceptance: `SUPPORTED`;
- D as best surface: `UNRESOLVED` after the new namespace negative result;
- current S as backend-neutral: `REFINED/CHALLENGED`;
- N as winner solely from 86/86 closure: `UNRESOLVED`;
- need for new FRANK semantics because of parser drift: `REFUTED_FOR_THIS_RUN`.

The repo-local Goodman validator could not be executed from this tool surface; official validator PASS is not claimed.

## Negative results

New durable results:

1. `NR-CC-D-FINITE-TERMINAL-IDENTIFIER-COLLISION-20260809` — finite declared bare-relation terminals captured the ordinary identifier namespace in the tested LALR proxy.
2. `NR-CC-D-DIGIT-LEADING-RELATION-ID-20260809` — current `4B_*` relation spellings cannot be current bare `ident` tokens.

Existing concurrent S namespace counterevidence was assimilated but not reauthored as independent evidence.

## Knowledge compilation

New micro-packet:

`research_entity/knowledge_micro_packets/claycode/KMP-CLAYCODE-D-IDENTIFIER-NAMESPACE-COLLISION-20260809.md`

It preserves the narrow negative result and its rescue/falsifier conditions.

## Highest-information next experiment

Do **not** redesign ClayCode semantics. Finish the already-started typed canonical semantic-hash work, then run the real production parser over the same frozen full G9+dialects corpus with matched reader policies:

1. N — explicit generic/normalized source;
2. S2 — lexically disjoint or quoted custom/sigil surface;
3. D2 — scoped soft-keyword declared relations with explicit escape semantics.

Require all arms to lower into the same typed canonical IR oracle and measure:

- full-corpus closure and intended AST;
- relation/identifier shadowing and mixed token classes;
- parse -> typed IR -> print -> parse equivalence;
- semantic-hash equality for equivalent surfaces;
- malformed/undeclared fail-closed behavior;
- diagnostics;
- migration edit count;
- source/token/context cost;
- parser/compiler complexity and latency;
- target Qwen-class reader accuracy and repair cost when target-model access exists.

Only that test should freeze the preferred reader surface. If N wins, it can remain canonical with optional later custom projections; if S2 or D2 wins, their surface must still be reversible into the same typed IR and remain non-authoritative.

## Completion / non-completion

Completed in this run:

- canonical boot and final parent reread;
- current trigger/protocol routing;
- current G9/grammar/stack grounding;
- deep ClayGraph and UnifiedDB cross-read;
- FRANK/GWT/Hyperposition/Emergenz/Harness constraints;
- matched local N/S/D relation-surface executable discriminator;
- new D identifier-namespace negative result;
- concurrent full-G9, S-namespace and semantic-hash-lane assimilation;
- primary-source external triangulation;
- Goodman review;
- hypotheses, negative results, micro-packet, manifests and durable final report.

Not completed and not falsely claimed:

- production parser implementation;
- official interconnect-preflight PASS;
- repo-local Goodman-validator PASS;
- fresh E2B run;
- full matched N/S2/D2 production benchmark;
- target Qwen reader benchmark;
- `CC-WP-02` PASS;
- any application acceptance item;
- BASE gate PASS;
- ClayCode semantic/canonical promotion.
