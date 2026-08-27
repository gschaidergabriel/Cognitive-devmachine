# ClayCode Trigger Run — G9 Surface Closure

Run: `20260809T1711p0700-chatgpt-g9-surface-closure`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`

## Executive result

The highest-information result is a concrete BASE blocker, not a new language feature.

The admitted current ClayCode stack points to `CLAYCODE_G9_FUSION_SPEC_V3.clay`, `DIALECT_REGISTRY_V3.clay` and `grammar.ebnf`. Direct comparison plus an executable surface audit shows the grammar is not closed over syntax already used by the admitted current artifacts.

Observed targeted failures:

1. `>` used in `rule diff>0 => ...` but absent from the grammar operator set;
2. `<` used in `rule diff<0 => ...` but absent from the grammar operator set;
3. `>=` used in generation-validity rules but absent from the grammar operator set;
4. structured `if residual.effect { ... }` used in the current main cycle but no `if_stmt` exists;
5. typed interface methods such as `verify(receipt:ReceiptRef)->Verification` occur in the dialect registry but no generic typed method-signature production exists.

A targeted local executable audit produced `5/5` failures on these current constructs and `0/2` failures on grammar-native positive controls. A minimal audit-only syntax closure — comparisons, `if_stmt`, and typed method signatures — reduced targeted failures to `0` without introducing a new semantic primitive.

This supports the current program law: **less change, more compile**.

## Negative result

`N-CC-20260809-001`: the current admitted `grammar.ebnf` is not surface-closed over current admitted G9 artifacts.

This is a parser/spec closure negative result. It does not establish semantic unsoundness of G9, whole-corpus parser failure, or target-Ubuntu runtime failure.

## Important unresolved parser question

The minimal repair is not sufficient for BASE freeze because expression precedence/associativity remains visibly underspecified. Current grammar uses a flat `expr = primary { operator primary }` form across arithmetic, implication, boolean, `requires`, equality and related operators.

Highest-information next parser experiment: implement two independent parsers or one parser plus a canonical oracle; generate a mixed-operator mutation corpus; require deterministic AST/canonical IR and stable semantic hashes; reject parser-specific implicit precedence unless versioned in the semantic contract.

## Cross-branch synthesis

### FRANK
The loop-of-loops directive remains OPEN research context. Its language demand is representability of loop identity, timescale, recurrence budget, halt/continue/escalate reasons, interventions and readouts. This run found no evidence that those require loop-specific ClayCode syntax. Generic records/rules should be tested first.

The expected root `research_entity/frank/FRANK_ARCHITECTURE.claycode.json` was not found through direct connector read and GitHub code search returned no indexed hit. This is a discovery limitation, not proof of repository-wide absence.

### GWT / Emergenz
Current contracts require typed WorkspaceEpisode/EmergenceReadout/intervention/receipt semantics and strict distinctions among broadcast, reconstruction, uptake, causal use, outcome and re-entry. These are typed data/contract requirements until an executable fixture proves otherwise.

### Hyperposition
N-ary role bindings, alternatives, topology identities, gain/delay/timescale and intervention readouts should first be represented with generic records/collections/interfaces. A new primitive is justified only if an executable fixture loses required semantics.

### ClayGraph
The current baseline/V2 substrate requires typed hyperrelations, role members, projection receipts, selection receipts and receiver causal-use receipts while preserving `activation != truth`. These are high-value ClayCode parser/type regression fixtures.

### UnifiedDB
The current stack uses a logical UnifiedDB with versioned work specs, capability observations and execution receipts. ClayCode should preserve this as typed semantic contracts and host adapters; no physical monolith follows from language integration.

### Harness
`H-WP-03-CLAYCODE-ADAPTER` is correctly blocked on ClayCode release. The immediate dependency is a versioned parser/canonicalizer/type-effect surface that can parse real current artifacts; Harness should not bridge grammar gaps with untyped host escape hatches.

## Independent external research

Primary-source evidence supports one existing ClayCode architecture class without validating project-specific details:

- WebAssembly Component Model/WIT provides typed interface imports/exports suitable for explicit host/component contracts.
- WASI describes host interaction through link-time and runtime capabilities/resources.
- Wasmtime documents typed guest-visible resources with non-forgeability guarantees and explicit preopen-based filesystem capability behavior.

Implication: WIT/WASI is a strong test candidate for ClayCode's typed FFI/effect boundary on Ubuntu, alongside a native Ubuntu backend. Matched application proofs must compare expressibility, latency, memory, interoperability and recovery before selection.

## Goodman anti-echo result

- External capability/effect authority boundary: `REFINED` — independently supported as an architecture class, exact ClayCode CapabilityToken/Witness schema unproven.
- FRANK loop-of-loops semantics: `UNRESOLVED` — no independent loop experiment in this run; generic representation first.
- Cross-branch readout representability: `REFINED` — keep requirements, prefer generic core + typed domain schemas/interfaces over branch-specific syntax until an executable failure forces more.

## Protocol drift

Current ClayCode protocol text still says "eight" branches and uses `clay` in its priority string, while the authoritative registry uses `clayresearch` and includes `harness` as a required ClayCode foundation. This run followed the registry and materialized nine current foundations in `INTERCONNECT_MANIFEST.json`.

## Current-stage implication

No ClayCode BASE work package is completed by this run. The run narrows the critical path:

1. `CC-WP-01-SPEC-FREEZE`: freeze only after grammar/surface closure and precedence semantics are explicit.
2. `CC-WP-02-PARSER-CANON`: implement a real parser + deterministic canonicalizer against the complete CURRENT stack corpus.
3. `CC-WP-03/04`: parse/type/effect representative fixtures from FRANK, GWT, Hyperposition, Emergenz, ClayGraph and UnifiedDB.
4. `CC-WP-06/07/10`: then attempt one real typed effectful application through native Ubuntu and/or WIT/WASI lowering.
5. Change semantics only when an executable fixture cannot preserve required behavior using the current semantic core.

## Highest-information next experiments

`EXP-CC-G9-FULL-PARSER-DIFF-001`: complete CURRENT `.clay` corpus; parser A vs parser B/reference oracle; mixed operators/nested generics/method signatures/control flow; AST and semantic hashes; strict positive/negative corpus.

Then `EXP-CC-WASI-NATIVE-EFFECT-001`: same ClayCode file/HTTP capability exemplar lowered to WIT/WASI and native Ubuntu adapter with matched authority and performance receipts.

## Promotion decision

No semantic candidate promotion. No BASE gate progress awarded. The negative result is durable; the minimal repair remains a candidate until a real parser/canonicalizer passes the complete current corpus and deterministic semantic-preservation tests.
