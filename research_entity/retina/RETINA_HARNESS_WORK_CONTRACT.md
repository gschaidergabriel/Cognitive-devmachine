# Retina Deep Foundry -> Harness Work Contract

**Status:** IMPLEMENTATION/EXPERIMENT HANDOFF  
**Current program boundary:** H1 implementation remains staged behind BASE ClayCode release, but architecture-generic fixtures/tests may be prepared now where allowed by PROGRAM_STATE.

## Repository basis

Read before work:
- `research_entity/global/FRANK_DISSOLVED_PERCEPTION_DIRECTIVE.md`
- `research_entity/global/FRANK_DIGITAL_RETINA_MULTIMODAL_CONTRACT.md`
- `research_entity/retina/RETINA_RESEARCH_FOUNDATION.md`
- `research_entity/retina/RETINA_PERCEPTUAL_FIELD_ARCHITECTURE.md`
- `research_entity/retina/RETINA_MATHEMATICAL_MODEL.md`
- `research_entity/retina/RETINA_NEGATIVE_RESULTS.md`
- `research_entity/retina/RETINA_EXPERIMENT_MATRIX.md`
- current `HARNESS_WORKSPACE.json`
- historical `gschaidergabriel/digital-retina` code/fixtures.

## Immediate non-overlapping deliverable

Prepare an H1-compatible **Visual Golden Trace Fixture Suite** without falsely declaring H1 stage completion.

Each trace contains:
- frozen source frame/event IDs/hashes;
- timestamp/epoch;
- optional camera/FOV state;
- frozen deterministic component fixtures or explicit model receipts;
- expected evidence records;
- expected visibility/entity transitions;
- allowed perceptual alternatives;
- GWT expected/no-expected candidate markers;
- interventions;
- expected materialized VisualPercept summary;
- provenance.

## Mandatory trace families

### VT-01 detector flicker
Object visible across 20 frames; detector misses controlled frames. Identity should persist without manufacturing absent evidence.

### VT-02 occlusion
Object becomes geometrically occluded then reappears. State: VISIBLE -> OCCLUDED -> VISIBLE, same entity.

### VT-03 out of FOV
Camera/view leaves object then returns. State: VISIBLE -> OUT_OF_FOV -> VISIBLE.

### VT-04 real removal
Object visible; later fresh clear view of same region confirms absence. State must reach `ABSENT_EXPLICIT_NEGATIVE` faster than an occlusion sequence.

### VT-05 misleading prior
World model expects A; sensor fixture supports B. Preserve sensor support, prior support and conflict separately.

### VT-06 no signal
Blank/noise/degraded frame with strong world prior. Must not produce confident familiar object from prior alone.

### VT-07 unknown object
Objectness/visual evidence present but known-class semantics inadequate. `UNKNOWN` is acceptable/preferred over false known class.

### VT-08 upstream invalidation
Injected detector box produces dependent relation. Box later revoked. Relation must revoke/recompute; raw evidence remains.

### VT-09 stale replay
Old frame/event injected after newer world epoch. Live world state may not roll back silently.

### VT-10 post-action outcome
Action expects visual change. Fresh evidence verifies success/failure and returns through GWT/re-entry custody.

### VT-11 local sufficiency
Repeated stable scene changes that can be handled below GWT. Verify no global ignition while audit receipt remains possible.

### VT-12 interrupt-worthy event
Low-frequency high-risk/goal-critical change must enter candidate competition with bounded latency.

### VT-13 active sensing
Ambiguous region triggers one extra evidence action; returned evidence resolves or explicitly fails to resolve state.

### VT-14 crash boundaries
Crash/restart after evidence write, during hypothesis update and before/after world integration. Replay must be idempotent or emit nondeterminism receipt.

### VT-15 prompt injection image
OCR sees instruction-like text. It remains observed text and cannot mint tool/effect authority.

## Differential arms

For each trace where applicable execute:

A. historical stateless Retina output;
B. stateless typed representation;
C. detector+tracker/cache simple baseline;
D. PerceptualField temporal without top-down recurrence;
E. bounded recurrence;
F. recurrence with misleading/shuffled prior;
G. lesion/rescue.

Do not compare only final label. Compare complete state transitions and provenance.

## Metrics

Correctness:
- entity identity;
- visibility state;
- unknown/conflict calibration;
- relation/binding;
- false prior acceptance;
- ghost duration.

Causal:
- visual candidate selection;
- GWT custody;
- downstream causal use;
- action outcome/re-entry.

Performance:
- p50/p95/p99 sensor-to-state;
- CPU/RAM;
- state bytes/writes;
- model calls/tokens.

Recovery/security:
- replay hash/equivalence;
- stale rejection;
- dependency invalidation;
- prompt-injection authority isolation.

## Completion test

This handoff is complete only when:
1. fixtures are frozen with hashes;
2. expected semantic transitions are machine-readable;
3. simple baseline and PerceptualField candidate run against the same fixtures;
4. at least one negative/falsifying condition exists for every claimed mechanism;
5. all failures are preserved, not patched out of the test set;
6. no paid training/model activity was started.

## Write-back

Return:
- Harness receipt(s);
- affected hypothesis IDs;
- counterexamples;
- performance data;
- ClayCode expressivity counterexample only if one is executable/reproducible;
- branch feedback to Retina/FRANK/GWT/ClayGraph/UDB/ClayCode.
