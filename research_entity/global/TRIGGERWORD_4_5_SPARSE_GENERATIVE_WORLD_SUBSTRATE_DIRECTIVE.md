# TRIGGERWORT 4/5 — Sparse Generative World Substrate / JIT World Extrapolation

Status: PROJECT-OWNER ARCHITECTURE EXTENSION
Date: 2026-08-28
Applies to: Triggerword 4 build lane + Triggerword 5 forensic/ingest lane

## 1. Core idea

Frankenstein 2.0 shall not maintain a permanently materialized monolithic world model. It shall maintain an external, sparse, vector-native generative substrate from which GRID10 can materialize only the task-relevant local structure needed for the current cognitive cycle.

Target law:

`WORLD != STORED COMPLETE GRAPH`

Instead:

`primitive state vectors + typed transformation operators + current boundary/end-state vectors + provenance/uncertainty -> just-in-time local world slice`

The complete world model does not need to exist at once. A useful local model may exist for milliseconds, participate in Hyperposition/GWT, then disappear while its evidence and learned transformation updates remain durable.

## 2. Recursive decomposition / generative composition

Represent complex entities as lazily decomposable compositions. Example only:

`human -> organs -> tissues -> cells -> molecular/genetic components`

The system does NOT need to recursively expand every entity to maximal physical depth on every query. Decomposition is lazy and convenience/information-gain gated.

Each entity/concept may have:

- primitive/source vector(s);
- composition operator(s);
- decomposition operator(s);
- relation operators;
- state variables;
- transformation parameters;
- valid domains/ranges;
- uncertainty/provenance refs;
- temporal validity / decay;
- reversible/approximately-invertible links where justified.

Forward composition example:

`z_human ≈ Compose(z_dna, z_cells, z_organs, z_context, θ)`

Reverse inference example:

`{z_dna?, z_organs?, ...} ≈ Decompose(z_human, constraints, evidence)`

Reverse inference is a hypothesis generator, not truth. Multiple inverse explanations remain in Hyperposition until discriminating evidence arrives.

## 3. Vector-native, not vector-only authority

The semantic/world payload is vector-native. Exact authority/provenance/epistemic metadata must remain typed outside the vector so that similarity cannot silently become truth.

Minimum metadata around every vector atom/operator:

```text
atom_id / operator_id
vector_space_version
source/evidence refs
observed | inferred | simulated | learned-rule
KNOWN | UNKNOWN | CONFLICT | NOT_COMPUTED
confidence / uncertainty
valid_from / valid_to / decay
causal_id / generation
privacy tags
operator version
```

This preserves UnifiedDB's exact epistemic/causal guarantees while allowing the world representation itself to be mathematically compact.

## 4. Start vector / end vector model

For a current cognitive question, the loop should prefer two bounded sets:

- `Z0`: relevant starting/boundary vectors (observed state, known constraints, memories, environment variables);
- `Zt`: relevant current/desired/predicted endpoint vectors.

It then selects only the transformation chain required to bridge them:

`Z0 --T1--> Z1 --T2--> ... --Tk--> Zt`

The chain may be forward, reverse or bidirectional. Intermediate states are scratch projections unless separately observed/verified.

The cognitive loop normally does not need the whole world graph; it needs the smallest transformation subspace that can discriminate current hypotheses or advance the current GoalContract.

## 5. Convenience / overlap / emergent activation

World-slice expansion follows the Retina principle: cheap, local, sparse and progressively sharpened.

Candidate atoms/operators receive activation from overlapping dimensions such as:

- current GoalContract relevance;
- semantic/vector similarity;
- causal proximity;
- temporal proximity;
- current perception;
- expected information gain;
- prediction-error relevance;
- current Hyperposition alternatives;
- unresolved completion deficits;
- novelty;
- confidence/uncertainty;
- resource cost;
- privacy/authority constraints;
- user convenience / interruption context where applicable.

No single similarity score decides retrieval. Activation emerges from intersection/overlap of independent signals.

Conceptual form:

`activation_i = F(goal, semantic, causal, temporal, perceptual, novelty, uncertainty, cost, policy, current_hyperposition)`

