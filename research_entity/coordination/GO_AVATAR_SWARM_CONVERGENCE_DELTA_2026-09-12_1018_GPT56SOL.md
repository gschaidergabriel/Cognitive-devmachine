# GO Avatar Swarm Convergence Delta — 2026-09-12 10:18 +07 — GPT-5.6 Sol

Status: **NONCANONICAL / INCREMENTAL**. This delta supersedes only stale frontier statements in the earlier 10:04 delta. It does not mint production, perceptual-benefit, whole-avatar, provider, HCU, J-Space, or training credit.

## Production subject remains protected

Current bounded production subject remains:

- machine: `ai-core-node`, owner `gabriel`
- live frontend: `/home/ai-core-node/.claude/star/visual/buehne.html`
- observed SHA-256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- daemon SHA-256: `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`
- service: `frankenstein-buehne.service`
- existing production Chrome PID in the current evidence epoch: `3033100`
- measured production status: `60.0 FPS` in the body-baseline receipt

No live Avatar source mutation was performed by this lane.

Main has since made the singleton rule explicit. Current canonical helper:

`research_entity/coordination/avatar_singleton_refresh.sh`

Live helper path on `ai-core-node`:

`/home/ai-core-node/.claude/star/visual/avatar_singleton_refresh.sh`

Any future admitted live Avatar update must use that singleton helper rather than spawning or manually substituting a second production Chrome.

## Parallax frontier correction — source/integrity is substantially closed

The earlier 10:04 statement `parallax provenance: OPEN` is now too weak.

Stronger existing swarm evidence establishes:

1. `tiefe_bauen.py` identifies the generation lineage as `depth-anything/Depth-Anything-V2-Small-hf` and contains the parallax generation mode/path.
2. The experimental parallax tree contains 48 RGBA PNGs at 1536x1024: 11 roll poses x 4 slices plus the zero reference family.
3. The depth-parallax manifest records four slices per pose and `alpha_summe_identisch=true`.
4. A corrected independent discriminator bound all 11 roll-pose four-slice recompositions exactly to the canonical `kopf_rgba/roll` source images: `alpha_eq=True`, `rgb_eq=True`, `ALL_ROLLS_SOURCE_BOUND=True`.
5. The parallax field around the eye region is too small to support the hypothesis that the parallax boundary itself is the dominant remaining eye-registration defect. At amplitude 1.0 the measured relative field was still only about 0.155 px in that discriminator.

What remains unproven:

- exact bit-reproducibility from original source + exact model/cache/runtime;
- perceptual benefit on the final display;
- live integration/activation.

Therefore:

`PARALLAX_SOURCE_PROVENANCE = BOUNDED_PASS`

`PARALLAX_SOURCE_BINDING_11_ROLLS = PASS`

`PARALLAX_LIVE_ACTIVATION = 0`

`PARALLAX_PERCEPTUAL_BENEFIT = UNPROVEN`

## Parallax amplitude search is now bounded

The current real-host extended CSS gate constrains the useful search range:

- A=0.25: previous seam/identity gate remained mechanically safe; max displayed motion is very small.
- A=0.50: previous gate still had no deep holes and is the useful larger comparator.
- A=0.75: 167 deep-hole pixels observed and max display shift about 0.303 px.
- A=1.00: 462 deep-hole pixels.
- A=1.25: 495 deep-hole pixels.
- A=1.50: 560 deep-hole pixels.
- A=2.00: 1028 deep-hole pixels.

So amplitudes >=0.75 are not the next rational perceptual search space.

A blind stimulus packet for exactly `{0, 0.25, 0.50}` has already run on the real host without production mutation. In that packet:

- blinded codes were `R2=0`, `K7=0.25`, `M4=0.50`;
- the zero-motion phase remained effectively identical (`p99=0`);
- nonzero phases were mechanically discriminable;
- perceptual-benefit credit remained zero because stimulus generation is not perceptual scoring.

Do not dispatch another parallax renderer or another amplitude sweep while the existing benefit lane owns that boundary.

## New highest-information eye frontier — residual transform composition

The live source already contains the older atomic timebase fix:

- `kopfRollAusgleichDeg = kopfRollWert`;
- measured `KOPF_ROLL_AUGEN_OFFSET` is applied on the same visible roll-photo step;
- eye/blink and gaze layers live inside `#kopf-dreh`.

That closes the former 2-3-frame Lerp lag. It does **not** automatically prove the static transform composition.

A new independent real-host scratch discriminator (`avatar-roll-css-generator-falsifier-20260912-1012-gpt56sol`) tested the actual live transform form:

`translate(measured_dx, measured_dy) rotate(roll)`

about the same neck anchor used by the head. Because the measured table is the final generator-observed eye-marker displacement, `rotate()` already contributes part of that displacement. Applying the full measured displacement again as `translate()` double-counts the rigid rotation component.

Scratch Chromium result over all 11 roll states:

- maximum current modeled marker error: `183.355405` native px at ±25°;
- analytically/browser-derived residual translations remove that modeled error to <= `1.5e-05` px in the discriminator;
- scope was explicitly `SCRATCH_HEADLESS_CSS_GEOMETRY_ONLY_NO_PRODUCTION_BROWSER_NO_LIVE_MUTATION`.

This is a **strong candidate defect**, not yet a production-negative, because final credit requires exact current-source binding plus a shadow visual discriminator.

## Residual candidate implementation

A disjoint feature branch now owns this frontier:

`chatgpt-gpt56sol-avatar-roll-residual-geometry-20260912`

Branch artifacts:

- `research_entity/avatar/tools/roll_eye_residual_geometry_gate.py`
- `research_entity/avatar/tools/build_roll_eye_residual_shadow.py`

Candidate law:

`local CSS translation = measured generator displacement - rigid rotation displacement about neck anchor`

The measured generator table remains authority; no new hand-fitted table is introduced.

The shadow builder is hash-guarded and refuses in-place mutation. It only writes a distinct scratch output.

A real-host gate has been queued through the existing Local Bridge:

`go-avatar-roll-residual-shadow-gate-20260912-1016-gpt56sol`

Command commit:

`cd7619021bffcdea5e02880901bb9968b2cd7dae`

Required postconditions of that queued gate:

- exact live input SHA must equal `18770d8e...`;
- both branch tools must Python-compile;
- Chromium browser-vs-analytic rotation math must agree fail-closed;
- current transform error must reproduce;
- residual candidate must reduce modeled error below the strict gate threshold;
- scratch shadow must be generated at a separate path;
- production HTML SHA must remain unchanged;
- production Chrome PID must remain unchanged;
- `frankenstein-buehne.service` must remain active.

At generation time of this delta, no result receipt for that command had yet been published. Therefore the branch candidate remains **UNPROMOTED**.

## Eye V6 harness classification

The first `go-avatar-eye-v6-idle-realhost-20260912-1006-gpt56sol` run failed because required CLI arguments (`--visual-root`, `--shadow`, `--out`) were omitted. It still verified production hash/PID invariance.

Classification:

`HARNESS_FAIL / NOT AVATAR_NEGATIVE`

A V2 rerun with exact shadow and explicit arguments was queued separately. Do not infer PASS/FAIL before its exact receipt exists.

## Swarm/provider fence remains hard

General multi-worker coordination is active and useful. Provider execution is a separate authority boundary.

Current Clay authority still says FreeSwarm/provider admission is `HARD_OFF`. The earlier attempted Nemotron provider command was removed from the current control tree and must not be resurrected by interpreting "swarm" as provider permission.

## Current nonduplicate next sequence

1. Consume the exact receipt for `go-avatar-roll-residual-shadow-gate-20260912-1016-gpt56sol` when present; preserve failure classification exactly.
2. If the residual gate fails: fix the discriminator/tooling, not production.
3. If it passes: use the generated residual shadow in one isolated matched visual/X11 A/B across neutral and nonzero roll states; preserve the existing production singleton.
4. Require eye/blink/gaze registration improvement without creating forehead seams, second-eye artifacts, or temporal pops.
5. Only then consider a separately admitted live mutation.
6. Any live mutation must re-read current source hash, re-check active Avatar workers, preserve rollback bytes, write exactly one subject, call canonical `avatar_singleton_refresh.sh`, and independently verify same display-2 production subject + FPS + hash/readback.
7. Parallax benefit scoring remains owned by the existing blind-benefit lane; do not duplicate it.

## Promotion vector

- production runtime health: bounded positive evidence
- measured roll table: positive source evidence
- atomic roll/photo timebase: implemented in current live source
- residual transform candidate: **STRONG CANDIDATE / SHADOW GATE QUEUED / NOT PROMOTED**
- Eye V6 first run: harness failure only
- parallax source provenance: bounded pass
- parallax 11-roll source binding: pass
- parallax perceptual benefit: unproven
- parallax live activation: 0
- whole-avatar acceptance: 0
- FreeSwarm/provider execution: HARD_OFF
