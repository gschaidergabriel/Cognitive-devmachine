# TRIGGERWORT 4 — Cognitive Micro-Lab + NeRD Physics + Consistency Simulation

Status: FUSED ARCHITECTURE ADDENDUM
Date: 2026-08-28
Source archaeology: `gschaidergabriel/Project-Frankenstein@39c5423e0bfae54b971aab0be82f225f7a5890b8`

This addendum extracts useful mechanisms from the historical Project-Frankenstein Experiment Lab, Hypothesis Engine, NeRD Physics, Invariants Engine, Quantum Reflector and Autonomous Research into the Frankenstein 2.0 cognitive loop. It does not restore the old services wholesale.

## 1. Core decision

Frankenstein 2.0 shall contain a **short-lived Cognitive Micro-Lab inside the GRID cognitive loop**.

It is not a separate cognitive agent and not a permanently materialized simulated universe.

It exists only when a current hypothesis, uncertainty, physical question, causal question or completion deficit has enough expected value to justify internal simulation.

Target:

```text
Observation / task / goal
  -> Emergent Retrieval
  -> WorldNeed / PhysicsNeed / ConsistencyNeed
  -> relevant primitive variables + transform operators
  -> ephemeral MicroLabCase
  -> cheapest adequate deterministic/sandbox simulator
  -> one or more candidate outcomes
  -> invariant/consistency checks
  -> SimulationEvidence
  -> Hyperposition / GRID / GWT
  -> discriminating real observation/action if still needed
  -> verified outcome
  -> prediction error / model update
```

`SIMULATION_EVIDENCE != REALITY_EVIDENCE`.

## 2. Historical Experiment Lab mechanisms to preserve

The historical `services/experiment_lab.py` already implemented a strong pattern:

- common `parse -> simulate -> narrate` station interface;
- deterministic pure local computation for fixed parameters;
- no external HTTP and no LLM inside the simulation core;
- hard per-run timeout;
- experiment budget;
- exact-input dedupe/cache;
- persistent experiment IDs/results;
- hypothesis ID binding;
- rejection of narrative/imagination contamination;
- multiple computational backends (physics, quantum/toy state models, astronomy, cellular automata, electronics, math, GAN).

Frankenstein 2.0 keeps the architecture pattern but changes the interface from natural-language station detection to typed world primitives.

Do not preserve the requirement for seven fixed narrative stations.

## 3. MicroLabCase ABI

Conceptual typed request:

```text
MicroLabCase {
  case_id
  causal_id
  generation
  goal_id?
  source_observation_refs[]
  source_worldslice_id?
  question_type
  primitive_state[]
  transform_candidates[]
  hypotheses[]
  unknowns[]
  protected_not_computed[]
  requested_outputs[]
  max_compute_ms
  max_trials
  random_seed_policy
  acceptable_model_error
}
```

Question types may include:

```text
PHYSICS_PREDICTION
COUNTERFACTUAL
CAUSAL_DISCRIMINATOR
MATHEMATICAL_CONSISTENCY
CONSTRAINT_SATISFACTION
STATE_REACHABILITY
PARAMETER_SENSITIVITY
OUTCOME_BOUNDS
COMPLETION_PLAUSIBILITY
```

## 4. SimulationEvidence ABI

Micro-Lab output is explicitly noncanonical:

```text
SimulationEvidence {
  case_id
  simulator_id
  simulator_version
  assumptions[]
  inputs[]
  predicted_outcomes[]
  outcome_distribution_or_bounds
  invariant_checks[]
  sensitivity[]
  model_scope
  model_limitations[]
  numerical_error_bound?
  confidence
  discriminator_value
  compute_cost
  provenance
}
```

It must never be silently promoted into `ObservedEvidence`.

## 5. NeRD Physics successor role

Historical NeRD Physics already contains useful local mechanics:

- 100 Hz semi-implicit Euler;
- gravity;
- simplified body/joint state;
- forward kinematics;
- contact detection;
- spring-damper contact forces;
- locomotion/reach state;
- optional learned dynamics with periodic analytical comparison.

For Frankenstein 2.0, NeRD becomes a **PhysicsNeed backend** rather than a permanent imaginary-avatar dependency.

Use it when perception/task state contains physically relevant uncertainty, e.g.:

```text
object trajectory
fall / loss of balance
collision
impact
reachability
support / tipping
moving object interaction
rough projectile path
rough contact sequence
physical plausibility of observed motion
```

The input should be reduced to the smallest adequate primitives inferred from Retina/WorldSlice:

```text
positions / coarse geometry
estimated masses or bounded classes
velocities / accelerations
support/contact relations
gravity
friction bounds
obstacle surfaces
uncertainty intervals
```

Do not require a full photorealistic scene reconstruction.

## 6. Human-room physical reasoning

When Retina sees an event with meaningful physical uncertainty, GRID may emit `PhysicsNeed`.

Example fall:

```text
Retina:
  person vertical -> rapid downward motion -> ground/contact -> motion reduction

WorldSlice:
  approximate height range
  body orientation range
  contact surface class
  observed velocity bounds

NeRD/MicroLab:
  candidate trajectories
  approximate impact velocity/energy proxies
  expected post-impact motion patterns

GRID overlap:
  PhysicsEvidence
  + visual continuity
  + audio/distress signal
  + user behavior afterward
  + context/history
  -> concern hypothesis distribution
```

The system must **not diagnose injury from physics alone**. It may conclude e.g. `LOW / MODERATE / HIGH CONCERN GIVEN OBSERVED IMPACT`, with explicit uncertainty, and seek confirming evidence or ask the user when appropriate.

Similarly, physical simulation can contribute to `playful contact vs potentially harmful impact` hypotheses, but cannot determine intent or violence by itself. GRID must overlap:

```text
motion/impact dynamics
+ repeated-contact pattern
+ mutual approach/avoidance
+ distress/laughter/audio cues if permitted
+ contextual continuity
+ post-event behavior
+ uncertainty
```

Ambiguous cases remain ambiguous.

## 7. Task/world physics reasoning

The same backend applies to abstract or benchmark tasks.

For an unknown interactive environment:

```text
Observed transition
 -> infer primitive object/action variables
 -> hypothesize transform
 -> MicroLab simulate candidate next states
 -> choose cheapest discriminating environment action
 -> compare observed next state
 -> update transform operator
```

This directly supports ARC-AGI-3-style exploration/world-model tests without hardcoding ARC game mechanics.

## 8. Hypothesis Engine successor

Historical `HypothesisEngine` explicitly implemented:

```text
Observe -> Hypothesize -> Predict -> Test -> Revise
```

and could automatically send experimentally testable hypotheses to the Lab, bind experiment IDs, resolve/refute, and create revisions.

Frankenstein 2.0 folds this into GRID/Hyperposition instead of keeping a competing daemon.

Required behavior:

```text
Hypothesis
 -> predicted measurable consequence
 -> testability classifier
 -> choose PASSIVE_OBSERVATION | MICROLAB | REAL_EXPERIMENT | DEFER
 -> result
 -> CONFIRM / REFUTE / INCONCLUSIVE
 -> revision or retirement
```

Refutation must preserve lineage and negative-result memory.

## 9. Invariants Engine successor

Historical Invariants included conservation-style bounded knowledge growth, entropy/conflict limits, a protected core and a triple-reality convergence scheme.

Do **not** inherit its claimed mathematical proof of guaranteed convergence as established fact.

Salvage the useful engineering pattern:

- hard constraints live outside ordinary cognitive voting;
- a small protected consistent core may be maintained;
- conflict/entropy budgets can trigger consolidation rather than silent overwrite;
- independent simulation seeds/models can reveal unstable regions;
- persistent divergence should remain `CONFLICT/UNSTABLE`, not be forced into false consensus.

For Micro-Lab this becomes `ConsistencyKernel`:

```text
hard invariants
soft constraints
unit/dimension checks
conservation checks where applicable
topological/logical constraints
known impossible-state filters
policy NOT_COMPUTED taint
```

## 10. Quantum Reflector successor

Historical Quantum Reflector was in practice a classical QUBO/annealing coherence optimizer over a discretized Frank state. It built static structural constraints plus dynamic state-dependent terms and monitored current-vs-low-energy solution gaps.

The useful mechanism is **constraint optimization**, not a quantum claim.

Frankenstein 2.0 may salvage it as a `ConstraintConsistencySolver` backend:

```text
candidate state variables
+ one-hot/exclusion constraints
+ pairwise compatibility/penalty terms
+ current evidence weights
-> low-cost candidate configurations
-> energy/violation/gap report
```

It may be useful for:

- selecting mutually compatible hypothesis bundles;
- checking state consistency;
- bounded planning configurations;
- comparing current cognitive state against constraint-respecting alternatives.

It must not collapse Hyperposition merely because one low-energy assignment exists; multiple near-optimal states remain candidates when evidence is insufficient.

## 11. Autonomous Research successor

Historical `autonomous_research.py` already provided a bounded loop:

```text
idle question
 -> worth-researching gate
 -> 3-8 step plan
 -> restricted tools
 -> max tool-call budget
 -> experiment / hypothesis / code sandbox / web / memory
 -> synthesis
 -> memory
```

Frankenstein 2.0 folds this into Persistent Agency + GRID as `ResearchPulse` rather than a separate autonomous brain.

It is useful when a goal has a factual or model deficit that cannot be closed locally.

## 12. Cheap-first simulator router

GRID chooses the cheapest simulator capable of discriminating the current hypotheses:

```text
R0a exact algebra / SymPy / units
R0b simple analytical physics
R0c constraint solver / QUBO-like optimizer
R0d discrete automaton / graph / state-transition simulation
R0e NeRD coarse kinematics/contact dynamics
R0f sandboxed Python numerical simulation
R1 model-assisted simulator construction only when deterministic backends are insufficient
R2 delegated child workpackage for genuinely complex experiment/model building
```

Default policy:

```text
DO NOT SPAWN A CHILD
if a 2-20 ms deterministic calculation answers the discriminator.
```

## 13. Emergent overlap integration

Micro-Lab is fed by the same overlap architecture as Retina/World Substrate.

It does not inspect all known physics/world variables.

Activation is computed from:

```text
current observation
+ goal relevance
+ causal proximity
+ physical salience
+ uncertainty
+ predicted consequence
+ memory/world operators
+ available simulator cost
```

Only the activated variables are materialized into the MicroLabCase.

This is crucial for low cost and for avoiding a full persistent simulation world.

## 14. Counterfactual micro-simulation

GRID may create multiple ephemeral variants:

```text
Observed Z0
  -> H1 parameters -> predicted Z1a
  -> H2 parameters -> predicted Z1b
  -> H3 parameters -> predicted Z1c
```

Then it chooses either:

- the hypothesis already strongly discriminated by observation;
- a cheap new sensor/VisualNeed;
- a real reversible test;
- HOLD if the difference has no current value.

## 15. Post-effect use

Micro-Lab also participates after a real effect:

```text
predicted outcome
+ real observed outcome
-> residual / prediction error
-> determine whether error came from
   bad state estimate | bad transform | hidden variable | execution failure
-> update World Substrate / Method Memory / Hypothesis lineage
```

## 16. Privacy and perception boundary

Micro-Lab receives typed primitives, not raw camera frames by default.

If a perception variable is `COMPUTE_OFF`, it must remain `NOT_COMPUTED` and may not be reconstructed through a simulator or world-model operator.

`SIMULATION_CANNOT_UNDO_PERCEPTION_POLICY`.

## 17. Safety/epistemic boundary for human physical events

Physics can estimate motion and impact plausibility. It cannot by itself establish:

- medical diagnosis;
- internal injury;
- criminal intent;
- whether contact was consensual/playful/violent;
- identity.

Those remain uncertainty-aware higher-level hypotheses with other evidence and, where warranted, direct human confirmation/emergency policy.

## 18. Acceptance tests

### CML-01 deterministic repeat
Same typed inputs/seed -> same deterministic result where backend is deterministic.

### CML-02 world-state isolation
Simulation scratch cannot mutate UnifiedDB canonical state.

### CML-03 NOT_COMPUTED taint
Protected missing variable cannot be regenerated downstream.

### CML-04 physics prediction
Known coarse trajectory/contact case -> predicted state within declared tolerance.

### CML-05 sensitivity
Uncertain input interval -> outcome range/sensitivity rather than false point certainty.

### CML-06 hypothesis discriminator
Competing transform hypotheses -> simulation identifies an observation/action that distinguishes them.

### CML-07 real-outcome correction
Wrong simulation prediction -> verified real outcome produces model revision rather than memory overwrite.

### CML-08 ambiguous human event
Insufficient fall/contact evidence -> output remains uncertainty/concern score, not injury/intent fact.

### CML-09 ARC-style unknown mechanics
Micro-Lab improves action efficiency on held-out interactive worlds without game-specific rules.

### CML-10 lesion
Disable Micro-Lab -> compare world-prediction error/action regret against enabled condition on matched held-out tasks.

### CML-11 cheap-first routing
Simple algebra/analytical problem does not invoke expensive simulator/model/child.

### CML-12 constraint multi-solution
Near-equivalent consistent configurations remain Hyperposition alternatives rather than forced single answer.

## 19. Assembly placement

Insert this capability after Research-Entity substrate / sparse world primitives are available and before or alongside full GRID canonical-control acceptance.

Recommended build sequence refinement:

```text
Stage 3    Research-Entity cognitive substrate
Stage 3.5  Context virtualization / recursive harness primitives
Stage 3.75 Cognitive Micro-Lab vertical slice
           - exact math/units
           - simple physics
           - typed SimulationEvidence
           - consistency kernel
Stage 4    Sparse world/GRID integration
Stage 4.25 NeRD physics + counterfactual expansion
           - perception PhysicsNeed
           - world-task PhysicsNeed
           - prediction-error re-entry
Stage 4.5  adaptive recursion/test-time compute
```

Do not block Stage 3.75 on rebuilding every historical Lab station.

## 20. Core law

```text
SEE / RETRIEVE
 -> REDUCE TO RELEVANT PRIMITIVES
 -> SIMULATE ONLY WHAT MATTERS
 -> KEEP ALTERNATIVES
 -> CHECK CONSISTENCY
 -> SEEK REAL EVIDENCE WHEN NEEDED
 -> LEARN FROM THE RESIDUAL
```

The Micro-Lab is an internal experimental instrument of GRID, not an oracle.
