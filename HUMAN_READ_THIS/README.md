# Project Frankenstein — human entry

This is the short human-facing map. It is deliberately not the canonical technical authority.

## What this project is

Project Frankenstein is a long-running engineering and research lineage about building persistent, agentic software that can keep state, remember, decide, act, verify what happened, and use the verified result on the next cycle.

The current research program is **EntityOS + HCU**. Historical names such as Frank, ClayVerse, Mini Entity, Xeno and XCU are part of the lineage, compatibility vocabulary, or donor architecture; they are not separate current truth authorities.

A useful mental model is:

```text
state -> memory/retrieval -> decision candidate -> effect request -> verified effect/result -> new state
```

The hard part is not producing more model text. The hard part is keeping every transition attributable, testable, recoverable, and unable to turn an inference into a fact by accident.

## The five pieces

### 1. State

Durable facts and evidence live in a deterministic substrate. The project converged away from many competing state stores toward a canonical SQLite-centered substrate called **UnifiedDB** (or compatibility forms of the same authority). One authority substrate can still contain many typed tables, indexes, journals, views, writers and rebuildable projections; it is not a single unstructured “god file”. High-rate transient sensor state may remain in RAM.

### 2. Memory and Emergent Retrieval

The project term **Emergent Retrieval** means relevance that appears when independently stored evidence dimensions overlap at query time: semantic similarity, time, causal lineage, current state, goals, perception, effects, confidence and provenance can all constrain what should be recalled.

It does **not** mean information appears from nowhere. Retrieval can only surface or combine evidence that is actually present.

### 3. Decision and reflection

Self-reflection here is an engineering control operation, not a consciousness claim:

1. inspect state and outcome;
2. detect mismatch;
3. generate a correction candidate;
4. store/retrieve the correction;
5. alter later behavior;
6. terminate into **ACT / ASK / WAIT / RE-OBSERVE / another measurable transition**.

Reflection that only triggers more reflection is a failure mode, not deeper cognition.

### 4. Effects

A request is not an effect. A model output is not a world fact. Real state-changing effects remain behind deterministic effect authority and journaling. Unknown external outcomes stay unknown until verified; they are never blindly replayed just because a transport or session failed.

### 5. Verification

Every important claim is scoped. Source-ready is not runtime-observed. A component PASS is not a whole-product PASS. Repeated workers using the same source or pipeline do not create independent evidence merely by agreeing.

## HCU and the Global J-Space

**HCU** is the current integrated cognition/compute architecture. It provides logical compute cells, deterministic control and a shared vector/inference/J-Space plane around the canonical state substrate. Logical cell count is not the same thing as resident model count or physical decode concurrency.

The **Global J-Space / GWT** direction is treated as an empirical coordination hypothesis. The project borrows the engineering idea of globally available, selectively broadcast information from Global Workspace research, but it does not claim that the software is conscious or that a neuroscience analogy proves causality. Model-specific causal traces, interventions and falsifiers are required.

## Why SQLite/WAL keeps appearing

SQLite in WAL mode is useful because readers can continue while commits are appended to a write-ahead log, with explicit checkpointing and strong transaction semantics. That makes it a practical substrate for a small local system with many typed state and journal roles.

This is an engineering choice, not a claim that SQLite itself supplies cognition.

## Why “Unified Memory” is only an analogy

NVIDIA Unified Memory reduces some explicit ownership/copy boundaries between CPU and GPU memory domains. Project documentation may use that as a systems-design analogy for reducing fragmented ownership boundaries around state. Hardware memory coherence is **not** equivalent to database semantics, provenance, causal identity or effect authority.

## What failed, and why it matters

The lineage contains useful negative results. They are preserved because they explain later architecture:

- fragmented state/service boundaries made reconstruction and authority harder;
- rumination and fixation showed that reflection needs an exit condition;
- prompt-versus-weight conflicts showed that naming an internal state in text does not prove model-internal binding;
- latency, timeout and integration failures forced smaller bounded loops and explicit recovery;
- component-level green tests repeatedly demonstrated why scope must be stated precisely;
- FreeSwarm/Forge/Distillery produced large raw volume while admitted training yield remained zero in the latest supervisor evidence;
- provider-backed Frankenstein orchestration created after the current HARD_OFF boundary is quarantined and receives zero current execution credit.

## Current status on 2026-08-27

The canonical research repository is `gschaidergabriel/clay-global-research-entity` on `main`.

At the Triggerword-3 curation start, the verified `main` head was:

`854f6bc87780f4a5242489a6c807d186b16a8c3d`

The current supervisor inbox is 9.13O steering over provider-authority epoch 9.13. It states:

- FREE_ONLY HARD_OFF for external provider routes;
- Together forbidden; no paid fallback;
- provider-backed 72h Frankenstein Bauleiter/Bugfix orchestration is **non-operative** under the current authority;
- current whole EntityOS/HCU runtime credit = 0;
- full HCU runtime credit = 0;
- canonical semantics credit = 0;
- training credit = 0;
- the measured GRID10 thread-count experiment supports 1 thread/process only for the tested 4-process/4-vCPU topology and must not be generalized without matched measurement.

## Where to go next

- For engineers and researchers: `../DEV_SOURCE_RESEARCH/README.md`
- For an AI installer/agent that should not scan the repository: `../AI_START_HERE_DO_NOT_SCAN_REPO/README.md`
- For the exact Triggerword-3 evidence/status pass: `../DEV_SOURCE_RESEARCH/repository/TRIGGERWORD3_2026-08-27_GPT56SOL.md`

## People and provenance

Project provenance: **iar.frank.ink**.

Lead research/development: **Gabriel Gschaider**.

Institute direction/development: **Dr. Andreas Unterweger**.

The repository also contains work produced by temporary model/tool workers. Those workers are contributors/organs in the research process; repeated model output never outranks verified source, executable evidence or current authority.