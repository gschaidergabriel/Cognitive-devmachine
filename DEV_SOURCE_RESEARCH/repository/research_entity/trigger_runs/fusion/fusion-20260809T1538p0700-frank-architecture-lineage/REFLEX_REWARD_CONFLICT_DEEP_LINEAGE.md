# FRANK Amygdala / Nucleus Accumbens / ACC — deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: archaeology + current target synthesis; no canonical promotion

## RRC-0 — organ cluster creation

Commit `ccebdc78f3c08013e08758c7386984cc5e70386f` (2026-03-03) introduced three explicit preconscious/value-monitor organs together with Thalamus:
- Amygdala: threat/emotion salience;
- Nucleus Accumbens (NAc): dopamine-like reward/motivation;
- ACC Monitor: conflict/error detection.

Their architectural value is not the biological naming. It is the separation of three fast computations before/around slower model cognition:
- `what is salient/risky?`
- `what changed expected value/motivation?`
- `where does self-model conflict with measured state?`

## AMY-1 — Amygdala two-stage appraisal

Frozen-head `services/amygdala.py` describes a target `<0.5 ms` pre-model path.

### Low road
Lexical/phrase scanner over hundreds of weighted patterns across six categories:
- hostile;
- identity_attack;
- manipulation;
- loss_rejection;
- system_probe;
- warmth_bond.

The historical implementation includes:
- contraction normalization;
- weighted phrase categories;
- passive-aggression/condescension patterns;
- negation/category flips;
- multilingual patterns.

### Somatic markers
Persistent learned fingerprints from confirmed emotional events:
- category;
- intensity;
- confirmation count;
- last confirmed;
- decay factor;
- extinction patterns.

### Downstream coupling
Amygdala categories map to E-PQ events and response-tone hints. Thalamus consumes Amygdala urgency as a breakthrough signal.

Current interpretation:
- lexical and learned threat/warmth scores are salience hypotheses, not truth or authority;
- direct user message remains source evidence;
- category/risk output is a typed fast observation with model/version/provenance.

## AMY-2 — identity-attack coupling risk

The historical system deliberately detected denials of FRANK's consciousness/existence and mapped them to identity-threat events.

This can be useful as interaction-state/safety classification, but the current target must not make metaphysical claims or self-preservation authority follow from this score.

Current separation:
`identity_attack detector output -> salience/affect candidate`, never `effect authority`.

## NACC-1 — initial NAc reward system

Creation commit reported 11 reward channels plus intrinsic curiosity. The later public source evolved to a larger set of named channels while its module header still described a 9-channel conceptual architecture, exposing documentation/schema drift.

Frozen-head channel definitions include historical/current names for:
- hypothesis confirmed/refuted/created;
- goal completed;
- good conversation;
- action success;
- novel thought;
- legacy entity-positive;
- Genesis accepted/authored/self-accepted;
- curiosity spark/fulfilled;
- room positive/negative;
- prediction error.

This schema history is itself important: reward-channel set changed as Entities became Rooms and Genesis was later disabled.

## NACC-2 — reward dynamics

Frozen implementation contains:
- channel-specific base magnitude;
- per-channel habituation rate and floor;
- expected reward EMA;
- reward-prediction error (RPE);
- phasic dopamine-like signal;
- tonic baseline/state;
- opponent-process accumulator;
- boredom based on repetitiveness/diversity rather than user absence;
- anhedonia protection;
- E-PQ coupling for sufficiently strong bursts/dips;
- persistent state/logging with sampled hot-path writes.

Representative constants:
- tonic baseline ~0.5;
- tonic decay toward baseline;
- RPE EMA alpha ~0.1;
- surprise amplification ~1.5;
- boredom based on low absolute RPE + low recent channel diversity;
- anhedonia threshold ~0.2 sustained ~30 min;
- opponent-process time constant ~300 s.

These are historical parameter candidates, not target invariants.

## NACC-3 — intrinsic curiosity

Creation commit added a Pankseppian SEEKING-inspired mechanism:
- sustained boredom can create a small `curiosity_spark` tonic nudge;
- `curiosity_fulfilled` rewards curiosity/hypothesis work;
- low motivation could create a small model-facing curiosity hint.

Current fused use:
- retain novelty/learning-progress/value signals as bounded goal/attention priors;
- do not let intrinsic reward self-authorize research/actions;
- reward must be outcome/source scoped to prevent self-reward loops.

## NACC-4 — major failure: inverted habituation semantics

Deep audit commit `07f8e26a...` (2026-03-13) reports:
- NAc habituation semantics were inverted;
- **9/14 channels were effectively dead**;
- fix included an automatic migration.

This is a critical regression class:
- formulas can look plausible while sign/state semantics kill most channels;
- reward channel health must be measured empirically per channel, not inferred from code presence.

Required test:
- repeated same-channel events show intended decay to floor;
- novel/sparse events retain responsiveness;
- migration from old state does not reinterpret habituation backwards.

## NACC-5 — channel diversity fix after reward collapse

Commit `290d5e2...` reports NAc channel variation changes to use actual `action_success`, `novel_thought` and `prediction_error` pathways. This indicates the earlier event graph did not exercise reward channels evenly.

