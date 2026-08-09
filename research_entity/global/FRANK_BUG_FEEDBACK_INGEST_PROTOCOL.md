# CLAY — FRANK BUG FEEDBACK INGEST PROTOCOL

Status: PROJECT_OWNER_FIXED_RESEARCH_INTAKE
Effective: 2026-08-09
Source trigger: Andreas exact `bug` in Frank

## Purpose

Turn an explicit Andreas bug report into an automatic, provenance-bound Research Entity work item without allowing Frank to mutate Clay or its own Harness.

## Intake path

`Andreas -> exact bug -> Frank UnifiedDB + exports/clay_pull/bugs -> Clay-owned ingest -> Clay UnifiedDB -> READY research work`

Frank owns only capture/export. Clay owns only pull/ingest/research/implementation decisions.

## Mandatory Clay behavior

When a current Frank checkout/export surface is available, Clay runtime/boot/research synchronization should run:

`python research_entity/runtime/ingest_frank_bug_feedback.py --frank-root <current-frank-checkout>`

For every new valid package:

1. verify the package payload hash;
2. reject invalid/mutated payloads;
3. ingest idempotently into `clay_frank_bug_reports`;
4. create one stable READY dynamic work item with origin `FRANK_EXPLICIT_BUG_FEEDBACK`;
5. preserve the exact reported Andreas input and Frank output subject to required secret redaction already performed by Frank;
6. treat the report as evidence requiring reproduction/causal localization, not as proof of cause;
7. preserve Frank self-Harness authority as `PROPOSAL_ONLY`;
8. only the Research Entity may implement/test/promote a Harness repair.

## Research completion expectation

A bug work item is not resolved merely because it was ingested. Completion should normally require:

- reproduction or explicit non-reproducibility result;
- causal localization with evidence;
- affected regression test(s);
- repair/reject/defer decision;
- rollback/recovery path for a promoted change;
- durable feedback/receipt linked to the bug id.

## Automatic does not mean hidden background claims

The local Clay-owned ingest process may run automatically whenever the runtime is active. A hosted ChatGPT worker that has not actually executed the ingest must not claim the bug has been ingested merely because Frank exported it.
