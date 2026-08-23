# MINI ENTITY HYPERPOSITION COMPUTATIONAL UNIT

Status: **OWNER-DIRECTED ARCHITECTURE CANDIDATE / SOURCE CONTRACT v2**  
Date: 2026-08-23  
Product: Mini Entity / EntityOS  
Package root: `the artefact/MicroEntity/hcu/`

## 1. Objective

Build a permanent resource-adaptive **Hyperposition Computational Unit (HCU)** on the separate KVM4-class host. It coordinates many logical ~0.8B ClayCog modules as one virtual cognitive substrate while keeping MiniUnifiedDB canonical and EffectGate as the only real-effect authority.

Reference deployment target:

```text
KVM 4
4 CPU cores
16 GB RAM
200 GB disk
16 TB bandwidth
```

The HCU is responsible for the heavy ongoing cognitive background load so Zero can remain thin and operational.

## 2. Reactive world-model law

The world model is **reactive, event-driven and script-first**.

Default path:

```text
canonical state/effect/feed/timer event
-> deterministic incremental scripts
-> changed-region + contradiction + relevance detection
-> selective module activation only when justified
-> Hyperposition/Global-J-Space update
-> falsification/calibration
-> bounded high-specificity ClayCode projection
-> Zero
```

Zero does not receive the bulk world model. It receives a minimum-sufficient decision capsule and can expand by receipt/handle only when needed.

See `REACTIVE_WORLD_MODEL_CONTRACT.md` and `ZERO_CLAYCODE_PROJECTION_CONTRACT.json`.

## 3. Authority boundary

```text
MiniUnifiedDB = canonical durable state/evidence/configuration authority
EffectGate    = only admitted real-effect authority
HCU           = scheduled cognition / world-model / simulation / proposal fabric
Zero          = runtime identity/configuration and operational perspective
LLMs          = candidate inference providers only
Hyperposition = unresolved alternative/coupling field, never truth by vote
```

Required laws:

`HCU != SECOND_ENTITY`

`HCU != SECOND_WORLD_TRUTH`

`HCU != EFFECT_AUTHORITY`

`MODULE_OUTPUT = CANDIDATE_OR_MEASUREMENT`

`MAJORITY_VOTE != TRUTH`

`WORLD_COVERAGE != WORLD_COMPLETENESS`

## 4. Cognitive independence

Canonical internal cognition must not depend on NVIDIA embeddings, Mistral, Groq or another external provider.

The HCU local ~0.8B + Global J-Space world field replaces provider-specific embedding/prestage dependencies for the canonical cognitive path.

External engines may remain:

- research/build workers;
- optional FREE_ONLY candidate feeds;
- direct targeted fallback engines.

Claude Code is the preferred high-capability targeted candidate-inference path, but HCU boot, world-model continuity, semantic routing, retrieval and Zero projection must continue without it.

See `COGNITIVE_INDEPENDENCE_POLICY.json`.

## 5. GPU-like logical grid over bounded physical workers

The HCU is not one full model process per logical module. It is many role/context cells over a small resident inference pool with shared immutable model bytes/page cache where the exact runtime proves this safe.

```text
                 reactive scheduler
                       |
          deterministic script plane
                       |
          +------------+------------+
          |                         |
   resident ~0.8B A           resident ~0.8B B
          |                         |
   many logical HPU cells / contexts / branches
          +------------+------------+
                       |
            Global J-Space fabric
                       |
           Hyperposition world field
                       |
             falsification gates
                       |
            ClayCode projection
                       |
                     Zero
```

No numeric module-count claim becomes runtime fact before exact measurement.

## 6. Reference logical lanes

Initial planning topology remains 16 logical slots with adaptive ceiling 24:

| Lane | Slots | Function |
|---|---:|---|
| world | 3 | changed-region causal update, temporal stitching, contradiction handling |
| goal | 2 | goal candidates/progress only when goal pressure requires cognition |
| simulation | 4 | forward/counterfactual/failure/recovery branches |
| zero_model | 2 | observable Zero outcome surrogate |
| hypothesis | 2 | hypothesis/counterhypothesis/discriminator generation |
| critic | 2 | adversarial review, calibration, Goodhart/falsification |
| provenance | 1 | source/receipt/identity checking |

These are roles, not identities and not separate model ownership.

## 7. Script plane before model plane

Scripts perform inexpensive deterministic maintenance first:

- generation fencing;
- canonical rebind;
- temporal expiry/delta stitching;
- provenance joins;
- contradiction/falsifier indexes;
- duplicate/correlation suppression;
- incremental projection updates;
- prediction-vs-outcome calibration;
- changed-region and Zero-relevance scoring;
- ClayCode packing.

`reactive_event_router_v1.py` is the first deterministic source mechanism for selective lane activation. Low-change events can remain script-only; contradictions, forecast/effect pressure or high uncertainty selectively activate only the required lanes.

## 8. World model as typed open-world overlay

The persistent world model maintains explicit coexisting classes:

```text
past/accepted knowledge
current observations and measurements
hypotheses
counterhypotheses
counterevidence/falsifiers
forecasts and alternative futures
explicit unknown/undercovered regions
```

The HCU never flattens these classes into one confidence number or narrative. Every element is time/provenance/generation bound.

The target is broad world coverage, not an impossible claim that the system knows the whole world.

## 9. Hyperpositional semantic compute

Each logical HPU cell is a bounded hyperpositional space using a fixed versioned ClayCode/GRF/native-~0.8B contract. The system intentionally permits field-like/higher-order interaction rather than forcing every intermediate state into a single deterministic symbolic chain.

However emergence is useful only when measurable and controllable. The HCU therefore exposes:

- alternatives and compatibility/exclusion sets;
- n-ary/higher-order relations;
- semantic/active/coordination/physical topology identities;
- coupling gain, delay, gating and timescale;
- pairwise-reduction error;
- lesion/rescue results;
- PID/PEID-style synergy where feasible;
- metastability/hysteresis/recurrence readouts;
- explicit uncertainty/provenance.

See `HYPERPOSITIONAL_SEMANTIC_FIELD_MATH.md` and the repository's existing Hyperposition emergence/readout research.

## 10. Global J-Space fabric

Each local HPU module contributes a typed projection to one Global J-Space basis and receives only the role-relevant slice back.

```text
local 0.8B J-Space_m
<-> module GWT_m
<-> Global J-Space
<-> world Hyperposition field
<-> other HPU modules
```

Exact local ~0.8B latent geometry may be measured after checkpoint/tokenizer/runtime calibration.

Claude Code remains `COMPILED_EXTERNAL` under current evidence: Global J-Space can compile a targeted vector/ClayCode/context projection for Claude and reintegrate its candidate result, but current public control surfaces do not establish direct access to Claude private residual activations. Direct hidden-state fusion is therefore a research target only if a future admitted interface actually exposes it.

## 11. Long simulation and forecasts

Simulation branches are resumable typed objects, not hidden chain-of-thought archives. They store state transitions, assumptions, interventions, predicted observations, falsifiers and uncertainty.

Future branch ranking may decay with depth/time and incorporate evidence quality/stability, but scores are scheduling/calibration quantities until outcome calibration supports stronger interpretation.

## 12. Zero behavioral surrogate

The HCU may model how Zero behaves from observable inputs/actions/outcomes to improve context selection and planning. It must not claim private hidden-mind access.

The objective is to predict which compact projection will let Zero act correctly with the least cognitive load.

## 13. FREE_ONLY external feed

External free models can add candidate evidence, counterhypotheses and research proposals, but do not participate as required inner cognition.

Provider consensus/repetition does not mint truth. Paid fallback is forbidden under current FREE_ONLY control and Together execution remains forbidden.

## 14. Capacity and physical scheduling

Reference source targets remain planning-only:

- logical slots: 16 target / 24 adaptive ceiling;
- resident inference workers: 2 target;
- physical decode concurrency: 2 default / 4 source ceiling;
- reserve at least 2 GiB for OS/DB/scheduler;
- soft Mini Entity RAM limit 12 GiB; hard 14 GiB.

`capacity_guard_v1.py` prevents these source numbers from becoming runtime claims without exact admitted measurement.

## 15. Persistence model

Canonical records live in MiniUnifiedDB. Suggested classes include:

```text
hcu_observation
hcu_measurement
hcu_causal_edge
hcu_hypothesis
hcu_counterhypothesis
hcu_counterevidence
hcu_falsifier
hcu_goal_candidate
hcu_goal_progress
hcu_simulation_branch
hcu_forecast
hcu_zero_behavior_model
hcu_strategic_proposal
hcu_projection_receipt
hcu_calibration_receipt
```

Vectors/tensors, local field states, caches, ANN indexes, graph projections and suspended runtime contexts are rebuildable unless separately admitted as canonical typed records.

## 16. Package law

All non-secret HCU product source/config/tests/contracts/receipts and admitted privacy-filtered exports belong under `the artefact/MicroEntity/hcu/` and in `MICROENTITY_CURRENT.zip` whenever changed.

## 17. Acceptance gates

Before promoting the HCU substrate, require exact evidence for:

- checkpoint/tokenizer/runtime identity and RAM/throughput scaling;
- provider-free boot/world-model/retrieval/Zero projection;
- script-first low-change path avoiding unnecessary model inference;
- pairwise vs higher-order matched-budget discrimination;
- edge/hyperedge lesions, topology shuffles, gain/delay sweeps and rescue;
- deterministic replay under exact TopologyBasis;
- Global J-Space re-entry and causal-use tests;
- Zero decision quality vs projection size;
- restart/recovery/generation fences;
- no EffectGate bypass;
- no hidden provider/embedding dependency.

Until then, controllable-emergence, direct Claude J-Space fusion and target-VPS performance remain research/acceptance targets rather than established facts.
