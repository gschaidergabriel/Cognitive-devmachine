# CURRENT AUTHORITY OVERRIDE — Frankenstein master cognition / 72h orchestration

**Date:** 2026-08-27  
**Status:** CURRENT-AUTHORITY SIDECAR — READ WITH `BUILD_ORCHESTRATION_PLAN_20260827.json` AND THE CANONICAL FRANKENSTEIN ENTRYPOINTS  
**Purpose:** preserve historical provider-backed donor source while making current authority and current caller-gate state explicit.

## 1. Re-entry changed the source state during this Triggerword-3 pass

Triggerword-3 started from canonical:

`main@854f6bc87780f4a5242489a6c807d186b16a8c3d`

Current `main` later advanced to:

`3c3dbe5020f57065f47bd4d0a2dce3c537128797`

That successor commit materially closes the source-side Frankenstein provider boundary. It:

- replaces the current build plan with `FRANKENSTEIN_BUILD_ORCHESTRATION_PLAN/v2` marked `QUARANTINED_NON_OPERATIVE_UNDER_CURRENT_PROVIDER_HARD_OFF`;
- preserves the old v1 plan byte-for-byte as `BUILD_ORCHESTRATION_PLAN_20260827_PROVIDER_QUARANTINED_854f6bc.json`;
- adds `frankenstein_authority_gate_v1.py`;
- turns `frankenstein_orchestrator_v1.py` and `frankenstein_bugfix_v1.py` into current authority-gated entrypoints;
- preserves the provider-backed implementations under explicit `_PROVIDER_QUARANTINED_854f6bc.py` donor names;
- moves the original orchestration/bugfix tests into historical-test provenance where appropriate;
- records a Triggerword-3 HARD_OFF closure receipt;
- reports 10/10 focused local tests green for the new source gate.

This curation organ did **not** independently re-run those exact 10 tests, so they remain `COMMIT_REPORTED_RESULT` here.

## 2. Current authority

Current supervisor inbox:

`research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`

Current provider authority remains:

`FREE_ONLY_HARD_OFF_ALL_PROVIDER_ROUTES_FALSE_TOGETHER_FORBIDDEN_NO_PAID_FALLBACK`

Current owner product target remains:

`VARIABLE COGNITIVE GRID + PERSISTENT DATABASE + CLAUDE CODE`

The newest explicit owner authority and current supervisor-selected authority always outrank this sidecar.

## 3. Exact current artifact status

| Artifact | Current status | Evidence boundary |
|---|---|---|
| `CONCEPT.md` | `CURRENT_SOURCE / RESEARCH_CONCEPT` | Useful donor/research concept. GRID10 is benchmark/donor scope where current owner target says runtime-variable N. |
| `BUILD_ORCHESTRATION_PLAN_20260827.json` | `CURRENT_SOURCE / QUARANTINED_PLAN_V2` | Explicitly says provider routes are not admitted, Together is forbidden, and the plan is non-operative under HARD_OFF. |
| `BUILD_ORCHESTRATION_PLAN_20260827_PROVIDER_QUARANTINED_854f6bc.json` | `HISTORICAL_SOURCE / QUARANTINED_DONOR` | Preserved old v1 plan including stale provider/Together assumptions. It cannot mint authority. |
| `frankenstein_authority_gate_v1.py` | `CURRENT_SOURCE / SOURCE_GATE` | Stdlib-only gate intended to resolve authority before provider import, secret lookup, network, Aider or fallback dispatch. |
| `frankenstein_orchestrator_v1.py` | `CURRENT_SOURCE / FAIL_CLOSED_ENTRYPOINT` | Current wrapper resolves authority before loading preserved provider-backed donor. Under HARD_OFF it must stop before external provider effects. |
| `frankenstein_bugfix_v1.py` | `CURRENT_SOURCE / FAIL_CLOSED_ENTRYPOINT` | Same authority-first wrapper rule. |
| `frankenstein_orchestrator_v1_PROVIDER_QUARANTINED_854f6bc.py` | `QUARANTINED_DONOR` | Historical provider-backed implementation, preserved for provenance/review; not current execution authority. |
| `frankenstein_bugfix_v1_PROVIDER_QUARANTINED_854f6bc.py` | `QUARANTINED_DONOR` | Historical NVIDIA→Groq→Mistral/watchdog implementation; not current execution authority. |
| `frankenstein_packages_v1.py` | `SOURCE_PRESENT / INTERNAL_MECHANISM_DONOR` | Package/dependency/CAS claim logic is provider-independent in principle; scheduling never grants capability. |
| original 854f6bc focused tests | `COMMIT_REPORTED_RESULT` | 29/29 reported green at the older source identity. No provider/runtime/whole-product credit. |
| 3c3dbe5 authority-gate tests | `COMMIT_REPORTED_RESULT` | 10/10 reported green locally at the successor source identity. Source/local-unit scope only. |

