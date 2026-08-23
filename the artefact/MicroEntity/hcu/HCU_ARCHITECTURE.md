# MINI ENTITY HYPERPOSITION COMPUTATIONAL UNIT

Status: **OWNER-DIRECTED ARCHITECTURE CANDIDATE / SOURCE CONTRACT v1**
Date: 2026-08-23
Product: Mini Entity / EntityOS
Package root: `the artefact/MicroEntity/hcu/`

## 1. Objective

Build a permanent, resource-adaptive **Hyperposition Computational Unit (HCU)** that can run on a separate low-cost VPS and coordinate as many useful logical ~0.8B cognition modules as the measured host can sustain.

Reference host:

```text
KVM 4
4 CPU cores
16 GB RAM
200 GB disk
16 TB bandwidth
```

The HCU is intended to support:

- persistent causal world-model maintenance;
- dynamic goal-candidate generation and goal-progress checking;
- long iterative forward and counterfactual simulations;
- an observable-behavior model of Zero;
- improvement-hypothesis generation and critique;
- confidence-calibrated future branches;
- ingestion of FREE_ONLY external LLM candidate information;
- continuous strategic proposals back into Zero/EntityOS.

## 2. Non-negotiable authority boundary

The HCU is a compute organ inside the same Mini Entity.

```text
MiniUnifiedDB = canonical durable state/evidence/configuration authority
EffectGate    = only admitted real-effect authority
HCU           = scheduled cognition / simulation / proposal fabric
Zero          = runtime identity/configuration and operational perspective
LLMs          = candidate inference providers
Hyperposition = unresolved alternative holder, never truth by vote
```

Required laws:

`HCU != SECOND_ENTITY`

`HCU != SECOND_WORLD_TRUTH`

`HCU != EFFECT_AUTHORITY`

`MODULE_OUTPUT = CANDIDATE`

`FREE_LLM_OUTPUT = CANDIDATE`

`ZERO_BEHAVIOR_MODEL != HIDDEN_MIND_ACCESS`

`FORECAST_CONFIDENCE != FACTUAL_TRUTH`

`MAJORITY_VOTE != TRUTH`

No HCU module may directly commit canonical facts, broaden permissions, execute host commands, bypass MiniUnifiedDB, or bypass EffectGate.

## 3. GPU-like grid without RAM duplication

The owner analogy is a graphics card: many small modules connected into one computational unit.

On a 4-core / 16-GB CPU VPS, the practical architecture is a **logical module grid over a small resident worker pool**, not one full model process per module.

```text
                    ┌──────────────────────────────┐
                    │      HCU SCHEDULER           │
                    │ resource + causal + priority │
                    └──────────────┬───────────────┘
                                   │
               ┌───────────────────┼───────────────────┐
               │                   │                   │
        ┌──────▼──────┐      ┌─────▼──────┐      ┌────▼───────┐
        │ ~0.8B worker│      │~0.8B worker│      │ optional   │
        │ resident A  │      │ resident B │      │ burst slot │
        └──────┬──────┘      └─────┬──────┘      └────┬───────┘
               │                   │                   │
      many logical contexts / roles / adapters / branches
               │                   │                   │
               └───────────────────┼───────────────────┘
                                   ▼
                         Hyperposition merge
                                   ▼
                     deterministic admission gates
                                   ▼
                           MiniUnifiedDB / Zero
```

The topology MUST adapt from measured runtime facts:

- free RAM;
- per-worker resident set size;
- KV/context memory;
- CPU saturation;
- p50/p95 decode latency;
- queue depth;
- swap pressure;
- thermal/host throttling signals where available.

No fixed module count is promoted as a runtime fact before measurement.

## 4. Reference logical lanes

The initial KVM4 profile allocates 16 logical slots:

| Lane | Slots | Function |
|---|---:|---|
| world | 3 | causal state update, contradiction scan, temporal stitching |
| goal | 2 | propose goals, check progress/falsifiers |
| simulation | 4 | forward, counterfactual, failure and recovery branches |
| zero_model | 2 | predict Zero's observable behavior/outcomes |
| hypothesis | 2 | improvement hypotheses and discriminating tests |
| critic | 2 | adversarial review, confidence calibration, Goodhart checks |
| provenance | 1 | source/receipt/identity checking |

These are logical roles. They MAY share one checkpoint and one runtime process. A role is not a persistent identity.

## 5. Scheduling model

The scheduler uses two distinct limits:

1. **logical slots** — queued or suspended module contexts;
2. **physical decode concurrency** — simultaneously decoding model workers.

Reference KVM4 source profile:

- target logical slots: 16;
- adaptive ceiling: 24;
- target resident inference workers: 2;
- hard physical decode concurrency: 4;
- default decode concurrency: 2;
- reserve at least 2 GiB RAM for OS, DB, scheduler and safety margin;
- soft Mini Entity RAM budget: 12 GiB;
- hard Mini Entity RAM budget: 14 GiB.

The scheduler MUST reduce residency/concurrency before swap thrash or memory exhaustion. It MAY increase logical slots when suspended-context storage is cheap enough.

## 6. Persistent world model

The permanent world model is not a second database. It is canonical MiniUnifiedDB state plus rebuildable HCU projections.

Recommended canonical record classes:

```text
hcu_observation
hcu_causal_edge
hcu_hypothesis
hcu_counterevidence
hcu_goal_candidate
hcu_goal_progress
hcu_simulation_branch
hcu_zero_behavior_model
hcu_strategic_proposal
hcu_feed_receipt
hcu_calibration_receipt
```

