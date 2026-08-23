# HCU Reactive World Model Contract

Status: **OWNER-DIRECTED SOURCE CONTRACT v2 / RESEARCH-ENGINEERING TARGET**  
Date: 2026-08-23  
Product: Mini Entity / EntityOS  
Authority: MiniUnifiedDB canonical; EffectGate only real-effect path.

## 1. Primary objective: move cognitive load away from Zero

The HCU world model is an event-driven cognitive substrate whose default behavior is to do **nothing expensive unless state change justifies it**.

Zero should not continuously reconstruct the world, run broad retrieval, compare every hypothesis, or maintain large exploratory context. Those functions move into the HCU. Zero receives only a bounded, highly specific ClayCode projection selected for the active decision.

Canonical path:

```text
MiniUnifiedDB append / effect outcome / timer / feed event
-> deterministic reactive scripts
-> selective HCU module activation only when needed
-> hyperpositional field update + falsification
-> compact ClayCode decision capsule
-> Zero
-> normal EntityOS / EffectGate path
```

Required laws:

`SCRIPT_FIRST = TRUE`

`MODEL_ALWAYS_ON = FALSE`

`ZERO_RECEIVES_WORLD_DUMP = FALSE`

`ZERO_INPUT = BOUNDED_HIGH_SPECIFICITY_CLAYCODE_PROJECTION`

`HCU_WORLD_MODEL != SECOND_TRUTH_STORE`

## 2. Reactive script-first processing

The following work should be deterministic/incremental scripts by default and invoke a ~0.8B module only when a measured trigger requires model cognition:

- canonical rebind and generation checks;
- temporal stitching and expiry;
- contradiction indexing;
- evidence/provenance joins;
- hypothesis/falsifier bookkeeping;
- incremental graph/field projection;
- calibration updates from prediction-vs-outcome;
- duplicate/correlated-source suppression;
- changed-region detection;
- stale-route quarantine;
- Zero relevance scoring;
- ClayCode packing and projection receipts.

Model activation is justified by novelty, unresolved contradiction, high uncertainty, causal ambiguity, forecast branching, effect pressure, explicit strategic demand, or a scheduled unresolved recheck.

## 3. Cognitive independence from external providers

The HCU internal cognition path must boot, retrieve, update, route, falsify, project and continue without NVIDIA, Mistral or another hosted provider.

NVIDIA embeddings and provider-specific embedding pre-stages are removed from the **canonical internal cognitive dependency graph**. Their historical data/code may remain bounded donor evidence or optional tooling.

NVIDIA, Mistral, Groq and other external models may be used only as:

1. research/build workers producing candidate evidence;
2. optional FREE_ONLY external candidate feeds;
3. direct targeted inference fallback where an admitted profile selects them.

They are never required for world-model continuity, semantic indexing, Hyperposition, J-Space/GWT operation, canonical retrieval or Zero context construction.

Claude Code remains the preferred high-capability targeted inference fallback/engine, but its result remains candidate inference and the HCU must retain a local path when Claude is absent.

`EXTERNAL_PROVIDER_REQUIRED_FOR_INTERNAL_COGNITION = FALSE`

`NVIDIA_EMBEDDING_CANONICAL_COGNITION_DEPENDENCY = FALSE`

`MISTRAL_CANONICAL_COGNITION_DEPENDENCY = FALSE`

`EXTERNAL_PROVIDER_OUTPUT = CANDIDATE_ONLY`

## 4. Open-world superposition

The HCU models the world as an explicit typed overlay, not a single flattened narrative:

```text
WorldField(t) =
  observed knowledge/history
  + current measurements
  + hypotheses
  + counterhypotheses
  + forecasts
  + falsifiers/counterevidence
  + explicit UNKNOWN regions
```

The target is broad open-world coverage. Completeness is never assumed.

`WORLD_COVERAGE_TARGET = OPEN_WORLD`

`WORLD_COVERAGE != WORLD_COMPLETENESS`

`UNKNOWN_REGION != ABSENT_REGION`