## 4. What is now closed vs. what is still not authorized

### Source-side closure now present

The current canonical entrypoints are designed to resolve authority **before**:

1. provider import;
2. provider secret lookup;
3. network I/O;
4. Aider invocation;
5. external fallback dispatch.

This directly addresses the earlier P0 source/caller-boundary finding for the Frankenstein entrypoints.

### Runtime/provider authorization remains closed

The existence of the gate does **not** mean providers are now allowed.

While current 9.13 HARD_OFF remains in force:

- provider routes remain OFF;
- Together remains forbidden;
- remaining Together paid-run authorization remains zero;
- provider-backed donor files remain quarantined;
- current entrypoints may only fail closed / expose authority status / participate in non-provider tests; they may not turn HARD_OFF into permission.

Therefore:

> source gate present ≠ provider route admitted

> 10/10 local gate tests ≠ provider runtime credit

> preserved donor ≠ current executable authority

## 5. Strongest next discriminator

The source-side gate is useful, but the next promotion-quality check is a **clean current non-provider exact-source execution** that binds:

- exact current `main` / tree / dirty=false state;
- exact authority inbox + selected steering bytes;
- exact `frankenstein_authority_gate_v1.py` bytes;
- exact canonical entrypoint bytes;
- stdout/stderr/result receipt;
- explicit counters proving, under HARD_OFF:

```text
provider_calls = 0
secret_lookups = 0
external_fallback_dispatches = 0
together_calls = 0
```

This should remain a non-provider test. It is not a reason to configure or probe credentials.

A future authority change may re-admit specific routes, but the entrypoint must resolve that future authority dynamically. Historical plan text, configured keys, provider names, “free” labels, or past success never self-authorize.

## 6. Package-dispenser salvage boundary

`frankenstein_packages_v1.py` remains a strong provider-independent donor for:

- decomposing long work into bounded packages;
- explicit dependency graphs;
- CAS-safe claims;
- race-aware worker claiming;
- completion state rather than one monolithic model context.

This is valuable for context/rate/failure resilience. But package scheduling cannot grant effects or provider capability; every package action still needs current authority at its real effect boundary.

## 7. Bugfix watchdog salvage boundary

Useful provider-independent ideas preserved by the quarantined bugfix donor include:

- a separate watchdog rather than one self-repairing monolith;
- separate local Git history for candidate fixes;
- immutable ur-baseline plus moving accepted checkpoint;
- promotion only under declared no-regression metrics;
- explicit recovery logging.

The old direct provider cascade and indefinite retry behavior are quarantined. If a future version reintroduces retry under a later admitted provider authority, it must **re-resolve authority before every future attempt** so a sleeping process cannot continue with stale permission after an emergency stop or authority change.

## 8. Evidence classification

### CURRENT_SOURCE

- variable-N owner target;
- 9.13 HARD_OFF supervisor state;
- canonical v2 quarantined plan;
- current stdlib authority gate;
- current fail-closed Frankenstein entrypoint wrappers.

### HISTORICAL_SOURCE / QUARANTINED

- old v1 provider/Together plan;
- old provider-backed Bauleiter and Bugfix implementations.

### COMMIT_REPORTED_RESULT

- `854f6bc…`: 29/29 older focused tests reported green;
- `3c3dbe5…`: 10/10 current authority-gate focused local tests reported green.

### NEGATIVE_RESULT / CAUSAL ENGINEERING INPUT

Before the 3c3dbe5 closure, fresh provider fallback provenance after HARD_OFF showed the external caller boundary could still be reached. That failure is preserved because it explains why the gate must sit before import/secret/network rather than being a documentation warning after the fact.

### OPEN_HYPOTHESIS — confidence 0.88

A provider-independent package dispenser + watchdog/checkpoint architecture remains reusable if every real effect is authority-gated at the actual caller boundary and retry re-resolves current authority.

**Falsifier:** an exact current non-provider HARD_OFF execution causes any secret lookup/provider/network/fallback event, or a later authority change can be bypassed by a stale long-lived retry loop.

## 9. Re-entry rule

Before future action:

1. fetch current `main`;
2. read current `SUPERVISOR_INBOX.json`;
3. read its selected steering;
4. read newest explicit owner authority;
5. inspect the current canonical Frankenstein plan/gate/entrypoint bytes;
6. treat preserved `_PROVIDER_QUARANTINED_*` files only as donor provenance;
7. if authority/source moved again, update or supersede this sidecar without rewriting older evidence.

This file makes authority/source evolution visible; it is not a frozen authority.