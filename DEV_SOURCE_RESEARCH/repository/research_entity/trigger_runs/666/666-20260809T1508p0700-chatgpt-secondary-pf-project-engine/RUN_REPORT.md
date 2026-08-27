# 666 Level-0 Run Report — Project Engine Authority Lineage

- Trigger: `666`
- Actor: `chatgpt-secondary`
- Provider/model: OpenAI / GPT-5.6 Sol
- Created: 2026-08-09T15:08:00+07:00
- Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- Program stage: `L0_ARCHIVE_ASSIMILATION`
- Project-Frankenstein frozen head: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- Exact Level-0 coverage credit from this shard: 0.0

## Scope

Non-overlapping semantic/history shard covering the Project Engine evolution from a project-root sandboxed coding-agent loop to a broad autonomous system agent, then checking which persistence, policy, observability and autonomy mechanisms survived at the frozen head.

Primary historical commits:

- `62a661f51271e8ec024c3557b921eaddda0267d3` — tool-use agent loop with project-root path confinement.
- `b6d8c17bde2087d88ef4a31c09d6db2756219739` — deliberate removal of project sandbox and broad filesystem/system access.
- `1c5c682aa84c13eadbf47fbc54e4219230ce5ee6` — context compaction, SSE tool visibility, persistent task state, 25-iteration loop; structural but not complete live E2E verification due insufficient API credits.
- `cfa7062ba62bc9d83fffada29dcc03a75c4f4050` — goal-driven autonomous Project Engine v3 with tiered routing, world model, policies, learning, heartbeats and checkpoints.

Frozen-head evidence reviewed from `services/project_engine.py` includes persistent goals, world entities/relations, policy rows, agent profile, traces, checkpoints, token budgets, dream-cycle maintenance, cross-project reads, deterministic Tier-0 actions and autonomous tool dispatch.

## Fusion 1 — historical mechanism reconstruction

The lineage contains two separable architectural trajectories:

1. **Cognitive/execution continuity improved:** persistent project truth, goals, world model, tasks, checkpoints, traces, token budgets, outcome learning and compact context were added to make long-running agent work resumable and observable.
2. **Effect authority weakened in-process:** an earlier project-root sandbox was explicitly removed and replaced by broad absolute-path/system access with only a small destructive-command blocklist.

This distinction matters for current Clay: the first trajectory contains reusable system mechanisms; the second is evidence for why cognition and execution authority must remain separate planes.

## Key findings

### PF-PE-AUTH-001 — Sandbox removal is a verified historical transition

The early coding-agent implementation resolved paths beneath the project root and rejected paths outside it. A later commit replaced this with an absolute/relative resolver and explicitly enabled broad system administration operations. This is a historical fact, not an inference.

### PF-PE-PERSIST-002 — Persistence/replay mechanisms survived

At the frozen head the Project Engine has structured persistent goals, entity/relation world state, policy records, an evolving agent profile, traces, crash checkpoints and project token budgets. Time-travel replay is built from traces, and dream-cycle maintenance can alter strategy/profile/policies.

### PF-PE-CTX-003 — Context compaction is useful but historically under-validated

The context-compaction lineage truncates older tool results once estimated context exceeds a threshold while retaining recent exchanges. The same commit records that API credits were insufficient for complete live end-to-end verification. Preserve it as a mechanism candidate/measurement foundation rather than a fully validated performance claim.

### PF-PE-AUTON-004 — Reviewed autonomy path exposes an authority-gap hypothesis

In the reviewed frozen-head slices, autonomous prompts explicitly demand immediate tool execution, and model tool calls are passed to `_exec_tool`. A mandatory `check_policy` or external capability-gateway call was not observed immediately before each tool dispatch in these reviewed paths.

This is deliberately bounded: it does **not** prove that no external service, OS account, systemd sandbox, container boundary or other wrapper constrained the process. That counterhypothesis remains open and is the next discriminating test.

