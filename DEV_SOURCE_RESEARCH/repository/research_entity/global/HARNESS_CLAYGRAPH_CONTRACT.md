# Harness ↔ ClayGraph Contract

**Status:** PROJECT_OWNER_FIXED_RELEASE INVARIANT
**Applies to:** every Reference Harness, Clay Harness, successor Harness and every material Harness experiment/replay

## 0. Hard law

Every Harness is built and evaluated as a pair:

`Harness implementation <-> Harness ClayGraph`

A Harness without its own current ClayGraph is incomplete and cannot release PASS.

The ClayGraph is not decorative documentation. It is the machine-readable structural and dynamical representation of the FRANK organism instantiated by that Harness.

## 1. Two required graph layers

### A. Static Architecture ClayGraph

Each Harness release must carry one frozen architecture graph representing at minimum:

- modules/subsystems;
- canonical state domains;
- typed state variables;
- causal/dependency edges;
- recurrent/re-entry edges;
- gating/inhibition/modulation edges;
- resource/authority boundaries;
- provenance dependencies;
- memory/Assembly relationships;
- GWT candidate/competition/workspace/receiver relations;
- personality/self/world/body/goal relations;
- UnifiedDB logical/query/state relations;
- Needle boundary relations;
- multiple timescales and delays;
- persistence/epoch domains;
- boot/order dependencies;
- recovery dependencies;
- intervention/lesion handles;
- source/version/provenance for every node/edge.

Required artifacts:

- Reference Harness: `REFERENCE_HARNESS_ARCHITECTURE.claygraph.json`
- Clay Harness: `CLAY_HARNESS_ARCHITECTURE.claygraph.json`

### B. Dynamic Run ClayGraph

Every Golden Trace, material experiment and differential replay must be able to emit a run-scoped graph/delta that records what actually became causally active.

At minimum:

- nodes/edges activated;
- pre/post state hashes for changed nodes;
- edge inputs/outputs;
- timing/order;
- gating decisions;
- winner/loser competition state;
- GWT addressability/delivery/reconstruction/uptake/causal-use/outcome/re-entry stages;
- memory retrieval vs admissibility vs consequential-use path;
- goal/personality/body state influences;
- effect/authority/resource path if applicable;
- provenance/source epochs;
- intervention/ablation applied;
- observed downstream delta.

Suggested artifact pattern:

`traces/<trace_id>/RUN_CLAYGRAPH.json`

or a deterministic graph-delta equivalent.

## 2. Reference Harness graph

The Reference Harness must generate/validate its ClayGraph from the same frozen architecture/state contracts it executes.

It must not maintain one executable architecture and a separately hand-maintained graph that can drift.

Required invariant:

`executed_architecture_hash == graph_declared_architecture_hash`

or an explicit typed derivation/normalization proof if the byte representations differ.

## 3. Clay Harness graph

The Clay Harness must generate/validate its own ClayGraph from the same frozen architecture but through the ClayCode implementation.

Required invariant:

`Clay Harness semantics -> Clay Harness ClayGraph`

The graph must not simply copy the Reference Harness graph as a static fixture. Its nodes/edges/state identities must be derived from or validated against the Clay Harness implementation so divergence can be detected.

## 4. Cross-Harness graph differential

Before Clay Harness PASS, compare:

1. Reference Harness execution state;
2. Reference Harness ClayGraph;
3. Clay Harness execution state;
4. Clay Harness ClayGraph.

The differential oracle must verify at least:

- node-set equivalence under declared mapping;
- edge/coupling equivalence;
- type/state-domain equivalence;
- timescale/order equivalence;
- persistence/epoch equivalence;
- GWT causal-stage equivalence;
- memory/admissibility path equivalence;
- goal/personality/body coupling equivalence;
- authority/effect boundary equivalence;
- intervention-handle equivalence;
- dynamic activation graph equivalence on Golden Traces;
- equivalent pre/post canonical state transitions after allowed representation normalization.

Required artifact:

`HARNESS_CLAYGRAPH_DIFFERENTIAL_VALIDATION.json`

No unexplained topology or dynamic causal-use divergence is allowed for PASS.

## 5. Relationship to the ClayGraph research branch

Harness graphs are consumers and executable test surfaces of the current ClayGraph branch semantics.

The ClayGraph branch remains responsible for deeper associative-memory/graph research and graph evolution. Harness may not silently redefine ClayGraph semantics.

Conversely, Harness-discovered graph defects, missing relation types, impossible provenance requirements, performance cliffs or intervention failures are scientific feedback and must be returned to the ClayGraph branch.

## 6. Relationship to architecture archaeology

Every static Harness ClayGraph must map its important nodes/edges to architecture-archaeology lineage IDs when historical predecessors exist.

This permits questions such as:

- Which current coupling descends from which Project-Frankenstein mechanism?
- Which historical bug affected this edge?
- Which current intervention tests the old design assumption?
- Which coupling is new with no historical predecessor?

Recommended node/edge fields:

- `lineage_ids`
- `first_project_version`
- `historical_failure_refs`
- `current_evidence_refs`
- `originality_class`

## 7. Emergent-coupling requirement

The graph must represent FRANK as a multi-timescale recurrent dynamical system rather than a simple call DAG.

At least these edge classes must be expressible:

- feed-forward;
- feedback;
- recurrent;
- inhibitory;
- excitatory/amplifying;
- gating;
- normalization;
- reward/credit;
- broadcast;
- re-entry;
- provenance;
- authority/resource;
- persistence;
- timing/order.

## 8. Release gate

A Harness release cannot PASS unless:

- static ClayGraph exists;
- graph validates against executable architecture;
- Golden Traces emit dynamic graph evidence;
- intervention/lesion handles are represented;
- archaeology lineage mapping coverage is measured;
- graph/state drift checks pass;
- for Clay Harness, cross-Harness graph differential passes.

## 9. Compact law

`no Harness without ClayGraph`

`no Clay Harness PASS without graph differential against Reference Harness`
