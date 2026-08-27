# Trigger-3 current-state and repository migration ledger

**Trigger:** `triggerword 3` / `3`  
**Organ:** GPT-5.6 Sol / ChatGPT  
**Baseline inspected:** `main@854f6bc87780f4a5242489a6c807d186b16a8c3d`  
**Purpose:** make the repository human-legible without erasing technical/research lineage or manufacturing a second authority.

This file is a migration ledger and evidence index. It is **not** canonical execution authority.

## 1. Authority re-entry result

| Surface | Observed at baseline | Evidence class | Trigger-3 interpretation |
|---|---|---|---|
| `main` | `854f6bc87780f4a5242489a6c807d186b16a8c3d` | `CURRENT_SOURCE` | exact source baseline for this phase |
| `CLAY_EXECUTION_AUTHORITY.md` | owner-provisioned `clay-direct-dev` sandbox broadly allowed; external provider spending separately gated | `CURRENT_SOURCE` | local/sandbox work may be permitted, but this does not open provider routes |
| `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` | schema 9.13, delta `9.13O_NON_AUTHORITY`, all provider routes false, Together forbidden, no paid fallback | `CURRENT_SOURCE` | current provider hard-off selected by the inbox |
| selected `SUPERVISOR_STEERING_9_13O...json` | Frankenstein 72h provider orchestration explicitly quarantined/non-operative | `CURRENT_SOURCE` | direct provider-calling orchestration cannot be deployed unchanged |
| `BOOTSTRAP_MINIMAL.json` | schema 8.78 | `CURRENT_SOURCE` with stale authority payload | secondary current-facing surface has authority drift |
| `PROGRAM_STATE.json` | schema 8.78 | `CURRENT_SOURCE` with stale authority payload | secondary current-facing surface has authority drift |
| uploaded Trigger-3 bootstrap | cached 8.63-era operating source that explicitly says GitHub/newer authority outrank it | `HISTORICAL_SOURCE` / fast cache | useful trigger definition, not current truth |

### Authority conclusion

`9.13` hard-off wins for provider execution at this baseline. The older 8.78/8.63 provider allowance text is useful provenance but cannot reopen provider calls.

## 2. Highest-value current contradiction

Latest main adds:

- `research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_packages_v1.py`
- `research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_orchestrator_v1.py`
- `research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_bugfix_v1.py`
- corresponding tests, with the commit message reporting 29 tests green.

But the orchestrator/bugfix source contains direct external free-pool/provider paths, including NVIDIA/Groq/Mistral, while the current supervisor requires provider calls and secret lookups to remain zero under hard-off.

**Status:** `CONTRADICTED + BLOCKED` at deployment scope.

The correct statement is:

> The source and non-network orchestration tests exist. The provider-calling 72-hour system is quarantined/non-operative under current 9.13 provider authority until its external caller boundary is fail-closed before secret lookup/provider import/network/Aider/fallback and independently re-executed under current authority.

The incorrect statement is:

> “29 tests green, therefore the 72-hour Frankenstein system is ready to run.”

## 3. Together conflict

`BUILD_ORCHESTRATION_PLAN_20260827.json` says exactly one Together training run is authorized. Current 9.13 state says zero remaining paid runs and Together forbidden.

**Lifecycle classification:**

- plan statement: `HISTORICAL_SOURCE / CONTRADICTED / RETIRED_AS_CURRENT_AUTHORITY`
- current Together execution: `BLOCKED`
- training credit added by the plan: `0`

Only a newer explicit owner authority change can alter that result.

## 4. Repository root observation

The baseline root is not yet the Trigger-3 target. It contains many current/historical technical surfaces including `.claude`, `.github`, `.env.example`, several bootstraps, authority files, dashboards, ClayCode manifests, `agentZero/`, `dump/`, `free swarm/`, `governance/`, `research_entity/`, `research_sources/`, `runtime_checks/`, `schemas/`, `tests/`, `the artefact/`, `tools/`, `vps_bridge/`, and several accidental-looking root files.

Trigger-3 human-facing target:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

### Important migration constraint

A literal four-entry filesystem root conflicts with platform semantics for some hidden files: for example, GitHub Actions conventionally consumes workflows from `.github/workflows/`, and root `.gitignore` has repository-wide Git semantics. Those cannot be moved merely for visual cleanliness without first proving an equivalent mechanism.

Therefore this phase treats the four-entry shape as the **canonical public/human topology target** while keeping platform-required hidden metadata as an explicit migration exception until exact tests prove relocation is harmless. This is a preservation decision, not a quiet weakening of the target.

## 5. Byte-preserving migration strategy

The migration must not become a giant rename that destroys navigability, Git blame or runtime assumptions.

