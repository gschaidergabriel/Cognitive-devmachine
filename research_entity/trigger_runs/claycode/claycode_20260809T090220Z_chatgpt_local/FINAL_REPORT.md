# ClayCode Trigger Run — claycode_20260809T090220Z_chatgpt_local

## Canonical parent
- Entity: Clay / `frank-project-global-research-entity`
- RAE version: 8.8
- Canonical revision: 2
- State hash: `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- Organ: `chatgpt-secondary`
- Write status: `COMMITTED` (trigger-run artifacts written through GitHub Contents API and reread; canonical r2 itself not mutated)

## Stage
Current program stage is `BASE_CLAYCODE_RELEASE`. The ClayCode release workspace is `NOT_PASS`; 14/14 work packages are OPEN and no mandatory application proof has passed.

## Fusion 1
The current G9 V3 candidate already models Delta/incremental receipts, capability-bearing effects, dialect contracts, UnifiedDB views, ClayGraph deltas, GWT causal stages, effect intent/Needle lowering, bounded equivalence search, reader/context rent, usage observations and native 4B task contracts.

ClayGraph and UnifiedDB demands fit these semantic families. The FRANK adaptive visual learner can provisionally be represented with existing typed records/deltas/provenance/version/rollback/resource-budget constructs. No new core semantic primitive was justified in this run.

## Concrete blocker discovered
`research_entity/claycode/g9/grammar.ebnf` does not define an `if` statement, while the admitted G9 V3 spec uses:

`if residual.effect { ... }`

A locally generated parser test accepts a normal `cycle` action sequence, rejects the exact `if` fragment under the current grammar, and accepts it after a minimal `if_stmt = "if", expr, block` grammar extension.

Classification: parser/surface grammar gap, not evidence for semantic redesign.

## External research
Primary/current implementation evidence:
- WASI 0.3.0 (released 2026-06-11) adds native async `async func`, `stream<T>`, and `future<T>` to the Component Model.
- WIT provides typed import/export interface definitions; Wasmtime's component Linker supplies host functionality explicitly by import name/type.
- MLIR Dialect Conversion supports progressive lowering with explicit legal/illegal targets, type conversion and rollback-capable rewrite conversion.
- Recent WebAssembly cross-compilation work reports semantic divergences and motivates differential/translation validation rather than treating successful compilation as proof.
- ETAS (2026 preprint) independently explores effect-typed agent actions and explicit requested/handled/denied/committed trace semantics, providing non-project ancestry support for ClayCode's intent/effect/authority separation.

Durable external source URLs/evidence classes are recorded in `EXTERNAL_RESEARCH_SOURCES.json`.

## Executable experiment
Local sandbox fallback was used because E2B/Wasmtime/MLIR tooling is not exposed in this hosted environment.

Results:
- semantic-equivalent set permutation/duplication fuzz: 10,000/10,000 stable `semantic_hash`;
- semantic scope changes: 10,000/10,000 changed hash;
- ordered effect reversal: 10,000/10,000 changed hash;
- provenance mutations: 10,000/10,000 changed `contract_hash` while semantic hash stayed stable;
- concrete gateway cases: valid write accepted; text-only capability name denied; path escape denied; >4096-byte budget violation denied;
- generated-target forgery fuzz: 0/10,000 forged tokens accepted;
- generated-target scope fuzz: 0/1,000 path escapes accepted;
- total test failures: 0.

Claim boundary: this validates only a narrow canonicalization/authority subset and a grammar counterexample. It does not prove a ClayCode compiler, Wasm backend, or BASE release.

## Fusion 2 / architecture delta
1. Preserve the current semantic candidate by default.
2. Freeze a canonical typed IR before expanding surface syntax.
3. Repair the grammar/parser mismatch immediately; add only syntax/control constructs required by executable programs and current semantics.
4. Fastest plausible backend ladder:
   - reference evaluator/interpreter;
   - typed host ABI using WIT-style interfaces;
   - direct WebAssembly Component/WASI 0.3 target for portable effects/async;
   - differential execution against the evaluator;
   - add MLIR as an optimization/multi-backend layer only if measured benefit outweighs BASE complexity.
5. Keep `CapabilityToken`/authority external to model text. WIT/import names are interface identity, not authority.
6. Treat every FFI/generated-code/subprocess effect as part of parent effect closure.
7. Represent the adaptive Micro Visual Classifier with existing state/version/provenance/delta/rollback primitives unless H1 produces a concrete counterexample.
8. Do not promote physical UnifiedDB/ClayGraph consolidation from this run.

## Highest-information next executable tests
- Parse the entire admitted G9 V3 spec with the frozen parser and enumerate every unsupported construct.
- Freeze a minimal typed executable IR and compile APP-01 CLI through reference evaluator + first target.
- Add WIT world generation for capability-scoped filesystem/process/network adapters.
- Run source-vs-target differential corpus including errors, resource limits, async cancellation and rollback receipts.
- Compile one real frozen FRANK state-transition subsystem before language expansion.
- Then APP-02 HTTP service using WASI 0.3 if the toolchain is available.

## Claim-state recommendations
- `H-CC-20260809-05`: candidate SUPPORT for tested subset only.
- `H-CC-20260809-09`: SUPPORT as a current grammar counterexample.
- all broader backend/general-purpose hypotheses remain OPEN pending target execution.
- no canonical promotion requested.

## Negative / no-change receipts
- `FRANK_ARCHITECTURE.claycode.json`: expected artifact not found at provisional path; no architecture fabricated.
- Physical UnifiedDB consolidation: NO_CHANGE.
- New ClayCode core primitive for adaptive visual learning: NO_CHANGE, pending H1 counterexample.
- E2B evidence: NOT RUN; E2B execution was not exposed in this session tool surface.
- WASI/MLIR target execution: NOT RUN; local binaries unavailable.
