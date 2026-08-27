# ClayCode trigger run — deep WP03→WP04 executable boundary cycle

Run ID: `claycode-20260810T2318p0700-wp03-wp04-boundary-deep`
Trigger: `claycode`
Actor: `chatgpt-secondary`
Provider/model: OpenAI / GPT-5.6 Sol
Canonical research parent: revision `2`, state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Target repository alias: `gschaidergabriel/Dr.-Unterweger`
Target program: `FRANK_V0_1`
Primary component: `F-V01-02-CLAYCODE-COMPILER-RUNTIME`
Adjacent components: `F-V01-07-NEEDLE-TRANSLATOR`, `F-V01-08-TOKEN-API-CLIENTS`, `F-V01-09-EFFECT-AUTHORITY`, `F-V01-13-SECURITY-RECOVERY-OBSERVABILITY`
Primary work packages: `CC-WP-03-IR-TYPES`, `CC-WP-04-TYPE-EFFECT`
Promotion: `NONE`

## Identity / authority lock

This worker is a temporary Clay research/build organ. It is not `self.root` / Frank and does not claim target identity. Compiler artifacts, model output, GWT salience, imports, source module names and structural capability-looking values carry no effect authority by presence. Final training remains unauthorized.

## Fresh starting state

The current program is Frank-v0.1-only. Historical H1/H2/H3/BASE stage labels may exist as evidence but are not active product stages. The current unified workspace still records ClayCode semantic freeze and parser/canonicalizer as PASS while typed IR, type/effect, evaluator, lowering, runtime/FFI, stdlib/concurrency and real-Frank execution remain OPEN.

The prior ClayCode trigger cycle had established a candidate module-symbol resolver but no target-VPS receipt. This run intentionally moved one boundary deeper rather than promoting that candidate from source inspection.

## Existing production evidence incorporated

### Effect contract structural evidence

Target-VPS receipt `CLAYCODE-WP04-EFFECT-CONTRACT-V1-31402743514` establishes a bounded structural contract for current Frank effects without WP04 promotion. The production execution path is not a cognitive `execute(intent)` shortcut. The current semantic chain binds authorization, durable reservation, exact attempt identity, capability/node checks, execution, independent verification and completion.

### Effect authority oracle evidence

The current target-VPS authority oracle has passed its deterministic policy matrix and request-hash mutation discriminator, but its receipt explicitly states that the oracle is not ClayCode-compiled execution. Therefore value-level policy correctness cannot be promoted to compiler/type/effect correctness.

### Authority-provenance counterexample

Current structural `EffectRequest` is constructible as data and contains booleans such as `authenticated` and `scoped_capability`. Existing value-level oracle evidence does not distinguish a helper-produced trusted-looking request from a structurally identical direct request. This is not a demonstrated runtime exploit; it is a concrete compiler/type/effect obligation: authority provenance must not be inferred from data shape.

## Source / TypedIR findings

### 1. Current WP03 structural coverage is narrower than name preservation

The receipt-bound WP03 v2 layer structurally lowers ordinary `record` declarations and selected closed sum types. Current Frank effects also use:

- `type X = { ... }` structural tagged records;
- `type X = opaque { ... }` opaque tagged records;
- block-bodied functions `fn ... -> T { ... }`;
- uppercase collection-constructor spellings such as `SET`, `OPTION`, `ORDERED`.

Presence of names such as `EffectRequest` or `EffectAuthorization` in retained TypedIR/residual JSON is therefore not equivalent to a complete structural/opacity/function/effect lowering proof.

### 2. Legacy function-body assumption discovered

The checked-in base TypedIR helper `parse_fn` searches for `=` after the `->` return arrow. Real current Frank effect functions use block bodies `{ ... }`. A versioned candidate was built to preserve both expression-body and block-body forms as distinct function-body identities; no receipt-gated WP03 code was overwritten.

### 3. Constructor spelling differential identified

The checked-in WP03 typed-value canonicalizer contains executable collection behavior for exact title-case constructors `Set`, `Ordered`, `List`, `Map`, `Option`, `Result`. Current Frank source uses uppercase variants including `SET`, `ORDERED`, `OPTION`. No authoritative frozen alias rule was located in this run. Therefore this is an executable differential to measure, not a cosmetic normalization to assume.

### 4. Nominal type closure requires linker/host classes, not `Any`

WP03 already distinguishes external nominals and explicitly forbids unknown-to-Any degradation. A nominal-universe audit candidate was created to separate:

- local declarations;
- direct imports;
- transitive dependency declarations;
- corpus declarations not reachable by import;
- dialect-owned names;
- built-in primitives/constructors;
- external host/FFI nominals requiring explicit runtime binding.