### Phase T3-0 — additive entry points — **DONE ON THIS BRANCH**

Add without moving existing source:

- `HUMAN_READ_THIS/README.md`
- `DEV_SOURCE_RESEARCH/README.md`
- `DEV_SOURCE_RESEARCH/repository/TRIGGER3_CURRENT_STATE_AND_MIGRATION_2026-08-27.md`
- `AI_START_HERE_DO_NOT_SCAN_REPO/README.md`
- topic-packet authority quarantine note

No root `README.md` rewrite.

### Phase T3-1 — machine-readable inventory

Generate a root/source inventory with:

- original path;
- blob/tree identity;
- file type;
- current references from code/docs/workflows;
- proposed destination;
- semantic relocation risk;
- compatibility alias/symlink requirement if any;
- evidence class/lifecycle status.

Acceptance: every move candidate has an explicit destination or a reason to remain.

### Phase T3-2 — reference graph before moves

For each candidate path, locate imports, relative links, workflow assumptions, packaging rules, shell scripts and runtime hard-codes. Paths with unresolved consumers are `BLOCKED_MOVE`.

Acceptance: no “move first, repair later” for authority, runtime, CI or installer paths.

### Phase T3-3 — bounded relocation batches

Move low-risk documentation/archive material first into `DEV_SOURCE_RESEARCH/repository/` and purpose-specific subdirectories. Preserve bytes where source modification is not intentional.

For each batch record:

- old path → new path;
- old/new Git blob identity where byte-identical;
- rewritten references separately;
- link/test result;
- compatibility surface if needed.

### Phase T3-4 — runtime/tool relocation

Only after reference tests close. Source trees that are runtime-imported may require package-aware moves or compatibility shims. Do not create duplicate canonical implementations.

### Phase T3-5 — public-root convergence

Human-visible root becomes the four Trigger-3 entry surfaces. Platform-required hidden metadata remains only where the host requires it and is documented as an exception.

### Phase T3-6 — installation acceptance

Run host/tool-specific installation checks. Final result per host is exactly one of:

`NATIVE | ADAPTED | DEGRADED | BLOCKED`

No fake success based on a file existing.

## 6. Research synthesis state by domain

| Domain | Current Trigger-3 classification | What still has to be proven or reconstructed |
|---|---|---|
| EntityOS | `ADOPTED current product identity`; whole-runtime `NOT PASS` | exact integrated runtime acceptance |
| HCU | `ADOPTED current compute architecture`; full-runtime credit 0 | exact multi-component/runtime evidence |
| GRID / GRID10 | `MEASURED in bounded component contexts`; GRID10 benchmark/topology, not whole product | topology-specific performance + retained authority receipts |
| Xeno | `RETIRED AS PRODUCT`, `ADOPTED AS TRANSITIONAL IMPLEMENTATION CODENAME` | map donor mechanisms to current EntityOS/HCU paths |
| UnifiedDB | `ADOPTED architecture direction` | chronology of multi-store collapse; exact current canonical schema/writers/readers |
| Emergent Retrieval | `ADOPTED project term / mechanism hypothesis` | executable retrieval evaluations by evidence dimension |
| Hyperposition | `SOURCE-READY / OPEN_HYPOTHESIS` at broad architecture scope | exact operators, tests and falsifiers tied to current source |
| GWT / workspace | `OPEN_HYPOTHESIS + architectural donor` | project-specific causal broadcast/uptake/re-entry evidence |
| Global J-Space | `OPEN_HYPOTHESIS`; model/runtime credit 0 | model-specific intervention evidence and exact interface binding |
| GRF | `HISTORICAL + current donor lineage` | Git-supported math/engineering chronology and current dependency map |
| ClayCode | `SOURCE PRESENT / multiple measured component lines` | current compiler/runtime/release gate chronology and exact acceptance scope |
| Claude bridge | `SOURCE / interface research`; deeper activation access unproven | strongest actually exposed interface + causal evidence |
| training | `PREPARED / research-heavy`; current training credit 0 | exact admitted dataset, frozen evals, current authority, execution receipt |
| FreeSwarm | `MEASURED high-volume historical/current lineage`; provider routes now hard-off | causal utility, quiescence and authority-safe archival synthesis |
| Forge | `MEASURED nominal historical acceptance exists` | evidence-qualified conversion path |
| Distillery | `NEGATIVE_RESULT`: last current supervisor-confirmed accepted dataset tokens 0/88,774 source tokens | one exact admitted positive packet then replay +0 |
| Frankenstein 72h orchestrator | `SOURCE PRESENT + TESTED NON-NETWORK LOGIC`, deployment `BLOCKED/QUARANTINED` | authority gate before every external boundary + clean reexecution |

