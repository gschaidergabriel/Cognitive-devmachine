# ClayCode deep cycle — Adjudication V2 after exact-current Hostinger diagnostic v3

Run lineage: `claycode-20260810T2318p0700-wp03-wp04-boundary-deep`
Actor: `chatgpt-secondary`
Target repository: `gschaidergabriel/Dr.-Unterweger`
Target program/component: `FRANK_V0_1 / F-V01-02-CLAYCODE-COMPILER-RUNTIME`
Primary packages: `CC-WP-03-IR-TYPES`, `CC-WP-04-TYPE-EFFECT`
Promotion from this adjudication: `NONE`

## Why this V2 exists

The first report/receipt captured a real direct-checkout bundle/import failure and a set of WP03/WP04 candidates. Subsequent target diagnostics localized two additional bootstrap/reproducibility failures, repaired them without weakening executor isolation, and finally executed the semantic counterexample ladder on the accepted self-hosted Hostinger runner.

This document preserves the exact distinction between:

- compiler substrate/reproducibility failures;
- real executable semantic differentials;
- source/frontend surface-dispatch gaps;
- bugs in the diagnostic harness itself;
- candidate repairs that still have no package promotion.

## Diagnostic chronology

### Diagnostic 1 — direct exact-bundle checkout is not self-contained

PR diagnostic run: `31406878642`
Job: `93515268433`
Runner: self-hosted `clay` / host `digital-retina`

All newly written Python candidates byte-compiled, but each semantic probe stopped while importing the checked-in WP03 bundle:

`ModuleNotFoundError: No module named 'claycode_base_frontend'`

Disposition: verified packaging/import-topology counterexample. No higher-layer semantic result was inferred.

Historical WP03 workflows were then inspected. Their successful path materialized exact V18 frontend/grammar/locked environment outside the checkout before executing TypedIR gates.

### Diagnostic 2 — historical materializer was credential-coupled

Self-hosted diagnostic job reached the newly added materialization step but failed before semantic probes with:

`fatal: could not read Username for 'https://github.com': No such device or address`

The historical V18 bridge contains a pre-extraction:

`git fetch --depth=1 origin "$OLD" "$FULL"`

Modern compiler/effect diagnostics intentionally use `persist-credentials: false`. Reintroducing a GitHub write/read credential into the semantic executor would weaken the evidence boundary, so the security isolation was not relaxed.

Disposition: verified security/reproducibility coupling in the historical bootstrap path.

### Credential-free exact-current bootstrap repair

A local-object materialization path was built. The historical remote fetch is replaced only with fail-closed local commit-object assertions:

- pinned old commit `c3709c4e4f78b6d45bfa8b174f2d07deb6091ff8` must exist locally;
- pinned full commit `ab2e2a7d0788c0ed0e243288cfa969dbf9ab2342` must exist locally;
- no network fallback exists.

A further audit against the most recent successful WP03 receipt found that frontend/grammar alone are insufficient. The accepted WP03 workflow reconstructs the current TypedIR from a content-addressed ancestor plus a committed delta.

Exact compiler substrate pinned by diagnostic v3:

- V18 frontend Git blob: `31598f85a27ade2d98466606af6bdf5a8473cc8d`;
- V18 grammar Git blob: `b27a4da99c9eff68302d550aad78c4e64cabe5c3`;
- reconstructed current TypedIR Git blob: `e8525ee10f5fe4b8d40db79f0d8264a5231eea63`.

The checked-in exact-bundle copy of `claycode_base_typed_ir.py` was not treated as equivalent merely because of its path/name; its Git object differs from the reconstructed accepted current TypedIR. This is a concrete example of why compiler identity must be content-addressed rather than path-addressed.

## Exact-current diagnostic v3

Draft diagnostic PR: `#210` (closed after evidence collection, never merged)
Actions run: `31410165704`
Job: `93526026924`
Runner class: self-hosted Linux/X64 accepted target diagnostic

Infrastructure/result boundary:

- credential-free full-history checkout: PASS;
- local-object exact V18 materialization: PASS;
- exact frontend blob check: PASS;
- exact V18 grammar blob check: PASS;
- exact reconstructed current TypedIR blob check: PASS;
- candidate Python byte compilation: PASS;
- all seven semantic/diagnostic probes executed: PASS as diagnostic execution;
- external effect execution: NONE;
- model-output execution: NONE;
- WP03/WP04 promotion: NONE.

The GitHub Actions job conclusion was `success` because the diagnostic ladder intentionally records counterexamples without aborting subsequent probes. Semantic status must therefore be read from each probe JSON, not from the overall job conclusion.

## v3 semantic matrix

### 1. Constructor spelling differential — REAL SEMANTIC COUNTEREXAMPLE

Probe status: `SUPPORTED_CONSTRUCTOR_SPELLING_LOWERING_GAP`
Probe pass: `true` as a discriminating experiment
Counterexample: `true`
Safe alias-candidate precondition: `true` in this corpus slice because no conflicting uppercase constructor declarations were found.