Current rule:
`defined reward channel != reachable reward channel`.
Harness must establish producer reachability and actual event distribution.

## NACC-6 — stale historical channels

Entity reward channels survived into code history even after Entities were replaced with Rooms; Genesis channels survived after Genesis was later disabled.

Current architecture requires:
- channel schema version;
- deprecated aliases and migration mapping;
- reachability status;
- no stale channel silently counted in diversity/boredom calculations.

## ACC-1 — conflict monitor semantics

Frozen `services/acc_monitor.py` defines seven domain-general conflict channels:
- mood: E-PQ mood vs external/derived mood signal;
- vigilance: E-PQ vigilance vs Amygdala alert frequency;
- coherence: E-PQ precision vs QR coherence/violations;
- body: expected service topology vs actual health;
- prediction: confidence vs actual surprise;
- identity: confidence anchor vs identity-attack pressure;
- activity: active goals vs rumination.

The same conflict math is applied across channels.

Historical subdivisions:
- dACC-like cognitive channels;
- vACC-like affective/somatic channels.

## ACC-2 — adaptive conflict thresholds

Frozen behavior:
- per-channel base thresholds;
- conflict increases threshold via Gratton-like adaptation;
- no-conflict decays threshold toward baseline;
- threshold state is persisted;
- conflict salience can fire E-PQ perturbations;
- model-facing PROPRIO line may summarize dominant conflict.

Reported historical correction in `f1ea0b47...`:
- ACC cooldown changed to ~600 s, preventing chronic repeated perturbation.

Frozen source comment confirms 600 s was chosen because shorter 120 s cooldown caused chronic hypervigilance.

Current principle:
- adaptive thresholding is useful to avoid alarm fatigue;
- adaptation itself must not hide persistent real conflict;
- state/cadence/restart need explicit time semantics.

## ACC-3 — belief vs reality is only as good as source typing

Historical ACC compares E-PQ self-model to AURA/QR/service/prediction/activity signals. Several of those sources were later renamed, removed or changed (AURA -> Swarm, QR endpoints, Entities -> Rooms).

A conflict monitor can produce nonsense when one side is stale or incorrectly mapped.

Current target requires each comparison operand to carry:
- semantic role;
- source identity;
- source/basis epoch;
- uncertainty/precision;
- validity state.

Unknown or stale source does not silently become zero and create conflict.

## RRC-1 — coupling with Thalamus and E-PQ

Historical causal cluster:
```text
user/system event
 -> Amygdala salience/threat
 -> Thalamus gating/breakthrough
 -> NAc reward/value state
 -> ACC conflict monitoring over slower snapshots
 -> GWT/PROPRIO/model projection
 -> response/outcome
 -> E-PQ/reward/conflict re-entry
```

The exact order varied by path and generation, but C4 explicitly preserved Amygdala/Thalamus/NAcc as distinct fast state machines in the Reflex Kernel.

## RRC-2 — evidence-class correction

These biological names do not prove biological equivalence. Current archaeology classifies much of the naming as analogy/external inspiration plus project-specific computational coupling.

The target preserves functional state machines and tests their contribution with lesions; it does not require biological labels in the implementation.

## RRC-3 — current fused target

### Amygdala-like fast appraisal
Typed fast salience/risk/warmth/interaction-state classifier with explicit source and uncertainty.

### NAc-like value dynamics
Bounded, outcome-grounded reward/RPE/novelty/learning-progress state. Utility may tune salience/goals but cannot write truth or authority.

### ACC-like conflict monitor
Compares explicitly typed self/predicted states against current evidence with uncertainty-aware discrepancy and adaptive thresholds.

All three may be physically colocated in H3, but remain semantically separate and independently lesionable.

## Mandatory regressions

- RRC-REG-01 Amygdala high urgency suppressed by downstream Thalamus relay bug;
- RRC-REG-02 negation flips threat/warmth incorrectly;
- RRC-REG-03 learned somatic marker persists after extinction/revocation;
- RRC-REG-04 NAc habituation sign inversion;
- RRC-REG-05 reward channels defined but unreachable/dead;
- RRC-REG-06 deprecated Entity/Genesis channels distort diversity/boredom;
- RRC-REG-07 self-generated event rewards itself without external/outcome evidence;
- RRC-REG-08 ACC stale/renamed source becomes artificial conflict;
- RRC-REG-09 ACC short cooldown produces chronic E-PQ hypervigilance;
- RRC-REG-10 adaptive conflict threshold rises until true persistent conflict is hidden;
- RRC-REG-11 crash/restart preserves time constants/threshold state correctly;
- RRC-REG-12 H1/H2/H3 lesion equivalence for each organ.

## Fusion decision

- Amygdala: `REUSE_FAST_APPRAISAL_SEMANTICS; RETEST_LEXICAL/LEARNED_ALGORITHM; NO_TRUTH_OR_AUTHORITY`.
- NAc: `REUSE_RPE_VALUE_HOMEOSTASIS_SEMANTICS; RETEST_CHANNELS/PARAMETERS; OUTCOME_SCOPED_CREDIT_ONLY`.
- ACC: `REUSE_CONFLICT_MONITORING_CONCEPT; ADAPT_TO_TYPED_SOURCE_EPOCHS_AND_UNCERTAINTY`.
