# GO Unusual-Experiment Atomic Lease Protocol

**Status:** CURRENT  
**Scope:** every exact user-triggered `go` macro-cycle across all parallel Clay workers/organs.  
**Purpose:** enforce the owner law that exactly one bounded unusual experiment may be consumed per user-triggered `go` macro-cycle.

## 1. Why this exists

A read-then-act check is not sufficient under parallel workers. Two workers can both observe an apparently free experiment slot and start different interventions before either writes a receipt.

Therefore the experiment budget is a **shared atomic lease**, not a local counter or prose convention.

A create-only file is atomic only when every worker derives **the same byte-identical claim path**. Trigger-key formatting is therefore part of the concurrency primitive, not presentation metadata.

## 2. Trigger key — one canonical encoding

Before any unusual experiment, resolve one deterministic `trigger_key` for the exact user `go` request.

### 2.1 Preferred identity

Use an immutable orchestration/request/conversation-turn identifier when the platform exposes one to every worker on that same user turn.

Canonical key:

`rid_<sha256-64-lowerhex>`

where the digest input is the exact UTF-8 bytes of that immutable identifier. No prefixes, labels, worker IDs, GitHub heads, join times or shortened hashes may be added.

### 2.2 Timestamp fallback

Use the timestamp fallback only when **all** of the following are true:
- no shared immutable request/turn identifier is exposed;
- the timestamp is immutable metadata of the exact user message, not worker current time;
- the source timestamp has at least **whole-second precision** and an explicit UTC offset or `Z`;
- workers can reproduce the same timestamp and literal trigger bytes exactly.

Normalize the source timestamp to UTC and encode it as exactly:

`YYYYMMDDTHHMMSSffffffZ`

with six fractional-second digits; append `000000` only when the immutable source has whole-second precision. Then compute the full lowercase SHA-256 of the literal UTF-8 trigger payload exactly as received.

Canonical fallback key:

`ts_<YYYYMMDDTHHMMSSffffffZ>__p_<payload-sha256-64-lowerhex>`

No alternate timestamp punctuation, timezone-offset form, inserted `go` label, shortened digest, digest prefix or case variation is valid.

### 2.3 Fail-closed identity rule

If the available user-message timestamp is only minute-precision, inferred from a worker clock, or otherwise not uniquely reproducible, the unusual-experiment slot is **COORDINATION_BLOCKED** and no unusual experiment may run.

The key must identify the user turn, not a worker join time or a later GitHub head. Deterministic regressions, source review, ordinary tests and already-consumed identical-intervention replication may continue while the unusual slot is blocked.

## 3. Atomic claim

The one lease path is:

`research_entity/continuity/go_experiment_claims/<trigger_key>.json`

The worker proposing the unusual experiment MUST attempt a GitHub create-only write for that exact canonical path before executing the intervention.

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

Before executing after a successful canonical create, inspect the claims directory for legacy/noncanonical files that encode the same immutable request identity, or the same exact timestamp plus payload digest. This inspection is **not** the lock primitive; it is a migration/race fence. If such a pre-existing semantic duplicate exists, classify the macro-cycle as `EXPERIMENT_BUDGET_RACE_VIOLATION`, do not execute a new intervention, and preserve every claim.

### Claim result

- canonical create succeeds and no semantic duplicate exists: this worker owns the one unusual-experiment lease for that user turn;
- canonical path already exists / create conflicts: slot is already owned; read the existing claim and do not start a different unusual experiment;
- a legacy/noncanonical semantic duplicate exists: macro-cycle slot is closed as a race violation; run no further unusual experiment;
- GitHub write/identity unavailable or uncertain: fail closed; do not run an unusual experiment.

A prior non-atomic search for claims is advisory only and never authorizes execution.

## 4. Execution ownership

Only the successful canonical claimant may initiate the unusual intervention.

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
- the successful canonical atomic claim + result;
- `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT` if no safe shared trigger identity/write surface existed; or
- `EXPERIMENT_BUDGET_RACE_VIOLATION` plus every known conflicting claim/result when semantic duplicate claims existed.

If evidence shows that multiple distinct unusual experiments were claimed or executed for the same semantic user turn, preserve every result, stop all further unusual experiments for that macro-cycle, and repair coordination before relying on the experiment-count invariant again. Different string formatting of the same timestamp/payload or request identity does **not** create different macro-cycles.

## 7. Current 2026-08-17 incidents

### 7.1 Earlier parallel execution race

The `go` user turn around 2026-08-17 13:20 +07 exposed the original read-then-act failure mode: parallel lanes recorded distinct unusual experiments while each believed it held the 1/1 budget. Existing evidence remains preserved and the slot remains closed.

### 7.2 Trigger-key canonicalization race

The `go` user turn represented by the 2026-08-17 13:35 +07 minute metadata and literal payload `go` exposed a second failure mode after create-only claims were introduced: workers created distinct paths using different timestamp/hash formatting for the same apparent timestamp/payload identity, including full-hash and shortened-hash variants, and claimed different experiments.

This is an `EXPERIMENT_BUDGET_RACE_VIOLATION`, not two valid leases. Because the available shared timestamp metadata for this turn is only minute-precision, no additional canonical fallback claim may be minted for it. The unusual-experiment slot is CLOSED; preserve all existing claims/results and run no further distinct unusual experiment for that macro-cycle.

## 8. Product-boundary note

This protocol is research/execution coordination substrate, not a second ClayVerse product authority. It exists to preserve the integrity of evidence used to converge `main/the artefact/` toward the one ClayVerse OCI container. It never overrides owner directives, UnifiedDB product authority, or exact isolated runtime evidence.
