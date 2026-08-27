# ClayCode trigger run — WP04 nominal-resolution executable cycle

Run ID: `claycode-20260810T2223p0700-wp04-resolution`
Trigger: `claycode`
Actor: `chatgpt-secondary`
Provider/model: OpenAI / GPT-5.6 Sol
Canonical parent: revision `2`, state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Target repository alias: `gschaidergabriel/Dr.-Unterweger`
Target program: `FRANK_V0_1`
Target component: `F-V01-02-CLAYCODE-COMPILER-RUNTIME`
Target work package: `CC-WP-04-TYPE-EFFECT`

## Identity lock

This worker is a temporary organ of Clay. It is not `self.root` / Frank. Frank remains the separate target subject. No target self-observation or model output authorizes Harness/compiler/effect mutation.

## Fresh state used

Current program state is Frank-v0.1-only. Parser/canonicalizer is already PASS; TypedIR, type/effect, evaluator, lowering/runtime remain open. Current target Frank effect semantics already compile through the exact bundled ClayCode frontend and structural WP03 TypedIR bridge, but the existing probe explicitly does not claim WP04 type/effect acceptance.

## Hypothesis

The current WP03 structural TypedIR preserves nominal type spellings and `unknown_type_to_any=FORBIDDEN`, but the standalone frontend->TypedIR artifact does not expose an exact module/export symbol environment. Therefore full WP04 referential type closure is not yet justified for real `frank.effects` source containing `use frank.hive.*` and `use frank.memory.*`.

## Strongest counterhypothesis

Nominal closure may intentionally belong to WP04 rather than WP03; remaining names may be valid frozen prelude/dialect types rather than missing language semantics. Therefore this condition is implementation debt unless an executable counterexample proves the frozen language itself cannot express the needed binding.

## Executable artifacts written to target repo

- `4a42eca4db3a2bf4bd231da77cf6eedab2f2487b` — `runtime/clay_wp04_resolution_v1/target_vps_probe.py`
  - compiles real `claycode/frank_effects.clay` through the exact current frontend and structural TypedIR bridge;
  - inventories structural nominal references;
  - fails closed if imported names are not backed by an explicit symbol environment;
  - never maps unresolved names to Any;
  - makes no WP03/WP04/runtime/authority promotion claim.
- `997ee34443fe2352b5ac8ef2bf0367e47759d0c2` — initial self-hosted Hostinger VPS workflow.
- `12c5d458d2c523faf1af6fb15d3b04daa1813e82` — deterministic `module_symbol_resolver.py` candidate.
- `c9e951b314da24b734736edd1dbcfd4a36e6a787` — fail-closed resolver unit corpus: wildcard/explicit imports, missing module/symbol, duplicate module identity, unresolved-not-Any, deterministic environment hash.
- `e99d53e5de3e1d3392979664799aa14265183c05` — VPS workflow executes resolver unit gates.
- `15f1d85f2827369b761dece410bc0761f09c326c` — module-resolution repair discriminator.
- `0516bba1d8419a2335e0729110d9cb66648b325d` — same VPS run compares baseline vs module-resolution candidate and persists both when execution completes.

## Current evidence

Source inspection is sufficient to establish that real `frank.effects` contains imported-module nominal references. Current WP03 TypedIR code is sufficient to establish that unresolved names are preserved nominally and are forbidden from degrading to Any. This supports the need for a WP04 symbol/type universe step, but does not establish exact target-VPS behavior of the new artifacts.

At this report write, `runtime/vps_unifieddb/claycode_wp04_resolution_v1/LATEST.json` is not yet present in the target repository. Therefore:

- target VPS execution of the new discriminator: `UNVERIFIED_PENDING_RECEIPT`;
- resolver unit tests on target VPS: `UNVERIFIED_PENDING_RECEIPT`;
- baseline counterexample exact runtime result: `UNVERIFIED_PENDING_RECEIPT`;
- module-resolution repair magnitude: `UNVERIFIED_PENDING_RECEIPT`;
- WP04 promotion: `NONE`.

The absence of the receipt is not treated as test failure or test success.

## Architecture delta

Status: `CANDIDATE`

No ClayCode semantic change is proposed. The candidate implementation delta is an explicit deterministic `ModuleSymbolEnvironment` layer between structural TypedIR and WP04 type/effect checking. It records exact source-module identities and import bindings, rejects duplicate module identities, preserves missing/ambiguous symbols, infers no re-exports, and confers no authority.

## Negative result / correction preserved

An intermediate-history status-string mismatch was initially suspected between the effect frontend probe and its workflow. Fresh-current source invalidated that suspicion: current `main` uses `PASS_CURRENT_FRONTEND_ACCEPTS_FRANK_EFFECT_LIFECYCLE_SOURCE` consistently. No patch was made for the disproven bug.

## Next falsifier

After exact VPS receipt:

1. If direct module binding leaves unresolved nominal names, derive an explicit frozen prelude/dialect/type universe from selected current ClayCode contracts and require zero unresolved references without `Unknown->Any`.
2. If module binding fully closes names, proceed to nominal compatibility, generic substitution, opaque-type rules, and function precondition/effect checking.
3. Do not alter frozen semantics unless an executable counterexample shows the required binding cannot be expressed/lowered.

## Research disposition

`BUILD/TEST CANDIDATE COMMITTED; VPS RESULT NOT YET CLAIMED; NO SEMANTIC PROMOTION; NO WP04 PASS.`