Expansion stops when marginal expected cognitive value falls below its compute/memory/latency cost or when the current discrimination/completion requirement is satisfied.

## 6. Just-in-time extrapolation

GRID10 asks for a bounded `WorldNeed`, not the full database.

```text
WorldNeed {
  cycle_id
  goal_id
  question_vector
  start_vector_refs[]
  endpoint_constraints[]
  required_variables[]
  max_depth
  max_atoms
  max_latency_ms
  max_compute
  uncertainty_target
  privacy_scope
  causal_scope
}
```

The World Substrate returns a noncanonical `WorldSlice`:

```text
WorldSlice {
  slice_id
  cycle_id
  selected_atoms[]
  selected_operators[]
  Z0
  candidate_Zt[]
  trajectories[]
  unresolved_alternatives[]
  predicted_discriminators[]
  evidence_refs[]
  counterevidence_refs[]
  uncertainty
  provenance_digest
  expiry
}
```

The slice enters Hyperposition/GWT as candidate structure. It never becomes canonical world truth by retrieval alone.

## 7. External database

The durable world substrate should live outside the hot GRID process in an external local database/service optimized for:

- vector atoms;
- sparse typed relations/operators;
- versioned transform parameters;
- exact metadata/provenance indexes;
- decay/tombstone state;
- fast bounded neighborhood expansion;
- append/reconcile/rebuild workflows;
- snapshots and recovery.

The database is not canonical authority over reality. Canonical observations/effects remain governed by UnifiedDB/Effect/Completion semantics. The world substrate is a learned/model projection layer whose claims are always traceable back to evidence or learned-rule provenance.

## 8. Two internal Xeno maintenance roles

Use one or two lightweight Xeno maintenance organs. They are functions, not independent sovereign agents.

### Xeno A — Assimilator / Composer

Continuously consumes admitted new observations, memory deltas, verified outcomes and model-learning candidates.

Responsibilities:

- factor new information into the smallest useful reusable vector atoms;
- link/combine atoms through existing operators;
- propose new operators when repeated transitions justify them;
- update confidence/temporal statistics;
- preserve contradictions rather than overwrite them;
- avoid duplicating semantically equivalent atoms;
- attach exact evidence/provenance refs.

### Xeno B — Gardener / Falsifier / Compressor

Continuously maintains substrate quality.

Responsibilities:

- decay stale low-value projections;
- remove/tombstone unsupported or superseded noncanonical atoms;
- detect duplicates and collapse equivalent representations;
- run inverse/forward consistency checks;
- compare predicted transitions with verified outcomes;
- downgrade rules that fail;
- promote reusable transformation patterns only after evidence thresholds;
- maintain bounded size/latency and rebuild indexes.

For minimal hardware, A and B may time-share one physical Xeno. For stronger operation, two logical Xeno roles may run concurrently on shared weights.

Neither Xeno may grant itself canonical truth or external effect authority.

## 9. Mutating capability token / cognition-only access

Direct arbitrary reads of the world substrate by ordinary executors, voice models or tools are forbidden. Access is through a GRID/XPU world-model adapter using short-lived, scope-bound capabilities.

Use a mutating capability chain, conceptually:

`cap_0 = Issue(epoch, cycle_id, goal_id, scope, nonce, expiry)`

`cap_{n+1} = Mutate(cap_n, request_digest, slice_digest, generation)`

Properties:

- opaque to LLMs where possible;
- generated/validated by deterministic control-plane code, not model text;
- bound to cycle, GoalContract, generation, scope and expiry;
- short TTL;
- each expansion/read advances or derives a new capability;
- stale/replayed capability is rejected;
- no capability text is stored in prompts, normal logs or durable memory;
- only the cognitive-loop adapter may request `WorldSlice` materialization;
- executor/Voice receives only the compiled result that GRID chooses to expose.

Maintenance Xeno uses a separate bounded writer capability class; writer tokens never imply reader/effect authority.

This is a containment and coupling mechanism, not a claim of cryptographic security unless the concrete implementation is separately audited.

## 10. Relationship to Retina

