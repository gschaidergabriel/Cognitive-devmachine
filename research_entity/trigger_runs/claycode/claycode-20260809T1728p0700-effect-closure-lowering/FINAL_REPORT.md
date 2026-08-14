# ClayCode Trigger Run — Compositional Effect Closure + Lowering Translation Validation

**run_id:** `claycode-20260809T1728p0700-effect-closure-lowering`  
**trigger:** `claycode`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**decision:** **RESEARCH DELTA COMMITTED · NO SCIENTIFIC PROMOTION · BASE GATE REMAINS NOT_PASS**

## Executive result

The prior current ClayCode runs had already reduced the parser/front-end question substantially and identified `typed effect summaries across calls` as a next open compiler blocker. This run tested that blocker directly rather than changing syntax.

A hosted-local executable proxy extended the existing typed function candidate with an external host-intrinsic signature/effect table and computed transitive function effects plus required capabilities by monotone least-fixed-point closure over the exact function call graph.

Results:

- random cyclic call graphs: **20,000**;
- effect-closure mismatches vs independent reference closure: **0**;
- maximum fixed-point rounds observed: **9**;
- recursive cycle closure: **PASS**;
- interpreter vs generated-Python lowering executions: **5,000**;
- output mismatches: **0**;
- effect-trace mismatches: **0**;
- textual capability-name forgery: **REJECTED**;
- missing HTTP capability: **REJECTED**;
- reserved `host.*` intrinsic shadowing: **REJECTED**;
- undefined function / arity mismatch: **REJECTED**.

No ClayCode source primitive was added. The tested design treats effect/capability requirements as compiler metadata and runtime capabilities as separate authority.

## Identity layering

A format-only source variant produced:
- a different source hash;
- a different exact `contract_hash`;
- the same `semantic_hash`;
- the same lowered artifact hash.

This is consistent with the recent Harness H-WP-02 result that semantic current-state identity, version/history identity and execution-trace identity answer different questions. The compiler path should analogously keep source/contract, semantic program, lowering artifact and execution trace identities linked but distinct.

## Cross-branch findings

- **FRANK:** C9/Needle effect-authority separation survives in refined form. Inferred/declared effect requirements do not grant execution authority.
- **ClayGraph:** no change. Graph relevance/activation must not resolve exact callees or mint authority.
- **UnifiedDB:** no change. Capability/resource observations, work requirements and execution receipts remain distinct semantic roles.
- **GWT / Emergenz:** no change. Recursive/cyclic closure is not evidence of GWT use or emergence.
- **Hyperposition:** no change. Alternative candidate topologies may remain represented during research, but one compiled artifact needs exact symbol/signature/effect binding.
- **Harness:** refinement. Translation/source-chain receipts should preserve layered program/contract/lowering/trace identities.
- **ClayCode:** implement type/effect closure in checker/IR and translation validation in lowerer; **no new surface syntax absent a production counterexample**.

## Independent comparison anchors

Independent primary sources were used only as design checks:
- Koka's official effect-typing material demonstrates compositional effect tracking across function boundaries.
- WASI capability-model documentation separates what a program requests/uses from capabilities actually provisioned to it.
- Alive2 is a translation-validation system for checking whether lowered/optimized IR transformations preserve semantics and can produce counterexamples.

These sources do not prove ClayCode is correct; they support the narrow architecture direction tested here.

## Goodman anti-echo

Verdict: **REFINED**.

FRANK/ClayCode shared ancestry was collapsed. The current executable proxy plus independent primary anchors support the narrow design law:

`function body/local intrinsic effects -> transitive effect summary -> required capability set`

while preserving:

`required capability != possessed capability != execution authority`.

Counterhypothesis: capability requirement metadata itself could serve as authority safely. The current adversarial tests reject that in the tested proxy, but production FFI/Ubuntu evidence is still required.

## Infrastructure negative result

The mandatory interconnect preflight has a current governance drift: `RESEARCH_TRIGGER_REGISTRY.json` uses `clayresearch`, while `tools/research_interconnect_preflight.py` still hard-codes `clay` in its branch priority sets and fail-closes when the registry set differs. This run therefore does **not** claim the exact repository-local preflight executable passed. An explicit nine-branch `INTERCONNECT_MANIFEST.json` was materialized and the drift is preserved as `N-CC-PREFLIGHT-CLAYRESEARCH-DRIFT-001`.

## Evidence boundary / limitations

This run is **not**:
- production G9 parser/canonical-IR evidence;
- E2B evidence;
- execution on Andreas' Ubuntu developer target;
- native or WASM/WASI backend evidence;
- a mandatory APP-01..APP-10 proof;
- a BASE work-package completion.

The generated Python shadow executed in the hosted worker process. It is a discriminating compiler semantics proxy, not a release artifact.

Therefore:
- all ClayCode BASE work packages remain **OPEN**;
- `GENERAL_PURPOSE_GATE` remains **NOT_PASS**;
- no canonical scientific promotion is made.

## Highest-information next path

1. Integrate the already-supported function-definition/call contract into the real production parser + canonical typed IR.
2. Implement the tested transitive effect/capability-requirement closure in the production type/effect checker.
3. Bind semantic program ID -> lowering-contract ID -> generated artifact ID -> execution receipt.
4. Translation-validate the same corpus through a real backend.
5. Run E2B when exposed to the worker and then the Ubuntu target.
6. Use the production path for APP-01 CLI; proceed toward APP-02 HTTP only after control/error/resource/async closure is executable.

## Decision

`RESEARCH_DELTA = COMMITTED`  
`SCIENTIFIC_PROMOTION = NONE`  
`CLAYCODE_CORE_CHANGE = NO`  
`TYPE_EFFECT_IMPLEMENTATION_DELTA = COMPOSITIONAL_LFP_EFFECT_AND_REQUIRED_CAPABILITY_CLOSURE`  
`LOWERING_DELTA = TRANSLATION_VALIDATION_REQUIRED`  
`AUTHORITY_RULE = REQUIRED_CAPABILITY_METADATA_NEVER_MINTS_AUTHORITY`  
`BASE_GATE = NOT_PASS`
