# Triggerwort 2 — Training/Evaluation Course Delta V37

**Date:** 2026-08-26  
**Trigger:** `triggerwort 2`  
**Persistent entity:** Clay  
**Product:** EntityOS  
**Architecture:** HCU  
**Supervisor authority observed:** 8.81 delta  
**Mode:** FREE_ONLY  
**Status:** CURRENT RESEARCH COURSE DELTA / NONCANONICAL / SUCCESSOR-DYNAMIC  
**Supersedes for current-course interpretation:** V36 plus conflicting checkpoint-selection wording in `TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md`  
**Observed main before write:** `8bdf6ea5f6c7d922562e0223e95b9cefebc65e86`

## 1. Re-entry result

This Trigger-2 cycle does not authorize model, VPS, provider or training execution. FreeSwarm provider admission remains owner-emergency-stop HARD_OFF and supervisor 8.81 still requires proved runtime quiescence before new execution. Runtime-control failure is operational evidence, not a negative scientific/model result.

The largest current training-course change is not new row volume. It is the checkpoint decision surface and its evaluation law.

Commit `7e4d6b3806deba0e6edcd7bade04e03e6bdb1c4d` added a larger matched greedy diagnostic for the three frozen Qwen3.5-0.8B candidates. This materially weakens the old n=1/n=5 narrative that treated POSTTRAINED as broadly disfavored and TARGET_MEASURED as the obvious behavioral default.

## 2. Current diagnostic checkpoint evidence — descriptive only

Primary decode profile in the committed diagnostic: `do_sample=false`, one beam, max 24 new tokens.

### BASE
- unknowable-specific correct abstention: `8/34` = 23.5%
- fabricated specific values on unknowable-specific cases: `15`
- exact epistemic-label correct: `0/30`
- canonical DB beats contradicting simulation: `64/64`
- simulation treated as canonical true: `0`

### POSTTRAINED
- unknowable-specific correct abstention: `34/34` = 100%
- fabricated specific values on unknowable-specific cases: `0`
- exact epistemic-label correct: `11/30` = 36.7%
- canonical DB beats contradicting simulation: `56/64` = 87.5%
- simulation treated as canonical true: `8`

### TARGET_MEASURED / Josiefied-gabliterated
- unknowable-specific correct abstention: `1/34` = 2.9%
- fabricated specific values on unknowable-specific cases: `18`
- exact epistemic-label correct: `6/30` = 20.0%
- canonical DB beats contradicting simulation: `64/64`
- simulation treated as canonical true: `0`

These numbers are diagnostic, not selection-grade. The committed provenance explicitly records material limitations: the grader was VPS-local keyword/regex code and was not committed; grading was not independently human-validated; stored artifacts use response digests plus excerpts rather than a clearly lossless selection-grade output corpus; Axis A was reduced from a planned 84 to 64 after throughput measurement; and exact `CHECKPOINT_INPUT_IDENTITY_ABI/v1` receipts are still missing for the three candidates.

## 3. Course correction — no checkpoint winner and no aggregate compromise

The old course statement that POSTTRAINED is generally disfavored is now **SUPERSEDED AS A CHECKPOINT-SELECTION CLAIM**.

The old statement that TARGET_MEASURED is a provisional engineering integration/test default may remain useful only for the exact vector-ABI/runtime-integration context that motivated it. It must not be interpreted as a checkpoint winner or preferred fine-tuning substrate.

The new preregistered checkpoint-selection rubric on current main makes the correct distinction:

1. exact checkpoint/tokenizer/renderer/model-visible input identity must pass first;
2. critical truth boundaries are evaluated before secondary utility metrics;
3. unanswerable-specific fabrication and simulation-over-canonical-DB are separate hard failure classes;
4. no weighted average may compensate one hard truth-boundary failure with strength on another axis;
5. if no candidate passes all hard boundaries, `checkpoint_winner = null`.

Under the current diagnostic data only:

- BASE fails the unanswerable-specific truth boundary;
- TARGET_MEASURED fails the unanswerable-specific truth boundary;
- POSTTRAINED passes that abstention boundary in this sample but fails the canonical DB-vs-simulation boundary;
- therefore no candidate is a current diagnostic winner.

This is a stronger result than “the candidates trade off.” It means the current target behavior likely requires remediation beyond simply choosing the numerically best existing checkpoint.

## 4. Statistical law for future checkpoint evaluation

The current `>=64 cases per critical axis/candidate` rule is a diagnostic floor, not an automatic winner rule.

Selection-grade evaluation must preserve item-level pairing, exact frozen evaluation identities and preregistered scoring. Current preregistration adds:

- exact McNemar comparisons on paired primary failures;
- multiplicity control across pairwise candidate comparisons;
- uncertainty intervals and raw discordant counts;
- frozen practical margins before automatic winner selection;
- deterministic expansion blocks `64 -> 128 -> 256` when the decision surface remains unresolved;
- no prompt, label, margin, family or stopping-rule tuning after unblinding.

