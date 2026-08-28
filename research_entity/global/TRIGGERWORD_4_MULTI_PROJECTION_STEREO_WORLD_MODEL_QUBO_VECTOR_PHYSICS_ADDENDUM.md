# TRIGGERWORT 4 — Multi-Projection Stereo World Model

Status: FUSED ARCHITECTURE ADDENDUM
Date: 2026-08-28
Historical source archaeology: `gschaidergabriel/Project-Frankenstein@39c5423e0bfae54b971aab0be82f225f7a5890b8`
Applies with the Sparse Generative World Substrate and Cognitive Micro-Lab directives.

## 1. Historical finding

Project-Frankenstein did not have one single world-model object. It had several partially overlapping world/state representations:

1. `tools/world_experience_daemon.py`
   - immutable/versioned `system_core.json` Anatomy versus learned Experience;
   - entities + typed causal links;
   - Bayesian confidence updates;
   - contextual fingerprints (thermal/logical/temporal/cross-module);
   - anomaly-prioritized retention;
   - information-gain-style `Wisdom vs Ballast` erosion;
   - Raw -> Dense -> Sparse aging;
   - structural hash changes degrade dependent causal links to legacy for revalidation rather than deleting history;
   - idle contradiction/revalidation pass.
2. Consciousness experience-space design
   - realized state snapshots represented as compact vectors with novelty/drift/recurrence semantics.
3. Quantum Reflector
   - QUBO/Simulated-Annealing projection of current state into a constrained binary compatibility space;
   - structural one-hot and pairwise coupling constraints;
   - state-dependent linear terms;
   - current-state energy versus low-energy candidate state and coherence gap;
   - repeated annealing runs expose energy spread.
4. Experiment Lab / NeRD Physics
   - deterministic/sandbox model-based prediction of selected dynamics.

The Quantum Reflector is therefore **not currently a complete external world model**; it is a constraint/coherence projection over a selected state vocabulary. That difference is useful and should be preserved.

## 2. Frankenstein 2.0 decision

Use:

```text
ONE DURABLE WORLD SUBSTRATE
        |
        +--> Vector/Causal Generative View
        +--> QUBO/Constraint Consistency View
        +--> Physics/Dynamics View when relevant
        +--> direct Observation Boundary
                 |
                 v
          CROSS-VIEW OVERLAY
                 |
          Hyperposition / GRID
```

Do **not** create two unsynchronized canonical world databases.

The durable substrate holds primitive atoms/operators/provenance/epistemic state. The different views are ephemeral projections of one `WorldNeed`/`WorldSlice`, computed through different inductive biases.

## 3. Why multiple views rather than one merged representation

The Vector/Causal view is strong at:

- continuous similarity;
- semantic generalization;
- open-world relations;
- partial evidence;
- compositional/lazy transforms;
- high-recall candidate generation.

The QUBO/Constraint view is strong at:

- explicit compatibility/incompatibility;
- discrete state alternatives;
- hard/soft constraints;
- mutually exclusive variables;
- global consistency inside a bounded active slice;
- exposing near-degenerate alternative configurations.

The Physics/MicroLab view is strong at:

- temporal/dynamical consequence;
- conservation/unit checks;
- contact/trajectory/state transition plausibility;
- counterfactual parameter sweeps.

These failure modes differ. Cross-view agreement can sharpen confidence; disagreement is itself information.

## 4. WorldBasis

Persistent conceptual base:

```text
WorldBasis {
  atom_id
  vector_payload
  typed_class
  relation/operator refs
  observed_or_inferred
  confidence/calibration
  provenance
  observed_at
  validity_scope
  structural_version
  causal_id
  generation
  privacy/NOT_COMPUTED taint
}
```

This is noncanonical predictive substrate. UnifiedDB remains canonical for exact observations, causal/effect state, provenance and epistemic class.

## 5. Vector/Causal Generative View

Input:

```text
WorldNeed
+ current observations
+ relevant WorldBasis atoms
+ current goal
+ causal/temporal/retrieval overlap
```

Output:

```text
VectorWorldView {
  candidate_states[]
  candidate_transforms[]
  support[]
  uncertainty[]
  missing_variables[]
  causal_paths[]
}
```

It should be high-recall and may retain contradictory candidates in Hyperposition.

Historical `world_experience` mechanisms to salvage here:

- causal link confidence;
- context fingerprints;
- anomaly score;
- structural-version-conditioned validity;
- information-gain-based evidence retention;
- old evidence compression.

