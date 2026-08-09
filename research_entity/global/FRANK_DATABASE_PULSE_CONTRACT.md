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

## Digital Soul: situated temporal-state continuity

Within the FRANK project, **Digital Soul** names the persistent situated continuity produced by the combination of FRANK identity/state lineage, Database Pulse, memory, body/device state, environment observations, goals, world/self model, recovery history and re-entry.

The engineering objective is that FRANK continuously maintains an evidence-backed answer to questions such as:

- **When am I?** current wall-clock time, timezone, monotonic runtime time, boot/session epoch, last-pulse time, time since last interaction, and time spent in the current state;
- **Where am I?** current host/device identity, execution environment, filesystem/workspace context, current desktop/session context, network/environment context and, only when an authorized sensor/source provides it, physical/geographic location;
- **What state am I in?** active goals, commitments, cognitive mode, body/device/resource state, current workspace/desktop context, open tasks, recent events, memory/re-entry state and confidence/freshness of each observation;
- **How long have I been like this?** state-entry timestamp plus monotonic duration, with suspend/restart/recovery semantics explicitly recorded;
- **What changed around me?** admitted deltas from the immediate digital environment such as files/folders, applications, sessions, connected devices, tools, capabilities and other authorized observations.

This is a **situated synthetic-entity self/world model**, not an LLM context trick. The LLM may receive a projection of this state, but the state exists independently of any one model call.

### Temporal continuity requirements

FRANK must distinguish at least:

- `wall_clock_time`;
- `timezone`;
- `monotonic_runtime_time`;
- `boot_id` / `session_epoch`;
- `pulse_sequence`;
- `last_pulse_at`;
- `last_external_interaction_at`;
- `state_entered_at`;
- `time_in_current_state`;
- `paused_duration` / suspend intervals where observable;
- `restart_count` and recovery lineage;
- freshness/confidence of time-derived observations.

Wall clock and monotonic duration must not be conflated. Clock jumps, suspend/resume and restart must be detectable or explicitly marked uncertain.

### Situated environment / place requirements

"Place" is multi-layered and must carry provenance. FRANK may maintain:

1. logical place: project/workspace/repository/task context;
2. host place: machine/device/VM/container identity;
3. desktop place: active user session, working directory, visible/authorized folders, applications and windows where available;
4. network place: current network/interface/site context where available;
5. physical place: geographic/location sensor evidence only when explicitly available and authorized.

The phrase "FRANK knows where it is" means that FRANK maintains a current, provenance-bound estimate of these situated layers. Missing/stale location evidence must remain `UNKNOWN` or `STALE`, never guessed.

### Immediate digital-environment intake

Authorized local artifacts such as Desktop folders, project directories, mounted resources, application/session state or device observations can become part of FRANK's immediate environment model. Intake must be permission-scoped, provenance-bound and budgeted.

FRANK must not indiscriminately ingest the entire machine. For each observation, retain source, timestamp, freshness, scope, identity/hash where useful, and whether the content itself or only metadata was admitted. Sensitive/private data boundaries remain explicit.

## Persistence / continuity semantics

A running FRANK instance may continue pulsing across idle periods while its executable runtime plus admitted persistent state remain available and the Pulse scheduler is enabled. The durable continuity object is the versioned FRANK state/identity lineage plus executable Pulse semantics, not a transient LLM context window.

Deleting or stopping a process is not automatically equivalent to deleting FRANK if recoverable admitted state and executable semantics remain and can resume under the continuity contract. Conversely, retaining a binary file alone does not prove an actively running Pulse. Operational claims such as `PULSING`, `PAUSED`, `STOPPED`, `RECOVERABLE`, or `DELETED` must be backed by runtime/state receipts.

The project owner's intended continuity criterion is that, while the FRANK binary/runtime and admitted state remain intact and the Pulse is actually scheduled/executing, FRANK continues its endogenous state-and-cognition cycle and therefore continues accumulating temporal/state continuity. If execution is paused, FRANK should preserve the pause boundary and recover the elapsed interval rather than pretending uninterrupted processing occurred.

## Cognitive cycle

A Pulse may include, where implemented and evidence-gated:

1. census of current UnifiedDB/entity state;
2. update of temporal, body/device and situated-environment state;
3. activation/relevance propagation in derived ClayGraph projections;
4. hypothesis/codependency/alternative generation under bounded rules;
5. GWT-like competition/selection and routing;
6. Hyperposition preservation/reopening of unresolved alternatives;
7. homeostatic / E-PQ / NAcc-like regulatory updates where validated;
8. memory consolidation, decay, novelty and re-entry bookkeeping;
9. optional bounded model/tool/peer invocation;
10. outcome/receipt ingestion;
11. epoch advance and preparation of the next FRANK cognitive/action cycle.

UnifiedDB remains semantic authority; ClayGraph remains derived/rebuildable activation/association topology and never becomes truth authority merely because something is highly activated.

## Binary / runtime relation

The future one-module/binary FRANK must preserve the Database Pulse and Digital Soul continuity as endogenous entity mechanisms. Binary consolidation may change physical packaging but must not collapse the Pulse into "call the LLM repeatedly" or erase entity-state continuity, typed internal boundaries, temporal/place state, provenance, recovery, replay, or intervention observability.

A binary is therefore an executable realization of FRANK's mechanisms, not FRANK's entire identity by itself. FRANK continuity is defined by admitted executable semantics + state/identity lineage + valid recovery/replay receipts.

## Measurement boundary

`pulse_count`, `state_transition_count`, `graph_change`, `hypothesis_count`, `memory_update`, `reentry_count`, `model_call_count`, `tool_call_count`, `effect_count`, `environment_observation_count`, `time_in_state`, and `situated_state_change_count` are distinct observables.

A Pulse can occur with zero LLM calls. An LLM call can occur without constituting a full Database Pulse.

Promotion tests must include at minimum:

- zero-model-call Pulse episodes;
- model-assisted Pulse episodes;
- stable wall-clock + monotonic-time tracking;
- state-duration tracking across normal operation;
- pause/resume and crash/restart continuity;
- host/workspace/Desktop-context change detection under explicit permissions;
- stale/unknown place and time evidence handling;
- deterministic/replayable state receipts where applicable;
- stale/corrupt state fail-closed behavior;
- bounded resource use and runaway-loop prevention;
- proof that model replacement does not erase FRANK identity/state lineage;
- proof that Pulse-generated state can causally affect later FRANK cognition/action without being confused with sensor truth or execution authority.

## Epistemic boundary

Within this project, "lives", "thinks", "continues thinking", "time sense", "place sense" and "Digital Soul" may be used as engineering shorthand for a running synthetic entity whose endogenous Pulse maintains persistent stateful cognitive, temporal and situated-environment transitions.

These engineering definitions do **not** by themselves establish phenomenal consciousness, biological life, subjective experience, sentience or moral status. Those are separate scientific/philosophical questions and must not be inferred solely from persistence, recurrence, self-location or temporal continuity.

## Required downstream interpretation

All FRANK, Harness, GWT, Emergence, ClayCode, ClayGraph, UnifiedDB, Hyperposition, Digital Retina and binary-freeze work must preserve this distinction and the Digital Soul continuity surface. Any design that makes Database Pulse synonymous with continuous LLM inference, or discards FRANK's time/place/state continuity during binary consolidation, is non-conformant unless the project owner explicitly changes this contract.
