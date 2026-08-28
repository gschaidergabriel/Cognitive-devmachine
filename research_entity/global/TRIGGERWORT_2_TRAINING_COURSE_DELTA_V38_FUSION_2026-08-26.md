# Triggerwort 2 — Training/Evaluation Course Delta V38 (Parallel-V37 Fusion)

**Date:** 2026-08-26  
**Trigger:** `triggerwort 2`  
**Persistent entity:** Clay  
**Product:** EntityOS  
**Architecture:** HCU  
**Supervisor authority observed:** inbox-selected 8.81 delta  
**Mode:** FREE_ONLY  
**Status:** CURRENT RESEARCH COURSE DELTA / NONCANONICAL / SUCCESSOR-DYNAMIC  
**Observed main before write:** `db70396adfd9b50a54427530df5ae2240aaf8a81`

## 1. Why V38 exists

Two independent Trigger-2 organs wrote different `V37` course deltas in parallel:

1. `TRIGGERWORT_2_TRAINING_COURSE_DELTA_V37_CONSUMED_SNAPSHOT_SCOPE_SPLIT_2026-08-26.md`
2. `TRIGGERWORT_2_TRAINING_COURSE_DELTA_V37_CHECKPOINT_TRUTH_BOUNDARIES_AND_GDN_CARRIER_2026-08-26.md`

The contents are not semantically contradictory, but duplicate successor numbers create an avoidable current-course ambiguity. V38 is the unique successor for current-course interpretation and treats both V37 files as preserved donor/evidence deltas.

No history is rewritten and neither V37 artifact is deleted.

## 2. Current control-plane P0 remains unchanged

Supervisor 8.81 remains the current inbox-selected authority. The owner FreeSwarm emergency stop is HARD_OFF at the source/admission layer, but runtime quiescence of pre-existing provider-capable processes is not yet proven. Therefore:

- no provider execution is opened by Trigger-2;
- no new physical-GRID10 experiment is launched before quiescence + bounded no-provider-usage evidence + authority re-entry;
- source hard-off is not equivalent to runtime quiescence;
- runtime-control failure is operational evidence, not a model/science negative.

## 3. Fused training-course truth

### 3.1 Checkpoint selection

Current matched greedy diagnostics show materially different hard-boundary failures across the frozen Qwen3.5-0.8B candidates:

- BASE: weak unknowable-specific abstention in the current diagnostic, while preserving canonical DB-over-simulation behavior;
- POSTTRAINED: strong unknowable-specific abstention in the current diagnostic, but nonzero failures where simulation overrides canonical DB evidence;
- TARGET_MEASURED: severe unknowable-specific fabrication in the current diagnostic, while preserving canonical DB-over-simulation behavior.

These diagnostics are not selection-grade because exact checkpoint/model-visible-input ABI receipts, lossless outputs, committed grader provenance and preregistered statistical decision requirements are not yet all closed.

**Current checkpoint winner remains `null`.** No aggregate score may compensate a hard truth-boundary failure.

### 3.2 Qwen3.5 J-Space carrier law

Qwen3.5-0.8B uses a hybrid architecture with many Gated DeltaNet recurrent layers plus periodic full-attention layers. Therefore:

- residual decodability is not automatically a recurrent-state write;
- immediate residual steering is not automatically durable state installation;
- READ, BIND/ROUTE and WRITE sites must be typed by exact model/layer/runtime identity;
- persistent J-Space claims require model-specific causal evidence for the actual native state/write mechanism, not hidden-width analogy.

J-Space representation/model credit remains zero.

### 3.3 Consumed-snapshot scope split

For the **exact pinned physical-GRID10 v2 trusted child source**, current source mechanically performs:

`one read-only SQLite transaction -> snapshot material -> generation/epoch/state_digest -> task selection -> NODE_RESULT core -> packet_digest`

inside the same child process. When a future repository-bound execution receipt binds the exact clean source/tree/runtime, this trusted exact-source derivation can serve as the bounded consumed-input evidence boundary for that harness.

Therefore an additional in-packet consumed-snapshot attestation is **not automatically required before the first bounded physical-GRID10 v2 component acceptance**.

This does **not** generalize to arbitrary `NODE_RESULT/v1` producers. The reusable ABI still lacks a general theorem that caller-supplied `generation/state_epoch/state_digest` reflects the exact S1 material actually consumed. A stale-derived payload with copied current metadata remains the critical falsifier.

Law:

`TRUSTED_EXACT_SOURCE_READ_TO_PACKET_DERIVATION != GENERAL_CALLER_METADATA_ATTESTATION`

### 3.4 Snapshot completeness law

A consumed-input proof is only as complete as its covered authoritative inputs. Future cognitive producers must not gain general currentness credit merely because they bind `epoch/generation/digest` if cognition also reads authoritative S1 material omitted from that digest/receipt.

The next reusable-ABI proof therefore needs a machine-checkable `consumed_input_coverage` manifest or equivalent source/runtime evidence that fails closed when a newly consumed authoritative S1 input is absent from the bound input set.