All six tested pairs diverged in the current executable typed-value canonicalizer:

- `Set<Symbol>` vs `SET<Symbol>`;
- `Option<Symbol>` vs `OPTION<Symbol>`;
- `Ordered<Symbol>` vs `ORDERED<Symbol>`;
- `List<Symbol>` vs `LIST<Symbol>`;
- `Map<Symbol,Int>` vs `MAP<Symbol,Int>`;
- `Result<Symbol,Int>` vs `RESULT<Symbol,Int>`.

Observed current source usage across 20 Clay source files in the diagnostic checkout:

- `SET<...>`: 215 occurrences; `Set<...>`: 0;
- `OPTION<...>`: 73; `Option<...>`: 0;
- `ORDERED<...>`: 9; `Ordered<...>`: 0;
- `MAP<...>`: 6; `Map<...>`: 0;
- `LIST<...>`: 0; `List<...>`: 0;
- `Result<...>`: 3; `RESULT<...>`: 0.

Executable behavior was not merely a parser rejection difference:

- title-case `Set` canonicalized duplicate/order-insensitive input to set semantics; uppercase `SET` was treated as an unknown nominal and rejected for the structured list value;
- title-case `Ordered`/`List`/`Map`/`Result` performed their dedicated constructor semantics while uppercase forms were rejected as unsupported/unknown nominals;
- most importantly, title-case `Option<Symbol>` produced the Option discriminator wrapper, while uppercase `OPTION<Symbol>` was treated as a generic nominal scalar and accepted the raw string `"x"` without the Option discriminator.

That last case is stronger than a cosmetic spelling mismatch: the current uppercase spelling can silently lose constructor semantics instead of always failing closed.

Disposition: real WP03 typed-IR/lowering compatibility gap. It does **not** prove that general case-insensitive nominal semantics are correct. Only a closed, versioned constructor-alias compatibility layer is justified by this evidence.

### 2. Real Frank block-function differential — SURFACE DISPATCH COUNTEREXAMPLE BEFORE FUNCTION LOWERING

Status: `COUNTEREXAMPLE_OR_BLOCK_FUNCTION_PROBE_GAP`

Exact V18 parsing of current `claycode/frank_effects.clay` failed at line 5 column 1 on:

`use frank.hive.*`

The V18 parser expected its declarative top-level forms such as `import`, `record`, `rule`, `cycle`, etc. Therefore the probe never reached the historical `parse_fn` equals-body assumption.

Disposition: no conclusion about the block-function candidate from this v3 probe. The first blocking layer is frontend surface dispatch.

### 3. Integrated effect-boundary probe — SAME SURFACE DISPATCH COUNTEREXAMPLE

Status: `COUNTEREXAMPLE_OR_IMPLEMENTATION_GAP`

The same V18 frontend rejected current `frank.effects` at the first `use` declaration. No effect-boundary admission logic ran.

Disposition: no bounded WP04 effect-checker PASS or FAIL may be inferred from this probe execution.

### 4–7. Four downstream probes — DIAGNOSTIC HARNESS IMPORT BUG, NOT LANGUAGE RESULT

Affected probes:

- indirect-reference/dependency-drift follow-up;
- nominal-universe audit;
- closed-world effect-completeness audit;
- dependency-closure function-linker differential.

All four failed with an AttributeError indicating the imported module named `target_vps_probe` did not contain the expected helper such as `current_frontend_contract`.

Root cause: the candidate probes prepend both their own directory and the older resolution-probe directory to `sys.path` using front insertion in an order that allows the older `runtime/clay_wp04_resolution_v1/target_vps_probe.py` to shadow the intended local `runtime/clay_wp04_type_effect_v1/target_vps_probe.py`.

Disposition: diagnostic harness namespace/import-order bug. It is neither a ClayCode semantic failure nor a runtime authority failure. These four probes require explicit module-path binding or a new structured-surface base helper before their semantic results are admissible.

## Architectural inference from the surface failure

The exact V18 frontend source itself states that its executable contract covers the declarative BASE-D-V18 G9/Dialect surface and that procedural structured ClayCode — block-bodied `fn`, `let`, `require`, `return`, loops — remains owned by a generic structured backend.

Current `frank.effects` uses a procedural structured surface including:

- `use module.*` imports;
- `type X = { ... }` structural tagged records;
- `type X = opaque { ... }` opaque tagged records;
- generic block-bodied `fn` declarations;
- `let`, `require`, `return`, nested `if`;
- calls, field paths and infix relation words.

Therefore the v3 `use` failure should not be repaired by silently teaching V18 a second language surface. The stronger architecture is explicit frontend dispatch:

- declarative G9/Dialect input -> receipt-gated BASE-D V18 frontend;
- current Frank procedural source -> distinct structured frontend contract;
- both produce canonical AST/IR artifacts whose surface, grammar, source and semantic identities are explicitly bound;
- no cross-surface relabel without an equivalence receipt.