## 6. QUBO/Constraint World View

Do not build one giant global QUBO over all world knowledge.

For each activated WorldSlice, lazily compile only relevant variables and constraints:

```text
active atoms / candidate relations
 -> discretization or bounded categorical variables
 -> hard constraints
 -> soft compatibility penalties
 -> observation-derived linear evidence terms
 -> anneal/solve
 -> top-K distinct low-energy configurations
```

Conceptual output:

```text
ConstraintWorldView {
  variable_schema
  hard_constraints
  soft_constraints
  top_k_states[]
  energies[]
  violations[]
  energy_gap
  degeneracy
  unsupported_variables[]
}
```

### Critical difference from historical Quantum Reflector

Do not return only one `best_state` as if it were reality.

The solver should preserve multiple distinct near-optimal solutions when their energy gap is small. This becomes a direct computational source for Hyperposition.

```text
small gap / high degeneracy -> uncertainty remains high
large separation + no violation -> stronger constraint support
```

QUBO feasibility means `consistent/compatible under encoded constraints`, **not true**.

## 7. Projection-independence law

If the QUBO penalties are mechanically generated from the exact same vector scores, agreement between Vector and QUBO is not independent corroboration.

Therefore use partially independent evidence construction:

- Vector view may use learned semantic/causal operators and similarity;
- QUBO hard constraints should primarily come from typed invariants, exact structural rules, verified causal exclusions, units/topology and explicitly accepted domain constraints;
- QUBO soft terms may use calibrated observation/causal priors, but their provenance must remain visible;
- Physics view should derive from explicit state/dynamics assumptions, not merely restate Vector scores.

The more independent the error mechanisms, the more informative cross-view agreement becomes.

## 8. Cross-View Overlay

Do not blindly average raw vector similarity, QUBO energy and physics scores because they have different scales.

Each view emits calibrated support/uncertainty/provenance. Initial fusion may use rank/calibrated evidence fusion; only use probability/log-odds fusion after calibration evidence exists.

Conceptual `WorldHypothesisEnvelope`:

```text
hypothesis_id
vector_support
constraint_support
physics_support?
observation_support
memory_support
cross_view_agreement
cross_view_conflict
unknowns
not_computed
next_best_discriminator
```

Interpretation:

```text
Vector high + QUBO compatible + Physics compatible + Observation match
 -> strong candidate

Vector high + QUBO hard violation
 -> inconsistent candidate; reject or revise unless constraint itself is disputed

Vector high + QUBO soft conflict
 -> keep in Hyperposition; seek discriminator

QUBO compatible + Vector low
 -> possible but not supported

Vector/QUBO agree + reality contradicts
 -> both model views lose causal credit; observation wins

all views uncertain
 -> OBSERVE / MICROLAB / ASK / HOLD depending expected value
```

## 9. Stereo sharpening by disagreement

The useful analogy is not two identical photographs averaged together.

It is stereo/parallax:

```text
same underlying situation
 -> different projection geometry
 -> disagreement exposes hidden variable / wrong assumption
 -> targeted sensing or experiment
 -> sharper reconstructed state
```

`DISAGREEMENT_IS_A_SENSOR`.

Cross-view disagreement should create one of:

```text
VisualNeed
PhysicsNeed
MicroLabCase
exact retrieval need
small real reversible experiment
HOLD with wake condition
```

rather than forcing consensus.

## 10. Integration with Retina

Retina already follows cheap-first progressive sharpening.

World modeling should mirror it:

```text
cheap current observation
 -> vector familiarity/causal projection
 -> constraint projection only if it adds information
 -> physics simulation only if dynamics matter
 -> deeper sensing only if disagreement/uncertainty matters
```

No full-world materialization.

## 11. Human-room example: fall/contact

```text
Retina View:
  downward trajectory, posture change, contact, post-contact motion

Vector World View:
  recent person state, scene familiarity, activity context, prior motion patterns

Constraint/QUBO View:
  support lost? feet/seat support? contact sequence compatible? mutually exclusive motion interpretations?

Physics View:
  plausible trajectory/impact range under uncertain height/mass/surface parameters

Overlay:
  physical concern distribution
  + distress/audio/context if available
  + post-event behavior
  -> GRID decides observe/ask/help/wait
```

The result is not an injury diagnosis and not an intent/violence fact. It is a better calibrated situational hypothesis.

## 12. Unknown interactive task example