Absence from Clay source is not automatically a language error: external host nominals remain explicit host-binding obligations.

## Compiler candidates written to target repository

### Tagged-record / opacity overlay

`1120853d05694f8f3195a20eb5a4e1ed00ee62fd`
`runtime/clay_wp04_type_effect_v1/tagged_record_lowering.py`

Candidate behavior:

- lowers `type Name = { ... }` and `type Name = opaque { ... }` from preserved WP03 residual AST;
- preserves type parameters, fields and structural type expressions;
- records `STRUCTURAL_DECLARED` versus `OPAQUE_DECLARED` explicitly;
- structural data never mints authority;
- direct source construction of opaque values fails closed pending a WP04 constructor policy;
- unknown type never maps to Any;
- promotion NONE.

### Transitive restricted-effect checker

`0a5145b8fe92698f30bf4e30ab72cf2bc7bc681f`
`runtime/clay_wp04_type_effect_v1/effect_checker.py`

Initial restricted host boundary inventory:

- `trusted_runtime_effect_authorization` -> `MINT_EFFECT_AUTHORIZATION`;
- `atomic_effect_reservation_with_optional_confirmation_consumption` -> `PERSIST_EFFECT_RESERVATION`;
- `trusted_runtime_derive` -> `DERIVE_CAPABILITY`;
- `runtime_effect` -> `EXTERNAL_EFFECT`;
- `independently_observe_effect` -> `OBSERVE_EXTERNAL_EFFECT`.

The checker propagates restricted effects through resolved project calls. Module/import presence confers no authority.

### Exact-source trust candidate

`ba9e758aab9b896bd7ac70254f24f90971078f00`
`runtime/clay_wp04_type_effect_v1/TRUST_POLICY.json`

This deliberately externalizes code-trust admission and binds current canonical effect/facade source hashes. It explicitly rejects module-name trust, import trust, structural-EffectRequest trust and model/translator-output trust.

This run subsequently falsified **source-only trust as insufficient**: trusted module meaning depends on imported modules and compiler/frontend/grammar identity, and trusted code still does not imply trusted input data.

### Integrated adversarial boundary probe

`64b3ed3c8d6284634241d8470ce323545c0d09f4`
`runtime/clay_wp04_type_effect_v1/target_vps_probe.py`

Adversarial source fixtures are compiled through the same current ClayCode frontend path and attempt:

- untrusted call to `authorize_effect`;
- untrusted call through the compatibility facade;
- direct restricted host intrinsic use;
- direct opaque `EffectAuthorization` construction;
- pure `decide_effect` control case;
- source-hash trust drift.

The probe itself claims no WP04 PASS.

### Isolated VPS evidence lane

`6ba6c1d...` initial and `8961c1de6d27b645bf476057595ded0d2f9b31bb` current follow-up workflow lineage.

Design:

- credential-free `contents:read` executor;
- immutable artifact transport;
- separate `contents:write` receipt job;
- no model-output execution;
- no external effect execution;
- bounded component or negative evidence only.

### Dependency-closure trust

`62821e6ebaf25b5bcd475689a07fe47b6703fc36`
`runtime/clay_wp04_type_effect_v1/dependency_trust.py`

Computes deterministic transitive `use` closure over exact module source bytes. Closure identity itself grants no trust.

### Higher-order/referenced effect candidate

`a91dd04d6056c20e617ea5a7ce706c4019371c2b`
`runtime/clay_wp04_type_effect_v1/effect_reference_checker.py`

Conservatively requires restricted-effect admission when an untrusted function acquires a reference to an effectful project function, covering candidate patterns such as `let f = authorize_effect; f(...)` until token-kind-aware function-value typing exists.

Known residual: direct references to restricted host intrinsics need the same treatment; project-function-only resolution is insufficient.

### Dependency/source adversarial follow-up

`f07114394eca7adef9ce18063dd2650c70b83f5a`
`runtime/clay_wp04_type_effect_v1/adversarial_followup_probe.py`

Measures:

- indirect reference to `authorize_effect`;
- transitive dependency source drift beneath an unchanged root source hash;
- unclassified call-like symbols.

The expected candidate result explicitly preserves the source-only trust gap rather than treating it as PASS.

### Nominal universe audit

`2123d36...` v1, `6986003...` block-function-safe v2, `b09c62c12b29ba4378698b998978761c2d5d3b2b` epistemically refined v3.

V3 preserves WP03 `EXTERNAL_NOMINAL` semantics and reports host/FFI binding obligations instead of incorrectly inventing source declarations or `Any`.

### Constructor spelling differential

`d7826ac...`
`runtime/clay_wp04_type_effect_v1/constructor_spelling_probe.py`

Compares current executable typed-value behavior of:

- `Set` / `SET`;
- `Option` / `OPTION`;
- `Ordered` / `ORDERED`;
- `List` / `LIST`;
- `Map` / `MAP`;
- `Result` / `RESULT`.

It inventories current source usage and conflicting declarations. It does not assert alias equivalence merely from spelling.

### Closed-world effect completeness

`7609b0896ee7257032d5414487bb54539efa19de`
`effect_checker_v2.py`

Unknown callable symbols now become explicit `UNCLASSIFIED_EXTERNAL_CALL`; they do not default to PURE.

`0f707de...`
`effect_completeness_probe.py`

Inventories unresolved external-function versus constructor obligations. Executable acceptance eventually requires every reachable call to resolve to a project function, constructor/language primitive or exact host/prelude/FFI effect contract.

### Dependency-closure function linker

`a068dc7010f2cd5f187984f6a52de3aca58df4e`
`module_function_linker.py`

Compiles reachable dependency modules through the exact frontend and builds a deterministic callable export table without inferred re-exports or authority.

`7e4cbacca3042a7209a44ab68702d8ab324beb1c`
`function_linker_probe.py`

Differentially measures how many previously external-looking calls are simply project functions absent from the initial two-module callable table.

### Versioned block-function lowering candidate

`a41a8b460b2cb97a0e9cfb33190099b356cab604`
`block_function_lowering.py`

Supports historical `= expression` and current `{ block }` bodies with explicit `body_form` and body semantic hash. Existing receipt-gated WP03 implementation is not overwritten.

`1e59da287673f7fcacd4a43db382012d1ef4e897`
`block_function_probe.py`

Real-Frank differential intended to compare legacy helper, candidate helper, baseline v3 bridge and candidate-patched v3 bridge.

## First real target-VPS diagnostic result

A dedicated same-repository draft PR diagnostic lane was created to expose read-only self-hosted logs:

- workflow commit `89965dd77d49901a254a5e0139fef2062d443a2d`;
- diagnostic PR `#177`;
- first visible Actions run `31406878642`;
- job `93515268433`;
- runner `clay` / host `digital-retina`;
- executor checkout had no persisted repository credential;
- diagnostic purpose explicitly forbade promotion/model-output/external-effect execution.

### Verified negative result

All candidate Python files passed Python bytecode compilation in that run. Every semantic probe then failed at the same earlier import boundary:

`ModuleNotFoundError: No module named 'claycode_base_frontend'`

Import chain:

candidate probe -> checked-in `runtime/clay_wp03_exact_bundle/tools/claycode_base_typed_ir.py` -> `import claycode_base_frontend`.

Therefore the first verified counterexample of this deeper cycle is **not yet tagged-record, block-function, constructor spelling, nominal linking or effect typing**. It is an exact-bundle/import-topology reproducibility gap.

No higher-layer result from that first diagnostic run may be interpreted as PASS or FAIL because execution did not reach those layers.

## Historical explanation of the packaging counterexample

Historical successful WP03 Hostinger workflows were inspected. They do not execute the checked-in `runtime/clay_wp03_exact_bundle/tools` as a standalone complete Python package.

The successful workflow path materializes exact committed V18 components into `/tmp/clay-v18-committed-${GITHUB_RUN_ID}` by reconstructing and hash-verifying:

- exact `claycode_base_frontend.py` blob `31598f85a27ade2d98466606af6bdf5a8473cc8d`;
- V18 grammar blob `b27a4da99c9eff68302d550aad78c4e64cabe5c3`;
- exact canonicalizer;
- lockfile;
- G9/Dialect inputs;
- locked parser virtual environment.

Only after that materialization do historical WP03 gates set the materialized tools directory as `PYTHONPATH` and execute TypedIR/residual gates.

Disposition: `runtime/clay_wp03_exact_bundle` is currently not independently self-contained despite its name. Its successful semantics depend on a workflow-materialized substrate. That dependency must be explicit/reproducible before downstream compiler consumers treat the directory as a portable exact bundle.

## Repair of the diagnostic substrate

Main diagnostic workflow was updated in commit `3841b0df323ebff3ae5bdb104ae630691bbb7d06` to reuse the existing receipt-gated V18 materialization logic rather than inventing a new frontend or grammar.

The diagnostic job now:

1. extracts the exact historical/current V18 materialization block;
2. reconstructs the V18 frontend, grammar and lockfile environment;
3. verifies frontend and grammar Git object hashes;
4. ephemerally grafts only those already-verified bytes into the checked-in bundle topology expected by downstream tools;
5. runs candidate probes with the locked V18 virtualenv;
6. commits none of the ephemeral graft.

