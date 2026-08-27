# Current authority and evidence — Triggerword 3 snapshot

**Curation snapshot time:** 2026-08-27, user trigger `triggerwort 3`  
**Base canonical `main`:** `854f6bc87780f4a5242489a6c807d186b16a8c3d`  
**Purpose:** make current-vs-historical boundaries explicit. This file is a snapshot, not a permanent authority surface.

---

## 1. Resolution order used for this curation pass

1. newest explicit owner authority;
2. newest admitted supervisor/provider authority;
3. exact current source/runtime evidence at exact identity;
4. current program/bootstrap surfaces;
5. older receipts/branches/PRs;
6. archive caches and conversational summaries.

A newer filename or larger version number does not automatically mean new authority. In particular, current `9.13O` and `9.14_GO` steering artifacts explicitly mark themselves **NON_AUTHORITY_STEERING_ONLY**.

---

## 2. Current repository head observed at start

`CURRENT_SOURCE`

```text
main = 854f6bc87780f4a5242489a6c807d186b16a8c3d
```

Commit title:

`frankenstein: erste lauffaehige Version Bauleiter/Bugfix/Paket-Dispenser (direkt vom Koordinator geschrieben)`

Its commit message reports 12/12 package tests, 7/7 orchestrator tests, 10/10 bugfix tests and 29 total green tests. Those are **source/component test claims at that commit**, not authorization to deploy the provider-calling loops and not whole EntityOS/HCU acceptance.

---

## 3. Owner architecture target

`CURRENT_SOURCE`

The highest-precedence owner correction used by this pass is:

`research_entity/global/OWNER_CORRECTION_ZERO_ENTITYOS_COGNITIVE_GRID_DB_CLAUDECODE_GLOBAL_JSPACE_2026-08-25.md`

It supersedes conflicting fixed-GRID10 interpretations.

Current target:

```text
VARIABLE COGNITIVE GRID + PERSISTENT DATABASE + CLAUDE CODE
```

Key consequences:

- grid size `N` is variable;
- GRID10 is a benchmark/debug configuration, not final architectural identity;
- the grid reproduces/distributes Zero/EntityOS cognitive processes;
- durable exact data belongs in the database rather than being re-simulated;
- Claude Code remains the strong model/tool/code partner;
- the Global J-Space bridge may use only the strongest actually exposed interface;
- unproven activation-level access to Claude Code must not be claimed;
- Qwen3.5-0.8B-class remains the first serious small-module training target in that directive.

---

## 4. Current execution authority vs. provider authority

Two different questions must not be collapsed.

### 4.1 Local / VPS sandbox development authority

`CURRENT_SOURCE`

`CLAY_EXECUTION_AUTHORITY.md` points to:

`governance/CLAY_VPS_SANDBOX_FULL_EXECUTION_AUTHORITY_2026-08-25.md`

That owner authority permits broad development/research work inside the designated `clay-direct-dev` sandbox, including root/sudo there, package installation, local model/runtime work, compilation, tests, fuzzing, benchmarks, ablations, process administration and scratch-destructive tests.

It does **not** automatically authorize paid-provider spend, subscriptions, unrelated external effects, credential exfiltration or attacks.

### 4.2 Provider execution authority

`CURRENT_SOURCE`

The current provider authority remains **9.13 HARD_OFF**. The 9.13O file says explicitly that it is steering only and does not supersede that authority.

Resolved current provider state:

```text
FREE_ONLY_HARD_OFF
all provider routes = false
Together = forbidden
paid fallback = forbidden
new provider execution = forbidden
runtime quiescence required before promotion
```

The current `SUPERVISOR_INBOX.json` identifies fresh post-hardoff NVIDIA/Mistral fallback activity as evidence that the external caller boundary was not completely gated.

---

## 5. Frankenstein 72-hour orchestrator status

`CURRENT_SOURCE + NEGATIVE_RESULT`

Recent source implements:

- `frankenstein_packages_v1.py` — package decomposition / CAS-safe claiming;
- `frankenstein_orchestrator_v1.py` — continuation/respawn orchestration;
- `frankenstein_bugfix_v1.py` — separate watchdog/rollback lane with provider fallback.

However, the current supervisor steering classifies the provider-calling 72-hour Frankenstein orchestration as:

```text
QUARANTINED_NON_OPERATIVE_UNDER_CURRENT_HARD_OFF
```

Therefore:

- source existence is preserved;
- component tests remain historical/current source evidence at their exact commit;
- provider-backed execution is not authorized;
- provider-authored core changes after the hard-off boundary require independent clean non-provider review/re-execution before promotion;
- Together/NVIDIA/Groq/Mistral fallback logic cannot be advertised as a valid current autonomous runtime path.

This is a good example of why **source-ready != runtime-authorized**.

---

## 6. Current runtime/product credit

`CURRENT_SOURCE`

From the current supervisor inbox/steering surfaces:

```text
whole EntityOS/HCU runtime credit = 0
full HCU runtime credit = 0
physical GRID10 runtime credit = 0
canonical runtime semantics credit = 0
training credit = 0
whole product PASS = false
```

There is substantial component/source/test evidence in the repository. The zeroes above mean that those components have not been promoted to the broader claimed scopes under the current authority/evidence rules.

