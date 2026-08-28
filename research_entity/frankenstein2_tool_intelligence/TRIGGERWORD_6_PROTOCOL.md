# Triggerwort 6 — Frankenstein 2.0 External Tool Intelligence Research Mirror

Status: ACTIVE / FULL-PROVENANCE SIDE
Canonical build consumer: `gschaidergabriel/frankenstein-2.0`

This directory is the Research-Entity mirror and raw provenance side of the Frankenstein-2.0 Trigger-6 research unit.

## Exact mission

Trigger 6 researches external GitHub repositories, tools, mechanisms and agent best practices that may measurably improve Frankenstein 2.0. It discovers, source-audits, falsifies, benchmarks, compares and distills them. It never grants architecture credit from popularity or README claims.

```text
5 = current Frankenstein donor forensics
6 = external tool/mechanism research + falsification
4 = F2/VPS build, integration and measurement
```

## Mandatory live delta fusion

Before every Trigger-6 task, refresh and fuse:

- current `frankenstein-2.0/main` HEAD, architecture, workpackages and checkpoints;
- latest Trigger-4 build/test/measurement/outcome deltas;
- latest Trigger-5 Frankenstein-forensic ingest deltas;
- new Research-Entity architecture deltas since the previous Trigger-6 cursor;
- existing Trigger-6 hypotheses/counterhypotheses/negative results;
- Trigger-4 feedback on previously handed-off candidates.

Emit a versioned `ArchitectureDeltaFusion` with exact source SHAs, affected modules, conflicts, supersessions and unresolved gaps. Research is snapshot-bound. If later F2/4/5 deltas affect its assumptions, mark it `STALE_REVIEW_REQUIRED` and re-evaluate before handoff.

## Five-slot cycle

Each exact `triggerwort 6` claims one currently most useful specialized slot:

1. `ARCHITECTURE_DELTA_FUSER`
2. `DISCOVERY_SCOUT`
3. `SOURCE_ARCHAEOLOGIST`
4. `EXPERIMENTAL_FALSIFIER`
5. `INTEGRATION_DISTILLER`

Five successive triggers should normally achieve broad role coverage, while information gain may justify repeating a role. Each worker is bounded, specialized and evidence-first.

## Evidence ladder

`E0 SEED -> E1 SOURCE_READ -> E2 ARCHITECTURE_MAPPED -> E3 CLAIM_REPRODUCED -> E4 F2_ABLATION -> E5 BUILD_CANDIDATE -> E6 F2_ACCEPTED`

No Trigger-6 worker can self-promote to E6. E6 requires a Trigger-4 build/test/measurement receipt from the actual F2/VPS front.

## Two-repository persistence law

F2 canonical paths:

- `research/tool_intelligence/`
- `research/tool_intelligence/pending_research.sqlite`
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
TRIGGER6 -> EVIDENCE -> TRIGGER4/VPS -> MEASURE -> TRIGGER6/RCPD
```
