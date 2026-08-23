# World-model / strategic-supervisor contract

The HCU hosts a long-lived strategic computation layer, but it does **not** become a second entity.

## Canonical split

**MiniUnifiedDB owns durable reality.** The HCU owns computation over that reality.

The HCU world model is a rebuildable/provenance-bound projection of canonical state plus explicitly
typed simulations. Long-lived caches are allowed only when their source generation/provenance is
bound and stale data is rejected.

## Components

### Causal WorldModel Projector

Builds a temporal/causal graph over admitted MiniUnifiedDB events and outcomes. It may infer candidate
edges, but inferred edges remain typed as inferred until validated.

### Dynamic Goal Synthesizer

Generates candidate objectives from:

- explicit owner/user goals;
- unresolved high-value contradictions;
- maintenance/recovery obligations;
- prediction error;
- resource opportunities;
- validated method-memory.

A generated goal has no effect authority. Goal admission remains subject to canonical policy.

### Simulation Farm

Runs bounded long-horizon counterfactuals and competing plans. Every branch is `SIMULATED`, carries
horizon/provenance and must preserve uncertainty rather than collapse it into truth.

### Zero Cognition Twin

Models Zero's likely behavior using observable/configured information:

- Zero runtime/configuration version;
- prior canonical turns and outcomes;
- accepted J-Space/GWT telemetry available at the system boundary;
- adapter/capability receipts;
- known failure modes.

It must not claim direct access to private model hidden state when no admitted mechanism exposes it.

### Hypothesis Compiler

Converts mismatches between prediction and observed outcomes into falsifiable Zero/EntityOS
improvement hypotheses:

```text
HCU_ZERO_HYPOTHESIS/v1 {
    hypothesis_id
    observed_anchor_ids
    predicted_behavior
    observed_behavior
    proposed_mechanism
    strongest_counterhypothesis
    falsifier
    bounded_intervention
    expected_observations
    authority = CANDIDATE_ONLY
}
```

Hypotheses are fed back to the canonical `go`/`zero` work selection and UCF/GWT path. They do not
self-modify EntityOS or bypass review/evidence gates.

## Recovery

After HCU restart:

1. bind to the current MiniUnifiedDB entity generation;
2. discard/mark stale ephemeral work from prior generations;
3. rehydrate world-model projections from canonical state;
4. preserve uncertain external-effect outcomes as UNKNOWN;
5. resume only simulation branches whose provenance and generation remain admissible.
