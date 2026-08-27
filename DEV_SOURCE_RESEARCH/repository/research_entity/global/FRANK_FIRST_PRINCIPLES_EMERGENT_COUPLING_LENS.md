# FRANK First-Principles & Emergent-Coupling Analysis Lens

**Status:** MANDATORY INTERPRETIVE LENS
**Applies to:** Project-Frankenstein archaeology, FRANK architecture, ClayCode, Reference Harness, Clay Harness, GWT, ClayGraph, UnifiedDB, Hyperposition, Emergenz

## 0. Owner design principle

A major part of Project-Frankenstein was developed by logical derivation from desired system behavior rather than by starting from conventional software patterns. The recurring design substrate is **emergent coupling**: many relatively simple state variables, gates, feedback loops, memories, rewards, resource constraints and timing relations interact so that higher-order behavior appears at the system level.

GWT is one important organizing example, but the analysis must not assume that every mechanism is merely an implementation of an existing GWT template.

Compact design law:

`target behavior + first-principles constraints -> local state variables/rules -> recurrent coupling -> higher-order system behavior`

## 1. Do not decompose away the invention

For every subsystem, archaeology must analyze both:

### Local mechanism
What does the module compute or enforce by itself?

### Coupling role
What changes only because this module interacts with other stateful modules over time?

A mechanism may be ordinary in isolation but innovative in its coupling topology, timing, feedback direction, state persistence, gating conditions or interaction with other modules.

Therefore:

`component novelty != system-level coupling novelty`

and

`known component + novel coupling can be a genuine project innovation candidate`.

## 2. First-principles reconstruction template

For every material mechanism or architecture family reconstruct:

1. **Target phenomenon / engineering objective** — what behavior was desired?
2. **Logical constraints** — what must be true for that behavior to exist?
3. **Minimal state variables** — what quantities were introduced to represent those constraints?
4. **Local update rules** — equations, thresholds, decay, reinforcement, inhibition, normalization, budgets, gates.
5. **Coupling edges** — which state influences which other state?
6. **Directionality** — feed-forward, feedback, recurrent, inhibitory, modulatory, broadcast, re-entry.
7. **Timescales** — milliseconds, seconds, minutes, hours, days, training cycles.
8. **Persistence** — which states survive turns/restarts/sessions?
9. **Competition / cooperation** — which processes compete for attention/resources and which reinforce each other?
10. **Boundary conditions** — saturation, reset, failure, resource exhaustion, stale state, missing input.
11. **Emergent prediction** — what system-level behavior should arise if the coupling works?
12. **Failure prediction** — what should disappear or distort when an edge/state/module is lesioned?
13. **Observed history** — did Project-Frankenstein exhibit the predicted behavior/failure?
14. **Current falsifier** — what experiment in the Harness can distinguish the mechanism from simpler explanations?

## 3. Coupling graph as a first-class artifact

Maintain a machine-readable cross-version coupling graph.

Each edge should bind at least:

- source mechanism/state;
- target mechanism/state;
- sign/type: excitatory, inhibitory, gating, normalization, reward, provenance, authority, broadcast, re-entry, resource;
- functional equation or rule if known;
- timescale;
- delay;
- persistence;
- confidence/evidence class;
- first known version/commit;
- last known version/commit;
- historical failures affecting the edge;
- current FRANK equivalent;
- Harness intervention handle.

Required future artifact:

`research_entity/architecture_archaeology/EMERGENT_COUPLING_GRAPH.json`

## 4. Multi-timescale analysis

The system must be analyzed as a dynamical system, not only as a call graph.

At minimum distinguish:

- reflex/fast routing scale;
- per-turn cognition scale;
- workspace/attention scale;
- short-term memory/salience scale;
- goal/personality adaptation scale;
- consolidation/dream scale;
- LoRA/training scale;
- restart/boot/recovery scale.

A coupling may be invisible in one turn but dominant over long horizons.

## 5. GWT-specific interpretation

GWT is treated as an organizing dynamical mechanism with explicit competition, selection, broadcast, reconstruction, uptake, causal use, outcome and re-entry.

The current RAE distinction remains mandatory:

`global_addressability != delivery != reconstruction != uptake != causal_use != outcome != reentry`

Historical Project-Frankenstein GWT implementations must be compared against this newer causal decomposition, not simply labeled correct/incorrect.

The archaeology must ask which historical states already approximated:

- candidate generation;
- salience/competition;
- workspace selection;
- broadcast;
- receiver-specific transformation;
- behavioral consequence;
- persistent re-entry.

## 6. Emergence claims require intervention

The design philosophy may intentionally seek emergent behavior, but evidence rules remain strict.

System-level behavior is not established as caused by emergent coupling merely because:

- many modules are connected;
- behavior looks coherent;
- a workspace exists;
- a variable correlates with an outcome;
- a module has a neuroscience-inspired name.

The Harness must support:

- edge lesions;
- module lesions;
- delay/timescale perturbations;
- gain changes;
- state clamping;
- shuffled coupling controls;
- replay under identical model output;
- rescue experiments;
- interaction-term measurements;
- alternative/common-driver controls.

## 7. Originality analysis must include coupling topology

Prior-art search must compare more than module names.

For every project-original candidate, search external work at four levels:

1. same local component;
2. same update rule;
3. same coupling pattern;
4. same full multi-timescale architecture/function.

A known local component does not refute originality of a project-specific coupling topology.

## 8. Harness requirement

Both Harness implementations must expose coupling as explicit machine state and intervention surfaces.

A mega-prompt that merely tells the model that subsystems are connected does not count as simulation.

For each coupling edge that materially affects Test 1, the Reference Harness and Clay Harness should be able to:

- record its input/output state;
- replay it;
- disable or alter it;
- compare downstream effects;
- preserve timing/order semantics;
- emit a receipt.

## 9. ClayCode requirement

ClayCode must be capable of representing the architecture as a dynamical relational system, including:

- typed state variables;
- equations/update rules;
- causal/dependency edges;
- multiple timescales;
- persistent epochs;
- competition/gating;
- recurrent/re-entry loops;
- uncertainty/UNKNOWN/conflict;
- resource and authority boundaries;
- intervention points.

If the final ClayCode cannot express these without falling back to opaque prose or arbitrary host code, the language release is incomplete for FRANK.

## 10. Core research question

For each historical and current FRANK behavior, ask:

> Is the behavior primarily encoded in one component/model, or does it arise from the structure and dynamics of coupled state transitions across the architecture?

The Harness is the instrument for answering this experimentally.
