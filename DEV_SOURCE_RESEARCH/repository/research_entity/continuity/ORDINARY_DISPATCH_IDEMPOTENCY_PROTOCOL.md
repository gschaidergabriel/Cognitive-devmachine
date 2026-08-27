# Ordinary dispatch idempotency protocol

Status: mandatory engineering coordination protocol for repeatable ordinary infrastructure/runtime dispatches. It does not grant execution, spend, provider, model, training, or effect authority.

## Problem

A repeatable ordinary probe can be requested by many parallel Clay organs and by many nearby `go` macrocycles. If every requester creates its own issue/event, `issues.opened` fan-out can create genealogically identical queued/running jobs even though only one measurement is needed.

`macrocycle_id` is intentionally NOT the identity of an ordinary reusable probe. Separate `go` macrocycles may legitimately request the same still-pending probe.

## Required semantic dispatch identity

Every repeatable ordinary dispatch class MUST have one canonical spec under:

`research_entity/continuity/ordinary_dispatch_specs/<dispatch-class>.json`

The spec defines a stable `dispatch_class` and integer `retry_generation`. The current dispatch key is exactly:

`<dispatch_class>-g<retry_generation zero-padded to four digits>`

The key MUST NOT contain or derive from:

- user `go` text;
- macrocycle id;
- wall-clock timestamp;
- issue number;
- workflow run id;
- branch name;
- current `main` SHA when unrelated source movement does not change probe semantics;
- organ/model/session identity.

A generation changes only after a terminal result requires a deliberate retry, or after an explicit infrastructure/probe-semantic change whose reason is recorded in the spec/claim lineage. A new `go` alone NEVER increments generation.

## Create-only claim before event creation

Before creating an Issue, workflow-dispatch event, or any other external trigger for a repeatable ordinary dispatch, an organ MUST atomically CREATE-ONLY:

`research_entity/continuity/ordinary_dispatch_claims/<dispatch_key>.json`

If the claim already exists, the organ MUST NOT create another trigger. Existing claim means `ORDINARY_DISPATCH_ALREADY_CLAIMED`, regardless of whether the requester belongs to the same or a different `go` macrocycle.

The claim is coordination state only. It does not prove that a runner executed or that the probe is reachable.

## Trigger envelope

An issue-backed dispatch body MUST contain these exact fields:

`dispatch_schema: CLAY_ORDINARY_DISPATCH/v1`

`dispatch_key: <current dispatch_key>`

The workflow MUST reject/skip events without the schema marker, events whose key is not the current spec key, and events whose create-only claim is absent or mismatched.

## Workflow defense in depth

A repeatable ordinary workflow MUST additionally:

1. use one stable concurrency group per dispatch class;
2. keep `cancel-in-progress: false` unless a newer explicit policy says otherwise;
3. check for an existing append-only result before touching the runtime/sandbox;
4. persist the result under the semantic dispatch key, not `GITHUB_RUN_ID`;
5. treat a second equivalent run after a result exists as `ALREADY_SATISFIED` and perform zero runtime probe work;
6. record event SHA and actual checkout HEAD separately;
7. never infer product/runtime PASS from issue creation or queued workflow state.

Canonical result path:

`research_entity/continuity/ordinary_dispatch_results/<dispatch_key>.json`

## Retry law

A terminal PASS, BLOCKED, or FAIL result closes that generation. Retrying requires an explicit generation increment with a recorded reason. Pending/queued status does not authorize another issue for the same generation.

## Legacy fan-out quarantine

When a pre-protocol fan-out already exists, create one quarantine claim for the current generation and do not create further triggers. Historical queued runs remain legacy evidence with unresolved execution until terminally observed. Do not relabel multiple legacy runs as independent scientific replication.

## Evidence boundary

Claim presence = coordination fact only.
Issue presence = trigger fact only.
Queued run = scheduler fact only.
Terminal exact-source receipt = bounded runtime evidence at the receipt scope only.
