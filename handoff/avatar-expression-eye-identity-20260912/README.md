# Avatar special-expression eye identity — review-only lane

Status: **REVIEW_ONLY / SUPERSEDED BY HOST-DERIVED EYE MASK / DO NOT PROMOTE THIS BRANCH**

## Why this branch is no longer mutation authority

This branch correctly identified a real defect in the current live `buehne.html` (SHA-256 `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`): special-expression frames are full-head RGBA images, while `_sonderLaeuft` suppresses the canonical `#pupillen-glow` and makes `blinzeln()` return early. That still means special expressions can own a different eye identity.

However, after this branch was created, an independent real-host lane produced a strictly better eye-mask candidate from measured image dynamics instead of this branch's rectangular eye-core approximation. To avoid two competing eye authorities, the scripts here are retained only as an independent design/review artifact.

The superseding real-host shadow candidate is:

- command `go-avatar-review-eye-mask-shadow-v1-20260912-0732`;
- `eye_identity_mask.png` SHA-256 `321ef6fa09c6dfb72ab9eb486d623b49d5a4e9c512ace80bfd09ef4e7f3867b0`;
- `eye_identity_open.png` SHA-256 `8ab1a11c6f8a738e34c516bbf65c00e0f48de70c7341bfa970f236e002c94fc9`;
- manifest SHA-256 `2e16c2fb6f7ed3b204a093707492826dd81bd146677604f3c07430ff9db41d95`;
- mask bbox `(39,52)-(273,117)` on the 319x152 patch;
- mapped nonzero mask fraction only `0.009863` of the 1536x1024 full canvas;
- zero live-file mutation during candidate construction.

It derives the eye region from open-vs-closed RGB dynamics, restricts it using the actually measured gaze signal, keeps exactly the two major eye components, then adds a hard margin plus feather. That is a more defensible identity boundary than the fixed rectangle used by this branch.

## Independent evidence

A second real-host read-only run evaluated the host-derived candidate over all 308 special-expression frames:

- hard-core cross-expression variance reduction: **99.811%**;
- mid-mask variance reduction: **98.728%**;
- pixels outside the mask: **max delta 0**.

This strongly supports the host-derived mask as the single candidate to carry forward.

Separately, the localized Blink candidate is now accepted on the productive `augen_blink_relief2` path by `go-avatar-gpt56sol-blink-relief2-live-promote-20260912-0744`:

- candidate -> live filesystem -> HTTP byte readback: PASS;
- real before/idle/blink captures: produced;
- FPS median/min: `60.0 / 60.0` over 15 samples;
- `BLINK_RELIEF2_LIVE_RUNTIME_GATE=PASS`.

This removes the former dependency fence that blocked special-expression eye work. It does **not** by itself close special-expression identity: current live HTML still suppresses gaze during `_sonderLaeuft` and still skips Blink there.

## What remains useful here

`build_canonical_eye_expressions.py` and `patch_buehne_canonical_eye_identity.py` remain useful as an independent architectural cross-check for two invariants:

1. the expression signal outside the eye ownership region must remain unchanged;
2. canonical gaze/Blink should have exactly one runtime ownership path rather than a second special-expression eye subsystem.

They must not be promoted as-is because their mask authority has been superseded.

## Next exact gate

Reuse the existing host-derived `eye_identity_mask.png` / `eye_identity_open.png` and the now-live accepted `relief2` Blink subject. Repair or replace the isolated-browser special-expression A/B harness that most recently failed on a WebSocket screenshot timeout. Only after a clean reversible A/B demonstrates canonical eye persistence through a special expression with no seam/ghost/identity/FPS regression should any live special-expression integration occur.

Live credit for special-expression eye identity remains **0** until that gate passes.