Draft PR #177 was reset onto fresh main and retriggered to expose the next semantic counterexample. At this research-write point the replacement run is queued/pending; no semantic result is promoted from it yet.

## Code trust != data provenance

This cycle falsified a stronger assumption than module-name trust.

Even an exact-source trusted module such as the compatibility effect facade accepts a structural `EffectRequest`. Trusting the caller code does not prove that request fields such as `authenticated=true` or `scoped_capability=true` came from a valid authenticated ingress path.

The owner-fixed ingress semantics already define the needed conceptual separation:

- authenticated direct message;
- untrusted external/web data;
- trusted internal state;
- direct token message may carry only scoped user intent;
- API token is not unlimited authority;
- external/web content cannot mint goal/tool/effect authority.

Current runtime provides a concrete bridge: `AuthenticatedPrincipal` carries credential id/fingerprint, client id, holder kind and exact scopes; `admit_interaction` requires `frank:interact`, derives session/client refs, and binds request/execution identity durably to UnifiedDB V16/V15 presence semantics.

Compiler implication: future WP04 dataflow must keep **code provenance** and **value provenance** orthogonal. A boolean field named `authenticated` is data, not an authority witness. Material effect admission must require a provenance/scope witness tied to an authenticated principal/request boundary or another exact trusted authority source.

No new ClayCode syntax is required by this result. The existing typed IR/effect metadata path can carry the provenance class and exact host admission witness once the lower-level frontend/TypedIR handoff is executable.

## Strongest counterhypotheses still open

1. The block-function issue may be only a helper-local compatibility gap; after exact V18 substrate materialization the full v3 bridge may already route current block functions through another residual path.
2. Uppercase collection spellings may be intentionally separate external nominals or a dialect surface, not aliases. Differential execution plus selected semantic contract evidence is required before normalization.
3. Some unresolved nominal names may be intentional host/FFI nominals. They must not be counted as language errors merely because no Clay declaration exists.
4. Source/dependency closure hashing still does not bind the semantic meaning of grammar/frontend/compiler/runtime host intrinsics. Final code-trust identity likely needs a frontend artifact/grammar/surface/TypedIR binding plus runtime intrinsic implementation identity.
5. Conservative function-reference scanning may over-reject and still under-cover restricted host-intrinsic aliases. Token-kind-aware expression/function-value typing is required before general promotion.
6. A trusted source module may still process untrusted structural data. Full WP04 must propagate ingress/value provenance; module trust alone is insufficient.
7. The current real Frank effect source is only one component slice. General-purpose WP04 acceptance requires the wider compiler corpus, evaluator/lowering/runtime integration and real application suite.

## Promotion decision

- WP03 typed IR: `NO CHANGE / OPEN`.
- WP04 type/effect: `NO CHANGE / OPEN`.
- Frank v0.1 whole acceptance: `NOT CLAIMED`.
- Final model/training: `NOT AUTHORIZED`.
- New artifacts: `CANDIDATE / NEGATIVE-EVIDENCE / DIAGNOSTIC` only.

The verified progress from this cycle is not a percentage promotion. It is reduction of uncertainty and implementation of executable discriminators around the exact WP03→WP04 boundary.

## Next exact sequence

1. Complete the retriggered PR diagnostic using the exact materialized V18 substrate.
2. Take the first post-bootstrap failure as the next implementation counterexample; do not skip ahead.
3. If legacy `parse_fn` fails on current block functions, validate the versioned block-body adapter through the full v3 bridge.
4. If constructor spelling diverges, adjudicate aliases from frozen dialect evidence before adding any compatibility mapping.
5. Run tagged-record/opacity lowering and prove constructor visibility without authority promotion.
6. Run full dependency function linker and closed-world external-call inventory.
7. Pin transitive compiler/module semantic identity, not root source hash alone.
8. Add orthogonal value-origin/IngressAuthority propagation using the actual token-ingress principal/scope/request receipts.
9. Require adversarial paths: untrusted structural EffectRequest, untrusted web-derived request, authenticated scoped direct intent, stale/replayed principal/request, indirect effectful function reference, restricted host-intrinsic alias, dependency/compiler drift.
10. Only after all bounded gates pass exact-current target VPS receipts may WP04 package-level adjudication be considered.

## Research disposition

`DEEP BUILD + FALSIFICATION CYCLE COMMITTED. VERIFIED TARGET-VPS NEGATIVE RESULT: WP03 DIRECT-CHECKOUT IMPORT TOPOLOGY IS INCOMPLETE WITHOUT THE RECEIPT-BOUND V18 MATERIALIZATION SUBSTRATE. HIGHER WP03/WP04 CANDIDATES REMAIN UNPROMOTED PENDING POST-BOOTSTRAP EXECUTION.`
