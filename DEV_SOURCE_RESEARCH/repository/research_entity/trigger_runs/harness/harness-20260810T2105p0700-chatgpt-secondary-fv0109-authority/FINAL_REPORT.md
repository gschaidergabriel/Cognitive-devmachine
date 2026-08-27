# Harness run — direct Frank v0.1 Effect Authority

Run: `harness-20260810T2105p0700-chatgpt-secondary-fv0109-authority`  
Program: `FRANK_V0_1`  
Component: `F-V01-09-EFFECT-AUTHORITY`  
Promotion: **component remains IN_PROGRESS**

## Result

This run followed the current owner supersession: Harness is a direct Frank v0.1 falsification/repair method, not a separate H1/H2/H3 product.

The highest-information open F-V01-09 gap was the owner-fixed default-allow / destructive-confirmation policy. The existing current Frank effect lifecycle had real target-VPS crash/reservation evidence, but the full owner-fixed EffectClass/EffectDecision/Confirmation policy was not yet executable in the current target source.

### Direct current-Frank code delta

Target repo `gschaidergabriel/Dr.-Unterweger`:

- `dbe249e5220af9faff74b31445f00ed36efe7ac3` — direct executable effect-authority policy falsifier;
- `b53420100cfeefef0f6135ce1ccb0ee28f2c5e9f` — bind owner-fixed effect classes, request identity, confirmation and opaque authorization into `claycode/frank_effects.clay`;
- `af4eab1754539df31e98505bcdfdac2950daf970` — separate target-VPS read-only test executor from the write-capable receipt persistence job;
- `0f51bcedbf9cee3caba853c9f4e05c14e3f80647` — extend current ClayCode frontend/TypedIR discriminator to authority declarations;
- `3b12db3b0271291b1befa26a01efaabb68dfc2da` — repair the CI status-interface regression introduced by that extension.

### Real accepted target-VPS policy result

Current hardened receipt: `runtime/vps_unifieddb/frank_effect_authority_v1/LATEST.json`, run `31397351794`.

Observed on `clay@digital-retina`:

- 20/20 policy cases PASS;
- 1000/1000 policy-relevant request mutations changed request identity;
- direct execution rate for eligible non-destructive fixture set = 1.0;
- unnecessary refusal rate = 0.0;
- destructive false-allow before required confirmation = 0.0;
- gate-oracle latency p50 0.21 us, p95 0.34 us, p99 0.44 us, max 19.911 us;
- executor repository permission = `contents:read`;
- checkout credentials absent in executor;
- executor repo-write attempted = false;
- evidence transport artifact digest = `799801b653984fe9297ddec0b1085ac212cb4fb11feb46416d78da8a76c582bd`.

This receipt does **not** claim ClayCode compiled execution, a real external provider effect, or whole Frank v0.1 acceptance.

## Parallel-source counterexample

During the run another worker added `claycode/frank_effect_authority.clay` at commit `6e59fddd91a4bef35d4732fd867ed8907a4e5a16`.

Cross-read found two material defects relative to already-established F-V01-09 regressions:

1. authentication truth lived in `EffectAuthorityFacts`, but confirmation validation did not receive those facts; therefore an `AUTHENTICATED_USER`-named request could reach confirmation without proving the factual authentication state at confirmation validation;
2. `request_hash` was supplied by `EffectAuthorityRequest` and was not derived from the policy-relevant facts, so mutable authority/destructive guard facts were not proven bound to the confirmation identity.

Smallest coherent repair was committed directly to the current target repo at:

`1d7d47174a2be16f0e044ea61965acb3350cfc07`

The repaired module now:

- derives `effect_authority_request_hash(req, facts)` from a policy-relevant projection;
- passes `EffectAuthorityFacts` into confirmation validation;
- rejects factually unauthenticated confirmation use;
- preserves narrow SYSTEM_POLICY preauthorization only for an explicitly preauthorized exact privileged change;
- keeps credential/financial/physical/destructive confirmation user-authenticated;
- adds explicit invariants for policy-fact hash binding and named-user/authentication separation.

This repair is **not promoted** until its exact current source passes the normal current ClayCode and target-VPS evidence surfaces.

## Provider boundary fusion

Parallel commit `dc2568ff863c4d7c4696c2d14c62db406f9fecb4` updated the Google effect bridge so an idempotency key alone no longer implies retry safety. Unknown provider outcomes route to `RECONCILE_REQUIRED` unless provider/operation evidence proves same-key retry safety.

This is compatible with the lifecycle evidence and was retained.

## Current truth boundary

The currently stored lifecycle receipt still binds old effect blob `9c318ce70536ed96740da6eaf792e079af51ea10`. It remains valid historical/current-lineage evidence for that source but is not promoted as exact-current-source lifecycle evidence after `b5342010...`.

The extended frontend/TypedIR probe was triggered for the current source. A status-string contract mismatch introduced by the extension was found and repaired in `3b12db3b...`. Until a new exact current-source receipt is persisted, frontend/TypedIR and current-source crash/replay remain OPEN.

## F-V01-09 disposition

`F-V01-09-EFFECT-AUTHORITY = IN_PROGRESS`.

Receipt-backed subchecks now credited:

1. owner-policy semantics + target-VPS matrix — PASS;
2. executor / receipt-writer authority isolation — PASS.

Still open:

1. exact-current-source lifecycle crash/replay;
2. current ClayCode frontend/TypedIR acceptance, including the parallel policy module;
3. source-of-truth consolidation/differential between `frank.effects` and `frank.effect_authority`;
4. real provider write with injected uncertain outcome and reconciliation;
5. verified outcome -> provenance-bound UnifiedDB re-entry -> DONE;
6. final `CLAY_0_1_EFFECT_AUTHORITY_RECEIPT` / terminal integration.

## Scientific / engineering interpretation

The useful result is not that a Python policy oracle can pass. The useful result is that the five prior authority-escalation counterexamples now have a directly tested target-VPS realization against exact Frank semantic bytes, and a newly concurrent policy source was immediately shown to reintroduce two of the same failure classes before promotion.

This is execution/falsification evidence, not proof of universal safety and not evidence of phenomenal consciousness.

## Re-entry

- `FRANK_V0_1_CODE_DELTA`
- `FRANK_V0_1_TEST_DELTA`
- `FRANK_V0_1_ARCHITECTURE_DELTA`
- `FRANK_V0_1_NEGATIVE_RESULT`
- `FRANK_V0_1_WORK_DELTA`

No paid/final model training was started or authorized.
