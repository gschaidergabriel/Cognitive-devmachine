# Harness Handoff — Dissolved Perception / Sensor-In-Module

**Status:** ACTIVE ARCHITECTURE HANDOFF  
**Source directive:** `research_entity/global/FRANK_DISSOLVED_PERCEPTION_DIRECTIVE.md`  
**Research run:** `research_entity/trigger_runs/q12/q12-20260809T0554p0700-dissolved-perception/REPORT.md`  
**Experiment plan:** `research_entity/trigger_runs/q12/q12-20260809T0554p0700-dissolved-perception/EXPERIMENT_PLAN.md`

## Harness implementation requirement

Do not implement Digital Retina only as:

`sensor -> vision service -> caption/full VisualPercept -> FRANK`

The Reference Harness must expose both:

1. the explicit historical/materialized baseline; and
2. the owner-fixed dissolved target in which sensor evidence becomes typed perceptual state deltas inside FRANK and can recurrently couple to world/memory/goals/context before selective GWT escalation.

## Required logical components/readouts

- `SensorEvidenceReceipt`
- `PerceptualStateDelta`
- logical `PerceptualField` view
- evidence precision vs prior precision vs goal/context bias
- unresolved/set-valued perceptual alternatives
- prediction-error/surprise state
- attention/thalamic gain
- optional/on-demand `VisualPercept` materialization
- GWT candidate/selection/delivery/uptake/causal-use/outcome/re-entry trace
- world/memory/action update trace

## Mandatory differential tests

- explicit Retina->VisualPercept baseline vs dissolved field;
- feedforward vs recurrent field;
- world-model feedback lesion/rescue;
- memory feedback lesion/rescue;
- goal/context feedback lesion/rescue;
- recurrence lesion/rescue;
- correct vs misleading prior;
- unknown object and no-signal tests;
- stale/replayed visual evidence;
- periodic full frame vs change-only vs hybrid anchor/change;
- external-process sensor ingress vs in-process H3 topology;
- VisualPercept reconstructability/replay from state lineage;
- model-visible context/token comparison.

## Non-negotiable safety/epistemic rule

A prior/world-model state may influence interpretation but never becomes sensor evidence. The Harness must make the contribution of sensor evidence and top-down prior separately inspectable and perturbable.

`UNKNOWN` and `CONFLICT` are valid successful perceptual states.

## H3 rule

H3 targets one FRANK module/binary/process identity containing the user-space sensor ingress and perceptual fast path where APIs permit. OS/kernel/device drivers may remain physical dependencies. An out-of-process Retina service is not the cognitive architecture and requires measured justification.

## Completion receipt

The Harness should eventually produce a `DISSOLVED_PERCEPTION_DIFFERENTIAL_RECEIPT.json` binding:

- baseline hashes;
- test corpus hashes;
- topology variants;
- latency/cost results;
- accuracy/calibration results;
- prior-bias safety results;
- replay/provenance results;
- selected/retained implementation boundaries;
- negative results;
- unresolved falsifiers.
