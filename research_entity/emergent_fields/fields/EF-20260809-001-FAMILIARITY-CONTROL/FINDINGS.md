# EF-20260809-001 — Familiarity Stability Control

## Spawn

- Trigger: `666`
- Mode: first post-Level-0 emergent field
- Seed: `10051668388208013663`
- Lens: compression/representation learning × control theory
- Current program attractor: `BASE_CLAYCODE_RELEASE`
- Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol

## Question

Can FRANK reduce visual compute as user-specific scenes become familiar without allowing its own predictions to become a self-reinforcing source of false familiarity?

## Working mechanism

Model the Micro Visual Classifier as a closed-loop controller over a frozen representation:

`visual feature -> familiarity estimate -> open-set gate -> routing decision -> evidence receipt -> trust-tier admission -> candidate update -> replay/retention/open-set evaluation -> promote or rollback`

The key control boundary is **training-evidence authority**, not confidence alone.

`prediction confidence != permission to rewrite trusted learner state`

This is consistent with the existing owner-fixed GOLD/SILVER/BRONZE contract and does not require a new semantic redesign unless executable ClayCode representability fails.

## External primary evidence

1. **CoTTA — Continual Test-Time Domain Adaptation** (`arXiv:2203.13591`): non-stationary pseudo-label adaptation can accumulate errors and catastrophically forget; long-term adaptation needs explicit stability mechanisms.
2. **Ranked Entropy Minimization for Continual Test-Time Adaptation** (`OpenReview:lHaGLJ65J9`, ICML 2025): naive continual entropy minimization can collapse toward trivial predictions; stability is a first-class requirement.
3. **Uncovering the Risk of Model Collapsing in Self-Supervised Continual Test-time Adaptation** (`OpenReview:EFS2hfLuUF`, NeurIPS 2024 workshop): repeatedly reusing incorrect predictions creates long-horizon degradation and a security/poisoning surface.
4. **On the Robustness of Open-World Test-Time Training** (`arXiv:2308.09942`): explicit OOD filtering plus prototype handling improves robustness when strong unknown contamination is present.

These are analogues, not direct FRANK evidence.

## Synthetic discriminating test

A reproducible 2D frozen-embedding simulation compared:

- naive confident self-update;
- sparse trusted-evidence prototype updates.

Across 30 replicates per contamination level:

| Unknown stream fraction | Naive unknown rejection | Gated unknown rejection | Wrong-unknown fraction among naive updates |
|---|---:|---:|---:|
| 0.10 | 0.385 | 0.421 | 0.078 |
| 0.25 | 0.339 | 0.419 | 0.224 |
| 0.40 | 0.319 | 0.419 | 0.389 |
| 0.55 | 0.283 | 0.432 | 0.553 |
| 0.70 | 0.261 | 0.440 | 0.724 |

Known-class accuracy remained nearly saturated until severe contamination, showing that **open-set health degrades earlier than ordinary known-class accuracy**.

This is synthetic evidence only. It supports a mechanism test, not a production claim.

## Cross-branch deltas

### FRANK / Retina

Keep the Micro Visual Classifier as a learned familiarity/routing controller. Preserve `UNKNOWN`, `AMBIGUOUS`, `CONFLICT`, evidence tier and sensor provenance. Do not let BRONZE self-predictions update trusted prototypes/classifier state.

### ClayCode BASE

The current release requirement already points in the right direction. ClayCode must express, without host-only hidden state:

- learner/prototype version identity;
- training example provenance + GOLD/SILVER/BRONZE tier;
- open-set/familiarity result;
- current vs candidate learner state;
- bounded update budget;
- shadow-evaluation receipt;
- atomic promotion/rejection;
- last-known-good rollback/replay.

No language-semantic change is justified yet; first try to encode this in the existing candidate semantics.

### UnifiedDB / ClayGraph

Persist learner state as versioned evidence-linked state, not as unqualified facts. Graph relations should distinguish `OBSERVED_VISUAL_EVIDENCE`, `FAMILIARITY_CANDIDATE`, `CONFIRMED_ENTITY`, `TRAINING_EXAMPLE`, and `DERIVED_PREDICTION` so a prediction cannot become its own provenance ancestor unnoticed.

### Harness

Prioritize `MVC-E4` pseudo-label poisoning and `MVC-E5` unknown rejection together. Add a metric for **fraction of autonomous accepted updates whose lineage ultimately depends only on self-prediction**. That should be zero for direct positive-truth admission under the current owner contract.

## Next discriminating experiment

On real frozen Retina embeddings from recurring user-specific scenes, sweep:

- unknown/OOD contamination rate;
- prototype vs linear head;
- confidence/open-set thresholds;
- SILVER minimum support/diversity;
- candidate promotion criteria;
- replay size;
- CPU/time budget.

Measure known retention, false familiarity, calibration, routing compute saved, promotion frequency and rollback frequency.

## Status

`SUPPORTED_WORKING_HYPOTHESIS_SYNTHETIC_PLUS_EXTERNAL_ANALOGUE`

Not promotable until H1 executes the real Retina-embedding tests.
