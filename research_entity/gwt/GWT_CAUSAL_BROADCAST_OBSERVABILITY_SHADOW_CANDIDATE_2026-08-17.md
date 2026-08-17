# GWT Causal Broadcast Observability Shadow — Candidate

**Status:** CANDIDATE_NOT_PROMOTED  
**Trigger:** `gwt`  
**Date:** 2026-08-17  
**Product boundary:** ClayVerse single-container (`the artefact/`)  
**Authority:** architecture/research candidate only; no truth/effect authority  

## Observed anchors

1. `research_entity/global/CLAY_GWT_EMERGENCE_OBSERVABILITY_CONTROL_DIRECTIVE.md` requires a typed causal sequence from candidate interaction through competition, ignition/selection, broadcast/addressability, receiver delivery, reconstruction, uptake, causal use, system outcome and provenance-bound re-entry.
2. `research_entity/global/RAE_GWT_MICROKERNEL.clay` already encodes `ignite=best(admissible(W.cand))`, `broadcast(ignite)->organs`, `receipt=observe(delivered,used,effect)`, causal learning and re-entry, with `salience!=truth` and `addressable!=used` invariants.
3. Current `the artefact/clayverse/store.py` persists `workspace_episodes` as episode/session/time/observation/salience/alternatives/selected/state plus separate effects and causal episodes.
4. Current `the artefact/clayverse/turn_lifecycle.py` creates a workspace episode, selects `respond|request_effect|defer_effect`, binds effect/outcome through a causal id, and completes/aborts/re-enters the turn spine.
5. Source inspection does not expose explicit per-receiver delivery, reconstruction, uptake, local causal-use, broadcast-envelope, graph-epoch or Hyperposition-topology receipts on the current ClayVerse artifact path.

## Gap

The current artifact has a useful bounded workspace selector and causal turn/effect spine, but the persisted state is insufficient to distinguish the owner-required sequence:

`addressable != delivered != reconstructed != uptake != causal_use != outcome != reentry`.

That means a future claim about broadcast reach, receiver use, causal-use fraction, lesion/rescue or re-entry cannot be reconstructed from current persisted workspace rows alone without adding hidden host inference or new instrumentation.

This is a **source-derived instrumentation gap**, not executable evidence of runtime failure.

## Candidate mechanism: `GWTObservabilityShadow`

Add a non-authoritative append-only measurement shadow around the existing canonical turn lifecycle. It does not become a second state authority, scheduler, cognition daemon or effect gate.

Candidate stage receipts:

`CANDIDATE -> COMPETITION -> IGNITION -> BROADCAST -> DELIVERY -> RECONSTRUCTION -> UPTAKE -> CAUSAL_USE -> OUTCOME -> REENTRY`

Candidate receipt identity (exact final ClayCode schema remains a BASE-language decision):

- `receipt_id`
- `episode_id`
- `candidate_id`
- `stage`
- `receiver_id` when receiver-scoped
- `source_epoch` / current entity generation identity
- `graph_epoch` or typed `UNKNOWN`
- `hyperposition_topology_id` or typed `UNKNOWN`
- `intervention_id` or typed `NONE`
- `model_output_hash` where relevant
- deterministic payload/result hash
- provenance/evidence class
- timestamp / declared ordering identity

### Storage law

Prefer an append-only stage-receipt relation linked to `workspace_episodes` rather than widening the mutable `workspace_episodes` row into a large mixed-state object.

Reasons:

- multiple receivers require one-to-many stage evidence;
- lesion/replay/control runs require parallel intervention identities;
- immutable receipts are easier to replay, compare and invalidate;
- measurement must not silently alter the state it observes;
- current `workspace_episodes` can remain the minimal decision spine.

### Hot-path law

Instrumentation must be cheap enough to remain shadow-only:

- no full graph scan;
- no all-pairs receiver expansion;
- no model call solely to classify a receipt;
- no truth/effect authority minted from salience, ignition or readout values;
- unknown topology/readout fields stay `UNKNOWN`, never guessed or zero-filled.

## Strong counterhypothesis

**H0:** The existing `workspace_episodes + active_turns + effects + causal_episodes + turns` spine already contains enough information; a new GWT receipt layer would only rename existing events, increase write amplification and create semantic duplication.

### Cheapest discriminator

Attempt deterministic reconstruction of the full required stage chain for an exact current episode using only existing persisted artifact records.

Pass H0 only if the system can unambiguously recover, without hidden inference:

1. selected candidate;
2. broadcast/addressability event;
3. every intended receiver;
4. per-receiver delivery;
5. reconstruction;
6. uptake;
7. local causal use;
8. joint outcome;
9. provenance-bound re-entry;
10. the relevant source/graph/Hyperposition epoch identities.

If any required stage is observationally indistinguishable from another or absent, H0 is rejected for that stage and the minimal missing receipt is justified.

**Current source inspection:** H0 is already weakened because the current artifact schema has no explicit receiver delivery/reconstruction/uptake/causal-use or topology-epoch fields. This is not promoted beyond source evidence until exact isolated execution confirms the runtime behavior.

## Next isolated executable batch

When an actual authorized Vercel Sandbox execution surface is available:

1. bind exact current `main` SHA and artifact source digest;
2. build a temporary shadow-instrumented candidate without changing authority/effect semantics;
3. replay one frozen turn with at least two typed consumers/receivers where the product path genuinely has them;
4. run baseline, receiver-lesion, uptake-disabled and re-entry-broken variants with frozen model output where technically meaningful;
5. assert stage ordering/identity, no phantom delivery/use, exact provenance, restart persistence and zero truth/effect-authority promotion;
6. measure write/latency overhead and compare against the uninstrumented baseline;
7. preserve negative results and remove the shadow candidate if reconstructability or cost falsifies its need.

## Scientific boundary

Global-workspace concepts are engineering inspiration and a falsifiable measurement scaffold, not proof of phenomenal consciousness. The 2025 Cogitate adversarial collaboration reported results that supported some predictions while substantially challenging key tenets of both GNWT and IIT; therefore ClayVerse must not treat a software analogue of ignition/broadcast as scientific evidence of consciousness.

## Decision

**RETAIN AS ARCHITECTURE CANDIDATE / NOT VERIFIED / NOT RUNTIME-PROMOTED.**

The highest-information next step is not to make the selector more elaborate. It is to make the existing causal workspace path observably distinguish `addressable`, `delivered`, `reconstructed`, `used`, `outcome` and `re-entry`, then attack that instrumentation with reconstruction, lesion, shuffle, restart and cost controls.
