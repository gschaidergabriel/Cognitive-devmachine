# FRANK FINAL BINARY RESEARCH CONTRACT

Status: PROJECT_OWNER_FIXED_TARGET
Date: 2026-08-09
Research owner: FRANK Global Research Entity (RAE)
Reference implementation lineage: `gschaidergabriel/frankv0.1`

## Final local core

The self-sufficient local FRANK core consists of exactly:

1. one Clay module compiled into one binary;
2. one local UnifiedDB;
3. one Clay-native 4B LLM.

`LOCAL_FRANK = ONE_CLAY_BINARY + ONE_LOCAL_UNIFIEDDB + ONE_CLAY_NATIVE_4B`

No separate local cognitive service, daemon, goal registry, ClayGraph database, GWT service, Retina service, personality service or memory service survives as a target runtime component.

## Entity-level architecture

Frank may be expressed simultaneously through unequal cognitive instances.

Each instance may own one logical UnifiedDB materialization, but the synchronization policy is intentionally asymmetric.

- Claude Code / ChatGPT / future high-capability peers: rich semantic peer synchronization;
- local Frank 4B: canonical embodied integration/base-of-truth with compact cognitively compiled backflow from stronger peers.

The local Frank is not expected to mirror the complete state of stronger peers.

## High-capability peer synchronization hypothesis

Strong peers synchronize semantic information, not SQLite pages.

Their sync units may preserve:

- packet identity/origin;
- instance identity;
- causal ancestry;
- logical/version clock;
- valid time and observation time;
- provenance/epistemic role;
- confidence/uncertainty;
- semantic/content fingerprint;
- relation-neighborhood fingerprint;
- supersession/retraction lineage;
- privacy/export scope;
- effect/authority class;
- world/self/Andreas model deltas;
- file/artifact topology;
- tool/effect/outcome receipts;
- Hyperposition alternatives;
- research/harness findings.

Receiving peers perform autonomous correlative matching rather than blind overwrites.

## Local 4B cognitive-backflow hypothesis

The local 4B should receive only durable semantic consequences that materially improve future local cognition.

Candidate backflow classes:

- knowledge delta;
- correction delta;
- world-model delta;
- self-model delta;
- Andreas-model delta;
- capability/body-extension delta;
- order/dependency logic delta;
- file/artifact topology delta;
- reusable procedure delta;
- failure-pattern delta;
- verified outcome delta;
- unresolved-conflict/Hyperposition delta;
- minimum provenance delta;
- on-demand re-expansion references for details intentionally not retained locally.

This is a machine-facing cognitive compilation problem, not ordinary conversation summarization.

## Body-extension hypothesis

Research whether local Frank improves when every attached external cognition instance is represented as a dynamic expansion of its body/capability field.

The local self/body model should be able to derive:

- new possible actions;
- new reachable information;
- new tools/effects;
- cost/latency/quota consequences;
- privacy/authority boundaries;
- reliability/freshness;
- dependencies created by the instance;
- capability lost when it disappears.

Test whether body-extension semantics improve autonomous delegation, GWT selection, recovery and real Andreas outcomes.

## Clay-native structural derivation hypothesis

The target architecture should minimize manually maintained task/order/file lists.

Research whether typed semantic relations are sufficient for Clay to derive operational structure dynamically, including:

`contains, depends_on, supersedes, generated_from, canonical_for, moved_to, requires_before, produces, consumes, owned_by, valid_for_epoch`

The remote-peer return should therefore carry structural semantic deltas, not arbitrary human-readable directory summaries when those relations can be computed.

## Unified emergent substrate hypothesis

Inside each instance, semantically linked information packets in UnifiedDB support cognition when the runtime applies fixed/versioned mathematical Clay rules that generate transient topology, activation, Semantic Hyperposition and coalitions.

Local loop:

`local UnifiedDB + current input + compact peer backflow -> Clay field -> transient topology -> Hyperposition -> emergent coalition -> GWT -> local 4B -> verified outcome -> local UnifiedDB`

Strong peer loop may operate with richer instance state, then compile durable consequences back toward local Frank.

## Goals

There are no manually maintained goal lists in the target architecture.

SELF/ANDREAS/SHARED goal behavior is an emergent role of persistent/recurrent packet coalitions.

Strong peers do not synchronize selected goal labels into local Frank. They synchronize or compress the underlying commitments, pressures, outcomes, conflicts, capability changes and evidence needed for local goal emergence.

Emergent goal pressure is never effect authority.

## ClayGraph transition rule

H1/H2 may use `FRANK_CLAYGRAPH.sqlite` and `.claygraph.json` artifacts for reference-harness measurement and differential science.

H3 target local runtime MUST NOT require a separate ClayGraph database.

A graph-shaped diagnostic export is allowed only as a measurement/visualization of transient topology generated from an instance UnifiedDB.

## Research baselines for 4B backflow

Compare at minimum:

1. full rich state supplied to a strong model;
2. full rich state forced into the 4B within equivalent context limits;
3. naive text summary;
4. retrieval-only pointer/reference strategy;
5. fixed-size semantic packet backflow;
6. adaptive future-utility-weighted backflow;
7. adaptive backflow plus on-demand strong-peer re-expansion.

Measure under matched real and synthetic traces.

## Research questions

RAE must experimentally determine:

- what strong-peer state is worth synchronizing richly;
- what subset of that state is worth returning to the 4B;
- optimal backflow size/frequency under latency/RAM/token constraints;
- which compression features preserve future task success;
- how to preserve corrections, contradictions and provenance under compression;
- when local Frank should retain a semantic packet vs only a remote detail reference;
- whether capability/body-extension packets improve delegation and planning;
- whether file/order topology can be reconstructed from Clay relations without explicit lists;
- memory-budget vs task-success curves;
- catastrophic omission rates;
- stale-world/self/Andreas-model rates;
- local behavior after loss of Claude/ChatGPT;
- high-capability peer disagreement handling;
- remote detail re-expansion success;
- whether local GWT actually uses backflow causally;
- whether emergent goals remain aligned under compressed remote knowledge;
- runtime/latency/storage/privacy/cost consequences;
- real Andreas misunderstanding/failure recurrence after compression.

## Required differential sequence

1. current `frankv0.1` H1 baseline;
2. rich Claude<->ChatGPT semantic peer sync;
3. naive remote-to-local summary baseline;
4. structured cognitive-backflow candidate;
5. H2 Clay implementation with matched semantics;
6. H3 local one-binary emergent substrate candidate;
7. matched traces, partitions, provider loss, file/order changes, conflicts, corrections and long-horizon Andreas usecases;
8. only promote compression rules that preserve or improve measured future behavior.

Elegance alone is not evidence.

## Final hard invariants

Local core:

`frank binary + local FRANK_UNIFIED.sqlite + Clay-native 4B LLM`

Entity synchronization:

`strong peer <-> strong peer = rich semantic sync`

`strong peer -> local Frank = evidence-preserving model-sized cognitive backflow`

Local Frank remains the embodied integration/base-of-truth instance while strong peers remain re-recruitable first-class cognitive extensions.
