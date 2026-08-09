# FRANK 0.1 Adaptive Visual Learning Directive

**Status:** PROJECT-OWNER FIXED FRANK 0.1 REQUIREMENT — NOT OPTIONAL  
**Recorded:** 2026-08-09  
**Applies to:** FRANK 0.1, Digital Retina / dissolved perception, Clay, ClayCode, ClayGraph, UnifiedDB, GWT, Harness H1/H2/H3, project-hardware acceptance and DOOMSDAY  
**Research foundation:** `research_entity/retina/RETINA_MICRO_VISUAL_CLASSIFIER.md`

## 0. Owner-fixed requirement

FRANK 0.1 MUST contain a user-adaptive visual learning path that makes recurring, user-specific visual content progressively cheaper, faster and more reliable to recognize while preserving open-set uncertainty and sensor-evidence provenance.

This is a release requirement for FRANK 0.1 and Clay 0.1 chief-developer first-test acceptance. It is not a post-0.1 enhancement and cannot be removed merely to simplify the first integrated build.

The first implementation SHOULD be the smallest architecture that satisfies the contract: a frozen reusable visual feature backbone plus prototype memory and/or a tiny learned readout such as a linear classifier. A heavier learner is not required unless measurement proves it necessary.

## 1. Required functional path

Minimum target:

`screen/image/crop -> cheap change gate -> reusable frozen visual feature -> adaptive Micro Visual Classifier -> calibrated confidence/open-set gate -> familiar fast path OR deeper Retina/PerceptualField escalation`

The Micro Visual Classifier is not a semantic authority. It is a learned familiarity/routing layer.

Hard laws:

`micro_classifier_prediction != sensor_truth`

`familiarity != evidence`

`confidence != authority`

`unknown/ambiguous/conflict -> deeper perception, never forced familiarity`

## 2. User-adaptive visual learning

FRANK 0.1 must be able to learn recurring visual content of the owning user/workspace, including where useful:

- applications, windows and UI layouts;
- recurring websites/pages/workspaces;
- user-named visual entities;
- familiar devices, tools and physical objects;
- stable rooms/viewpoints;
- recurring project artifacts;
- recurring visual action/outcome states;
- familiar visual regions and relations that repeatedly matter to the user.

Personal learning remains scoped to the owning user/workspace unless an explicit future sharing contract says otherwise.

## 3. Cyclic autonomous learning

FRANK 0.1 MUST support bounded autonomous cyclic updates of the Micro Visual Classifier.

The autonomous loop is event/budget driven, not a full retrain every visual heartbeat:

1. collect compact feature/example receipts during normal perception;
2. admit only sufficiently trusted GOLD/SILVER examples to the training/update buffer;
3. update prototypes and/or train a candidate tiny readout in bounded low-priority bursts;
4. evaluate candidate against frozen replay, retention, open-set negatives and recent held-out user-specific samples;
5. promote atomically only when gates pass;
6. retain the last known-good classifier/prototype state for rollback.

BRONZE one-shot/self-generated labels MUST NOT autonomously become training truth.

## 4. Resource requirement

The user intent is that this learning is operationally unnoticeable during normal use.

Therefore FRANK 0.1 MUST implement explicit CPU/time/RAM/state-growth budgets and benchmark them on project hardware.

Required architecture preferences:

- frozen visual backbone in the normal online cycle;
- reuse features Retina already computes;
- prototype/nearest-centroid baseline retained;
- linear head preferred before tiny MLP;
- one low-priority CPU worker/thread maximum by default for background update work;
- bounded micro-bursts / idle-window training;
- over-budget learning pauses or disables itself without disabling perception;
- no claim of negligible resource use without measured project-hardware receipts.

## 5. Confidence / open-set contract

The learned pre-classifier output must preserve enough information to distinguish genuine familiarity from weak similarity.

At minimum retain or derive:

- candidate identity/class;
- score/probability/logit margin;
- prototype similarity/distance where applicable;
- support count/diversity;
- confirmation recency;
- open-set/unknown score;
- calibration/version identity;
- training evidence tier.

Required semantic outcomes:

- `KNOWN_HIGH_CONFIDENCE`
- `KNOWN_NEEDS_CONFIRMATION`
- `AMBIGUOUS`
- `UNKNOWN`
- `CONFLICT`

Only calibrated `KNOWN_HIGH_CONFIDENCE` may substantially bypass broad recognition. Sensor evidence and provenance remain preserved.

## 6. Relationship to dissolved Retina and visual heartbeat

The Micro Visual Classifier belongs inside the dissolved visual-perception architecture rather than surviving as a separate cognitive service.

For the current candidate main-screen heartbeat:

`~19 s anchor screenshot -> cheap tile/hash delta -> changed regions -> reusable feature extraction -> Micro Visual Classifier -> familiar fast path or deeper Retina`

The exact 19-second cadence remains a tunable implementation parameter unless separately owner-frozen. FRANK may request immediate additional screenshots before/after actions, under uncertainty/conflict, or when active sensing has positive expected information value.

The long-term intent is:

`familiarity increases -> required visual compute tends to decrease`

