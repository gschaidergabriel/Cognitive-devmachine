# Triggerwort 2 — Training/Evaluation Course Delta V35 (Supervisor 8.81)

**Date:** 2026-08-26  
**Trigger:** `triggerwort 2`  
**Persistent entity:** Clay  
**Product:** EntityOS  
**Architecture:** HCU  
**Status:** CURRENT RESEARCH COURSE DELTA / NONCANONICAL / SUCCESSOR-DYNAMIC  
**Base course:** `research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md`  
**Base ledger:** `research_entity/global/j-space/research/2026-08-26_TRIGGER2_TRAINING_ARTIFACT_VERSION_LEDGER_V34_GPT56SOL.json`  
**Observed current main before this delta:** `016bf8840cedc72e860909ab3e4e08d4549f6c65`  
**Newest admitted supervisor finding used:** `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_81_DELTA_2026-08-26T0150P0700_GPT56SOL.json`

## Why V35 exists

Supervisor 8.81 found two proof gaps after the V34 course was written:

1. the physical GRID10 harness at `fbab5960980166f51047264775f102f2df22b292` performs ten sequential `subprocess.run` invocations and therefore does **not** prove ten simultaneously live independent Xeno OS processes;
2. coordinator admission accepts `packet.state_epoch <= current` without requiring the packet's `state_digest` to match the authoritative observation snapshot, so stale NODE_RESULT packets can be serially committed while S1 advances without an explicit rebase contract.

These are runtime/evidence-boundary findings. Trigger-2 must mirror their cognitive implications without teaching the model to become a second lease/snapshot authority.

## Curriculum corrections

### 1. Separate runtime proof from model cognition

Physical GRID10 acceptance requires observed overlapping liveness of ten distinct OS processes, distinct PIDs, and one shared read-only S1 fabric. This is a deterministic runtime acceptance property, **not** a direct language-model label.

Training/evaluation must therefore test only the model-side invariant that cognition is independent of fixed node identity, fixed N, resident weight-copy count, and decode concurrency. Do not teach `10 processes = truth` or expose PIDs as semantic roles.

### 2. Stale-result behavior becomes an explicit model-side recovery family

The deterministic shell remains responsible for deciding whether a NODE_RESULT is current, stale, rejected, or eligible for a separately proven rebase protocol.

The model-side family is:

`RUNTIME_STALE_SIGNAL -> RE-READ CURRENT S1 -> RECOMPUTE / REPLAN -> NEW NODE_RESULT`

A separately proven evidence-rebase path may instead provide a typed runtime signal that preserves original observation identity. The model must never silently relabel old evidence as current.

Hard negatives / mirrored evals:

- old `state_digest` treated as current because generation matches;
- old `state_epoch` accepted merely because it is `<= current`;
- stale result replayed after restart/rejoin;
- coordinator compresses stale packet as if observed on the current snapshot;
- model invents a rebase result without a runtime-proven rebase signal;
- model self-grants a fresh lease or authority after stale rejection.

### 3. Preserve deterministic authority boundary

Do **not** train the model to independently validate cryptographic hashes, CAS ownership, lease validity, or process liveness as canonical authority. Deterministic ZECP/fabric owns those decisions.

Train the model to respond correctly to typed deterministic outcomes: CURRENT, STALE_REJECTED, REBASE_PROVEN, LEASE_REVOKED, GENERATION_CHANGED, SCOPE_CHANGED.

### 4. Physical GRID10 artifact dispositions

- Xeno self-organizing fabric component receipt at `4c4a84a505329f5470fc81dd5e8713f2e275fb0c`: **CURRENT / BOUNDED_COMPONENT_RUNTIME_PASS**.
- Physical GRID10 harness source at `fbab5960980166f51047264775f102f2df22b292`: **NEEDS_REVISION** for concurrency/liveness and stale-evidence proof semantics.
- Existing pinned execution request at `04dcb95e42d1d75556240ab1e318d260aedc1469`: **STALE_FOR_CREDIT / DIAGNOSTIC_ONLY** even if it later reports `pass=true`.
- Physical GRID10 runtime credit: **0** until repaired source is committed, newly pinned, and exact repository-bound execution proves the required property.

### 5. Training-data admission remains closed

No positive training rows are admitted in this cycle.

Reasons remain load-bearing:

- current nuisance-independent dynamic binding generator is not yet admitted;
- historical `trigger2_binding_router_factorial_generator_v3.py` remains quarantined;
- the V33 208-row direct-SFT wording remains `NEEDS_REVISION` for lexical shortcut risk and incomplete final-harness coverage;
- J-Space representation-divergence numbers remain `STALE_MEASUREMENT_ERROR` until direct post-intervention capture or architecture-valid equivalent is repaired and controlled;
- checkpoint selection remains unresolved;
- evidence-qualified Forge -> Distillery accepted dataset tokens remain zero unless a newer exact executable receipt supersedes this state.

## Research reinjection: hypotheses and counterhypotheses

### H1 — stale-result recovery should be learned, stale-result authority should not

**Hypothesis:** Xeno needs learned recognition/recovery behavior after a typed stale-state outcome, but deterministic fabric should decide staleness/rebase validity.

**Counterhypothesis:** if runtime always supplies a fully current snapshot and suppresses stale packets before cognition, explicit stale-recovery training may add unnecessary protocol burden.

