# Avatar body / shoulder microkinematics — preregistration

Date: 2026-09-12
Owner goal: increase lifelike full-body motion while preserving head/eye identity and keeping runtime cost low.

## Authority / subject fence

This lane is deliberately disjoint from the currently active eye-identity and head-parallax lanes.

Observed live HTML subject at lane start:

`18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`

Current live body-follow law observed in that subject:

- head wrapper has its own spring around the real roll pose;
- body wrapper follows 34% of the CURRENT head wrapper value with a softer independent spring;
- therefore body-vs-head lag already exists;
- independent left/right shoulder articulation is not yet evidenced.

No claim in this lane may overwrite eye registration, semantic eye identity, expression assets, head parallax or their active worker branches.

## Hypothesis

A very low-dimensional body rig can increase perceived biological motion without an AI inference pass and without materially increasing CPU/GPU load.

The first candidate exposes these independent DOFs:

1. torso follow: retain the existing delayed body spring;
2. respiration: low-frequency, zero-mean chest/upper-torso deformation;
3. left shoulder: small lift/drop and tiny local roll;
4. right shoulder: independently phased small lift/drop and tiny local roll;
5. optional event impulse: bounded asymmetric shoulder response to an already-existing motion/expression event, only if a real event source exists.

The shoulder DOFs MUST NOT be implemented as a second global body rotation. They must be spatially local or mesh-local.

## Candidate implementation ladder

### B0 — current live baseline

Existing single body plate + current `#koerper-dreh` delayed follow.

### B1 — scratch-only local mesh / weighted layer prototype

Use the exact current body texture in an isolated browser/scratch harness. Prefer a tiny 2-D textured mesh or weighted precomputed shoulder layers. Zero-deformation output must reconstruct B0 to a strict image-difference bound.

### B2 — bounded biological microkinematics

Initial amplitude search region, intentionally conservative:

- shoulder vertical displacement: 0.20–1.20 CSS px at the rendered scale;
- shoulder local roll: 0.05–0.35 degrees;
- left/right phase separation: 12–70 degrees, never perfect mirror lock;
- respiration period: 3.2–6.8 s with slow bounded drift;
- shoulder micro-period: 5–13 s, coupled weakly to respiration, not to random per-frame noise;
- torso-scale breathing delta: <= 0.25% for first A/B.

The search may narrow these ranges; it may not silently widen them in production.

## Causal acceptance gates

A candidate is promotion-eligible only if all are true on the exact current subject or an explicitly rebound successor:

1. **Identity preservation** — body/face/eye source hashes and existing eye/head geometry remain unchanged outside the body candidate scope.
2. **Zero-offset reconstruction** — candidate at zero deformation matches baseline within a preregistered image bound; exact match preferred.
3. **No neck seam regression** — crop around head/neck/body junction has no new high-contrast or alpha discontinuity compared with B0.
4. **No shoulder ghosting** — moved shoulder layers do not reveal a duplicated stationary shoulder silhouette beyond the accepted pixel-error bound.
5. **Independent DOF proof** — left/right shoulder traces are measurably distinct and not reducible to the existing global `#koerper-dreh` transform.
6. **Temporal smoothness** — no one-frame displacement jump above 0.35 px or 0.12 degrees in the first conservative candidate unless tied to an explicitly measured existing pose transition.
7. **Performance** — 60-fps live acceptance must remain at the established gate; no production performance credit from a headless-only microbenchmark.
8. **Rollback** — removal of the candidate restores the exact pre-candidate source/artifact state.

## Measurements

For each B0/B1/B2 capture persist:

- exact `buehne.html` SHA-256;
- exact body texture SHA-256;
- viewport and rendered body bbox;
- shoulder/neck crop coordinates;
- per-frame L/R shoulder transform trace;
- baseline-vs-candidate RGB/alpha image metrics;
- neck-seam edge-energy delta;
- max inter-frame transform derivative;
- observed FPS series on the admitted live runtime;
- post-test live source readback.

## Failure classification

- geometry/ghost/seam regression after exact execution -> PRODUCT_NEGATIVE for this candidate only;
- stale body source/hash -> EVIDENCE_INVALID; rebind before further inference;
- bridge/browser/renderer failure -> INFRA_AUTH_TRANSPORT_QUOTA; do not mutate architecture from it;
- concurrent eye/parallax mutation -> DEFER or rebind; do not compose old visual evidence into a new subject.

## Promotion rule

Scratch evidence can select a body-rig candidate but cannot by itself mint LIVE acceptance. A live candidate must be reversible, exact-subject bound and followed by screenshot/readback + FPS evidence.

Whole-avatar completion, semantic GWT/J-Space, EntityOS completion and training remain outside this lane.