---

## 7. Important measured results that survive curation

### UnifiedDB deeper negative run

`PROJECT_MEASUREMENT + NEGATIVE_RESULT`

`research_entity/trigger_runs/unifieddb/unifieddb-20260811T0441p0700-chatgpt-secondary-deeper-deltas/FINAL_REPORT.md`

Reproduced six gaps on the accepted target while keeping canonical state/effects untouched:

1. source certificate did not attest live SQLite schema;
2. symmetric pair certificate made a derived graph an availability dependency of canonical authority;
3. stale derived graph reads were not fully gated and source root was not bound;
4. mixed temporal text order + ambient clock could create false-current semantics;
5. snapshot receipt could hash live mutable files from different logical instants;
6. exact repository HEAD was broader than the semantic dependency set.

The report also measured normalized live-schema digest cost around p50 `91.17 µs`, p95 `126.77 µs`, p99 `148.112 µs` on that exact target.

These results support splitting canonical storage/schema/root/projection/time/snapshot/selection/effect proof surfaces rather than one broad certificate.

### Current GRID/thread diagnostic

`PROJECT_MEASUREMENT`

Current steering records an exact 4-process/4-vCPU diagnostic in which one thread per process averaged about `8.3197 s/call`, two threads about `23.1806 s/call`, and four threads produced zero completed calls within the tested timeout window.

Scope law: this supports a conservative default for that exact topology. It does not establish a universal HCU scaling law and does not turn `N=10` into final architecture.

### Distillery yield

`PROJECT_MEASUREMENT + NEGATIVE_RESULT`

Current steering reports `0 accepted_dataset_tokens` from `88,774 collected_source_tokens` for the cited snapshot. Source-token accumulation is therefore not equivalent to training-data yield.

### Project Frankenstein archive coverage

`HISTORICAL_SOURCE + NEGATIVE_RESULT`

`PROJECT_FRANKENSTEIN_MANIFEST.json` is explicitly:

```text
PARTIAL_NOT_FROZEN
exact_tree_enumerated = false
exact_history_enumerated = false
denominator_frozen = false
exact_obligation_credit = 0
```

It contains valuable deep reads and lineage anchors, but it cannot support a claim that complete Project Frankenstein Git history has been reconstructed.

---

## 8. Evidence quarantine table

| Surface | Current classification | Why |
|---|---|---|
| Historical Project Frankenstein source | `HISTORICAL_SOURCE` | Preserved donor/provenance; not current authority by itself. |
| Archive assimilation manifests | `HISTORICAL_SOURCE / PARTIAL` | Useful index; denominator/history not frozen. |
| Zero export (`agentZero/`) | `PROJECT_SOURCE / EXPORT_SNAPSHOT` | Rich state/code/evidence export; snapshot identity matters. |
| UnifiedDB negative run | `PROJECT_MEASUREMENT / REPRODUCED` | Exact negative discriminators reproduced on accepted target. |
| GRID10 source/tests | `CURRENT_SOURCE / COMPONENT` | Useful implementation evidence; fixed ten is not final owner target. |
| 72h Frankenstein provider orchestrator | `SOURCE_READY / QUARANTINED` | Current provider authority is HARD_OFF. |
| 9.13O / 9.14_GO steering | `NON_AUTHORITY_STEERING_ONLY` | Files say so explicitly. |
| local/VPS `clay-direct-dev` work | `OWNER_AUTHORIZED_SANDBOX` | Broad development authority at exact sandbox scope. |
| provider calls under current epoch | `FORBIDDEN` | 9.13 HARD_OFF. |
| whole EntityOS/HCU PASS | `NOT_ESTABLISHED` | Current broad credit remains zero. |

---

## 9. Current highest-value blocker cluster

`INFERENCE`, derived from current supervisor/owner surfaces:

1. **authority-before-side-effect closure:** the provider caller boundary must resolve HARD_OFF before secret lookup/import/network/fallback;
2. **runtime quiescence:** no hidden/stale process may continue a now-forbidden provider path;
3. **independent review of quarantined post-hardoff core changes;**
4. **re-align fixed GRID10 implementation language with the variable-`N` owner target;**
5. **convert cognitive-process census into a stable ABI and DB-vs-simulation boundary;**
6. **obtain causal re-entry evidence for the grid/workspace/Claude Code bridge at actually exposed interfaces;**
7. **turn collected research traces into accepted, leak-resistant training data rather than raw token volume.**

---

## 10. Claim hygiene for all future curation

When updating this layer, write the exact scope beside the claim.

Bad:

> Frankenstein now has autonomous self-healing.

Better:

> `frankenstein_bugfix_v1.py` exists at commit X and its own unit tests passed; the provider-calling path is currently quarantined by 9.13 HARD_OFF, so deployed autonomous self-healing is not established.

Bad:

> UnifiedDB solved memory.

Better:

> UnifiedDB work consolidated deterministic state authority and reproduced specific schema/projection/time/snapshot/dependency gaps; final end-to-end continuity acceptance remains open.

Bad:

> Global J-Space is connected.

Better:

> Workspace/J-Space bridge mechanisms exist at specified interfaces; model-internal or cross-model causal coupling receives credit only when an exact intervention/re-entry test demonstrates it.