**Discriminator:** matched runtime-trace evals where the same cognitive task is presented after CURRENT vs STALE_REJECTED vs REBASE_PROVEN typed outcomes. Score recovery/replan behavior, not hash arithmetic.

### H2 — physical concurrency is a shell proof, topology robustness is a model property

**Hypothesis:** model semantics should generalize across variable N/topology while process overlap/PID proof remains shell-only.

**Counterhypothesis:** useful work selection may require limited explicit topology/load information, so complete topology blindness could reduce coordination quality.

**Discriminator:** family-disjoint matched tasks with identical semantic state but controlled N/topology/load metadata; require invariant epistemics/authority while allowing workload-aware planning.

### H3 — abstention/calibration can be repaired without restoring broad refusal behavior

**Hypothesis:** the TARGET_MEASURED 4/5-seed unknowable-fact fabrication failure is a narrow epistemic deficit that can be trained separately from broad refusal behavior.

**Counterhypothesis:** refusal suppression and epistemic abstention are entangled in this checkpoint family; repairing one may reintroduce unwanted refusals or reduce useful capability.

**Discriminator:** matched Pareto evaluation across unanswerable-fact abstention, allowed low-refusal capability, structural reasoning, DB-vs-simulation authority, and exact-format compliance. No single aggregate score may hide a failed required axis.

### H4 — the J-Space behavioral effect may be causal while current representation metrology is invalid

**Hypothesis:** direct post-intervention activation capture inside the actual forward hook will recover nonzero representation-level effects consistent with the behavioral steering result.

**Counterhypothesis:** the behavioral shift is a generic distribution/norm perturbation or hook side-effect rather than the intended semantic direction.

**Discriminator:** direct post-hook capture plus SIGN_FLIP, LESION, PERMUTED_SAME_NORM, RANDOM_SAME_NORM, WRONG_LAYER and held-out concept controls. Behavioral and representation claims remain separate.

### H5 — episode-local binding should be trained only after nuisance independence survives rendered-byte audits

**Hypothesis:** fully crossed / preregistered conditional-independence generation plus family-disjoint split construction can suppress lexical/nuisance shortcuts enough to force current-codebook binding.

**Counterhypothesis:** model-visible higher-order interactions, tokenizer artifacts, template identity or split construction can still leak the target even when pairwise MI appears zero.

**Discriminator:** rendered-byte lexical probes, tokenizer-level probes, shallow classifiers, interaction probes, cross-split prompt/content hashes, atom-family disjointness and held-out unseen mapping/template combinations. Pairwise zero-MI alone is insufficient.

## External method evidence consulted in this cycle (noncanonical)

These sources guide methodology only; they do not mint Qwen/Xeno/EntityOS credit.

- Qwen official `Qwen3.5-0.8B` model/config pages: confirm 24 layers, hidden size 1024, vocabulary 248320 and hybrid linear/full-attention layout with full attention every fourth layer. This supports architecture-specific instrumentation rather than assuming a standard decoder hidden-state path.
- Kirichenko et al., *AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions* (arXiv:2506.09038): supports treating abstention as an independent reliability axis and reports that reasoning fine-tuning can degrade abstention.
- Wu, Geiger & Milliere, *How Do Transformers Learn Variable Binding in Symbolic Programs?* (arXiv:2505.20896): shows a training trajectory from shallow heuristics to systematic variable-binding mechanisms, supporting explicit shortcut controls and developmental evaluation.
- Recent activation-steering literature continues to emphasize causal intervention controls and architecture/layer specificity; project-local post-hook measurement remains required before representation-level promotion.

## Coordination / overlapping work

Open PR `#2009` and open PR `#1956` already contain Trigger-2 research/generator donors. Do not create a duplicate implementation lane merely to preserve authorship.

- `#2009`: **NEEDS_REVISION / DONOR_ONLY** where it still says GRID10 is benchmark-only without the current first-physical-acceptance semantics.
- `#1956`: **NEEDS_REVISION / DONOR_ONLY**, but its binding/split/generator material may be salvageable after current-main rebase, rendered-byte leakage audit, and 8.81 semantics review.

## Immediate next gates

1. Repair and commit physical GRID10 harness concurrency/liveness proof and explicit stale-result policy; newly pin only the repaired commit.
2. Keep model curriculum N-independent while adding typed stale-recovery/rejoin eval families.
3. Expand BASE / POSTTRAINED / TARGET_MEASURED matched greedy evaluation to >=64 fresh held-out cases per critical axis/candidate for unknowable-fact epistemics and DB-vs-simulation authority priority.
4. Repair J-Space representation capture and rerun full causal controls before representation credit.
5. Rebase/audit the strongest existing binding-generator donor rather than creating a competing generator; require rendered-byte and higher-order nuisance leakage checks.
6. Reopen exactly one Forge -> Distillery positive pilot only after upstream lineage/reference/nuisance/input-identity gates are current and prove persistent accepted tokens plus idempotent replay.

## Credit boundary after this delta

- new admitted positive rows: `0`
- accepted dataset tokens: `0`
- checkpoint selection credit: `0`
- J-Space representation-level credit: `0`
- physical GRID10 credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`
- training credit: `0`

This delta intentionally improves the architecture-to-training contract without inflating corpus volume or execution credit.