### PF-PE-POLICY-005 — Policy state is valuable but not a sufficient authority plane

The reviewed policy checker is category/string/threshold based. It can express risk preferences and some spending/contact constraints, but it is not strong enough by itself to constitute a complete effect-authorization mechanism.

## Counterhypotheses

1. **External-confinement counterhypothesis:** Project Engine may have run under OS/service/container confinement that made in-process sandbox removal less dangerous than the source diff suggests.
2. **Hidden-callpath counterhypothesis:** unreviewed call sites may always invoke policy or approval logic before privileged `_exec_tool` calls.
3. **Prototype-scope counterhypothesis:** unrestricted authority may have been an intentional single-user development prototype boundary rather than a proposed production invariant.

None of these counterhypotheses can be resolved without exhaustive tree/callgraph/deployment inspection.

## Current Clay architecture implications

### Reuse with adaptation

- crash checkpoints and resumable execution state;
- time-travel/replay traces;
- persistent task/goal/world state;
- tool outcome statistics and strategy history;
- tiered cost/model routing;
- loop detection;
- token budgets;
- user-visible activity/effect receipts;
- context compaction as a benchmarkable mechanism.

### Do not inherit as-is

- unrestricted model-owned shell/filesystem authority;
- conversational credential collection as a control mechanism;
- prompt/string policy matching as sufficient authorization;
- autonomous contact/system effects without an external capability/commit boundary.

### Required convergence rule

Current FRANK/ClayCode/Harness work should preserve the useful Project Engine continuity mechanisms while forcing every material effect through an external capability/commit gateway. The gateway must have explicit grant scope, denial, provenance, receipt, recovery/rollback where meaningful, and bypass tests. Model output, GWT broadcast, ClayGraph activation, internal policy text and learned preference must not independently authorize execution.

## Branch implications

- **frank:** reuse persistent goal/world/checkpoint/replay patterns; reject unrestricted effect authority.
- **harness:** add differential tests proving no privileged effect can bypass the capability/commit gateway; include crash/replay and denial receipts.
- **claycode:** make effect/capability requirements first-class semantic IR rather than prompt prose.
- **unifieddb:** persist grants, authorization decisions, effect receipts and rollback/recovery separately from policy/preference state.
- **claygraph:** association/activation may inform selection but never grant execution authority.
- **clayresearch:** treat Project Engine as an architecture quarry with positive and negative inheritance classes.
- **gwt/emergenz/hyperposition:** no direct scientific promotion; keep broadcast/selection/coupling measurements separate from authority-to-act.
- **q12_index:** preserve the historical design turn and its tradeoff explicitly.

## Earned-work mapping

No new avoided-work hours are quantified in this receipt. The mechanisms clearly contain historical value, but hour credit is withheld until row-level deduplication against existing core, safety/authority and LCME/SOMA mappings. This prevents duplicate completion credit.

## Level-0 effect

`666_RELEASE_GATE` remains **NOT_PASS**.

The current exact blocker remains Project-Frankenstein exhaustive tree/history denominator closure. The connected GitHub surface exposes file, commit, search and compare reads but no recursive read-tree/archive/clone read operation; therefore this shard is noncounting evidence until the denominator is frozen.

## Next discriminating work

1. Obtain or expose an exhaustive recursive Project-Frankenstein tree/history read surface or equivalent deterministic manifest.
2. Run exhaustive `_exec_tool` callgraph analysis and deployment/service sandbox inspection.
3. Cross-map Project Engine checkpoint/replay/task mechanisms into current ClayCode/Harness contracts with mandatory capability-gateway bypass tests.
4. Continue other non-overlapping semantic/history shards while the recursive denominator surface is unavailable.

## Provenance

This report stores reproducible evidence references and bounded inferences only. No hidden chain-of-thought is persisted. Historical commit claims remain historical evidence; no claim is promoted to current canonical truth solely because it appears in Project-Frankenstein.
