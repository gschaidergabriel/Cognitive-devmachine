# Trigger-3 current-state and repository migration ledger

**Trigger:** `triggerword 3` / `3`  
**Organ:** GPT-5.6 Sol / ChatGPT  
**Initial baseline inspected:** `main@854f6bc87780f4a5242489a6c807d186b16a8c3d`  
**Re-entered main during macrocycle:** `main@3c3dbe5020f57065f47bd4d0a2dce3c537128797`  
**Purpose:** make the repository human-legible without erasing technical/research lineage or manufacturing a second authority.

This file is a migration ledger and evidence index. It is **not** canonical execution authority.

## 1. Authority re-entry result

| Surface | Observed | Evidence class | Trigger-3 interpretation |
|---|---|---|---|
| `main` initial | `854f6bc87780f4a5242489a6c807d186b16a8c3d` | `CURRENT_SOURCE` at initial re-entry | exposed an ungated Frankenstein provider caller contradiction |
| `main` re-entry | `3c3dbe5020f57065f47bd4d0a2dce3c537128797` | `CURRENT_SOURCE` | same-cycle source/local-unit closure of that caller reachability gap |
| `CLAY_EXECUTION_AUTHORITY.md` | owner-provisioned `clay-direct-dev` sandbox broadly allowed; external provider spending separately gated | `CURRENT_SOURCE` | local/sandbox work does not open provider routes |
| `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` | schema 9.13, delta `9.13O_NON_AUTHORITY`, all provider routes false, Together forbidden, no paid fallback | `CURRENT_SOURCE` | current provider hard-off selected by the inbox |
| selected `SUPERVISOR_STEERING_9_13O...json` | Frankenstein provider orchestration quarantined/non-operative | `CURRENT_SOURCE` | provider donor code may not self-authorize |
| `BOOTSTRAP_MINIMAL.json` | schema 8.78 at initial re-entry | `CURRENT_SOURCE` with stale authority payload | secondary current-facing surface has authority drift |
| `PROGRAM_STATE.json` | schema 8.78 at initial re-entry | `CURRENT_SOURCE` with stale authority payload | secondary current-facing surface has authority drift |
| uploaded Trigger-3 bootstrap | cached 8.63-era operating source that explicitly says GitHub/newer authority outrank it | `HISTORICAL_SOURCE` / fast cache | useful trigger definition, not current truth |

### Authority conclusion

`9.13` hard-off wins for provider execution. Older provider allowance text cannot reopen provider calls. The new `3c3dbe50...` gate makes that rule structurally earlier in the canonical Frankenstein entrypoints at source/local-unit scope; it does not change the authority state from OFF to ON.

## 2. Highest-value finding → same-cycle repair

### Initial observation at `854f6bc...`

The canonical Bauleiter/Bugfix scripts still contained direct external free-pool/provider paths, including NVIDIA/Groq/Mistral, while current authority required provider routes hard-off.

Old source state:

```text
canonical Frankenstein entrypoint
-> provider/free-pool implementation reachable
-> authority contradiction under 9.13 HARD_OFF
```

### Re-entry observation at `3c3dbe50...`

Parallel Trigger-3 work landed a nonduplicate repair:

- `frankenstein_authority_gate_v1.py` is stdlib-only and resolves current `SUPERVISOR_INBOX` before external/provider boundaries;
- canonical `frankenstein_orchestrator_v1.py` and `frankenstein_bugfix_v1.py` are wrappers that gate before loading preserved provider-backed donor implementations;
- old implementations are preserved under `*_PROVIDER_QUARANTINED_854f6bc.py` rather than rewritten as if they never existed;
- the old plan is preserved separately and the active plan removes current Together authorization;
- new focused tests require hard-off to block before the donor path is reached;
- commit reports **10/10 PASS** in local source/unit scope.

New source state:

```text
canonical Frankenstein entrypoint
-> current authority gate
-> HARD_OFF => stop before provider import/secret lookup/network/Aider/fallback
-> preserved provider donor remains unreachable
```

**Current classification:** `SOURCE/LOCAL_UNIT_CLOSURE`, not provider runtime acceptance.

**Remaining exact discriminator:** clean exact-current non-provider review/re-execution at the same declared scope. Future provider execution still requires a newer explicit authority and then-current admission/economic provenance gates.

## 3. Together conflict — now quarantined in active source

The original `BUILD_ORCHESTRATION_PLAN_20260827.json` stated that one Together training run was authorized. Current 9.13 says zero remaining paid runs and Together forbidden.