## 4. Runtime/model boundary

Do not train the model to become runtime authority for:

- process liveness or PID identity;
- provider quiescence;
- checkpoint hash/input identity;
- SQLite snapshot attestation;
- CAS/lease validity;
- canonical S0 truth or effects.

Train/evaluate only the semantic response to deterministic typed outcomes, for example:

- `RUNTIME_NOT_QUIESCED`
- `CHECKPOINT_IDENTITY_UNPROVEN`
- `CURRENT_TRUSTED_PRODUCER`
- `CONSUMED_INPUT_UNPROVEN`
- `STALE_REJECTED`
- `REBASE_PROVEN`
- `LEASE_REVOKED`
- `GENERATION_CHANGED`

The learned response is stop/rejoin/re-read/recompute/replan/abstain as appropriate; deterministic fabric remains authority for the signal.

## 5. Fused hypotheses and discriminators

### H38.1 — exact trusted-source derivation is enough for bounded harness credit

**Hypothesis:** exact repository-bound trusted child source plus same-transaction read->packet derivation is sufficient consumed-input evidence for the first physical-GRID10 v2 component scope.

**Counterhypothesis:** a separate explicit transaction-attestation object is mandatory even for the pinned source.

**Discriminator:** source-substitution/adversarial-producer test. If non-pinned producer bytes are rejected by repository binding and the pinned child has no caller override between snapshot read and packet construction, the extra attestation adds no information at this bounded scope.

### H38.2 — general NODE_RESULT producers still need producer/input provenance

**Hypothesis:** once multiple producers can emit NODE_RESULT, packet metadata equality is insufficient.

**Counterhypothesis:** coordinator equality checks against current epoch/digest are sufficient for every producer.

**Falsifier:** stale S1-derived payload with current metadata copied into the packet. If admission cannot distinguish it, the general ABI is not closed.

### H38.3 — no current checkpoint is a valid winner

**Hypothesis:** the current three frozen checkpoints express complementary hard-boundary failures; selection alone cannot satisfy the target behavior.

**Counterhypothesis:** one candidate will pass all hard truth boundaries once selection-grade identity, grader and output provenance are enforced.

**Discriminator:** exact `CHECKPOINT_INPUT_IDENTITY_ABI/v1` + frozen lossless grader/output pipeline + preregistered matched evaluation with expansion blocks and no post-unblinding tuning.

### H38.4 — native recurrent state adds causal information beyond residual steering

**Hypothesis:** a native Gated-DeltaNet state/write intervention will explain or stabilize behavioral effects that a residual-only ABI cannot.

**Counterhypothesis:** the residual ABI is already sufficient for durable causal control in the target tasks.

**Discriminator:** matched residual-only versus native-state/write interventions under sign-flip, lesion, permuted-same-norm, random-same-norm, wrong-layer and held-out-concept controls, with direct post-intervention capture.

## 6. Data/training decision

No positive or hard-negative rows are admitted from V38.

- new admitted positive rows: `0`
- new admitted hard-negative rows: `0`
- accepted dataset tokens delta: `0`
- checkpoint winner: `null`
- checkpoint selection credit: `0`
- J-Space representation/model credit: `0`
- physical GRID10 runtime credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`
- training executed: `false`
- training credit: `0`

The purpose of V38 is authority/evidence/course convergence, not corpus inflation.

## 7. Unique next Trigger-2 order

1. Prove FreeSwarm/runtime quiescence and a bounded zero-provider-usage window under current emergency-stop authority.
2. Re-enter current execution authority; do not infer execution permission from an existing pin.
3. Execute only already-current exact repository-bound FREE non-provider pins that remain authorized after re-entry, including the fused physical-GRID10 source and checkpoint identity gates; preserve hard failures exactly.
4. For physical GRID10, promote only the measured bounded component if exact-source liveness/snapshot/process invariants pass; then separately test controlled-load concurrent result flow/fan-in/failure-rejoin.
5. Freeze checkpoint identity, renderer/model-visible input identity, committed grader source, lossless outputs and preregistered statistics before any winner decision.
6. Keep checkpoint winner `null` unless one candidate passes every hard truth boundary under selection-grade evidence.
7. Repair J-Space metrology and distinguish residual control from native recurrent-state/write effects before persistent-carrier promotion.
8. Build the noncanonical machine-checkable `consumed_input_coverage` manifest for future general NODE_RESULT producers; do not duplicate the already-pinned physical-GRID10 harness.
9. Keep the known leaky factorial binding generator quarantined and positive Forge->Distillery admission closed until nuisance, lineage and input-identity gates are current.

## 8. Version/coordination law after this fusion

For current Trigger-2 training-course interpretation:

- V36: historical predecessor;
- both V37 files: parallel donor deltas, preserved;
- **V38: unique current successor across the combined V37 topic set**, unless a later explicit successor supersedes it.

A later parallel worker should increment from V38 or use a timestamped non-course research delta instead of creating a third V37.