```text
Observed state Z0
 -> Vector view proposes transforms T1/T2/T3
 -> QUBO view removes impossible/constraint-violating combinations
 -> MicroLab simulates cheap consequences
 -> GRID chooses action maximizing goal progress + information gain
 -> observed Z1
 -> separate prediction residual for each view
 -> update causal operators / constraints independently
```

This is directly usable for ARC-AGI-3-style held-out worlds.

## 13. Learning / credit assignment

Do not update all world-model views identically after an outcome.

For each verified transition:

```text
Observation Z0
Action A
Observed Z1

Vector prediction error -> update causal/vector operator confidence
QUBO constraint error    -> update/dispute soft constraint or structural mapping
Physics residual         -> update state estimate/model parameter bounds
```

Hard invariants are not silently modified by a model miss; a contradiction against a hard invariant creates an explicit invariant-dispute/fault path.

## 14. Historical WorldExperience features promoted to 2.0

### Structural version invalidation

Project-Frankenstein hashes its `system_core.json`; on change it degrades dependent causal links to `legacy` confidence rather than deleting them.

2.0 generalizes this:

```text
operator/schema/source version changes
 -> dependent predictions become STALE/LEGACY
 -> require revalidation under new version
```

### Wisdom-vs-Ballast retention

Repeated evidence that adds negligible information should not keep full high-fidelity payloads.

Promote:

```text
high anomaly OR high information gain -> retain richer evidence
redundant confirmation -> update sufficient statistics, discard heavy payload
age -> raw -> dense -> sparse projection
```

This strongly matches the Sparse Generative World Substrate goal.

### Fingerprints

Generalize old thermal/logical/temporal/cross-module fingerprints to typed situational context fingerprints:

```text
perceptual
physical
temporal
causal
goal/context
system/tool
```

They are evidence context, not the world itself.

## 15. Historical limitations not to inherit

Do not copy these literally:

- treating every pair with multiple relation types as a contradiction;
- blindly halving the lower-confidence relation rather than preserving contextual alternatives;
- treating QUBO minimum as truth;
- fixed global 39-variable schema for all domains;
- opaque exploration noise as evidence;
- metaphysical `quantum` terminology for a classical simulated-annealing solver;
- static hard-coded couplings without provenance/version/calibration;
- global daemons doing expensive work when no current WorldNeed exists.

## 16. Multi-projection acceptance tests

### MPW-01 same-slice identity
All views bind to the same WorldNeed/WorldSlice generation and source observation refs.

### MPW-02 hard contradiction
Vector candidate violates independently sourced hard constraint -> conflict is detected before action.

### MPW-03 soft disagreement
Soft QUBO disagreement does not delete vector hypothesis; Hyperposition remains open.

### MPW-04 top-K degeneracy
Near-equal QUBO minima produce multiple candidates, not false certainty.

### MPW-05 cross-view discriminator
Disagreement causes a cheaper targeted observation/MicroLab test that reduces ambiguity.

### MPW-06 reality wins
If all model projections agree but verified observation differs, canonical observation remains authoritative and model views receive negative causal credit.

### MPW-07 version invalidation
Change a structural/operator version -> dependent learned rules become legacy/stale until revalidated.

### MPW-08 retention compression
Repeated redundant confirmations update sufficient statistics without unbounded raw evidence growth; anomalies remain richer.

### MPW-09 lesion
Compare Vector-only, QUBO-only, Vector+QUBO, Vector+Physics and full overlay on held-out unknown interactive tasks.

### MPW-10 compute efficiency
QUBO/Physics projection is not invoked when cheap vector/observation evidence already meets the decision threshold.

## 17. Ablation matrix

Required held-out comparison:

```text
A observation + retrieval only
B + vector/causal world view
C + QUBO constraint view only
D + vector + QUBO overlay
E + vector + Physics
F + vector + QUBO + Physics
G full system + disagreement-driven active sensing/MicroLab
```

Measure:

```text
world prediction error
action regret
information gain per external action
false certainty
premature hypothesis collapse
cross-view disagreement resolution rate
compute latency
WorldSlice size
transfer gain
negative transfer
```

Promote the dual/multi-view architecture only if it beats the simpler view at acceptable compute cost.

## 18. Core law

```text
ONE WORLD BASIS
 !=
 ONE WORLD PICTURE

Generate several cheap, differently biased projections of the same relevant slice.
Agreement sharpens.
Disagreement identifies what to inspect next.
Reality remains the final discriminator.
```