At `3c3dbe50...` the legacy plan is preserved as a quarantined provenance file and the active plan explicitly carries zero Together allowance plus a future reactivation gate.

**Lifecycle classification:**

- historical plan statement: `HISTORICAL_SOURCE / CONTRADICTED / RETIRED_AS_CURRENT_AUTHORITY`
- active current plan: `HARD_OFF / TOGETHER_ZERO`
- current Together execution: `BLOCKED`
- training credit: `0`

## 4. Repository root observation

The human-visible root is still not the Trigger-3 target. It contains many current/historical technical surfaces including `.claude`, `.github`, `.env.example`, several bootstraps, authority files, dashboards, ClayCode manifests, `agentZero/`, `dump/`, `free swarm/`, `governance/`, `research_entity/`, `research_sources/`, `runtime_checks/`, `schemas/`, `tests/`, `the artefact/`, `tools/`, `vps_bridge/`, and several anomalous-looking root files.

Trigger-3 human-facing target:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

### Important migration constraint

A literal four-entry filesystem root conflicts with platform semantics for some hidden files: GitHub Actions consumes `.github/workflows/`, root `.gitignore` has repository-wide Git semantics, and tool-specific instruction files may have fixed discovery locations. Those cannot be moved merely for visual cleanliness without proving equivalent behavior.

This phase therefore treats the four-entry shape as the **canonical public/human topology target** while keeping platform-required hidden metadata as explicit exceptions until exact host tests prove relocation is harmless. This is preservation, not silent target drift.

## 5. Byte-preserving migration strategy

### Phase T3-0 — additive entry points — **DONE ON THIS BRANCH**

- `HUMAN_READ_THIS/README.md`
- `DEV_SOURCE_RESEARCH/README.md`
- this migration ledger
- `DEV_SOURCE_RESEARCH/research/CHRONOLOGY_SEED_VERIFIED_GIT_2026-08-27.md`
- `DEV_SOURCE_RESEARCH/repository/ROOT_TOPOLOGY_INDEX_2026-08-27.json`
- `AI_START_HERE_DO_NOT_SCAN_REPO/README.md`
- topic-packet current-authority status note

No root `README.md` rewrite.

### Phase T3-1 — machine-readable inventory — **SEED DONE, REFERENCE GRAPH OPEN**

`ROOT_TOPOLOGY_INDEX_2026-08-27.json` classifies observed root entries and blocks moves that still need import/workflow/authority/path analysis.

Next acceptance data per entry:

- exact blob/tree identity;
- incoming references from code/docs/workflows;
- proposed destination;
- semantic relocation risk;
- compatibility alias/shim requirement if any;
- evidence/lifecycle class.

### Phase T3-2 — reference graph before moves

Locate imports, relative links, workflow assumptions, packaging rules, shell scripts and runtime hard-codes. Unresolved consumers => `BLOCKED_MOVE`.

### Phase T3-3 — bounded relocation batches

Move low-risk documentation/archive material first into `DEV_SOURCE_RESEARCH/repository/` and purpose-specific subdirectories. Preserve bytes where modification is not intentional. Record old/new path, blob identity, rewritten references separately, and link/test result.

### Phase T3-4 — runtime/tool relocation

Only after reference tests close. Runtime-imported trees may require package-aware moves or compatibility shims. Do not create duplicate canonical implementations.

### Phase T3-5 — public-root convergence

Human-visible root converges to the four Trigger-3 entry surfaces, with only explicitly justified host/platform hidden exceptions.

### Phase T3-6 — installation acceptance

Per host, final result is exactly one of:

`NATIVE | ADAPTED | DEGRADED | BLOCKED`

A copied config file is not installation proof.

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
| Claude bridge | `SOURCE / interface research`; deeper activation access unproven | strongest exposed interface + causal evidence |
| training | `PREPARED / research-heavy`; current training credit 0 | exact admitted dataset, frozen evals, current authority, execution receipt |
| FreeSwarm | `MEASURED lineage`; current provider routes hard-off | causal utility, fleet quiescence and authority-safe archival synthesis |
| Forge | `MEASURED nominal historical acceptance exists` | evidence-qualified conversion path |
| Distillery | `NEGATIVE_RESULT`: latest supervisor-confirmed accepted dataset tokens remained zero at the inspected authority snapshot | one exact admitted positive packet then identical replay +0 |
| Frankenstein provider caller | `SOURCE/LOCAL_UNIT HARD_OFF CLOSURE @ 3c3dbe50` | clean exact-current review/re-execution; no provider runtime credit |
| Frankenstein 72h deployment | `BLOCKED/QUARANTINED` while providers are hard-off | future explicit provider authority + then-current safety/economic gates + runtime evidence |

