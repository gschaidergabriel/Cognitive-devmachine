# Retina -> ClayCode Executable Requirements

**Status:** REQUIREMENTS HANDOFF; LANGUAGE CHANGES REQUIRE EXECUTABLE COUNTEREXAMPLES  
**Source:** Retina deep foundry 2026-08-09

## Goal

ClayCode must be able to express the visual architecture without falling back to prose, opaque JSON blobs or an untyped host-language side architecture. These requirements do **not** automatically authorize ClayCode semantic changes. If current ClayCode can express them faithfully, use the existing primitives.

## Required semantic families

### 1. Sensor evidence

Need a typed equivalent of:

`SensorEvidence<Kind,Value> {
  id
  source
  source_epoch
  capture_time
  spatial_scope
  transform
  transform_version
  value
  bottom_up_precision
  calibration_ref
  provenance
}`

Properties:
- immutable after commit except explicit revocation annotation;
- content/semantic identity deterministic where inputs are deterministic;
- stale/replayed epoch detection;
- physical backing ref optional and capability-controlled.

### 2. Perceptual alternatives

Need:
- set-valued alternatives;
- compatibility/exclusion;
- support/contradiction edges;
- individual evidence/prior/context contribution;
- confidence/uncertainty;
- `PROVISIONAL/STABLE/UNKNOWN/CONFLICT/REOPENED`.

This can reuse Hyperposition semantics if information-equivalent.

### 3. Visibility state

Need exact enum/state machine:

`VISIBLE_CONFIRMED`
`VISIBLE_UNCERTAIN`
`OCCLUDED`
`OUT_OF_FOV`
`ABSENT_EXPLICIT_NEGATIVE`
`UNKNOWN`
`SENSOR_DEGRADED`
`STALE`
`REVOKED_DERIVATION`

Transitions must be executable/testable and carry evidence refs.

### 4. Persistent entity identity

Entity identity must not equal current label. ClayCode must express:
- same entity, revised type;
- track split/merge;
- re-acquisition;
- relation revision;
- temporal validity;
- evidence lineage.

### 5. Sparse deltas / multi-rate execution

Need semantics for:
- change-region event;
- local field update;
- state age/timer;
- scheduled/adaptive anchor;
- fast vs slower semantic loops;
- atomic/transactional commit or explicit eventual semantics;
- deterministic epoch ordering.

### 6. GWT visual contracts

Need typed:
- `VisualCandidate`;
- ignition features/readout;
- BroadcastEnvelope refs;
- delivery/reconstruction/uptake/causal-use/outcome/re-entry receipts;
- `PerceptualSufficiencyReceipt` for local non-escalation when enabled.

### 7. Active sensing

Need:
`SenseActionIntent`
`ExpectedInformationGain`
`CostEstimate`
`SenseActionReceipt`
`SenseOutcome`

No sensing/model/effect action receives authority merely because a model proposes it. Runtime capability/effect gateway remains external authority.

### 8. Dependency invalidation

Derived visual hypotheses/world edges must declare parents. ClayCode runtime must support:

`invalidate(parent_evidence_or_transform)`
`-> identify dependent derived states`
`-> revoke/recompute/quarantine according to policy`

Historical state remains queryable.

### 9. VisualPercept materialization

Need a pure/deterministic-where-possible projection:

`materialize_visual_percept(evidence_epoch, field_epoch, world_epoch) -> receipt`

Receipt includes evidence, alternatives, prior contribution, selected interpretation, provenance and GWT/use refs.

### 10. Counterfactual interventions

Harness needs executable intervention syntax for:
- remove evidence;
- shuffle prior/context;
- clamp visibility;
- disable recurrence;
- disable world feedback;
- disable memory feedback;
- change precision/gain;
- replace transform/model result;
- replay stale frame;
- swap anchor policy.

## Compiler/lowering obligations

A single semantic program should be lowerable to:
- deterministic H1 host reference;
- H2 Clay runtime;
- H3 one-module binary;
- desktop full-frame source;
- Android/edge source;
- future event source.

The lowering may change buffers, kernels, concurrency and device backends. It may not silently change evidence identity, temporal semantics, authority or visual world-state meaning.

## Concrete language falsifiers

A ClayCode release is insufficient for Retina if it cannot execute tests such as:

1. object visible -> occluded -> reappears preserving identity;
2. object visible -> out-of-FOV -> returns;
3. object visible -> explicit fresh empty view -> ABSENT;
4. same evidence + misleading prior -> preserve sensor/prior contribution separately;
5. conflicting detector/CLIP hypotheses -> retain CONFLICT;
6. revoke detector box -> dependent relation becomes revoked without deleting raw frame evidence;
7. stale replay -> rejected from live state;
8. local visual update -> sufficiency receipt without GWT;
9. uncertainty -> active OCR/crop request -> evidence returns -> hypothesis resolves;
10. H1/H2 trace hashes/semantics match.

If current ClayCode cannot express one of these without untyped host escape, that concrete failure becomes the semantic-change case for BASE.
