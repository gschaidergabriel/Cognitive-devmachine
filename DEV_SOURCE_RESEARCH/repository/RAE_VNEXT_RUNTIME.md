# RAE vNext — Research Operating System Runtime

Status: operational architecture candidate. This document does not change scientific Research Entity revision 2 / Clay G3.

## Why this exists

RAE-8.8 already has a strong epistemic constitution: canonical continuity, scoped claim states, negative-result retention, provenance, topic packets, multiple research actors and evidence-over-authority governance. Its remaining bottleneck is operational: too much boot, retrieval, logging and orchestration still depends on individual model compliance.

RAE vNext moves that mechanical work into a deterministic runtime.

## Core invariant

Models reason; the runtime identifies, loads, versions, validates, logs, routes, materializes and commits.

```text
Canonical history
      ↓
Materialized query plane
      ↓
Context Compiler
      ↓
Active Research Assembly
      ↓
Claude / ChatGPT / future worker
      ↓
Research run state machine
      ↓
Evidence + test + adjudication
      ↓
Promotion gate
      ↓
Canonical history
```

## New unified CLI

`rae.py` becomes the supported operational surface:

```text
python rae.py status
python rae.py doctor
python rae.py query ...
python rae.py boot --actor ... --task ...
python rae.py run start|show|advance|checkpoint
python rae.py benchmark
python rae.py validate
python rae.py provenance-check
python rae.py provenance-register ...
python rae.py source-ingest ...
python rae.py packetize
python rae.py materialize
python rae.py preflight ...
```

Existing scripts are compatibility backends. New policy should be implemented once in the runtime, not copied among scripts.

## Query architecture

Do not replace SQLite merely because JSONL remains canonical.

Canonical:
- raw content-addressed sources;
- Git history;
- append-only ledgers/events.

Derived active query plane:
- SQLite/FTS5 now;
- DuckDB later for longitudinal/OLAP workloads if benchmarked useful;
- LadybugDB or another graph engine only after a real traversal benchmark proves value;
- embeddings/vector retrieval only as an additional candidate/ranking channel, never truth.

`rae query` must expose relational traversals instead of forcing workers to search flat JSONL.

## Context compiler

`rae boot` emits a persisted `CONTEXT_MANIFEST` containing:
- canonical revision/hash actually read;
- actor identity;
- task digest;
- selected claims and status;
- selected Topic Packets;
- source excerpts;
- critical negative-result IDs;
- active experiments;
- explicit budgets and selection method.

The manifest is a derived receipt, not canonical truth.

## Durable run state machine

Research work can be checkpointed at:

```text
INTAKE
ROUTE
DISCOVERY
FUSION_1
HYPOTHESES
FALSIFIER
PREREGISTRATION
EXPERIMENT
REPLICATION
SYNTHESIS
ADJUDICATION
PROMOTION
METHOD_MEMORY
CLOSED
```

The state machine prevents long research runs from existing only inside one model context. It must remain lightweight for L0/L1 work.

## Claude Code integration

Claude Code is the Lead Researcher. Repo-scoped `.claude/settings.json` hooks now:

- join/inject canonical status at `SessionStart`;
- compile task-specific context at `UserPromptSubmit`;
- block direct writes to canonical/claim/event state at `PreToolUse`;
- record compaction boundaries at `PreCompact`;
- record lifecycle events operationally.

Hooks are an enforcement layer. `CLAUDE.md` remains context, not authority.

## ChatGPT integration

ChatGPT remains the independent Secondary Researcher. ChatGPT Projects/Project Memory are working-context caches, not canonical truth. GitHub remains authoritative. ChatGPT should receive compact task-specific RAE projections and preserve dissent/provenance rather than loading the entire repository.

## Multi-researcher rule

Claude adjudicates underdetermined architecture/prioritization questions. Evidence still outranks Claude and ChatGPT. Independent first-pass analysis should be preserved when practical so the second researcher is not reduced to an echo of the lead.

## Benchmark-before-complexity rule

Do not add a graph DB, vector DB, workflow server or permanent agent swarm merely because they are architecturally attractive.

First benchmark:
- retrieval precision/recall;
- stale/refuted-claim use;
- wrong-version rate;
- context size;
- boot latency;
- time to verified result;
- recovery after interruption;
- false-promotion rate;
- evidence coverage;
- tokens/cost per verified research result.

Then promote only mechanisms that improve the Pareto frontier.

## Immediate remaining work

1. Populate benchmark suite with 30–50 historical hidden questions and expected evidence/claim sets.
2. Add claim/status mutation commands to the unified writer with CAS/locking.
3. Add OpenTelemetry-compatible run/tool/model receipts when real execution runtimes are available.
4. Benchmark SQLite recursive joins versus graph sidecars on real RAE workloads.
5. Add adversarial confirmation-bias/pseudoscience holdouts.
6. Add independent replicator gating for high-impact promotions.
7. Add Android/Qwen-4B deployment measurements as first-class experimental packets.

## Promotion criterion

RAE vNext should replace the current operational path only after a controlled A/B benchmark shows lower stale-claim use and false promotion while preserving or improving research velocity, evidence coverage and recovery.