`novelty/conflict/uncertainty increases -> visual compute and/or active sensing tends to increase`

This performance relation is a hypothesis to measure, while adaptive learning itself is a fixed FRANK 0.1 requirement.

## 7. Milestone integration

### L0_ARCHIVE_ASSIMILATION

Preserve historical Retina learning/pattern/dictionary/familiarity mechanisms and negative results as evidence. L0 does not need to implement the new learner, but must not lose relevant historical lineage needed to build/test it.

### BASE_CLAYCODE_RELEASE

ClayCode must be able to express the state/update semantics required by the adaptive learner: versioned classifier/prototype state, training-example provenance/tier, confidence/open-set result, candidate promotion/rollback, resource-budget state and deterministic replay hooks. The general-purpose compiler gate remains independent; no unnecessary language redesign is allowed.

### H1_REFERENCE_HARNESS — mandatory implementation

H1 MUST contain an executable reference implementation of the Micro Visual Classifier and autonomous bounded update loop.

H1 PASS requires at minimum:

- MVC-0 prototype baseline;
- MVC-1 frozen-backbone tiny learned classifier OR an executable result proving MVC-0 already satisfies the frozen acceptance threshold;
- known/unknown/conflict routing;
- GOLD/SILVER/BRONZE admission rules;
- candidate-vs-current shadow evaluation;
- rollback/versioning;
- resource instrumentation;
- forgetting/retention and pseudo-label-poisoning tests.

### H2_CLAYCODE_HARNESS — mandatory semantic parity

H2 MUST reproduce the frozen H1 adaptive-visual-learning semantics in ClayCode/Clay state and pass differential state/receipt behavior for:

- learning-buffer admission;
- prototype/readout updates;
- confidence/open-set decisions;
- promotion/rejection/rollback;
- stale/version migration;
- learner resource budgets;
- known-vs-novel routing.

H2 cannot PASS if the learner is bypassed as an external opaque service whose semantic state cannot be represented/replayed.

### H3_ONE_MODULE_FRANK — mandatory physical integration

H3 MUST integrate the adaptive visual learner into the one-module/binary FRANK identity as far down the runtime as technically feasible, alongside dissolved Retina/perceptual state.

H3 PASS requires the learner to operate on the real in-process visual path or an explicitly justified physical lowering, not as a semantically separate cognitive authority.

### UDB_UNIFIED_DATABASE — mandatory persistence

UnifiedDB/ClayGraph must persist/recover the required adaptive-visual-learning state and provenance, including classifier/prototype version identity, trusted-example lineage, calibration/threshold metadata, feature-backbone version compatibility and rollback/rebuild information.

### DATA_LORA_TRAINING_DATA

The final Clay/model training corpus gate remains distinct from the online Micro Visual Classifier. However, any FRANK model-facing visual Assembly/schema needed to consume familiarity/unknown/conflict state must be represented in the frozen training/held-out corpus. Online personal visual data is not automatically promoted into final model training data.

### CLAY_0_1_FULL_INTEGRATION / PROJECT_HARDWARE_DEPLOYMENT

The integrated build must run the adaptive learner with the actual Retina/PerceptualField path and measure its real project-hardware overhead, routing benefit, retention and recovery.

### CLAY_0_1_ACCEPTANCE_RUN / DOOMSDAY

DOOMSDAY cannot PASS if adaptive visual learning is absent, disabled, non-replayable, unbounded, demonstrably forgetting prior learned classes beyond the frozen threshold, unable to reject unknowns at the frozen threshold, or capable of self-training from unverified self-labels without the required trust gate.

## 8. Mandatory acceptance experiment families

At minimum freeze and run:

- `MVC-E1` resource invisibility / bounded overhead;
- `MVC-E2` user-specific personalization gain;
- `MVC-E3` sequential-class retention / forgetting;
- `MVC-E4` pseudo-label poisoning resistance;
- `MVC-E5` unknown/open-set rejection;
- `MVC-E6` routing/computation benefit without task loss;
- `MVC-E7` feature-backbone version migration/invalidation;
- crash/restart + rollback/replay of learner state;
- long-horizon visual action loop using familiar plus novel content.

Exact numerical thresholds are evidence-gated and must be frozen before final acceptance. A never-run test is not a PASS.

## 9. Promotion boundary

Fixed for FRANK 0.1:

- adaptive user-specific visual learning exists;
- cyclic autonomous bounded update exists;
- confidence/open-set gating exists;
- trusted-example admission exists;
- rollback/replay/versioning exists;
- the learner is integrated with dissolved Retina and milestone acceptance.

Still research-gated:

- prototype vs linear vs tiny MLP winner;
- exact feature backbone;
- exact update cadence/batch size;
- exact confidence calibration method;
- exact CPU/RAM/time thresholds;
- exact 19-second heartbeat policy;
- measured speed/accuracy savings.

## 10. Supersession / provenance

This directive promotes the architectural requirement proposed in `research_entity/retina/RETINA_MICRO_VISUAL_CLASSIFIER.md` into a project-owner fixed FRANK 0.1 milestone requirement while preserving that file as the research/implementation foundation. It does not convert its unmeasured performance hypotheses into facts.
