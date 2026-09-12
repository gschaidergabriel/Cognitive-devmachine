# Depth-warp final-display mechanical readback — 2026-09-12

Status: **A=1.00 ACCEPTED AT MECHANICAL FINAL-DISPLAY SCOPE ONLY**

Execution subject: real `ai-core-node` assets, read-only scratch render at 620×414.
Contact-sheet SHA-256: `b3c2a3fc075781880a010e59343b6106a7a5ccc8878d6a40e59b4eac834f2985`.
Source mutation: none.
Whole-avatar/live credit: 0.
Perceptual/lifelikeness verdict: **UNRESOLVED — requires matched-image readback**.

## A=1.00

All 11 roll poses passed the pre-existing mechanical identity guard.

- failed rolls: none
- alpha exact in every pose: yes
- maximum eye shift: `0.0 px`
- Laplacian detail ratio: `0.9716086005 .. 0.9783808475`
- maximum active-region RGB MAE: `4.7652984`
- maximum active-region RGB p99: `48`
- maximum displacement at final display: `0.40364593 px`
- maximum p95 displacement at final display: `0.40257511 px`
- minimum active pixels changed by >1: `0.67178218`
- minimum active pixels changed by >3: `0.48278328`

Interpretation: the signal survives final display resampling while preserving the measured alpha, eye-registration and detail constraints at all tested rolls.

## A=1.25

Rejected as a general mechanical candidate under the same guard.

- failed rolls: `-25`, `-20`, `-10`, `+05`, `+10`
- alpha exact in every pose: yes
- maximum eye shift: `0.0 px`
- Laplacian detail ratio: `0.9676146867 .. 0.9763590732`
- maximum active-region RGB MAE: `5.8526120`
- maximum active-region RGB p99: `59`
- maximum displacement at final display: `0.50455737 px`

The failures are not repaired by changing thresholds. A=1.25 remains rejected at this scope unless a later independently justified architecture changes the discriminator itself.

## Credit fence

This result does **not** establish perceptual superiority, uncanny realism, live integration, whole-avatar correctness, or production acceptance. The next valid promotion is matched visual/perceptual readback of A=1.00 against the exact baseline, followed only then by a reversible live-integration gate.