Retina is the reference pattern:

`cheap signal -> overlap/familiarity -> uncertainty -> selective sharpening -> event`

World substrate generalizes this to cognition:

`primitive vectors -> overlap/goal activation -> sparse transform chain -> uncertainty -> selective expansion -> temporary WorldSlice`

Both should support editable processing heads and `COMPUTE_OFF / OUTPUT_OFF / MEMORY_OFF`-like semantics where meaningful.

A disabled world-model variable/head must remain `NOT_COMPUTED`, not silently reconstructed through a downstream dependency. Dependency taint propagation is therefore required for protected world-model dimensions just as in Perception Control.

## 11. GRID10 integration

Recommended cognitive sequence:

```text
canonical observations + goal + current memory
        -> WorldNeed
        -> capability issue
        -> sparse world retrieval
        -> transform/extrapolation
        -> candidate trajectories
        -> Hyperposition
        -> counterhypothesis / discriminator generation
        -> GWT fusion
        -> decision / VisualNeed / ASK / ACT / WAIT
        -> observed outcome
        -> prediction error
        -> Xeno Assimilator/Gardener update
        -> next cycle
```

World modelling is therefore not a permanent second brain beside GRID10. It is a dynamically materialized cognitive organ called from the loop.

## 12. Counterfactuals and simulation

`WM_TEST` / `NESTED_SIM` may use the same substrate but write to L3/simulation branches only.

Simulation may fork candidate endpoint vectors and transformation paths:

`Z0 -> {trajectory A, trajectory B, trajectory C}`

These branches remain explicitly simulated. Only real observation can close prediction error against canonical state.

## 13. Mutation / learning rule

Verified transition:

`observed Z0 + executed action/effect + observed Zt`

may update a transform operator candidate.

Unverified model-generated transition:

`predicted Z0 -> Zt`

may never receive the same learning credit.

Preferred update law:

`verified outcomes >> corroborated observations >> inferred relations >> pure simulation`

Negative results and failed predictions are first-class training/maintenance signals.

## 14. Human-editable Cognitive Twin

The real world substrate remains machine-oriented and sparse. Human visibility comes through a read-only Cognitive Twin projection.

The Twin may visualize:

- currently activated primitive variables;
- selected transform chain;
- candidate endpoints;
- Hyperposition alternatives;
- convenience/activation contributions;
- confidence/uncertainty;
- why expansion stopped;
- which variables/heads are disabled;
- prediction error after outcome.

Human edits modify policy/config/operator approval through gated control paths; they do not directly mutate canonical reality state.

## 15. Acceptance tests

At minimum prove:

1. same WorldNeed reconstructs a useful bounded structure without loading a whole model;
2. irrelevant atoms remain untouched;
3. decomposition depth adapts to the task;
4. forward composition can predict a known endpoint within calibrated uncertainty;
5. reverse decomposition yields alternatives rather than false certainty;
6. Hyperposition preserves multiple plausible trajectories;
7. stale/replayed capability tokens are rejected;
8. executor/Voice cannot directly query the world DB;
9. Xeno maintenance cannot mint canonical/effect authority;
10. verified outcomes update operator confidence while simulated outcomes do not receive equal credit;
11. old/low-value projections decay/tombstone without deleting canonical evidence;
12. latency/memory are bounded and measured;
13. lesion of convenience-overlap routing causes measurable retrieval/quality/cost regression versus the normal path;
14. protected `COMPUTE_OFF` variables remain `NOT_COMPUTED` through downstream dependency chains.

## 16. Triggerword behavior

Triggerword 5 should mine current Frankenstein/Research-Entity/Xeno material for mechanisms that can populate or constrain this substrate, especially Retina/Familiarity, Emergent Retrieval, typed epistemics, Hyperposition, action-grounded memory, causal outcomes, graph/vector routing and current world-model experiments.

Triggerword 4 should implement this incrementally only after the relevant GRID/UnifiedDB control gates are stable. Start with a tiny synthetic/local substrate and falsification suite, then connect real observations and Xeno maintenance. Do not attempt to ingest "the whole world" before proving sparse JIT reconstruction works.
