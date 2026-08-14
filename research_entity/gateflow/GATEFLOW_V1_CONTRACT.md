# CLAY GATEFLOW v1

Status: ACTIVE_CONTROL_PLANE_CANDIDATE  
Revision: 1.1  
Scope: Clay research/program coordination only. This contract does not modify Frank's Harness, cognition, effect authority, or owner-fixed acceptance semantics.

## Purpose

GateFlow regulates the conversion of swarm work into accepted Frank v0.1 gate credit without suppressing adversarial research. It optimizes flow through the critical path, not raw token or commit production.

## Primary objectives

GateFlow MUST optimize two product-throughput metrics and one anti-Goodhart safety metric together:

1. `accepted_gate_weight_delta_per_1m_tokens`
2. `accepted_gate_weight_delta_per_worker_hour`
3. `risk_retired_per_1m_tokens`

The third metric is mandatory. No policy, dashboard, scheduler, or worker objective may omit it when ranking aggregate swarm performance.

### Risk retired

A risk event is creditable only when it is tied to a concrete Frank v0.1 gate/subcheck and has evidence that either:

- falsifies a promotion claim and causes the candidate to be blocked/superseded/fail-closed; or
- verifies a repair that removes the previously evidenced failure mode on the required evidence class.

Risk credit is evidence-weighted and severity-weighted. The default deterministic weights are:

- severity: `P0=8`, `P1=5`, `P2=3`, `P3=1`
- evidence: `TARGET_VPS=1.0`, `EXACT_CURRENT_CI=0.8`, `LOCAL_EXECUTABLE=0.5`, `MECHANISM_ONLY=0.25`, `THEORETICAL=0.0`
- disposition: `RETIRED=1.0`, `PROMOTION_BLOCKED=0.6`, `OPEN=0.0`

`risk_retired_units = severity_weight * evidence_weight * disposition_weight`

The numerator is the sum of unique risk-event units. Duplicate reproductions of the same risk do not multiply credit unless they retire a distinct failure domain. A repaired risk may receive the remaining credit up to the severity/evidence ceiling, but cannot be double-counted beyond that ceiling.

This metric is deliberately separate from gate weight. Finding a severe target-VPS counterexample can therefore improve swarm value even when accepted gate weight remains unchanged.

## Work classes

Every new run MUST declare one class:

- `PROMOTION`: adjudication, fresh-main replay, receipt materialization, workspace-credit proposal.
- `IMPLEMENTATION`: minimal gate-directed repair/build tied to one declared subcheck.
- `FALSIFICATION`: bounded adversarial test of the active owner/candidate or a promotion invariant.
- `EXPLORATION`: hypothesis discovery not yet tied to a promotion-ready subcheck.

Exploration is never banned globally. Under promotion backlog pressure, GateFlow reserves a falsification budget so the system cannot optimize itself into easy-gate Goodhart behavior.

Default backlog-pressure allocation target (initial calibration only):

- 60-65% promotion/fresh-main/receipt closure
- 20-25% active blocker repair and falsification
- ~10% next critical-path substrate
- ~5% free exploration

These are calibration targets, not owner-fixed law. Measured flow data may change them.

## Semantic frontier leases

A subcheck may have at most:

- one `IMPLEMENTATION_OWNER`
- one `FALSIFIER`
- one `PROMOTION_OWNER`

A worker entering an occupied semantic surface MUST choose `JOIN`, `COUNTERTEST`, `SUPERSEDE`, or `WAIT` before creating a new implementation lane.

Each lease binds:

- Frank work package and subcheck
- semantic surface
- target repository/PR/head SHA
- base SHA
- dependency-cone identifiers
- role
- status
- next required event
- expiry/refresh timestamp

Leases coordinate work; they do not grant Frank runtime authority.

## Promotion state machine

Normal states:

`DISCOVERED -> REPRODUCED -> REPAIR_CANDIDATE -> LOCAL_VERIFIED -> TARGET_VERIFIED -> FRESH_MAIN_VERIFIED -> INTEGRATION_VERIFIED -> PRODUCT_MAIN_MERGED -> RECEIPT_READY -> ADMITTED -> WORKSPACE_CREDITED`

Side states:

`NEGATIVE_EVIDENCE`, `INFRA_FAILURE`, `HARNESS_FAILURE`, `STALE_BASE`, `DUPLICATE`, `SUPERSEDED`, `BLOCKED_EXTERNAL`.

`PRODUCT_MAIN_MERGED` is deliberately separate from `WORKSPACE_CREDITED`. A real repair may be on the target repository's `main` and still contribute zero formal Frank-v0.1 gate weight until the required exact-current receipt is adjudicated and the canonical workspace explicitly records that credit.

