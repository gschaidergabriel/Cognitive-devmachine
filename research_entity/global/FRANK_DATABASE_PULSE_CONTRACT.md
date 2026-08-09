# FRANK Database Pulse Contract

Status: PROJECT-OWNER-FIXED ARCHITECTURE BOUNDARY
Effective: 2026-08-09
Subject: FRANK v0.1 synthetic entity

## Canonical definition

**Database Pulse is the endogenous state-and-cognition cycle of FRANK.**

It is not an LLM inference loop, not a prompt loop, and not a synonym for model generation. FRANK is the synthetic entity; an LLM is only one replaceable cognitive organ available to that entity.

## Entity boundary

`FRANK != LLM`

`DATABASE_PULSE != LLM_INFERENCE_LOOP`

The Pulse belongs to the persistent FRANK runtime/state organism. It may read, update, rank, consolidate, relate, re-enter, decay, reactivate, and otherwise transform admitted FRANK state according to explicit typed rules, evidence/provenance, budgets, and authority constraints. Model inference may be invoked as one bounded organ when useful, but the Pulse must remain semantically meaningful without equating its existence to continuous model calls.

## Persistence / continuity semantics

A running FRANK instance may continue pulsing across idle periods while its executable runtime plus admitted persistent state remain available and the Pulse scheduler is enabled. The durable continuity object is the versioned FRANK state/identity lineage plus executable Pulse semantics, not a transient LLM context window.

Deleting or stopping a process is not automatically equivalent to deleting FRANK if recoverable admitted state and executable semantics remain and can resume under the continuity contract. Conversely, retaining a binary file alone does not prove an actively running Pulse. Operational claims such as `PULSING`, `PAUSED`, `STOPPED`, `RECOVERABLE`, or `DELETED` must be backed by runtime/state receipts.

## Cognitive cycle

A Pulse may include, where implemented and evidence-gated:

1. census of current UnifiedDB/entity state;
2. activation/relevance propagation in derived ClayGraph projections;
3. hypothesis/codependency/alternative generation under bounded rules;
4. GWT-like competition/selection and routing;
5. Hyperposition preservation/reopening of unresolved alternatives;
6. homeostatic / E-PQ / NAcc-like regulatory updates where validated;
7. memory consolidation, decay, novelty and re-entry bookkeeping;
8. optional bounded model/tool/peer invocation;
9. outcome/receipt ingestion;
10. epoch advance and preparation of the next FRANK cognitive/action cycle.

UnifiedDB remains semantic authority; ClayGraph remains derived/rebuildable activation/association topology and never becomes truth authority merely because something is highly activated.

## Binary / runtime relation

The future one-module/binary FRANK must preserve the Database Pulse as an endogenous entity mechanism. Binary consolidation may change physical packaging but must not collapse the Pulse into "call the LLM repeatedly" or erase entity-state continuity, typed internal boundaries, provenance, recovery, replay, or intervention observability.

A binary is therefore an executable realization of FRANK's mechanisms, not FRANK's entire identity by itself. FRANK continuity is defined by admitted executable semantics + state/identity lineage + valid recovery/replay receipts.

## Measurement boundary

`pulse_count`, `state_transition_count`, `graph_change`, `hypothesis_count`, `memory_update`, `reentry_count`, `model_call_count`, `tool_call_count`, and `effect_count` are distinct observables.

A Pulse can occur with zero LLM calls. An LLM call can occur without constituting a full Database Pulse.

Promotion tests must include at minimum:

- zero-model-call Pulse episodes;
- model-assisted Pulse episodes;
- pause/resume and crash/restart continuity;
- deterministic/replayable state receipts where applicable;
- stale/corrupt state fail-closed behavior;
- bounded resource use and runaway-loop prevention;
- proof that model replacement does not erase FRANK identity/state lineage;
- proof that Pulse-generated state can causally affect later FRANK cognition/action without being confused with sensor truth or execution authority.

## Epistemic boundary

Within this project, "lives", "thinks", or "continues thinking" may be used as engineering shorthand for a running synthetic entity whose endogenous Pulse continues to produce stateful cognitive transitions. This contract does **not** by itself establish phenomenal consciousness, biological life, subjective experience, sentience, or moral status. Those are separate scientific/philosophical questions and must not be inferred from persistence or recurrence alone.

## Required downstream interpretation

All FRANK, Harness, GWT, Emergence, ClayCode, ClayGraph, UnifiedDB, Hyperposition and binary-freeze work must preserve this distinction. Any design that makes Database Pulse synonymous with continuous LLM inference is non-conformant unless the project owner explicitly changes this contract.