A repository search during this run did not locate an immediately reusable checked-in executable `generic structured backend`. A bounded candidate was therefore started rather than modifying V18.

## New post-v3 candidates

### Constructor compatibility v1

Closed alias table only:

- `SET -> Set`
- `OPTION -> Option`
- `ORDERED -> Ordered`
- `LIST -> List`
- `MAP -> Map`
- `RESULT -> Result`

Properties:

- source text is not rewritten;
- original spelling is retained as provenance;
- nominal matching is not made generally case-insensitive;
- unknown names remain unknown;
- no Any fallback;
- no authority grant;
- promotion NONE.

### FRANK_STRUCTURED_V1 surface/frontend

A separate LALR grammar/frontend candidate was added for the procedural constructs already present in current `frank.effects`. It has its own surface name, frontend schema, grammar hash, semantic hash and contract hash. It reuses only the existing canonical Tree/Token -> JSON representation and later current TypedIR lowerers; it cannot be relabelled as BASE-D V18.

The real-Frank probe is designed to require:

- strict LALR construction;
- deterministic full-source parse/reparse;
- exactly two current `use` declarations;
- all 13 expected Frank effect functions;
- block body identity preserved for all 13;
- all expected tagged records;
- exact three opaque types (`Capability`, `EffectAuthorization`, `EffectReservationReceipt`);
- all expected closed sum types;
- explicit constructor compatibility accounting;
- deterministic current TypedIR hash.

No package promotion is attached to a green bounded diagnostic.

## Code trust versus data provenance remains independently open

The exact current Frank effect source hash was still identical between the target-VPS authority oracle receipt and the source-only trust-manifest candidate. The authority oracle is real Hostinger evidence and passes its deterministic policy matrix, but explicitly says `claycode_compiled_execution=false`.

Therefore compiler work is testing the same policy source, not a drifted replacement.

However, module/source trust alone remains insufficient. Current `EffectRequest` contains structural booleans such as `authenticated` and `scoped_capability`. A trusted code module receiving an untrusted structural value does not make that value authoritative.

The owner-fixed ingress contract already distinguishes:

- `AUTHENTICATED_DIRECT_MESSAGE`;
- `UNTRUSTED_EXTERNAL_DATA`;
- `TRUSTED_INTERNAL_STATE`.

Current token runtime supplies concrete admission evidence: authenticated credential ID/fingerprint, client ID, holder kind, scopes, and durable request/session identity. `frank:interact` is checked from the canonical credential record, not accepted from the request payload.

Future WP04 dataflow therefore needs orthogonal dimensions:

1. **code/compiler identity** — exact source + surface/grammar/frontend + TypedIR/effect summary + dependency closure + runtime intrinsic identity;
2. **value origin/authority witness** — ingress class + credential/principal fingerprint + admitted scope + client/session/request identity or equivalent trusted internal policy witness.

A field named `authenticated=true` is data, not an authority witness.

## Status decision after v3

- Credential-free exact-current compiler bootstrap: **BOUNDED PASS**.
- BASE-D V18 declarative frontend: prior receipt status unchanged; not modified here.
- Real current Frank source through V18: **COUNTEREXAMPLE — WRONG SURFACE/DISPATCH**.
- Constructor casing compatibility: **SUPPORTED EXECUTABLE LOWERING GAP**.
- Block-function compatibility: **NOT YET ADJUDICATED because source fails earlier at surface dispatch**.
- Tagged-record/opacity candidate: **NOT YET TARGET-ADJUDICATED**.
- WP03 package: **OPEN / NO PROMOTION**.
- WP04 package: **OPEN / NO PROMOTION**.
- Whole Frank v0.1: **NOT CLAIMED**.
- Final training: **NOT AUTHORIZED**.

## Exact next evidence sequence

1. Execute strict `FRANK_STRUCTURED_V1` parser on full current `frank.effects` on Hostinger.
2. If grammar fails, patch only the first concrete unsupported current syntax; never widen with permissive text capture.
3. Once parse passes, lower the same canonical structured AST through the exact reconstructed current TypedIR with versioned block-body compatibility.
4. Verify all functions/types/opacity/sums and constructor compatibility deterministically.
5. Rebase module-symbol/function-linker probes on the structured frontend and fix their module-shadowing bug via explicit file/module identity.
6. Run closed-world call/effect inventory; unknown external calls remain non-pure obligations.
7. Bind exact module dependency closure and compiler/frontend/grammar identities to code trust.
8. Add value-origin/IngressAuthority propagation and request-admission witness; module trust never substitutes for data provenance.
9. Re-run adversarial cases including untrusted structurally forged `EffectRequest`, web-derived request, authenticated scoped direct intent, source/compiler/dependency drift, indirect function reference and unknown host intrinsic.
10. Only then consider a bounded WP04 component adjudication; package PASS still additionally requires general-purpose corpus/evaluator/lowering/runtime/FFI evidence.