Only `WORKSPACE_CREDITED` contributes accepted gate weight. Negative evidence contributes risk-retired value when it meets the risk rules above.

## Receipt-first admission contract

Gate-directed runs SHOULD declare before execution:

- `work_package`
- `subcheck`
- `candidate_identity` (repo, base SHA, head SHA, relevant artifact hashes when available)
- `decision_test`
- `expected_receipt`
- `dependency_cone`

Runs missing these fields may still be scientifically useful, but are classified as exploration until mapped and adjudicated.

## Freshness / dependency cone

Freshness is semantic, not merely branch age.

- `GREEN`: main changed outside the declared dependency cone.
- `AMBER`: relevant dependency changed; rerun cheap exact-source/local checks before target scheduling.
- `RED`: contract/schema/authority/runtime dependency changed; target scheduling or promotion must stop until rebased/re-adjudicated.

A candidate may not become `RECEIPT_READY`, `ADMITTED`, or `WORKSPACE_CREDITED` while `RED`.

## Promotion train

Target-VPS jobs are treated as a scarce serialized validation resource. GateFlow SHOULD batch only promotion-ready candidates with non-conflicting dependency cones against a fresh-main snapshot. Cheap/static/exact-source checks run before Target-VPS scheduling. Every Target result remains bound to exact SHA/artifact identity.

## Conversion telemetry — v1.1

GateFlow v1.1 makes the research-to-product path measurable instead of inferring it from commit volume.

A conversion event may record stage timestamps and exact source references. Machine checks enforce:

- stage timestamps may not move backward;
- a `PRODUCT_MAIN_MERGED` or later event must carry the exact product-main SHA;
- a `RECEIPT_READY` or later event must carry the receipt reference;
- a `WORKSPACE_CREDITED` event must carry both the workspace-credit reference and positive credited weight;
- an observed later stage may not coexist with an earlier declared `current_stage`;
- incomplete observation windows may report observed fractions but MUST NOT report population conversion rates.

The current conversion window is stored separately from the durable GateFlow frontier so rapid product movement can be measured without rewriting owner-fixed program state.

`observed_conversion_pipeline_depth_index` is a process-flow diagnostic only. It is NOT Frank product progress, technical completion percentage, or DOOMSDAY probability.

## Formal progress versus technical/process evidence

GateFlow MUST keep three notions separate:

1. `formal workspace credit`: only adjudicated `WORKSPACE_CREDITED` weight;
2. `conversion/process depth`: where observed evidence currently sits in the research -> target -> main -> receipt -> workspace pipeline;
3. `risk retired`: evidence-weighted removal/blocking of concrete failure modes.

No composite may silently collapse these into one "percent complete" number.

## Critical-path scheduling — v1.1

`research_entity/gateflow/CRITICAL_PATH_V1.json` materializes a coordination-only dependency-wave view derived from the current Frank v0.1 contract.

The waves prioritize scarce promotion/Target-VPS capacity; they do not ban parallel later-wave research. Earlier-wave P0/P1, identity, authority, recovery or dependency-cone blockers outrank raw novelty. Under promotion pressure, workers should prefer rebase/adjudication/receipt/workspace re-entry over spawning semantically duplicate implementations.

## WIP and stop-the-line rules

When accepted gate delta is zero while candidate/evidence arrival remains high, GateFlow enters `PROMOTION_PRESSURE` rather than spawning additional broad implementation lanes.

Stop-the-line overrides throughput optimization for:

- P0/P1 safety or identity counterexamples
- evidence of stale/forgeable runtime authority
- recovery/rollback resurrection
- ambiguous current-source provenance
- invalid terminal receipt claims

## Required dashboard

At minimum:

- generated repo text tokens (exact when available, proxy explicitly labeled otherwise)
- gate-relevant tokens
- machine-verifiable/testable surface
- accepted gate weight delta
- accepted gate weight / 1M tokens
- accepted gate weight / worker-hour
- risk retired units
- risk retired / 1M tokens
- observed conversion pipeline depth, explicitly labelled non-product-progress
- target-verified -> product-main merge latency
- product-main merge -> workspace-credit latency
- evidence-to-admission latency
- promotion conversion rate only for a complete population window
- stale evidence rate
- duplicate/superseded work ratio
- target queue yield
- median WIP age
- fresh-main survival rate
- workspace staleness relative to observed product-main head
- E2E causal-chain coverage

## Non-authority boundary

GateFlow proposes and records promotion state. It MUST NOT silently increment Frank v0.1 workspace progress, mutate Frank's Harness, authorize training, mint effect authority, or claim terminal acceptance. Workspace changes remain explicit adjudicated program writes under the existing owner-fixed contract.
