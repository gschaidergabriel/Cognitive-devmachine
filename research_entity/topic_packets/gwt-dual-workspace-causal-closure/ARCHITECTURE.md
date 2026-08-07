# Candidate Architecture — Dual Workspace Causal Closure

## Planes

`LATENT_WS` is optional and model-internal. It may expose J-space-like coordinates, latent probe windows, intervention handles and confidence, but it is never authority.

`EVENT_WS` is the system-level causal workspace:

`candidate → competition → selection/ignition → logical workspace register → causal push router ↔ query/pull rescue → audience reconstruction → effect proposal → external authority/effect gateway → outcome → causal-freshness gate → re-entry`.

## Workspace Register and delivery modes

Global availability is a semantic/logical property, not a requirement to physically push every payload to every module. The current candidate stores an immutable workspace payload/hash in a globally addressable register, then uses:

- `SELECTIVE_PUSH`: route immediately to audiences predicted to have high causal value;
- `PULL_RESCUE`: an unpushed audience may query the current workspace when local need emerges;
- `WIDENED_PUSH`: increase fanout when router/rescue confidence falls;
- `FULL_PUSH`: fallback for low confidence, high criticality or experiments requiring the dense baseline.

The controller must optimize/monitor causal audience recall, misses, rescue latency, false/irrelevant delivery, physical fanout, energy/cost and perturbation amplification. Sparse delivery is never declared equivalent merely because average task accuracy is unchanged.

## Required receipts

- `candidate_id`: producer, payload ref/hash, score vector, uncertainty, dependencies.
- `competition_id`: candidates, winner, runner-up, margin, policy version.
- `ignition_id`: intervention-curve ref, threshold/sharpness/hysteresis metrics; optional until empirically demonstrated.
- `broadcast_id`: logical scope, audience plan, routing confidence, fanout budget, payload hash.
- `audience_receipt`: audience identity, push/pull mode, transport status and latency.
- `reconstruction_receipt`: local reconstructed representation hash/status.
- `effect_receipt`: effect identity, causal parent, authority reference, effect hash.
- `outcome_receipt`: measured outcome/utility vector/environment delta.
- `reentry_receipt`: outcome source, target decision, delay, truth-binding hash, source-state hash, validity epoch/regime tag, age-at-use, predictive-freshness estimate and stale/reject reason.
- `latent_bridge_ref`: model call + latent probe window when available.

## Causal Freshness Gate

A re-entry payload is not accepted simply because it is truthful and recent. At consumption time the gate evaluates:

`truth binding + source-state compatibility + validity epoch + age-at-use + estimated predictive/causal value`.

A stale or regime-incompatible payload may remain historical context but should not automatically update active control state. TTL is task/regime dependent and should be learned/validated from replay, not frozen globally.

## Dual-workspace cross-lesion preregistration

Use paired compute-matched 2×2 interventions:

- serial `LATENT_WS → EVENT_WS`: both single lesions large; double lesion approximately occludes the stronger single;
- redundant parallel: single lesions modest; double lesion strongly worse;
- additive parallel: double lesion approximately additive;
- latent epiphenomenal: latent lesion near-null, event lesion large;
- event epiphenomenal: event lesion near-null, latent lesion large.

These are candidate signatures, not claims about current FRANK topology.

## Causal Workspace Closure Certificate (CWCC)

CWCC is vector-valued. Track competition/winner margin, ignition intervention response, logical audience scope, causal audience recall, missed-audience rate, pull-rescue count/latency, reconstruction, effect mediation, outcome receipt, re-entry sensitivity, age-at-query/use, stale-apply/reject rate, predictive freshness, next-state influence, capacity/load, physical fanout, perturbation amplification, latent/event concordance and cost/recovery shadows.

## Authority rule

Workspace selection, routing, reconstruction or freshness acceptance never grants execution authority. Effect proposals still pass the external capability/root/nonce/expiry/invariant/rollback gateway.
