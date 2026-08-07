# Candidate Architecture — Dual Workspace Causal Closure

## Planes

`LATENT_WS` is optional and model-internal. It may expose J-space-like coordinates, latent probe windows, intervention handles and confidence, but it is never authority.

`EVENT_WS` is the system-level causal workspace:

`candidate → competition → selection/ignition → logical availability → selective multicast → audience reconstruction → effect proposal → external authority/effect gateway → outcome → re-entry`.

## Required receipts

- `candidate_id`: producer, payload ref/hash, score vector, uncertainty, dependencies.
- `competition_id`: candidates, winner, runner-up, margin, policy version.
- `ignition_id`: intervention-curve ref, threshold/sharpness/hysteresis metrics; optional until empirically demonstrated.
- `broadcast_id`: logical scope, audience plan, fanout budget, payload hash.
- `audience_receipt`: audience identity, transport status.
- `reconstruction_receipt`: local reconstructed representation hash/status.
- `effect_receipt`: effect identity, causal parent, authority reference, effect hash.
- `outcome_receipt`: measured outcome/utility vector/environment delta.
- `reentry_receipt`: outcome source, target decision, delay, truth-binding hash.
- `latent_bridge_ref`: model call + latent probe window when available.

## Causal Workspace Closure Certificate (CWCC)

CWCC is vector-valued. Track competition/winner margin, ignition intervention response, audience reach, reconstruction, effect mediation, outcome receipt, re-entry sensitivity, next-state influence, capacity/load, perturbation amplification, latent/event concordance and cost/recovery shadows.

## Physical broadcast rule

Global availability is a semantic/logical property. Physical delivery may be selective if every relevant audience can access the payload and causal receipts prove downstream reconstruction/use. Fanout should be controlled by causal value and perturbation-amplification risk rather than maximized.

## Authority rule

Workspace selection never grants execution authority. Effect proposals still pass the external capability/root/nonce/expiry/invariant/rollback gateway.
