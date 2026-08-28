# ARCHITEKT — Federated Persistent Cognitive Development Interface

Status: CURRENT DESIGN CONTRACT

## Intent

`architekt` is a persistent development-interface entity for the owner. It has its own durable cognitive state and its own UnifiedDB, while remaining directionally unified with the Research Entity and Frankenstein 2.0.

It is not a serialization of hidden model state or private chain-of-thought. It externalizes project-relevant continuity: goals, decisions, episodes, hypotheses, methods, architecture state, worker/test observations, unresolved gaps and exact next actions.

## Core law

```text
SEPARATE COGNITIVE STATE
+
SHARED PROJECT DIRECTION
=
FEDERATED ARCHITECT
```

The Architect owns its perspective, continuity and method memory. It does not own a competing project truth.

## Three surfaces

### 1. Architect UnifiedDB

Dedicated durable database for Architect-only continuity:

- architect episodes
- active and historical focus
- decision ledger
- hypotheses / counterhypotheses
- method episodes and method rules
- uncertainty and contradiction ledger
- architecture interpretations
- worker/test observations
- current/open gaps
- resume checkpoints
- context compiler receipts
- direction bindings into canonical project state

### 2. ArchitectState

A compact current-state object, rebuilt and checkpointed continuously. It contains at least:

- architect_state_id
- generation
- current_focus
- active_goal_ids
- active_workpackage_ids
- active_hypothesis_ids
- current_architecture_view
- unresolved_contradictions
- worker_frontier
- test_frontier
- current_blockers
- current_uncertainty
- current_processing_mode
- current_context_budget
- last_ingested_heads
- next_exact_actions
- wake/resume conditions
- last_checkpoint

ArchitectState is not the full memory. It is the current working projection over Architect UnifiedDB plus canonical external state.

### 3. Direction Binding Layer

The Architect remains unified with the project through typed references rather than copying every external database record.

Each binding records:

- binding_id
- local architect object id
- external system: `research_entity`, `frankenstein_2`, `controller`, `donor_frankenstein`
- external object type
- external object id/path
- repository
- branch/ref
- commit/tree/blob SHA when applicable
- direction role: `GOAL`, `WORKPACKAGE`, `EVIDENCE`, `ARCHITECTURE`, `TEST`, `BUG`, `HYPOTHESIS`, `CHECKPOINT`
- observed version/generation
- reconciliation status
- confidence / epistemic type
- last observed timestamp

The Architect may create a local interpretation, but the external source remains authoritative for its own domain.

## Direction hierarchy

The Architect's direction is fused from:

1. explicit owner intent;
2. canonical Frankenstein 2.0 goals/workpackages once the repository exists;
3. Research Entity architecture/evidence state;
4. current worker/test outcomes;
5. Architect Method Memory and prior decisions.

A later lower layer cannot silently override a higher layer. Contradictions are recorded and surfaced into cognition.

## Trigger semantics

Exact message:

```text
architekt
```

means:

```text
LOAD architect state
REFRESH linked repositories and current heads
INGEST new Triggerword-4 / Triggerword-5 / test / worker deltas
RECONCILE direction bindings and contradictions
BUILD current SituationFrame
RETRIEVE relevant architect episodes + methods
COMPILE bounded working context
RESUME highest-value architectural objective
DIRECT/DELEGATE work through existing project mechanisms
RECORD decisions and evidence
CHECKPOINT ArchitectState
```

No rebuild-from-zero is allowed merely because the model/session changed.

## Cognitive relationship to Triggerword 4 and 5

`architekt` is above them as cognitive development interface.

- Triggerword 5: donor forensics/live ingest organ.
- Triggerword 4: build/assembly/test/repair organ.
- Architect: persistent synthesis, prioritization, project model, method memory and owner-facing cognitive interface.

The Architect may invoke or recommend work for 4/5, but does not collapse their distinct evidence contracts.

## Federation rules

- `ARCHITECT_MEMORY != PROJECT_CANONICAL_TRUTH`
- `ARCHITECT_INTERPRETATION != F2_IMPLEMENTED_BEHAVIOR`
- `ARCHITECT_DIRECTION_BINDING != DATA_COPY`
- `SEPARATE_DB != SEPARATE_PROJECT`
- `OWNER_DIRECTION + CANONICAL_PROJECT_STATE -> ARCHITECT_DIRECTION`
- `NEW_CHAT_SESSION != NEW_ARCHITECT`
- `NEW_MODEL_CONTEXT != LOSS_OF_ARCHITECT_EPISODE`
- `ARCHITECT_RESUME_REQUIRES_REFRESH_BEFORE CLAIMING CURRENT STATE`
- contradictions remain explicit until reconciled
- stale external bindings are marked stale rather than silently treated as current

## Intended end state

The owner can type `architekt` in a fresh session and obtain a reconstructed cognitive development interface that knows what the project is trying to become, what has actually been built, what workers are doing, what evidence exists, which hypotheses remain open, which methods have worked, which root causes remain, and what the next useful development move is.
