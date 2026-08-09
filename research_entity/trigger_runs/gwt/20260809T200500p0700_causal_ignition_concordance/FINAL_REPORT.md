# GWT Research Delta — Causal Ignition Concordance

- run_id: 20260809T200500p0700_causal_ignition_concordance
- actor: chatgpt-secondary
- entity_parent: r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346
- home_room: gwt
- mode: SOLO_RESEARCHER
- program_stage: BASE_CLAYCODE_RELEASE
- evidence_class: PRIMARY_PREPRINT + PEER_REVIEWED_PRIMARY + CANONICAL_INTERNAL_CONTRACT
- status: OPEN_RESEARCH_DELTA

## Coordination preflight

Canonical identity, bootstrap, actor registry, trigger registry, room registry and program state were reread. No materialized GWT ROOM_STATE or indexed active overlapping GWT worker was found through the available connector surface. Work was therefore bounded to a non-overlapping BASE semantic/readout delta. No training or H1 execution was started.

## External evidence

1. Rahbar, *The Ignition Index* (arXiv:2608.05160v1, 2026) operationalizes ignition steepness from sigmoid fits to layer/iteration probe curves. It reports shuffled-label selectivity, architecture differences, and recurrence-axis ignition, but explicitly leaves causal intervention for future work.
2. *Verbalizable Representations Form a Global Workspace in Language Models* (arXiv:2607.15495v1, 2026) identifies a candidate J-space and shows direct vector-swap effects on verbal report. This supports causal manipulation of a privileged representation, but does not by itself establish per-receiver causal use, provenance-bound re-entry, or long-horizon recurrence.
3. Cogitate Consortium et al., Nature 642, 133–142 (2025), adversarially tested GNWT and IIT and reports that results both align with and challenge key predictions. Methodological import for FRANK: preregister discriminating predictions and preserve failed predictions; do not rescue GWT post hoc.

## New hypothesis

### H-GWT-CIC-001 — Causal Ignition Concordance

A FRANK WorkspaceEpisode is a stronger GWT mechanism candidate when four independently measured axes converge under matched interventions:

- threshold axis: abrupt candidate-to-episode transition under controlled signal/gain sweep;
- availability axis: broad typed receiver delivery/reconstruction;
- causal-use axis: receiver-specific uptake and outcome dependence under lesion/rescue;
- re-entry axis: provenance-bound influence on later competition/state, exceeding shuffled/provenance-broken controls.

No axis is sufficient alone. The joint result remains a vector, not a consciousness or emergence scalar.

### Proposed typed addition

```text
CausalIgnitionConcordance {
  episode_id
  sweep_axis: SIGNAL | LAYER | ITERATION | TIME | COUPLING_GAIN
  threshold_fit { beta; midpoint; fit_quality; uncertainty; null_delta }
  availability { delivered; reconstructed; receiver_set; coverage }
  causal_use { used_receivers; lesion_loss; rescue_recovery; outcome_delta }
  reentry { truthful_delta; shuffled_delta; provenance_broken_delta; horizon }
  concordance_pattern: BITSET4
  discordance_class
  cost_shadow
  evidence_status
  receipt_refs
}
```

The `BITSET4` is descriptive indexing only and MUST NOT become an aggregate truth score.

## Counterhypotheses

- CH-1 Probe Threshold Artifact: steep beta reflects probe geometry or corruption protocol, not workspace ignition.
- CH-2 Report Bottleneck: J-space intervention changes report while leaving non-report receiver computation unchanged.
- CH-3 Graded Workspace: useful global availability can be graded; a sharp threshold is not necessary.
- CH-4 Recurrent-Axis Mislocalization: measuring layer depth misses ignition expressed over iterations/time.
- CH-5 Common Driver: availability, use and re-entry covary because of an upstream driver rather than causal broadcast.
- CH-6 Extra-Context Effect: truthful re-entry gains arise from extra context volume, not provenance-bound recurrent closure.

## Highest-information discriminating test

Preregister a factorial frozen-episode sweep:

A = ignition threshold/gain low vs high
B = broadcast route intact vs lesioned
C = re-entry truthful vs shuffled/provenance-broken

Hold model output fixed where feasible. Measure beta along signal, iteration and time axes; per-receiver delivery/reconstruction/uptake/use; outcome; next-turn recurrence; latency/token/memory/instability. Add rescue of the broadcast route. The key prediction is not merely a nonzero interaction term but a specific discordance transition:

`threshold-only -> availability -> causal-use -> truthful-reentry`

If beta remains high after broadcast lesion while causal use vanishes, ignition steepness is a local transition marker, not evidence of complete workspace function.

## BASE ClayCode implication

ClayCode needs native semantics for:

- explicit sweep-axis identity and ordered coordinates;
- versioned threshold-fit estimator and fit-quality receipt;
- receiver-stage vectors bound to one episode/intervention;
- concordance pattern without scalar promotion;
- discordance classes and UNKNOWN values;
- preregistered prediction/falsifier bindings;
- matched lesion/rescue and truthful/shuffled/provenance-broken re-entry groups.

This is additive to the current GWT Emergence Readout Contract. It does not reopen existing semantics unless an executable counterexample proves they cannot express these bindings.

## Cross-room feedback

- claycode: add typed sweep-axis, estimator receipt, concordance/discordance semantics.
- frank: preserve logical separation of ignition detection, delivery, causal use and re-entry inside the Observability Plane.
- harness: schedule the factorial frozen-episode test for H1 after BASE PASS.
- emergenz: treat ignition beta as one dynamics feature, never emergence by itself.
- claygraph: attach each concordance axis to exact measured paths; graph activation is not evidence.
- unifieddb: defer physical layout; record future query needs only after H1 access traces.

## Claim-state decision

- H-GWT-CIC-001: OPEN / TESTABLE / NOT_PROMOTED
- CH-1..CH-6: OPEN
- No existing claim refuted.
- No phenomenal-consciousness inference.
- No paid training authorized or started.

## Continuation

Next GWT cycle should either:
1. formalize this schema in the BASE ClayCode type/effect system, or
2. produce an executable counterexample showing the current contract already captures all axis/receipt bindings without ambiguity.
