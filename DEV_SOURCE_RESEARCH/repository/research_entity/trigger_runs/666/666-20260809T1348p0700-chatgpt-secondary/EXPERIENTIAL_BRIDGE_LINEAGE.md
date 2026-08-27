# Level-0 Shard — Project-Frankenstein Experiential Bridge

## Scope

This shard reconstructs the historical bridge from real external actions into persistent state that can affect future cognition.

The useful mechanism is functional and causal:

`effect -> outcome observation -> durable/derived state -> selective re-entry`

It is **not** evidence of phenomenal subjective experience.

## Introduction — 2026-03-01

Commit `3a47fef19027b2677bf96c6d5d6965364251a425` introduced the Experiential Bridge. Core-proxy tools, agentic tools, chats and entity sessions wrote directly to `consciousness.db.activity_log`. Tool results fired E-PQ success/failure events. Entity sessions additionally stored pre/post mood, metadata, narrative reflection and affective feedback. A SQL daily-activity summary was injected into idle-thought prompts.

The same audit also repaired several bridge failures:

- cross-process calls to `get_consciousness_daemon()` instantiated a heavyweight daemon in the wrong process;
- tool-proxy failures had not been recorded;
- entity experience used a race-prone UPDATE of the newest row;
- agentic tools lacked matching E-PQ events.

These are valuable negative results for any modern effect/outcome bus.

## Frozen-head state

At frozen HEAD `abba90a5767d85abc8a1ac340bae92842dab35c1`:

- `core/app.py` still records core-proxy tool activity directly to SQLite;
- `agentic/executor.py` still records agentic execution activity and E-PQ success/failure;
- `consciousness_daemon.py` retains `record_activity()` and structured room-experience recording;
- `activity_log` is explicitly capped to the latest **500 rows**;
- room completion publishes a `room_session_complete` GWS event with duration, mood delta, exit reason and summary;
- room sessions generate a derived first-person narrative reflection;
- daily activity summaries remain available, but the former unconditional injection into deep thoughts has been restricted to data-driven prompt paths because raw metrics caused prompt leakage/semantic conflict.

This proves a persistent architectural lineage for effect-to-re-entry coupling, not a complete causal audit trail.

## Why the historical bridge is not a modern effect ledger

Frozen bridge records are lossy:

- the 500-row ring buffer deletes older events;
- core-proxy context records only one selected payload field and truncates it;
- core-proxy duration is stored as zero;
- raw tool result bodies and hashes are absent;
- stable request/capability/plan/claim correlation IDs are absent;
- agentic successful activity rows generally carry no input/result context in this bridge record;
- core-proxy success defaults to true if a response dictionary has no explicit `ok` field.

Therefore:

`effect telemetry != authoritative effect receipt`

and

`execution_success != goal_success`.

## Re-entry negative result

The bridge originally tried broad global availability by injecting daily metrics into idle thoughts. Frozen-head logic narrows this. Deep-thought prompts should not see raw metric blocks by default because those numbers conflicted with the prompt's semantic frame and caused leakage.

This yields a useful GWT engineering constraint:

`global availability != indiscriminate prompt injection`.

A workspace should make evidence addressable/available while selecting a task-compatible projection for the active context.

## Current architecture implication

A stronger current sequence is:

`model proposal`
`-> deterministic capability decision`
`-> effect request_id`
`-> executor`
`-> immutable raw effect/outcome receipt`
`-> derived activity/experience projection`
`-> selective workspace/context re-entry`
`-> later outcome measurement`
`-> causal link back to goal/claim/proposal`

Each authoritative receipt should include stable identifiers, capability decision, input/result hashes, timestamps/durations, pre/post state, errors, rollback linkage and source provenance.

## Experimental implication

The Experiential Bridge provides a historical precursor for one of the strongest current GWT/emergence tests:

- truthful effect/outcome re-entry;
- shuffled re-entry control;
- no-re-entry lesion;
- restoration/rescue;
- delayed outcome measurement.

If truthful re-entry improves subsequent decisions and shuffled re-entry degrades them under matched conditions, that would support a causal role for re-entry. It would still not establish phenomenal consciousness.

## Coverage

- exact Level-0 coverage credit: `0.0`;
- historical earned-work hours: `0.0` pending row-level deduplication;
- full Project-Frankenstein history/tree denominator remains unfrozen.

Durable receipt:
`research_entity/archive_assimilation/receipts/666_20260809T1419p0700_chatgpt_secondary_pf_experiential_bridge_lineage.json`
