# ClayCode Requirements — PerceptualField / Dissolved Vision

**Status:** ACTIVE BASE REQUIREMENTS INPUT  
**Source:** `research_entity/global/FRANK_DISSOLVED_PERCEPTION_DIRECTIVE.md`  
**Research run:** `research_entity/trigger_runs/q12/q12-20260809T0554p0700-dissolved-perception/REPORT.md`

ClayCode BASE must be able to express the dissolved-perception target without hiding the mechanism in opaque host callbacks.

## Required semantic capabilities

### Sensor evidence identity

Typed representation for:
- source/device identity;
- source class;
- capture/arrival/ingress timestamps;
- sensor/frame/event epoch;
- spatial region/coordinate identity;
- evidence hash/provenance;
- stale/replayed status.

### Perceptual state deltas

ClayCode must express incremental updates rather than requiring full-scene replacement:
- add/update/remove evidence;
- change/motion regions;
- feature/entity/relation hypotheses;
- spatial binding updates;
- uncertainty/precision updates;
- novelty/prediction-error updates;
- activation/salience updates.

### Set-valued alternatives

Need representation for:
- multiple candidate interpretations;
- compatibility/exclusion;
- evidence refs per alternative;
- prior/context refs per alternative;
- confidence/precision;
- selected/collapsed interpretation;
- reopening after contradictory evidence.

### Evidence vs prior separation

Must not collapse these into one untyped score:
- bottom-up sensor evidence precision;
- world/learned prior precision;
- memory/context contribution;
- goal/action bias;
- final current belief/percept confidence.

### Recurrent coupling

Need explicit typed coupling/update semantics for:
- perceptual state <-> world model;
- perceptual state <-> ClayGraph memory/Assemblies;
- perceptual state <-> goals/action context;
- perceptual state <-> previous perceptual state;
- perceptual state -> thalamic/attention gain;
- perceptual state -> GWT candidacy;
- GWT/outcome -> perceptual re-entry.

Couplings require intervention handles for lesion, gain change, delay change, shuffle and rescue.

### Materialized VisualPercept receipt

ClayCode must be able to materialize an auditable percept receipt from state lineage when requested, while not requiring that receipt to be the sole hot-path carrier.

Receipt semantics require:
- sensor evidence refs;
- state epoch;
- entities/features/relations;
- unresolved alternatives;
- uncertainty and evidence/prior contribution;
- transformation lineage;
- GWT/memory/action links;
- deterministic identity/hash or explicit nondeterminism receipt.

### Event/change fast path

ClayCode must express:
- anchor-frame evidence;
- change/event evidence;
- validity/expiry;
- anchor refresh trigger;
- event accumulation windows;
- bounded buffers/rings/resources;
- missed/stale event state;
- fallback to full evidence.

### Unknown/conflict

`UNKNOWN`, `CONFLICT`, `STALE`, `REVOKED` or equivalent explicit epistemic states are mandatory. Perception must not force a familiar label when evidence is insufficient.

## Compiler/runtime constraint

Do not solve these requirements by exposing one opaque host function `vision() -> caption` or `vision() -> VisualPercept`.

Host kernels/models are allowed for physical feature extraction, but the state/coupling/provenance semantics above must remain visible in ClayCode IR and testable by the Harness.

## Completion test for BASE

BASE should include a small executable visual-state fixture that:

1. ingests anchor evidence;
2. applies a change delta;
3. maintains two ambiguous interpretations;
4. changes world-prior gain;
5. selects or retains `CONFLICT`;
6. emits a GWT candidate only when a threshold/policy is met;
7. materializes a replayable `VisualPercept` receipt on demand;
8. lesions world feedback and shows the expected trace difference;
9. rejects stale/replayed sensor evidence.

This is a language expressibility/conformance test, not evidence that the final perception mechanism is superior.
