# Triggerwort 6 — Frankenstein 2.0 External Tool Intelligence Research Mirror

Status: ACTIVE / FULL-PROVENANCE SIDE
Canonical build consumer: `gschaidergabriel/frankenstein-2.0`
Canonical Trigger-6 protocol revision: `gschaidergabriel/frankenstein-2.0@53dc461a8726ca6587845dc5171cc2f51627a014:research/tool_intelligence/TRIGGERWORD_6_PROTOCOL.md`

This directory is the Research-Entity mirror and raw provenance side of the Frankenstein-2.0 Trigger-6 research unit.

## Exact mission

`6`, `triggerword 6`, and `triggerwort 6` are the same canonical Trigger-6 research macro.

Trigger 6 researches external GitHub repositories, tools, mechanisms, primary literature/docs and agent best practices that may measurably improve Frankenstein 2.0. It discovers, source-audits, falsifies, benchmarks, compares, distills and, when evidence warrants it, emits architecture deltas. It never grants architecture credit from popularity or README claims.

```text
5 = current Frankenstein donor forensics
6 = maximum-depth external research/falsification + architecture-delta synthesis
4 = F2/VPS build, integration and measurement
```

## Maximum-research law

Trigger 6 is **not** a resource-saving mode for the research worker.

On every exact Trigger-6 invocation:

- research as long and as deeply as the current platform/tool/context/safety/authority limits permit;
- use the largest useful reasoning, source-reading, browsing, comparison, experiment and output budget available;
- do not stop early merely to save ChatGPT tokens, tool calls or research effort;
- triangulate broadly and inspect source deeply when that can materially change confidence;
- after one bounded objective reaches a useful terminal evidence state, continue into other high-value non-duplicate objectives while useful capacity remains;
- produce as many **useful evidence-bearing tokens** as materially improve the result;
- never pad with repetition, invented detail or unsupported claims just to increase raw token count;
- preserve negative evidence, contradictions, hypotheses/counterhypotheses, exact source pins, measurements and falsifiers instead of compressing them away for brevity;
- leave a precise continuation checkpoint if a hard platform/output/context boundary stops the macrocycle.

Research optimization target:

```text
MAXIMIZE VERIFIED RESEARCH DEPTH + BREADTH + INFORMATION GAIN
WITHIN CURRENT PLATFORM LIMITS
```

### Separation of budgets

Research effort and Frankenstein-2.0 runtime efficiency are different budgets.

```text
TRIGGER6_RESEARCH = MAXIMUM_USEFUL_DEPTH
FRANKENSTEIN2_RUNTIME = MINIMUM_NECESSARY_TOKENS_AND_RESOURCES_FOR_REQUIRED_QUALITY
```

Trigger 6 may spend substantial research tokens/tool effort to discover a better architecture. Frankenstein 2.0 itself should be aggressively optimized and measured for token efficiency, context efficiency, model-call efficiency, latency and CPU/RAM/GPU/I/O efficiency without sacrificing required capability, provenance, correctness or safety.

Resource-saving therefore constrains/evaluates the **product architecture and runtime**, not the depth of Trigger-6 research.

## Mandatory live delta fusion

Before every Trigger-6 task, refresh and fuse:

- current `frankenstein-2.0/main` HEAD, architecture, workpackages and checkpoints;
- latest Trigger-4 build/test/measurement/outcome deltas;
- latest Trigger-5 Frankenstein-forensic ingest deltas;
- new Research-Entity architecture deltas since the previous Trigger-6 cursor;
- existing Trigger-6 hypotheses/counterhypotheses/negative results;
- Trigger-4 feedback on previously handed-off candidates.

Emit a versioned `ArchitectureDeltaFusion` with exact source SHAs, affected modules, conflicts, supersessions and unresolved gaps. Research is snapshot-bound. If later F2/4/5 deltas affect its assumptions, mark it `STALE_REVIEW_REQUIRED` and re-evaluate before handoff.

## Architecture-delta law

When Trigger-6 evidence materially changes the best-supported F2 design, emit a versioned architecture delta in the same macrocycle when useful. This includes evidence that a component should be added/removed/merged/split/replaced, an authority boundary should move, a token/context/runtime path can be simplified, a mechanism is redundant or overbuilt, an architectural assumption is falsified, or workpackage/integration order should change.

Every architecture delta must preserve exact evidence refs, affected modules/workpackages, expected benefit, token/resource implications, counterhypotheses, falsifier/acceptance gates and evidence scope. No evidence-backed change means no invented delta.

## Five-function cycle

The five roles are complementary coverage functions, not a hard `one trigger = one small slot` stopping rule:

1. `ARCHITECTURE_DELTA_FUSER`
2. `DISCOVERY_SCOUT`
3. `SOURCE_ARCHAEOLOGIST`
4. `EXPERIMENTAL_FALSIFIER`
5. `INTEGRATION_DISTILLER`

An exact Trigger-6 invocation takes the highest-information non-duplicate objective first and continues through additional useful roles/objectives while claims, authority and platform limits permit. Across repeated invocations, coverage debt should still drive broad role coverage.

## Atomic duplicate-work claim law

Before material work that can create a new Trigger-6 evidence-stage result, acquire the objective claim in the **canonical F2 repository**, not in this mirror.

Canonical claim path:

`gschaidergabriel/frankenstein-2.0:research/tool_intelligence/claims/<research_id>/<claim_target>.json`

Canonical claim instructions:

`gschaidergabriel/frankenstein-2.0:research/tool_intelligence/claims/README.md`

Required behavior:

