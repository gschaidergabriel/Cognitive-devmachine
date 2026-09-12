# Avatar special-expression eye identity — candidate lane

Status: **SOURCE CANDIDATE / NOT LIVE / ZERO LIVE VISUAL CREDIT**

## Defect

The current live `buehne.html` (SHA-256 `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`) renders `ausdruck_erweitert/.../frontal/stufe_00..06.png` as full 1536x1024 RGBA head frames. During `_sonderLaeuft` it deliberately suppresses the canonical `#pupillen-glow`, and `blinzeln()` skips the canonical blink channel. Therefore a special-expression frame owns its own eye pixels instead of preserving one eye identity across all states.

This is a separate boundary from the already validated `blink_identity_contamination` candidate (`e8d09af9b3fb3df9020ee3956111f3ba99a1ce5d`).

## Candidate architecture

`build_canonical_eye_expressions.py` builds a **shadow copy** of all 44 x 7 frontal special-expression frames. It does not alter the source tree. In every frame:

- pixels outside the measured eye mask remain pixel-identical to the source expression;
- the hard eye core is pixel-identical to the active canonical neutral head `kopf_rgba/kopf_zero_ohne_rotes_augenglow.png` (expected SHA-256 `489e928fd436253c087183a25b01d685d4ba138bc75bc1b3c4c70a415762f261`);
- a feathered transition surrounds the hard core to avoid a rectangular seam;
- no red gaze signal is painted into the generated frame. Gaze remains a separate runtime channel.

The mask is derived from the already measured eye-local Blink candidate bbox `[42,50,274,118]` in the 319x152 eye-patch coordinate system and from the existing live CSS geometry (`left:31%`, `top:12%`, `width:27%`) on the 1536x1024 head canvas. Current hard core: `[513,170,851,294]` canvas pixels.

`patch_buehne_canonical_eye_identity.py` is bound to the exact live HTML preimage. It only removes the two ownership exceptions that currently turn canonical eye channels off during a special expression:

1. Blink no longer returns early solely because `_sonderLaeuft` is true.
2. Measured gaze opacity is no longer forced to zero solely because `_sonderLaeuft` is true.

The normal gaze honesty rule remains unchanged: if the real face/presence signal says no usable target, opacity remains zero.

## Promotion fence

Do **not** promote this lane until the existing blink-identity candidate is independently accepted live. Otherwise the old high-coverage Blink patch can still reintroduce noncanonical eye/skin pixels during a blink.

Promotion order:

1. Refresh live hashes and ownership. Abort on drift.
2. Require accepted live Blink-identity evidence.
3. Build the 308 expression candidates in a non-live staging directory.
4. Require builder manifest: 44 expression directories, 308 frames, zero outside-mask invariant failures, zero hard-core invariant failures.
5. Produce offline before/after contact sheets across at least the expression families used by the runtime pools.
6. Back up the complete live `ausdruck_erweitert` tree and `buehne.html`.
7. Swap the canonical-eye expression tree first.
8. Apply the exact-preimage HTML patch second. This ordering is intentional: canonicalized assets are safe with eye overlays still disabled; the reverse ordering can briefly render two eye identities.
9. Reload and use the existing deterministic/live hooks to exercise Blink plus special expression; capture before/after evidence.
10. Require no rectangular eye seam, no second-eye/foreign-eye appearance, no non-eye expression regression, and no FPS regression below the current accepted runtime floor.
11. On any failure, rollback HTML first, then expression assets.

## Evidence boundary

What this candidate can eventually prove if promoted and visually accepted:

- one canonical base eye identity persists through special expressions;
- the same canonical Blink channel can operate during special expressions;
- the same measured gaze channel can operate during special expressions.

It does **not** prove whole-avatar photorealism, full GRID10, GWT/J-Space, training readiness, or whole-product completion.
