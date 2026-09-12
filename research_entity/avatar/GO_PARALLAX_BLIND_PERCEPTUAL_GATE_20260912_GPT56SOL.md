# GO — Avatar depth-warp blind perceptual gate

Date: 2026-09-12  
Actor: GPT-5.6 Sol / ChatGPT organ  
Scope: Avatar parallax/depth-warp promotion falsifier only

## Why this gate exists

The accepted isolated AMD WebGL gate proves that the guarded single-texture depth warp can execute near 60 FPS with GL error 0. The existing display-space gate proves that a subpixel signal survives 620x414 minification while alpha, eye registration and detail can remain bounded. Neither result proves that a human observer receives useful 3D depth rather than a brightness, resampling, position, expectation or registration artifact.

Therefore this gate generates a blinded final-display review set. It does **not** promote the live Avatar and does **not** award perceptual-benefit or production credit by itself.

## Tool

`research_entity/avatar/tools/depthwarp_blind_perceptual_gate.py`

Default candidate amplitudes: `1.0` and `1.25` over all 11 roll poses `-25..+25`.

Default display footprint: `620x414`, matching the current display-space gate.

## Controls

For every roll the generator renders:

- BASE: canonical live-bound roll source downsampled through `INTER_AREA`.
- NULL_REMAP: the exact depth-warp remap pipeline with amplitude `0.0`, then the same downsample path.
- WARP: the guarded depth warp at A=1.0 or A=1.25, then the same downsample path.

BASE↔WARP pairs are randomized deterministically. The public blind manifest never contains the condition labels. The answer key is a separate artifact and contains the RNG seed and source SHA-256 bindings.

Six default sham BASE↔NULL_REMAP trials estimate position/expectation and zero-displacement resampling bias.

## Objective eligibility fence

A BASE↔WARP case is merely eligible for blind review when all default conditions hold:

- alpha is byte-identical,
- final-display Laplacian detail ratio >= 0.90,
- eye phase shift <= 0.25 display px,
- active-region RGB MAE is >= max(0.20, 3 × NULL_REMAP MAE),
- absolute mean-luma bias / RGB MAE <= 0.50.

These thresholds are falsification/eligibility fences, not proof of perceptual superiority.

## Human blind read

`blind_scores.csv` asks the reviewer to choose A, B or INDISTINGUISHABLE for coherent 3D depth while preserving identity, plus confidence and identity-artifact severity. The answer key must not be opened before scoring.

No automatic majority threshold is encoded in the generator. A promotion decision must be preregistered before unblinding and must separately control sham/position bias.

## Evidence law / credit

Allowed from this gate alone:

- source/tooling credit,
- objective identity-eligibility credit,
- reproducible blind-test material.

Forbidden from this gate alone:

- perceptual-benefit credit,
- live parallax credit,
- production-performance credit,
- whole-Avatar credit.

The film-treatment/live-compositor path remains a separate execution boundary. Offline 620x414 evidence must not be relabeled as final production perception.

## Real-host execution contract

A real-host run must:

1. bind the exact tool commit SHA,
2. read production assets only,
3. write all outputs under a scratch/evidence directory,
4. record pre/post hashes of `buehne.html`, `buehne_daemon.py`, and `filmlook.js`,
5. prove those hashes are unchanged,
6. preserve `blind_manifest.json`, `answer_key.json`, `objective_report.json`, `blind_scores.csv`, and pair images,
7. award zero production/perceptual credit until independent blind scoring exists.
