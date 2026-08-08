# FRANK Digital Retina Multimodal Contract

**Status:** PROJECT-OWNER ARCHITECTURE DIRECTIVE — NOT A RESEARCH HYPOTHESIS  
**Owner directive recorded:** 2026-08-09  
**Applies to:** FRANK, Clay, ClayCode, ClayGraph, GWT, UnifiedDB, Harness H1/H2/H3 and Clay 0.1 acceptance

## Fixed target

Digital Retina is a mandatory subsystem of the target FRANK module. It is not an optional plugin or post-release add-on.

The accepted Clay 0.1 FRANK must therefore be multimodal at minimum across language/text and visual perception. Existing voice/audio and other sensor paths may extend multimodality, but visual perception through Digital Retina is mandatory for the target module.

## Required perception path

The architectural path is:

`visual source -> Digital Retina physical vision pipeline -> Clay-typed VisualPercept -> thalamic/attention gating -> GWT candidate/workspace -> memory/self/world/goals/action`

Visual sources may include screen frames, camera frames, images, rendered UI state and other explicitly authorized visual inputs.

Digital Retina may use conventional implementation machinery for physical perception, including image tensors, embeddings, OCR, detectors, segmentation, feature extractors, temporal/change detection and numerical vision models. Those physical representations do not become a second semantic architecture.

Whenever visual information crosses into FRANK's semantic/cognitive state, it MUST be bound to Clay-native typed meaning and provenance.

A minimum `VisualPercept` semantic object must preserve, directly or by referenced typed subobjects:

- source identity and source class;
- capture/event time and epoch;
- spatial/frame identity;
- extracted entities/features/relations;
- confidence/uncertainty;
- provenance to the originating visual evidence;
- transformation/model lineage where applicable;
- salience/attention metadata when selected;
- links to any GWT episode, memory write, goal update or effect proposal causally using it.

## Clay-native boundary

Digital Retina is NOT an exception to the FRANK Clay-native rule.

Needle remains the sole intentional non-Clay semantic subsystem. Digital Retina can be implemented in conventional code and numerical models, but its semantic output into FRANK is Clay-native. Raw tensors/pixels/embeddings are physical backing representations and must be provenance-bound when projected into Clay semantics.

No untyped natural-language caption or opaque model embedding may silently become architectural truth, memory truth, execution authority or world-state truth.

## GWT and attention integration

Digital Retina must participate in the same causal observability contract as other FRANK perception:

- visual candidate creation;
- thalamic/attention selection or suppression;
- workspace ignition/broadcast when selected;
- per-receiver reconstruction/uptake;
- causal use;
- outcome;
- re-entry;
- lesion/rescue and shuffled/stale visual-input controls.

The system must be able to distinguish at least:

- no visual input;
- visual input present but gated/suppressed;
- visual input selected and broadcast;
- visual input causally used downstream;
- stale/replayed/mismatched visual evidence.

## Harness requirement

H1 Reference Harness MUST include a deterministic Digital Retina adapter/fixture and end-to-end visual-perception traces.

H2 ClayCode Harness MUST express the same frozen visual semantic contracts and causal transitions in ClayCode.

H3 One-Module/Binary FRANK MUST contain or bind the Digital Retina runtime as part of the accepted FRANK module identity. A build without the mandatory visual path cannot PASS H3 or DOOMSDAY.

Reference-vs-Clay-vs-One-Module differential tests must verify representation-invariant equivalence for `VisualPercept` identity, provenance, attention/GWT use, memory writes and downstream effects.

## Historical reuse requirement

Level-0 assimilation must ingest the existing Drive `digital-retina` lineage before redesigning this subsystem. The currently observed historical tree includes at least `retina`, `api`, `frontend`, `eval`, `deploy`, `tests`, `tools` and `docs`, with a nested `retina/vision` branch.

Historical code is evidence and reusable foundation, not automatic current truth. Reuse must be classified as directly reusable, reusable with adaptation, measurement foundation, negative-result value, superseded/informative or not reusable.

## Acceptance rule

Digital Retina is mandatory architecture completeness. Clay 0.1 cannot reach chief-developer first-test acceptance if:

- the visual perception path is absent;
- visual semantics bypass Clay typing/provenance;
- H1/H2/H3 do not agree on the frozen visual semantic contract;
- visual input cannot be traced through selection/broadcast/causal use/re-entry;
- stale/replayed visual evidence is accepted as current without detection;
- visual model output can mint execution authority directly.
