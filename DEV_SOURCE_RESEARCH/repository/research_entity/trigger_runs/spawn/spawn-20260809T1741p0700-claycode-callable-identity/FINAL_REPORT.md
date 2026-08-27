# SPAWN Research Report — ClayCode Callable Identity Layering

Run ID: `spawn-20260809T1741p0700-claycode-callable-identity`  
Origin branch: `claycode`  
Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
Canonical parent: `r2` · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**

## Spawn selection

The OS-backed weighted draw selected ClayCode at 29.44464% under the 50/10/10/6/6/5/5/4/4 distribution. After current-evidence filtering, the stochastic microdirection draw selected **exact callable symbol/signature identity, ambiguity and replay/effect-boundary layering**.

A concurrent spawn later selected adaptive visual learner state semantics, and autonomous ClayCode workers moved onto strict-LALR conflict localization. The selected callable-identity direction therefore remained non-duplicative.

## Main result

The strongest current candidate is not one monolithic function ID. It is a layered identity model:

```text
source scope/name -> BindingKey
params + result -> FunctionTypeId
BindingKey + FunctionTypeId + body semantics -> DefinitionSemanticId
DefinitionSemanticId + ABI + provenance/version -> ContractId
resolved DefinitionSemanticId + emitted artifact/ContractId -> execution/replay receipt
```

Static effect information is split again:

```text
declared effect contract -> may constrain callable contract/type
inferred effect summary -> analysis result checked against declared contract
runtime capability token -> fresh invocation authority
```

The critical negative is:

`inferred_effect_summary != lexical_binding_identity`

and the existing authority law remains:

`potential_effect_summary != runtime_effect_authority`.

## Executable discrimination

### Mutation matrix

50,000 randomized callable mutations produced the expected layer-specific identity changes:

- rename changed BindingKey, definition and contract while type stayed stable;
- signature changes changed type/definition/contract while BindingKey stayed stable;
- body changes changed definition/contract while BindingKey/type stayed stable;
- ABI/provenance changes affected ContractId without contaminating semantic binding/type identity;
- inferred-effect-only changes left every layered callable identity stable, while a deliberately bad effect-in-binding key changed every one of 8,259 such cases.

### Resolver discriminator

Across 20,000 generated overload pairs:

- unique-name policy accepted first definitions and rejected the same-name second definition in 20,000/20,000 cases;
- signature-aware overload resolution accepted both and resolved exact typed calls in 20,000/20,000 cases;
- deliberately partial type information made the constructed overload pair ambiguous in 20,000/20,000 cases.

Therefore overloading is technically possible, but there is currently no evidence that BASE should pay its ambiguity/diagnostic complexity. The minimal policy remains **fail closed on same-scope duplicate names until a real application counterexample requires overloading**.

### Recursive effect countertest

2,000 random recursive call graphs with 20 functions each produced 40,000 callable states:

- layered binding dependency graph: acyclic;
- effect-in-binding dependency graph: cyclic;
- BindingKey stable: 40,000/40,000;
- declared contract type stable: 40,000/40,000;
- bad effect-in-binding churn after effect mutation: 3,061;
- inferred effects remained inside declared bounds in 37,603 states; 2,397 exceeded the declared bound and should be rejected/refined rather than silently changing binding identity.

This refines, rather than rejects, effect-typed functions: **declared** effects can be static type/contract material; **inferred** effects cannot be allowed to retroactively mint lexical identity.

## Preserved negative result

The first hash-collision counter in this run was invalid: it counted repeated identical preimages as hash collisions. It was discarded and replaced with a hash→preimage check. Corrected observation: 319,529 unique hash slots, 80,471 repeated identical preimages, **0 observed true SHA-256 collisions**. This is a method negative result, not evidence of universal collision impossibility.

## Cross-branch implication

- **ClayCode:** exact symbol resolution belongs to parser/canonical typed IR/checker, not ClayGraph/GWT/model fallback.
- **Harness:** a replay receipt should identify the resolved implementation/contract, not only a lexical name.
- **UnifiedDB:** semantic identity and exact provenance/ABI contract identity remain different useful keys.
- **ClayGraph:** relevance/activation may retrieve candidates but cannot mint compiler binding.
- **Hyperposition:** multiple candidates may coexist before compilation; each emitted call must collapse to one explicit exact binding.
- **FRANK:** no new FRANK-specific callable primitive is justified.
- **GWT/Emergenz:** no scientific state change.

## External comparison

Independent compiler/language specifications are consistent with the separation: MLIR uses explicit symbol tables/references; LLVM and WebAssembly distinguish callable target/signature/validated invocation; Rust separates namespace resolution and function item/type identity; Koka demonstrates that effect information can be represented in static function types. These are design comparison anchors only and do not select ClayCode syntax or policy.

## Decision

`RESEARCH_DELTA = YES`  
`SCIENTIFIC_PROMOTION = NONE`  
`BASE_GATE_EFFECT = NONE`  
`SELECTED_CANDIDATE = LAYERED_CALLABLE_IDENTITY`  
`INFERRED_EFFECT_IN_BINDING = NEGATIVE_RESULT`  
`DEFAULT_OVERLOADING = NOT_SELECTED / OPEN`

The next highest-information production test is to integrate this identity layering immediately behind whichever strict-LALR frontend survives conflict localization, then carry exact callable IDs through type/effect SCC closure, lowering, emitted artifact hashes and an Ubuntu execution/replay receipt.
