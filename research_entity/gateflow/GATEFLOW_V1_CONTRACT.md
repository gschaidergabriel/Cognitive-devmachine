# CLAY GATEFLOW v1

Status: ACTIVE_CONTROL_PLANE
Scope: Clay research/program coordination only. GateFlow does not modify Frank's Harness, cognition, effect authority, owner-fixed acceptance semantics, or training authorization.

## Purpose

GateFlow regulates the conversion of swarm work into accepted Frank v0.1 gate credit without suppressing adversarial research. It optimizes critical-path flow, not raw token, commit, branch, or PR production.

## Primary objectives

Every aggregate GateFlow objective/dashboard MUST carry all three:

1. `accepted_gate_weight_delta_per_1m_tokens`
2. `accepted_gate_weight_delta_per_worker_hour`
3. `risk_retired_per_1m_tokens`

`risk_retired_per_1m_tokens` is a mandatory anti-Goodhart metric. Removing it invalidates the aggregate optimization surface.

## Risk Retired semantics

Risk credit exists only for a concrete Frank v0.1 failure domain tied to a gate/subcheck and evidence.

A risk can contribute in two ways:

- `PROMOTION_BLOCKED`: executable evidence prevents an unsafe/invalid candidate from entering the accepted path. The residual design risk remains open, so only partial credit is given.
- `RETIRED`: the evidenced failure domain has a verified repair/mitigation at the claimed evidence class and `residual_open=false`. Full credit is given.

Default deterministic weights:

- severity: `P0=8`, `P1=5`, `P2=3`, `P3=1`
- evidence: `TARGET_VPS=1.0`, `EXACT_CURRENT_CI=0.8`, `LOCAL_EXECUTABLE=0.5`, `MECHANISM_ONLY=0.25`, `THEORETICAL=0.0`
- disposition: `RETIRED=1.0`, `PROMOTION_BLOCKED=0.6`, `OPEN=0.0`

`risk_retired_units = severity_weight * evidence_weight * disposition_weight`

This intentionally rewards strong negative evidence before gate credit moves, while retaining a distinction between containment and full retirement.

### No double counting

A `unique_failure_domain` is the accounting identity. Two risk IDs may not claim the same failure domain. Reproductions improve confidence/evidence class but do not multiply units. When a blocked risk is later repaired, update the same risk event/disposition instead of appending a second credited event.

## Work classes

Every new run SHOULD declare one class before execution:

- `PROMOTION`: fresh-main replay, adjudication, receipt materialization, workspace-credit proposal.
- `IMPLEMENTATION`: minimal repair/build tied to one declared gate/subcheck and lease scope.
- `FALSIFICATION`: bounded adversarial test of the active candidate or promotion invariant.
- `EXPLORATION`: hypothesis discovery not yet tied to a promotion-ready surface.

Runs missing gate/subcheck/candidate/decision-test/expected-receipt/dependency-cone metadata remain valid research but do not receive promotion priority until mapped.

Exploration is never globally banned. Under promotion pressure GateFlow preserves a falsification reserve so the swarm cannot maximize easy gate closures by avoiding difficult counterexamples.

Initial calibration allocation under promotion pressure:

- 60-65% promotion/fresh-main/receipt closure
- 20-25% active repair + falsification
- ~10% next critical-path substrate
- ~5% free exploration

These are calibration targets, not owner-fixed product law.

## Semantic frontier leases

WIP is limited per **semantic lease scope**, not globally per work package/subcheck.

A subcheck may contain multiple independent failure domains or semantic surfaces. Each declared `lease_scope` may have at most:

- one `IMPLEMENTATION_OWNER`
- one `FALSIFIER`
- one `PROMOTION_OWNER`

A second worker entering the same lease scope MUST choose `JOIN`, `COUNTERTEST`, `SUPERSEDE`, or `WAIT` instead of silently creating a competing implementation.

Each lease binds at minimum:

- work package + subcheck
- stable lease-scope ID
- semantic surface/failure domain
- target repo/PR/branch/head/base identities when available
- dependency cone
- owner role(s)
- freshness/state
- next required event

Leases coordinate Clay work only and mint no Frank runtime authority.

## Promotion state machine

Normal path:

`DISCOVERED -> REPRODUCED -> REPAIR_CANDIDATE -> LOCAL_VERIFIED -> TARGET_VERIFIED -> FRESH_MAIN_VERIFIED -> INTEGRATION_VERIFIED -> RECEIPT_READY -> ADMITTED -> WORKSPACE_CREDITED`

Side states:

`NEGATIVE_EVIDENCE`, `INFRA_FAILURE`, `HARNESS_FAILURE`, `STALE_BASE`, `DUPLICATE`, `SUPERSEDED`, `BLOCKED_EXTERNAL`.

Only `WORKSPACE_CREDITED` contributes accepted gate weight. A `RED` freshness item cannot be receipt-ready/admitted/credited.

## Receipt-first admission contract

Gate-directed runs SHOULD declare before execution:

- `work_package`
- `subcheck`
- `lease_scope`
- `candidate_identity` (repo, base SHA, head SHA, artifact hashes when available)
- `decision_test`
- `expected_receipt`
- `dependency_cone`

## Conservative diff -> gate mapping

`GATEFLOW_V1_RULES.json` provides conservative path-to-gate candidate mapping. A path match means a gate/subcheck needs review/evidence; it never grants PASS. The mapper outputs affected surfaces and missing-evidence templates so workers can decide whether to join an existing lease or open a new independent scope.

## Freshness / dependency cones

Freshness is semantic, not merely branch age:

- `GREEN`: current-main changes are outside the relevant dependency cone or exact-current validation already covers them.
- `AMBER`: relevant dependency changed; rerun cheap exact-source/local checks before scarce target scheduling.
- `RED`: contract/schema/authority/runtime dependency changed; stop promotion/target scheduling until rebased/re-adjudicated.

## Promotion train

Target-VPS validation is a scarce serialized resource. GateFlow SHOULD:

1. run cheap/static/exact-source checks first;
2. select only promotion-ready, fresh candidates;
3. batch non-conflicting dependency cones against a fresh-main snapshot;
4. preserve exact SHA/blob/run binding per candidate;
5. immediately classify result -> promotion/negative/infra/stale;
6. materialize receipt/admission proposal before starting broad new work in the same scope.

## WIP and stop-the-line

When accepted gate delta remains zero while candidate/evidence arrival is high, GateFlow enters `PROMOTION_PRESSURE` and limits new implementation WIP.

Stop-the-line overrides throughput optimization for:

- P0/P1 safety/identity counterexamples
- stale/forgeable runtime authority
- rollback/recovery resurrection
- ambiguous current-source provenance
- invalid terminal receipt claims

## Required dashboard

At minimum:

- generated repo text tokens (exact when available; proxy explicitly labeled)
- gate-relevant tokens
- machine-verifiable/testable surface
- accepted gate weight delta
- accepted gate weight / 1M tokens
- accepted gate weight / worker-hour
- risk retired units, split into fully-retired and promotion-block contributions
- **risk retired / 1M tokens**
- evidence-to-admission latency
- promotion conversion rate
- stale evidence rate
- duplicate/superseded ratio
- target queue yield
- median WIP age
- fresh-main survival rate
- E2E causal-chain coverage

## Non-authority boundary

GateFlow proposes and records coordination/promotion state. It MUST NOT silently increment Frank v0.1 workspace progress, mutate Frank's Harness, authorize training, mint effect authority, or claim terminal acceptance. Workspace promotion remains an explicit adjudicated program write under the owner-fixed finished contract.