## 7. Failure → engineering move chronicle seeds

These are index seeds; each needs commit/source evidence before chronology dates are asserted.

| Failure / negative evidence | Engineering response to reconstruct |
|---|---|
| fragmented state across stores/services | convergence toward UnifiedDB/canonical state substrate |
| recursive reflection / rumination risk | explicit exit transitions and measurable state changes |
| prompt/context contamination | stronger typed state/provenance and split/holdout discipline |
| prompt-vs-weight conflicts | training/interface decomposition and hard negatives |
| vector transport without semantic behavioral control | separate transport/readout/binding/write claims; stronger causal controls |
| component green tests promoted too broadly | explicit evidence-scope and promotion laws |
| source-ready provider/free-pool paths bypassing authority | provider gate at the actual external caller boundary |
| massive FreeSwarm token generation with no Distillery yield | conversion-funnel-first optimization and zero-yield blocker |
| concurrency/latency assumptions | topology-specific matched measurements; preserve counterexamples |
| stale authority islands | successor-dynamic authority resolution and re-entry before claims |

## 8. Open hypotheses for Trigger-3 documentation/reconstruction

### H1 — External substrate improves useful reflective agency

**Claim:** a richer external substrate of state, memory, perception, arbitration, effect receipts and outcome re-entry can improve useful agency compared with model-only reflection.

**Engineering confidence:** 0.65 / 1.00 (architecture plausibility, not product proof).

**Counterhypothesis:** gains come mainly from more context/tool calls rather than the typed substrate or verified re-entry structure.

**Falsifier:** matched task suite with equal model/token/tool budget where removing typed provenance/outcome re-entry does not worsen correction persistence, effect accuracy or recovery from errors.

### H2 — Emergent Retrieval beats single-axis retrieval on stateful tasks

**Claim:** overlap of semantic, temporal, causal, goal/state and provenance dimensions yields more useful retrieval than semantic similarity alone.

**Engineering confidence:** 0.60 / 1.00.

**Counterhypothesis:** the extra dimensions mostly add hand-designed leakage/heuristics and do not generalize.

**Falsifier:** preregistered family-held-out tasks where multi-dimensional retrieval fails to improve retrieval precision/decision outcome over semantic-only while controlling candidate count and context budget.

### H3 — Workspace recurrence helps coordination without minting truth

**Claim:** bounded broadcast/uptake/re-entry can improve coordination across specialized compute functions.

**Engineering confidence:** 0.55 / 1.00.

**Counterhypothesis:** recurrence merely repeats prompt/schema content and apparent convergence is correlation.

**Falsifier:** shuffle/lesion/rescue controls where claimed workspace signal can be disrupted without changing downstream behavior, or where schema-preserving fake recurrence performs equally well.

### H4 — Provider hard-off can be made structurally unbypassable at the Frankenstein caller boundary

**Claim:** resolving canonical authority before secret lookup/provider import/network/Aider/fallback can force `provider_calls=0` and `secret_lookups=0` under hard-off without modifying Frank Harness.

**Engineering confidence:** 0.90 / 1.00 at source-design level.

**Counterhypothesis:** import-time side effects or an alternate external path bypass the intended gate.

**Falsifier:** static/reference graph or executable hard-off test reaches any secret lookup, provider import side effect or network call before the gate.

## 9. External-primary notes that constrain implementation language

- GNW literature is an analogy/source of testable workspace ideas, **not project runtime evidence and not a consciousness requirement**.
- NVIDIA Unified Memory is a memory/coherence mechanism, **not database authority or transaction semantics**.
- SQLite/WAL concurrency has real writer/checkpoint constraints; current official SQLite documentation also reports a rare WAL-reset bug fixed in newer releases. The project must measure its exact SQLite version before claiming exposure.
- Reflexion is external evidence that one episodic textual-feedback agent design can alter later decisions, **not evidence that Frankenstein’s reflection mechanism has passed**.

## 10. Next exact Trigger-3 gates

1. Land/review the additive entry-point layer without rewriting root README.
2. Keep the 72-hour provider orchestration explicitly quarantined until the actual caller boundary is hard-off-safe.
3. Generate the machine-readable root inventory and reference graph before the first relocation batch.
4. Reconstruct Git chronology domain-by-domain with “first verified in accessible Git” language.
5. Build source/receipt deep-link indexes and a hypothesis/negative-result catalog.
6. Only then relocate technical clutter in bounded, byte-verified batches.
7. Re-enter current `main` after every material merge because authority and parallel work are moving rapidly.

This ledger intentionally favors a reversible, evidence-preserving migration over a cosmetic mass move.