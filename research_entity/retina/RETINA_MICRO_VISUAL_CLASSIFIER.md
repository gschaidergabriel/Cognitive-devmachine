# Retina Micro Visual Classifier — User-Adaptive Pre-Classifier

**Status:** OWNER-PROPOSED ARCHITECTURE CANDIDATE / IMPLEMENTATION DIRECTIVE SUBJECT TO HARNESS VALIDATION  
**Recorded:** 2026-08-09  
**Applies to:** Retina, FRANK, ClayGraph, UnifiedDB, GWT, ClayCode, Harness

## 0. Core idea

Add an extremely small user-adaptive visual learner in front of expensive semantic vision routing.

It is NOT a second heavy vision encoder. It consumes visual embeddings/features that Retina already computes (initially CLIP/DINO or an equivalent frozen feature backbone) and learns only a tiny user-specific readout/prototype layer.

Target path:

`screenshot/crop -> cheap change gate -> frozen reusable visual features -> Micro Visual Classifier -> confidence/open-set gate -> known fast path OR normal Retina/PerceptualField escalation`

The classifier continuously becomes better at recurring user-specific visual entities, layouts, applications, UI regions, objects and contexts.

## 1. Resource law

The learner MUST remain operationally negligible compared with the normal Retina path.

Therefore:

- do not retrain the visual backbone in the normal online cycle;
- reuse already-computed feature vectors wherever possible;
- prefer prototypes / nearest-centroid / linear probe as the first implementation;
- permit a tiny MLP only if executable benchmarks prove material gain;
- one low-priority CPU thread maximum by default;
- train only during idle/budget-permitted windows or in bounded micro-bursts;
- hard CPU/time/RAM budgets must be enforced by the runtime;
- failure/over-budget disables learning, never normal perception.

No fixed latency or CPU claim is canonical before project-hardware measurement.

## 2. Recommended implementation ladder

### MVC-0 — Prototype memory, no gradient training

For each learned concept/entity maintain several normalized feature prototypes plus variance/context metadata.

Inference:

`similarity(current_feature, prototypes) -> familiarity candidate + distance/margin/open-set evidence`

Advantages: effectively no training cost, trivial rollback, transparent, naturally incremental.

### MVC-1 — Frozen-backbone linear classifier

Train only a small linear head on frozen visual embeddings. This is the preferred first neural Micro-AI.

Properties:

- no backbone forgetting;
- tiny parameter count;
- very cheap inference;
- cheap cyclic retraining;
- classifier version can be swapped atomically;
- prototypes remain as independent baseline and open-set aid.

### MVC-2 — Tiny MLP / adapter

Only after MVC-1 is beaten on held-out user-specific data under the same budget. Suggested topology is one small hidden layer or similarly bounded adapter, never an unconstrained second vision stack.

### MVC-3 — rare offline encoder adaptation

Not part of the default autonomous cycle. Any adaptation of the underlying visual encoder requires a separate evidence gate, replay evaluation and rollback because feature drift can invalidate prototypes, calibration and historical embeddings.

## 3. What it learns

Potential personal classes/entities include:

- recurring applications and windows;
- user-specific UI layouts or panels;
- known websites/pages/workspaces;
- recurring devices, tools and physical objects;
- stable rooms/viewpoints;
- known project visual artifacts;
- user-named entities;
- recurring action/outcome visual states;
- high-value regions that repeatedly matter to the user.

Learning is scoped to the owning user/workspace. No implicit cross-user sharing.

## 4. Training data trust ladder

Autonomous cyclic training MUST NOT blindly train on its own predictions.

Training examples have evidence tiers:

### GOLD
- explicit user label/correction;
- deterministic external ground truth;
- strongly verified action/outcome identity where ambiguity is absent.

May train directly.

### SILVER
- same entity observed consistently across multiple views/times;
- independent Retina kernels agree;
- world-state continuity supports identity;
- no contradicting evidence;
- high confidence sustained over repeated observations.

May train with bounded weight after minimum support threshold.

### BRONZE
- one-shot pseudo-label;
- Micro-AI self-prediction;
- single weak model suggestion;
- context-only expectation.

Must NOT directly become positive training truth. Store as candidate until confirmed.

This prevents self-reinforcing hallucination loops.

## 5. Cyclic autonomous training

Training is event/budget driven, not triggered by every screenshot.

Candidate policy:

1. every visual observation may append a compact embedding receipt;
2. only validated GOLD/SILVER examples enter the learning buffer;
3. retrain/update when enough novel validated examples accumulate OR an idle interval is reached;
4. build candidate classifier in shadow mode;
5. evaluate candidate against:
   - frozen replay buffer;
   - prior-class retention set;
   - open-set/unknown negatives;
   - recent user-specific holdout;
6. promote atomically only when candidate beats/equates current model under retention and calibration gates;
7. otherwise discard candidate and keep previous classifier.

No autonomous learner may overwrite its last known-good version.

## 6. Confidence is not one softmax number

The pre-classifier output should contain at least:

- candidate class/entity;
- classifier probability/logit margin;
- prototype similarity/distance;
- number/diversity of supporting examples;
- recency of confirmation;
- open-set score;
- calibration version;
- context/familiarity support;
- explicit evidence tier.

Suggested output states:

- `KNOWN_HIGH_CONFIDENCE`
- `KNOWN_NEEDS_CONFIRMATION`
- `AMBIGUOUS`
- `UNKNOWN`
- `CONFLICT`

Only `KNOWN_HIGH_CONFIDENCE` may substantially bypass expensive broad recognition, and even then current sensor evidence/provenance remains preserved.

## 7. Routing behavior

### Familiar fast path

If Micro-AI identifies a familiar item with calibrated high confidence and no contradiction:

- update/reconnect known ClayGraph entity;
- run only the cheap transforms needed for changed attributes;
- avoid broad vocabulary/object search where unnecessary;
- keep full Retina available on demand.

### Novel/uncertain path

If confidence, margin, prototype support or open-set tests fail:

`Micro-AI -> UNKNOWN/AMBIGUOUS -> normal Retina/PerceptualField escalation`

Novelty therefore gets MORE visual compute rather than being forced into a familiar class.

## 8. Relationship to 19-second visual heartbeat

For the proposed default main-screen heartbeat:

`19 s anchor screenshot -> tile/hash delta -> changed region(s) -> feature extraction -> Micro-AI`

If unchanged: almost no semantic work.

If changed but familiar: Micro-AI handles identity cheaply and Retina inspects only changed attributes/relations.

If novel/uncertain: full/targeted Retina path activates.

FRANK may request additional screenshots at any time, especially before/after actions, on uncertainty, on visual conflict or when active sensing has positive expected information value.

## 9. Continual-learning safety

Mandatory defenses:

- frozen backbone by default;
- prototype baseline retained independently of neural head;
- bounded replay/retention set for old classes;
- class-balanced sampling;
- candidate-vs-current shadow evaluation;
- explicit open-set negatives;
- per-class calibration/thresholds where required;
- rollback/versioning;
- drift detection;
- no training directly from self-generated labels;
- confidence cannot become canonical sensor evidence.

## 10. Harness experiments

### MVC-E1 — resource invisibility
Measure inference/training CPU time, RAM and tail latency while FRANK performs normal work. Reject any implementation whose user-visible impact is material.

### MVC-E2 — personalization gain
Freeze a user-specific held-out set. Compare base Retina vs prototype vs linear vs tiny-MLP on recurring entities/layouts.

### MVC-E3 — forgetting
Add classes sequentially and measure old-class accuracy/calibration after every update.

### MVC-E4 — pseudo-label poisoning
Feed high-confidence wrong pseudo-labels and verify BRONZE examples cannot autonomously rewrite truth.

### MVC-E5 — unknown rejection
Use visually similar but unseen entities; measure false-familiarity rate, not only known-class accuracy.

### MVC-E6 — routing benefit
Measure how often Micro-AI safely avoids expensive Retina stages and the resulting CPU/latency savings without task loss.

### MVC-E7 — feature-version migration
Change the backing visual encoder/version and verify old prototypes/models are invalidated or explicitly migrated rather than silently reused.

## 11. Scientific prior

Current few-shot/continual-learning literature supports the general architecture class:

- frozen pretrained visual representations with lightweight learned classifiers can perform strong few-shot adaptation;
- prototype-based continual learning can reduce memory/training requirements;
- recent CLIP personalization work demonstrates new/rare classes can be adapted without retraining the encoder;
- freezing the feature extractor substantially limits catastrophic forgetting compared with sequential full-model updates.

These external results support trying the mechanism. They do not establish FRANK-specific gains; those require MVC-E1..E7 on project hardware/data.

## 12. Integration law

The Micro Visual Classifier is a **learned routing/readout layer**, not a new semantic authority.

`Micro-AI confidence != observed truth`

`familiarity != evidence`

`prediction != perception`

Its purpose is to make familiar visual cognition cheaper and faster while pushing novel, contradictory or weakly supported input toward deeper perception.
