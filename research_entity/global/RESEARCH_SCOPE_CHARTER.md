# GLOBAL RESEARCH SCOPE CHARTER — UCM-ONLY

## Mission

Until explicitly changed by the human owner, the entire Research Entity studies, builds, falsifies and improves **only the Unified Clay Machine (UCM)**.

All former broad research domains are frozen unless they are directly required to improve or test the UCM.

## Experimental body

The Research Entity does not mutate the main Clay/Frank/ClayVerse instance during research. It develops an isolated second Clay Machine under:

`research_entity/unified_clay_machine/UCM2/`

UCM2 is the mutable research body. The main instance is a source of current architecture, runtime observations, VPS work logs, receipts, failures and requirements.

## Input authority

Every cycle starts from the newest verifiable evidence available, in this order where present:

1. latest versioned VPS work reports and exact receipts;
2. latest admitted/main repository state and exact commit SHA;
3. current main-instance architecture/state contracts;
4. prior UCM2 work reports and experimental state;
5. external research only when it directly informs a UCM question.

Chat/model/provider memory is never research authority.

If direct VPS freshness cannot be verified, the cycle must record an explicit `VPS_FRESHNESS_GAP` rather than silently treating older evidence as current.

## What belongs to UCM research

Research is in scope only when it directly advances the Unified Clay Machine, including:

- fluid UnifiedDB/state materialization;
- integrated wiki/knowledge/memory;
- module/organ model and module lifecycle;
- state machines and execution continuity;
- self/world models;
- Semantic Hyperposition and GRT/GRF possibility state;
- GWT/reentry when represented as UCM state/topology;
- ClayGraph as derived topology/index/projection;
- retrieval, activation and bounded assemblies;
- provenance, epochs, transactions, replay and recovery;
- sync/distribution/HA required by UCM;
- API and small runtime/binary required to operate UCM;
- model/tool adapters required for frontier models to use/read/test UCM2;
- observability, benchmarks, fuzzing, ablation, failure injection and security required to validate UCM.

Anything else is OUT OF SCOPE unless it is a direct dependency of one of these items.

## Frontier-model research law

Frontier models are temporary workers, not authorities. They should use UCM2 as a real experimental machine:

- read/query its current state;
- inspect its module graph and history;
- propose and implement bounded UCM2 mutations;
- run self-read/replay/recovery/failure tests;
- compare predictions with measured outcomes;
- preserve negative results;
- emit exact work reports with source and tested SHAs.

A model claim without an executable or independently inspectable receipt remains a hypothesis.

## Separation from the main instance

UCM2 may import or mirror main-instance semantics and evidence, but it may not write experimental state into the main instance as truth.

Promotion path is one-way and explicit:

`MAIN/VPS evidence -> UCM2 experiment -> versioned report/receipt -> bounded candidate knowledge for main instance`

The main instance may later consume the reports when working on ClayVerse, but must independently admit/promote any mechanism according to its own authority gates.

## Work-report law

Every material research cycle ends with a new append-only report in:

`research_entity/unified_clay_machine/UCM2/reports/`

Each report records at minimum:

- report id and parent report;
- timestamp;
- source main repo SHA(s);
- source VPS receipt/work-log identifiers and observed freshness;
- UCM2 before/after commit or state epoch;
- question/hypotheses/counter-hypotheses;
- changes made;
- tests and exact outcomes;
- failures/negative evidence;
- what is VERIFIED / OBSERVED / INFERRED / HYPOTHESIS / REFUTED;
- reusable finding for the main instance;
- next highest-information UCM experiment.

No material cycle is DONE until its report and associated changes are versioned in the repository.

## Success criterion

The target is a measured working Unified Clay Machine whose durable semantics are primarily represented as a fluid typed data/state fabric, with derived topology, a small trustworthy runtime/binary and a unified API, and whose state can be replayed, recovered, inspected and used by frontier models without depending on provider chat memory.
