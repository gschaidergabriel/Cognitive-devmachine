# GO Unusual-Experiment Atomic Lease Protocol

**Status:** CURRENT  
**Scope:** every exact user-triggered `go` macro-cycle across all parallel Clay workers/organs.  
**Purpose:** enforce the owner law that exactly one bounded unusual experiment may be consumed per user-triggered `go` macro-cycle.

## 1. Why this exists

A read-then-act check is not sufficient under parallel workers. Two workers can both observe an apparently free experiment slot and start different interventions before either writes a receipt.

Therefore the experiment budget is a **shared atomic lease**, not a local counter or prose convention.

## 2. Trigger key

Before any unusual experiment, resolve one deterministic `trigger_key` for the exact user `go` request.

Preferred key material, in order:
1. immutable orchestration/request/conversation-turn identifier when exposed;
2. exact user-message timestamp plus a hash of the literal trigger payload;
3. another immutable coordinator-provided request identity that every worker on the same user turn can reproduce.

The key must identify the user turn, not a worker join time or a later GitHub head.

If workers cannot derive the same exact trigger key with high confidence, the unusual-experiment slot is **COORDINATION_BLOCKED** and no unusual experiment may run. Deterministic regressions, source review, ordinary tests and already-consumed identical-intervention replication may continue.

## 3. Atomic claim

The one lease path is:

`research_entity/continuity/go_experiment_claims/<trigger_key>.json`

The worker proposing the unusual experiment MUST attempt a GitHub create-only write for that exact path before executing the intervention.

Required claim fields:
- `schema`: `clay-go-experiment-claim/v1`
- `trigger_key`
- `trigger`: `go`
- `experiment_name`
- `claimant_organ`
- `claimed_at`
- `observed_canonical_main`
- `intervention_contract`
- `status`: `CLAIMED`

Create-only semantics are mandatory. Never overwrite or delete an existing claim to acquire the slot.

### Claim result

- create succeeds: this worker owns the one unusual-experiment lease for that user turn;
- path already exists / create conflicts: slot is already owned; read the existing claim and do not start a different unusual experiment;
- GitHub write/identity unavailable or uncertain: fail closed; do not run an unusual experiment.

This is the concurrency primitive. A prior non-atomic search for claims is advisory only and never authorizes execution.

## 4. Execution ownership

Only the successful claimant may initiate the unusual intervention.

Other workers may:
- inspect its claim/result;
- do ordinary deterministic tests and regressions;
- perform source review and fusion;
- rerun the exact already-consumed intervention only when explicitly classified as replication/regression and when that does not create a materially different intervention.

Other workers may NOT rename a different intervention as a regression or consume a second unusual slot.

## 5. Result record

After the claimed experiment executes or becomes blocked, the claimant creates:

`research_entity/continuity/go_experiment_claims/<trigger_key>.result.json`

with:
- claim path/hash;
- exact experiment name and intervention identity;
- source/artifact/environment identity;
- execution surface;
- observed result;
- PASS/FAIL/BLOCKED classification;
- whether whole-product evidence is established (normally false for a bounded discriminator);
- durable receipt references.

The result file is also create-once. Corrections are separate append-only receipts; never rewrite history to hide negative evidence.

## 6. Macro-cycle closure

Every substantive `go` receipt must reference either:
- the successful atomic claim + result, or
- `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT` if no safe shared trigger key/write surface existed.

If evidence shows that multiple distinct unusual experiments ran for the same trigger key, classify it as `EXPERIMENT_BUDGET_RACE_VIOLATION`, preserve every result, stop all further unusual experiments for that macro-cycle, and repair coordination before relying on the experiment-count invariant again.

## 7. Current 2026-08-17 incident

The `go` user turn around 2026-08-17 13:20 +07 exposed the failure mode this protocol addresses: parallel lanes recorded distinct unusual experiments while each believed it held the 1/1 budget. Existing evidence must be preserved; it must not be rewritten into a fictitious single execution.

For that already-running macro-cycle, the slot is considered CLOSED and no new distinct unusual experiment is authorized. The canonical product/research receipts must describe the race transparently.

## 8. Product-boundary note

This protocol is research/execution coordination substrate, not a second ClayVerse product authority. It exists to preserve the integrity of evidence used to converge `main/the artefact/` toward the one ClayVerse OCI container. It never overrides owner directives, UnifiedDB product authority, or exact isolated runtime evidence.