Each durable row should bind:

- entity generation;
- causal/episode/turn identifiers where applicable;
- source/provenance;
- valid/observed time;
- confidence class and calibration version;
- contradiction links;
- supersession/retraction status.

Caches, vector indexes and graph projections are rebuildable.

## 7. Dynamic goals

The HCU MAY autonomously generate **goal candidates**.

It MUST NOT autonomously mint effect authority.

Goal lifecycle:

```text
observation / unresolved state
-> goal candidate
-> critic + falsifier
-> deterministic GoalGate
-> admitted strategic goal OR rejected/deferred
-> simulation / planning
-> StrategicProposal to Zero
-> normal EntityOS/EffectGate path
```

A goal candidate can be useful even when rejected; it remains research/evidence data.

## 8. Long iterative simulation

Simulation branches are first-class typed objects rather than hidden chain-of-thought.

A branch stores concise state transitions, assumptions, interventions, predicted observations and uncertainty — not private model reasoning.

```text
SimulationBranch {
    branch_id
    parent_branch_id?
    causal_anchor
    horizon_steps
    assumptions[]
    proposed_actions[]
    predicted_observations[]
    uncertainty
    falsifiers[]
    status
}
```

Long simulation is implemented as resumable batches. The scheduler can pause branches and re-enter them later without keeping all model KV state resident.

## 9. Forecast confidence

Future confidence must decay and be calibrated against observed outcomes.

A candidate ranking function may use:

```text
forecast_score =
    calibrated_base
    * exp(-lambda_step * simulated_depth)
    * exp(-lambda_time * forecast_horizon)
    * evidence_quality
    * branch_stability
```

This is a prioritization/calibration quantity only.

It MUST NOT be stored or displayed as factual probability unless an accepted calibration procedure justifies that interpretation.

## 10. Modeling Zero

The HCU may maintain a **Zero behavioral surrogate** using observable data:

- tasks presented to Zero;
- context/projection given;
- selected actions;
- verified outcomes;
- errors/retries;
- latency/resource observations;
- explicit user corrections.

It must not claim access to Zero's private hidden cognition or Claude's internal activations unless an admitted local mechanism actually measures them.

The purpose is predictive control:

```text
"If Zero receives context X under state S, which action/outcome class is likely?"
```

not metaphysical mind-reading.

## 11. Improvement-hypothesis feedback

The HCU may derive improvement hypotheses for Zero/EntityOS, but the feedback path is fail-closed:

```text
observed failure / inefficiency
-> hypothesis
-> counterhypothesis
-> cheapest discriminator
-> source/test proposal
-> admitted isolated test
-> measured receipt
-> owner/policy promotion gate
-> optional product change
```

No module can silently rewrite its own authority, merge code, deploy itself, or relax gates merely because internal simulations prefer a change.

## 12. FREE_ONLY LLM feed

The HCU can be continuously fed from the project's existing free-token/provider pool.

The feed uses typed `ExternalCandidatePacket` records and reuses the existing FREE_ONLY controller/rate-limit policy.

Hard rules:

- no paid fallback;
- Together execution remains forbidden under the current owner control;
- HTTP 402 is a hard stop;
- HTTP 429 triggers provider-wide backoff, not key rotation;
- tokens/credentials never enter prompts, source, MiniUnifiedDB exports or ZIP archives;
- provider output never becomes canonical truth on arrival;
- duplicate/provider-correlated answers are not independent evidence;
- external models do not receive effect authority.

The feed should prioritize evidence diversity, provenance and unresolved questions over raw volume.

## 13. Hyperposition aggregation

Module disagreement is an asset.

The HCU stores competing outputs as an unresolved set:

```text
HyperpositionSet {
    issue_id
    alternatives[]
    supporting_evidence[]
    counterevidence[]
    discriminators[]
    unresolved_facets[]
}
```

Collapse requires evidence or a deterministic policy decision. Raw vote count, repeated sampling or provider consensus cannot silently promote a factual claim.

## 14. Data and package placement

All HCU project artefacts generated for release belong under:

`the artefact/MicroEntity/hcu/`

and are included in:

`the artefact/MicroEntity/MICROENTITY_CURRENT.zip`

The archive includes non-secret HCU source/config/contracts/receipts and admitted privacy-filtered data exports.

Operational MiniUnifiedDB remains runtime state. Secrets and credential-bearing files are excluded even when other HCU data is packaged.

## 15. `go` integration

Every exact `go` must treat HCU as a first-class parallel Mini Entity workstream.

The HCU does not permanently steal the whole frontier. Work selection remains:

`information gain × Mini Entity convergence × non-duplication × executable availability`.

A useful `go` may advance the core Mini Entity, the HCU, or both. When an HCU delta is made, package files and `MICROENTITY_CURRENT.zip` must stay synchronized.

## 16. Acceptance gates for the KVM4 deployment target

Before claiming the HCU fits or performs on the target VPS, collect exact admitted evidence for:

- model/runtime/checkpoint identity;
- peak RSS per resident worker;
- per-context/KV memory;
- safe logical-slot ceiling;
- safe physical decode concurrency;
- token throughput and p95 latency under representative queue load;
- scheduler degradation under RAM pressure;
- restart/recovery with no state fork;
- MiniUnifiedDB generation fencing;
- FREE_ONLY feed backoff;
- Hyperposition non-collapse regressions;
- Zero behavioral-surrogate calibration;
- effect-path non-bypass.

Until then, KVM4 capacity numbers are planning targets, not verified performance claims.