## 7. Failure → engineering move chronicle seeds

| Failure / negative evidence | Engineering response to reconstruct |
|---|---|
| fragmented state across stores/services | convergence toward UnifiedDB/canonical state substrate |
| recursive reflection / rumination risk | explicit exit transitions and measurable state changes |
| prompt/context contamination | stronger typed state/provenance and split/holdout discipline |
| prompt-vs-weight conflicts | training/interface decomposition and hard negatives |
| vector transport without semantic behavioral control | separate transport/readout/binding/write claims; stronger causal controls |
| component green tests promoted too broadly | explicit evidence-scope and promotion laws |
| source-ready provider/free-pool paths bypassing authority | **same-cycle repair:** actual caller gate before external boundary |
| massive FreeSwarm token generation with no Distillery yield | conversion-funnel-first optimization and zero-yield blocker |
| concurrency/latency assumptions | topology-specific matched measurements; preserve counterexamples |
| stale authority islands | successor-dynamic authority resolution and re-entry before claims |

## 8. Open hypotheses for Trigger-3 documentation/reconstruction

### H1 — External substrate improves useful reflective agency

**Claim:** a richer external substrate of state, memory, perception, arbitration, effect receipts and outcome re-entry can improve useful agency compared with model-only reflection.  
**Engineering confidence:** 0.65 / 1.00.  
**Counterhypothesis:** gains come mainly from more context/tool calls rather than typed substrate or verified re-entry.  
**Falsifier:** matched equal-budget tasks where removing typed provenance/outcome re-entry does not worsen correction persistence, effect accuracy or recovery.

### H2 — Emergent Retrieval beats single-axis retrieval on stateful tasks

**Claim:** overlap of semantic, temporal, causal, goal/state and provenance dimensions yields more useful retrieval than semantic similarity alone.  
**Engineering confidence:** 0.60 / 1.00.  
**Counterhypothesis:** extra dimensions mainly add hand-designed leakage/heuristics.  
**Falsifier:** family-held-out equal-context evaluation where multi-dimensional retrieval fails to improve retrieval precision/decision outcome.

### H3 — Workspace recurrence helps coordination without minting truth

**Claim:** bounded broadcast/uptake/re-entry can improve coordination across specialized compute functions.  
**Engineering confidence:** 0.55 / 1.00.  
**Counterhypothesis:** recurrence merely repeats prompt/schema content.  
**Falsifier:** shuffle/lesion/rescue controls where claimed workspace signal can be disrupted without downstream effect, or schema-preserving fake recurrence performs equally well.

### H4 — Hard-off caller boundary is structurally enforceable

**Initial confidence:** 0.90 source-design.  
**Same-cycle evidence:** `3c3dbe50...` implements the gate and reports 10/10 focused local tests.  
**Updated classification:** `SOURCE/LOCAL_UNIT SUPPORTED`, not runtime-verified.  
**Counterhypothesis:** an alternate canonical path/import-time side effect bypasses the gate.  
**Next falsifier:** clean exact-current audit/re-execution plus reference graph proves no alternate canonical provider path reaches secrets/provider/network before authority resolution.

## 9. External-primary notes that constrain implementation language

- GNW literature is an analogy/source of workspace hypotheses, **not project runtime evidence and not a consciousness requirement**.
- NVIDIA Unified Memory is a memory/coherence mechanism, **not database authority or transaction semantics**.
- SQLite/WAL has real writer/checkpoint constraints; current official SQLite docs report a rare WAL-reset bug fixed in newer releases. Measure the project’s exact SQLite version/access pattern before claiming exposure.
- Reflexion is external evidence that one episodic textual-feedback agent design can alter later decisions, **not evidence that Frankenstein reflection has passed**.

## 10. Next exact Trigger-3 gates

1. Review/merge the additive human/research/installer/index layer without rewriting root README.
2. Independently re-execute/review the new `3c3dbe50...` authority gate at exact-current source scope; preserve zero provider-runtime credit.
3. Build the full incoming-reference graph before the first root relocation batch.
4. Expand Git chronology domain-by-domain with opened source/receipts and “first verified in accessible Git” language.
5. Build source/receipt deep-link indexes and a hypothesis/negative-result catalog.
6. Relocate only low-risk clutter in bounded, byte-verified batches after references close.
7. Re-enter current `main` after every material merge because parallel work is moving rapidly.

This ledger intentionally favors reversible, evidence-preserving convergence over a cosmetic mass move.