Every element carries source identity, valid/observed time, generation, epistemic class, conflict links and falsification status.

## 5. Hyperpositional compute substrate

Each logical HCU module is a bounded local hyperpositional computation space over the same fixed ClayCog/ClayCode/GRF semantics. The module does not need to reason generically about arbitrary human topics unless those topics are present in its current typed field. Its job is to transform a narrow semantic neighborhood under a stable contract.

The grid creates a larger virtual substrate by composing many such bounded spaces through explicit higher-order relations, gains, delays, gates, timescales and shared Global J-Space projections.

The design goal is not uncontrolled chaos. It is **measurable emergence**:

- allow alternatives and nonlinear/higher-order coupling to coexist;
- retain field/resonance effects when they outperform simpler reductions;
- expose every coupling through readouts and intervention handles;
- fit/control gains, delays, thresholds and topology only from measured evidence;
- continuously compare against pairwise/deterministic reductions.

## 6. Deterministic repeatability envelope

The hyperpositional computation should be repeatable at the admitted envelope by binding:

- exact checkpoint/tokenizer/runtime;
- exact ClayCode/GRF contract versions;
- exact semantic/activation epochs;
- exact topology basis;
- exact module role and input projection;
- deterministic or otherwise receipt-bound decoding policy;
- generation/causal identity;
- scheduler decision receipt.

Determinism means reproducibility **within a bound execution contract**, not a claim that every neural runtime/platform is bit-identical by default.

## 7. Global J-Space module fabric

Every HCU module exposes a local J-Space projection into one versioned Global J-Space fabric:

```text
local ~0.8B J-Space_m
<-> module GWT_m
<-> typed Global J-Space basis
<-> other module projections
<-> world-model Hyperposition field
```

The common fabric carries typed semantic coordinates, role/basis identity, activation epoch, confidence/evidence class and causal provenance. A module may receive only the slice relevant to its current role.

For local hookable ~0.8B models, J-Space geometry may be measured directly after exact calibration. For Claude Code or another closed engine, the HCU uses a **compiled external vector/control projection** and reintegrates the returned candidate. Current public Claude interfaces do not establish direct residual-stream access, so the architecture must not claim direct Claude-hidden-state fusion without a separately measured mechanism.

Target research direction:

```text
0.8B measured J-Space
-> Global J-Space aligned semantic basis
-> compiled targeted vector/ClayCode projection
-> Claude Code candidate inference
-> measured system-level re-entry
```

If a future admitted interface exposes genuine Claude latent access, it may receive a measured adapter profile; until then `CLAUDE_JSPACE_DIRECT_LATENT_ACCESS = UNOBSERVED`.

## 8. Zero projection: minimum sufficient cognition

The HCU projection to Zero contains only what changes the current decision:

- current causal anchor;
- selected high-relevance facts/measurements;
- unresolved alternatives that matter;
- one or more discriminating falsifiers;
- forecast envelope when relevant;
- recommended next action classes;
- confidence/calibration class;
- provenance/receipt handles;
- explicit UNKNOWNs.

It excludes bulk history, raw provider responses, unrelated alternatives, full simulation traces and internal module chatter.

Zero can request expansion by handle, but the default is a small ClayCode capsule.

## 9. Falsification-first world maintenance

A world state is strengthened by surviving targeted counterevidence, not by repetition or model consensus.

For every material hypothesis the HCU should maintain:

```text
hypothesis
counterhypothesis
predicted observations
cheapest discriminator
observed result
survival/failure status
scope
```

When a simpler pairwise/deterministic mechanism predicts the same outcomes at lower cost, the more complex emergent representation should remain unpromoted or be demoted.

## 10. Persistence boundary

MiniUnifiedDB stores canonical evidence/state and the admitted typed records. HCU field tensors/vectors, caches, active topologies and suspended contexts are rebuildable projections unless separately admitted as canonical record classes.

No HCU field value, vector resonance, module activation or Claude result can directly authorize a real-world effect.
