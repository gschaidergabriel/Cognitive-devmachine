# CURRENT AUTHORITY OVERRIDE — Frankenstein master cognition / 72h orchestration

**Date:** 2026-08-27  
**Status:** CURRENT-AUTHORITY SIDECAR — READ BEFORE `BUILD_ORCHESTRATION_PLAN_20260827.json`, `frankenstein_orchestrator_v1.py`, or `frankenstein_bugfix_v1.py`  
**Purpose:** preserve historical/current source without allowing stale plan text to mint execution authority.

## 1. Authority resolved for this curation pass

Canonical `main` observed at Triggerword‑3 start:

`854f6bc87780f4a5242489a6c807d186b16a8c3d`

Current supervisor inbox:

`research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`

Selected steering at start:

`research_entity/claycode/autonomous/SUPERVISOR_STEERING_9_13O_DELTA_2026-08-27T2341P0700_GPT56SOL.json`

Current provider authority:

`FREE_ONLY_HARD_OFF_ALL_PROVIDER_ROUTES_FALSE_TOGETHER_FORBIDDEN_NO_PAID_FALLBACK`

Current owner product target:

`VARIABLE COGNITIVE GRID + PERSISTENT DATABASE + CLAUDE CODE`

The newest current authority always outranks this sidecar if it changes later.

## 2. Exact status of the 72h Frankenstein artifacts

| Artifact | Current status | Evidence boundary |
|---|---|---|
| `CONCEPT.md` | `CURRENT_SOURCE / RESEARCH_CONCEPT` | Useful engineering concept; GRID10 language is benchmark/donor scope where it conflicts with current variable-N owner target. |
| `BUILD_ORCHESTRATION_PLAN_20260827.json` | `QUARANTINED_NON_OPERATIVE` | Contains external provider/Together assumptions that conflict with 9.13 HARD_OFF. Plan text cannot authorize execution. |
| `frankenstein_packages_v1.py` | `SOURCE_PRESENT / INTERNAL_MECHANISM_DONOR` | Package decomposition/CAS claim logic may be reviewed/tested independently; no provider authority is implied. |
| `frankenstein_orchestrator_v1.py` | `QUARANTINED_WHERE_PROVIDER_CALLING` | Source exists and non-networked orchestration tests were added, but provider dispatch is not currently authorized. |
| `frankenstein_bugfix_v1.py` | `QUARANTINED_WHERE_PROVIDER_CALLING` | Contains explicit NVIDIA→Groq→Mistral direct fallback and indefinite retry logic; do not execute that path under current HARD_OFF. |
| focused Frankenstein tests | `COMMIT_REPORTED_RESULT` | Commit `854f6bc…` reports 29/29 green. This Triggerword‑3 curation did not independently re-run them and does not upgrade that report to provider/runtime authority. |

## 3. Why this override is necessary

Current 9.13 steering had already found and quarantined the provider-calling 72h orchestration because it:

- selected NVIDIA/Nemotron, Groq and Mistral through the external fallback surface;
- relied on a still-ungated caller path after HARD_OFF;
- treated one Together training run as available even though current authority authorizes **zero** remaining paid runs and forbids Together.

After that quarantine, commit `854f6bc…` added concrete Bauleiter/Bugfix/package source and tests. This temporal order does **not** reverse the authority decision.

Source existence ≠ execution authority.

Test greenness ≠ provider authorization.

Plan text ≠ owner/supervisor authority.

## 4. Current hard stop

While current 9.13 HARD_OFF remains in force:

- **DO NOT** execute NVIDIA/Groq/Mistral/OpenRouter provider calls from these orchestration paths;
- **DO NOT** run Together inference/training/preflight from this plan;
- **DO NOT** read provider secrets merely to test whether the route might work;
- **DO NOT** import/initialize a provider client before resolving the current authority gate where that import itself can trigger credential/network side effects;
- **DO NOT** use Aider/external fallback dispatch as an indirect provider bypass;
- **DO NOT** modify Frank's own Harness to defeat the current gate.