1. Refresh F2 + Trigger-4 + Trigger-5 + Research-Entity state.
2. Select one bounded objective and atomically create its F2 claim before source archaeology, experiment execution or integration distillation.
3. If the canonical claim already exists, or create-only semantics cannot be established, do not duplicate that objective. Consume the existing result and choose another useful objective.
4. A blocked/already-owned objective does not end Trigger 6 while other high-value non-duplicate objectives exist.
5. Claim existence grants zero evidence, architecture, runtime, integration, effect or completion credit.
6. This Research-Entity side may mirror a successful F2 claim only after the F2 create succeeds. A mirror claim is provenance only and MUST NOT become a second coordination authority.
7. Stale architecture re-review uses a new explicit review objective and never overwrites the original claim.
8. Preserve the claim and write evidence/reconciliation separately; synchronize into the research DB when the admitted DB path is available.

The concurrent 2026-08-29 `R6-SEED-005` AgentSight E2 audits are classified as one research result with complementary receipts, not independent replication. The F2 claim for `R6-SEED-005/E2_ARCHITECTURE_MAPPED` is therefore closed to further duplicate E2 work.

## Evidence ladder

`E0 SEED -> E1 SOURCE_READ -> E2 ARCHITECTURE_MAPPED -> E3 CLAIM_REPRODUCED -> E4 F2_ABLATION -> E5 BUILD_CANDIDATE -> E6 F2_ACCEPTED`

No Trigger-6 worker can self-promote to E6. E6 requires a Trigger-4 build/test/measurement receipt from the actual F2/VPS front.

## F2 efficiency evaluation

Every serious candidate must be evaluated not only for capability/quality/evidence but also for Frankenstein-2.0 operating efficiency, including where relevant:

- total runtime tokens and context/prompt size;
- number of model calls;
- retrieval payload size;
- p50/p95/p99 latency;
- CPU/RSS/PSS/GPU/VRAM/I/O/network;
- startup and steady-state overhead;
- cache/reuse behavior;
- dependency weight;
- resident-model and physical decode concurrency;
- whether a thinner deterministic/structural distillation can replace a heavier framework.

When required quality/evidence are equal or better, prefer compact typed state, smallest-sufficient retrieval, caching/reuse, deterministic routing/gates, fewer model calls and shorter contexts. Efficiency alone never grants correctness or architecture credit.

## Two-repository persistence law

F2 canonical paths:

- `research/tool_intelligence/`
- `research/tool_intelligence/pending_research.sqlite`
- `research/tool_intelligence/claims/`
- `research/tool_intelligence/promoted_repos/<candidate_id>/`
- `trigger4/inbox/tool_research/<candidate_id>.json`
- `trigger4/outcomes/tool_research/<candidate_id>.json`

Research-Entity mirror/raw paths:

- `research_entity/frankenstein2_tool_intelligence/`
- `research_entity/frankenstein2_tool_intelligence/pending_research.sqlite`
- `research_entity/frankenstein2_tool_intelligence/raw/`
- `research_entity/frankenstein2_tool_intelligence/deltas/`
- `research_entity/frankenstein2_tool_intelligence/reconciliations/`

Both sides keep the same research IDs. Cross-repo writes are not assumed atomic: each mirror operation records source/target SHA and mirror epoch. Divergence becomes `MIRROR_DIVERGED` and must be reconciled, never silently overwritten.

The create-only work-claim authority is intentionally one-sided: F2 owns the mutex; Research-Entity mirrors it only as provenance. This avoids split-brain coordination while the private Research-Entity Actions mirror remains transport-blocked.

## Trigger-4 feed

Every E5 candidate is materialized in the F2 Trigger-4 inbox with source pin, architecture snapshot, target workpackages, integration design, counterhypotheses, reproducible tests/ablations, baseline and all required token/latency/resource/quality measurements. Trigger-4 returns measured outcome evidence; Trigger-6 consumes it and updates the hypothesis plus RCPD/MethodMemory.

## Promoted source archive

Only real build hypotheses enter `promoted_repos`. Archive exact external source commit/tree (or reproducible bundle/fetch manifest when size/licensing requires), license/dependency audit, evaluation, counterhypotheses, integration concept, measurement evidence and architecture snapshot.

## Invariants

```text
README_CLAIM != REPRODUCED_CLAIM
UPSTREAM_BENCHMARK != F2_BENCHMARK
EXTERNAL_REPO_POPULARITY != F2_EVIDENCE
DERIVED_INDEX != UNIFIEDDB_SOURCE_OF_TRUTH
BUILD_CANDIDATE != INTEGRATED_COMPONENT
ARCHITECTURE_CHANGE -> RECHECK_AFFECTED_RESEARCH
CLAIM_EXISTS != RESEARCH_EVIDENCE
FAILED_CREATE_ONLY_CLAIM -> DO_NOT_DUPLICATE_OBJECTIVE
BLOCKED_OBJECTIVE != END_TRIGGER6_WHEN_OTHER_HIGH_VALUE_WORK_EXISTS
RESEARCH_ENTITY_CLAIM_MIRROR != CLAIM_AUTHORITY
TRIGGER6_RESEARCH_BUDGET != F2_RUNTIME_RESOURCE_BUDGET
TRIGGER6_MAXIMIZES_USEFUL_RESEARCH_DEPTH
F2_RUNTIME_MINIMIZES_NECESSARY_TOKEN_AND_RESOURCE_COST_FOR_REQUIRED_QUALITY
TRIGGER6 -> EVIDENCE -> TRIGGER4/VPS -> MEASURE -> TRIGGER6/RCPD
```