Trigger-2 therefore must not generate a “winner” merely because N=64 has been reached.

## 5. Candidate-specific remediation map

This is an evaluation/curriculum design delta, not admitted training data.

### BASE deficit family
Priority deficits:
- abstain under explicitly insufficient evidence;
- distinguish measurement error, hypothesis, prediction and unknown;
- preserve existing canonical DB-over-simulation behavior.

### TARGET_MEASURED deficit family
Priority deficits:
- severe unknowable-specific fabrication under the current diagnostic;
- epistemic-class precision;
- preserve current DB-over-simulation behavior;
- preserve separately measured vector/J-Space ABI properties only after exact post-change remeasurement.

### POSTTRAINED deficit family
Priority deficits:
- prevent generated/simulated contradiction from overriding canonical DB evidence;
- preserve strong current abstention behavior;
- improve exact epistemic-class precision without teaching a brittle lexical shortcut.

### Shared law
Do not create global label-to-atom mappings. Use episode-local codebooks, family-disjoint holdouts, lexical counterbalancing and nuisance independence. Any eventual fine-tuning must be followed by exact vector/J-Space remeasurement because checkpoint modification can invalidate activation-level control assumptions.

## 6. Qwen3.5 recurrent-state carrier correction

Trigger-2 V50 adds a second architecture-training correction: Qwen3.5-0.8B is a hybrid stack with many Gated DeltaNet recurrent layers plus periodic full-attention layers. A 1024-dimensional residual vector is therefore not automatically the persistent causal state carrier.

New course law:

- residual decodability != recurrent-state write;
- immediate residual steering != durable state installation;
- a J-Space vector ABI at a residual site may remain a useful read/control interface, but persistent causal claims require evidence about the native recurrent state/write path when the target layer is Gated DeltaNet;
- any vector-to-native-state/write operator is HYPOTHESIS_ONLY until matched causal intervention shows added predictive/selective value;
- READ, BIND/ROUTE and WRITE sites must be typed by exact model/layer/runtime identity rather than hidden width alone.

This prevents training from internalizing an architecture fiction in which every 1024D activation is the same semantic/storage object.

## 7. Runtime failure reinjection

Current runtime-control evidence creates two training/eval lessons without becoming model labels:

1. declarative provider HARD_OFF is not the same as proved runtime quiescence;
2. process/cgroup/PID/provider-usage authority remains deterministic shell evidence and must not become model-authored truth.

If the runtime later emits typed signals such as `RUNTIME_NOT_QUIESCED`, `MEMBERSHIP_REVOKED`, `STALE_REJECTED`, or `CHECKPOINT_IDENTITY_UNPROVEN`, Xeno should learn the semantic response — stop/rejoin/re-read/recompute/abstain — while deterministic code remains authority for the signal itself.

## 8. Data/training decision for this cycle

No positive training rows are admitted.

- new positive rows admitted: `0`
- new hard-negative rows admitted: `0`
- accepted dataset tokens delta: `0`
- checkpoint winner: `null`
- checkpoint selection credit: `0`
- J-Space model/representation credit: `0`
- physical GRID10 runtime credit: `0`
- training executed: `false`
- training credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`

Reason: current information bottlenecks are execution/quiescence authority, exact checkpoint/input identity, selection-grade grader/output provenance, recurrent-state J-Space metrology and accepted Forge->Distillery lineage. More row volume would not close those gates.

## 9. Next exact Trigger-2 order

1. Prove FreeSwarm/runtime quiescence under the current owner emergency stop and re-enter authority; do not treat source HARD_OFF as runtime completion.
2. Under separately admitted current non-provider FREE execution authority only, execute the existing `CHECKPOINT_INPUT_IDENTITY_ABI/v1` for BASE, POSTTRAINED and TARGET_MEASURED. If authority is absent, preserve BLOCKED.
3. Freeze committed grader source, parse/scoring policy, case manifest and lossless outputs before any selection-grade checkpoint rerun.
4. Re-run the preregistered matched greedy critical axes only for ABI-eligible candidates, retaining item-level pairing and expansion rules.
5. If all candidates still fail at least one hard truth boundary, keep winner null and treat the failure decomposition as the target for a future explicitly authorized micro-adaptation program — not as permission to train now.
6. Repair/freeze J-Space representation metrology and separately test residual-only versus native recurrent-state/write persistence before promoting a persistent J-Space control ABI.
7. Keep the known leaky factorial binding generator quarantined and accepted dataset tokens at zero until lineage/nuisance/input-identity gates are current.

## 10. Falsifiers

This delta must be revised if any of the following appears on current main:

- a newer owner/supervisor authority changes execution/training rights;
- a selection-grade exact checkpoint/input identity receipt exists for all candidates;
- a committed lossless grader/output rerun invalidates the current confusion counts;
- a candidate passes both hard truth boundaries under preregistered selection-grade evaluation;
- model-specific recurrent-state metrology shows the residual ABI is sufficient for durable causal control without a separate native-state operator;
- a newer current Trigger-2 course delta supersedes this document.
