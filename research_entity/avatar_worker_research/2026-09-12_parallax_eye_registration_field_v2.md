# Avatar parallax / eye-registration field discriminator v2

Date: 2026-09-12
Organ: GPT-5.6 Sol / GO macrocycle
Status: BOUNDED_EVIDENCE_CLOSURE

## Question

Is the accepted four-slice head parallax field itself large or spatially discontinuous enough around the dynamic eye patch to plausibly be the dominant source of the remaining visible eye identity / registration problem during roll poses?

This note records a read-only discriminator only. It does not mutate the live avatar and does not claim final eye-identity or whole-avatar acceptance.

## Authority / subjects

- Research main used as branch base: `e736b492a1f94003f8e26f31efb4f64317649d0e`.
- Control command: `local_bridge/commands/go-avatar-gpt56sol-parallax-registration-field-v2-20260912-0752.json`.
- Control command blob SHA: `bd832f656b0866bc159ede3c3e16c2928f6eac97`.
- Result receipt: `local_bridge/results/receipts/go-avatar-gpt56sol-parallax-registration-field-v2-20260912-0752.json` on `chatgpt-local-ai-core-node-results`.
- Result-branch batch commit containing the receipt: `b3c92c7842a471df34560a23fd1987024f315a81`.
- Real local execution boundary: `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`.
- Exact `buehne.html` subject before and after measurement: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`.
- Live source mutation by this discriminator: `0`.

## Correction of the earlier failed discriminator

Earlier receipt `go-avatar-review-parallax-eye-registration-field-20260912-0750` ended with `STATE_COUNT 0` and `AssertionError: 0`.

Classification: **EVIDENCE_INVALID**, not `PRODUCT_NEGATIVE`.

Root causes in the discriminator:

1. It addressed the wrong source layout (`kopf_rgba_tiefe/parallax`) instead of the actual accepted parallax tree `kopf_rgba_parallax/gier_+00_nick_+00_roll_<state>`.
2. It asserted 12 states although the actual roll pool is 11 states: `-25,-20,-15,-10,-05,+00,+05,+10,+15,+20,+25`.

Independent corrected source-binding evidence already showed all 11 reconstructed four-slice states exactly binding to the canonical roll images (`alpha_eq=True`, `rgb_eq=True`, `ALL_ROLLS_SOURCE_BOUND True`).

## Corrected discriminator

The v2 command rebuilt the existing dynamic-eye support from current blink/gaze assets, mapped it into the same head-canvas coordinate system used by the previous discriminator, then measured the local parallax coefficient field across all 11 roll states.

Regions:

- `EYE_CORE`: high-confidence dynamic-eye core.
- `EYE_NZ`: non-zero eye support.
- `EYE_RING15`: 15 px neighborhood outside the eye support, used to detect a local field discontinuity across the eye boundary.
- `UPPER_CONTROL`: broader upper-face control region outside the eye support.

Parallax slice coefficients were measured as `[1, 1/3, -1/3, -1]` before amplitude scaling.

## Result

Receipt status: **PASS**, exit code `0`.

State count: **11 / 11**.

At amplitude `0.25`:

- eye-core p90 effective displacement across states: min `0.232353 px`, median `0.242810 px`, max `0.248039 px`;
- absolute EYE_CORE-vs-EYE_RING15 mean differential: min `0.008185 px`, median `0.025795 px`, max `0.038782 px`.

At amplitude `0.5`:

- eye-core p90 effective displacement: min `0.464706 px`, median `0.485621 px`, max `0.496078 px`;
- core-vs-ring mean differential: min `0.016369 px`, median `0.051591 px`, max `0.077565 px`.

At amplitude `1.0`:

- eye-core p90 effective displacement: min `0.929412 px`, median `0.971242 px`, max `0.992157 px`;
- core-vs-ring mean differential: min `0.032738 px`, median `0.103182 px`, max `0.155129 px`.

Dynamic-eye mask identity in this run:

- mask SHA256: `69c77b4fc9b6eeacbf25d84531f1065cd49881b0d7334aed771fc0101c13170c`;
- EYE_CORE pixels: `7728`;
- EYE_RING15 pixels: `13620`.

## Interpretation

Within the exact metric measured here, the accepted parallax field is **not supported as the dominant cause** of the remaining eye-registration / identity defect.

Reason: even at full unit amplitude, the measured average differential field across the eye-support boundary stays below `0.156 px`, while eye-core p90 displacement stays below `1 px`. At the smaller amplitudes relevant to conservative runtime use, the differential is substantially smaller.

This is a falsification of one narrow hypothesis only:

`PARALLAX_FIELD_BOUNDARY_IS_DOMINANT_EYE_REGISTRATION_CAUSE` -> **NOT SUPPORTED BY THIS DISCRIMINATOR**.

It is **not** proof that parallax has zero perceptual effect, because this measurement does not characterize all local high-frequency geometry, temporal compositing, resampling, roll-transition timing, eyelid/iris semantic mismatch, or subjective identity perception.

## Promotion / non-promotion

Promoted at exact scope:

- corrected source-layout understanding for the accepted parallax stack;
- exact 11-state source binding;
- read-only real-host coefficient-field measurement around the current dynamic-eye support;
- rejection of the specific hypothesis that a large eye-boundary parallax differential is the dominant registration cause.

Explicitly **not promoted**:

- final canonical eye identity acceptance;
- expression-eye A/B acceptance;
- whole-avatar photorealism or lifelikeness completion;
- body-motion completion;
- HCU / Typed Entry architectural credit;
- semantic GWT / J-Space runtime credit;
- model-training or dataset credit;
- whole EntityOS / Frankenstein product completion.

Training credit remains `0`.

## Next exact gate

Do **not** add per-eye parallax compensation from this evidence; that would be an unsupported mutation and risks creating a new registration error larger than the measured field differential.

The next high-information gate is the already-active **expression/eye fixed-identity A/B lane**: compare the canonical-identity eye treatment against the current live treatment under identical head-roll / blink / gaze states, with parallax held constant. If that lane still shows a defect, measure temporal overlay alignment / roll-step atomicity and semantic eye-texture identity before changing the parallax geometry.

HCU / Typed Entry: **NO_CHANGE_WITH_REASON** — this visual registration result does not exercise or falsify those architectural boundaries.

Global J-Space / GWT / training readiness: **NO_CHANGE_WITH_REASON** — this run generates no canonical model target-state labels and no model-specific causal intervention evidence.