Non-provider deterministic source review, local tests, static analysis, package-graph work, documentation, provenance repair and other currently admitted local/sandbox validation may continue inside the current execution boundary.

## 5. Required future closure before re-admission

A future operational Frankenstein orchestrator must place one canonical authority gate **before every provider boundary**, including before:

1. secret lookup;
2. provider import/initialization where it has side effects;
3. network I/O;
4. Aider invocation;
5. fallback dispatch;
6. retry/backoff loop entry.

Under HARD_OFF an executable receipt must establish at minimum:

```text
provider_calls = 0
secret_lookups = 0
external_fallback_dispatches = 0
together_calls = 0
```

The caller must fail closed before any of those effects.

A future authority change may re-admit specific routes, but re-admission must be derived from the then-current canonical authority; it must not be inferred from historical plan text, configured keys, a provider name, an HTTP success, or a statement that a route is “free.”

## 6. Provider-caller boundary identified by current steering

Current P0 closure targets the actual external fallback caller chain around:

`stern.py -> harness_aider.py -> last-resort/llm.py`

The specific filenames/locations may evolve. The invariant is semantic: **gate the external caller before it can inspect secrets or reach a provider boundary**.

The current instruction explicitly says not to solve this by modifying Frank's own Harness.

## 7. Package-dispenser salvage boundary

`frankenstein_packages_v1.py` contains potentially reusable architecture independent of provider use:

- split a long operation into bounded packages;
- explicit dependency graph;
- CAS-safe claim behavior;
- race-aware worker claiming;
- completion state rather than one giant model prompt.

This is a strong donor principle for future orchestration because it reduces context-limit and worker-failure coupling.

It still needs current-authority integration before becoming a production control plane. A package may describe forbidden work; package scheduling cannot grant the capability to execute it.

## 8. Bugfix watchdog salvage boundary

Useful provider-independent ideas in `frankenstein_bugfix_v1.py` include:

- a separate watchdog role rather than one self-repairing monolith;
- its own local Git history for candidate fix rollback;
- immutable ur-baseline plus moving accepted checkpoint;
- promotion only when declared metrics show no regression;
- explicit recovery logging.

The direct provider cascade and “never give up” external retry loop are **not currently admissible**. Persistent retry is especially dangerous across an authority change: a process that sleeps during HARD_OFF must re-resolve authority before each future attempt rather than assuming yesterday's permission still exists.

## 9. Evidence classification

### CURRENT_SOURCE

- current owner variable-grid target;
- current supervisor inbox/steering;
- current Frankenstein concept/scripts/tests present on main.

### COMMIT_REPORTED_RESULT

- `854f6bc…` reports 12/12 package + 7/7 orchestrator + 10/10 bugfix tests green.

### NEGATIVE_RESULT / AUTHORITY VIOLATION EVIDENCE

- fresh NVIDIA/Mistral fallback provenance after the HARD_OFF epoch shows that the external caller boundary remained reachable after provider execution should have stopped.

### QUARANTINED

- 72h provider-calling loops;
- Together allowance in the plan;
- any interpretation that test-passing source is therefore deployable now.

### OPEN_HYPOTHESIS — confidence 0.81

A provider-independent package dispenser + watchdog + checkpoint architecture can remain useful if every action packet carries current capability/authority identity and all external effects are gated at the actual caller boundary.

**Falsifier:** a clean non-provider implementation still permits a package/watchdog transition to create an external effect without current deterministic authority admission, or the authority can change while a retry loop continues using stale permission.

## 10. Re-entry rule

Before any future action on these files:

1. fetch current `main`;
2. read current `SUPERVISOR_INBOX.json`;
3. read its selected steering;
4. read newest explicit owner authority;
5. compare this sidecar to the current state;
6. if the current state differs, update/replace this sidecar rather than silently relying on it;
7. preserve this file as historical evidence if superseded.

This sidecar exists to make the conflict visible, not to freeze authority forever.