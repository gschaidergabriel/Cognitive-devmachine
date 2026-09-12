# Canonical eye identity — convergence checkpoint

Date: 2026-09-12

Status: **PRE-LIVE CANDIDATE / LIVE MUTATION FENCED**

## Current exact live subject

- `visual/buehne.html` SHA-256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- `visual/buehne_daemon.py` SHA-256: `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`
- productive masked open eye / `augen_blink_relief2/blink_000.png`: `8ab1a11c6f8a738e34c516bbf65c00e0f48de70c7341bfa970f236e002c94fc9`
- semantic shadow candidate: `4fb62046e650f993edb89be24c40262fb8e7202e2c7cda14df7aa0113cfbfb4d`

Any live-subject drift invalidates this promotion packet until re-measured.

## What is now closed

### Serving authority

Real-host HTTP byte readback proves:

- `/augen_blink/blink_000.png` serves exactly `8ab1a11c...`;
- the old nearly-full-alpha `augen_blink/blink_000.png` file remains historical/local data and is **not** what the live public route serves;
- `/augen_gaze/rotglow_tracking_master.png` likewise resolves to the productive `augen_gaze_relief2` asset.

This closes the serving-route ambiguity without creating a second public route.

### Builder call-graph defect

The first deterministic semantic-shadow rebuild correctly failed because the builder assumed the blink end-state opacity mutation still lived inside `blinzeln()`.

Real-host forensics proved the current call graph is split:

- `blinzeln()` schedules the frame sequence and delegates to `blinzelAbspielen()`;
- `blinzelAbspielen()` owns the terminal eye-opacity state.

The builder was repaired accordingly. It now:

1. removes only the `_sonderLaeuft` early-return from `blinzeln()`;
2. restores `BLINK_BILDER[0]` and keeps opacity `1` at the terminal branch of `blinzelAbspielen()`;
3. preserves canonical `/augen_blink/...` routing;
4. keeps gaze above the canonical eye plate;
5. hides gaze on actual `blinzelPhase`, not merely because a special expression is active.

### Deterministic real-host shadow build

`go-avatar-gpt56sol-eye-shadow-regression-v3-20260912-1054` passed on `ai-core-node` with all eight invariants true and no live source mutation.

Candidate SHA-256: `4fb62046e650f993edb89be24c40262fb8e7202e2c7cda14df7aa0113cfbfb4d`.

### Isolated special-expression compositing

`go-avatar-gpt56sol-expression-eye-ab-v2-20260912-1050` passed on the real host in an isolated browser DOM:

- special expression: `anime_90s/anime_fassungslos`;
- canonical eye produced a visible delta;
- gaze compositing produced a visible delta;
- source mutation: false.

This proves the intended layer path can materially affect the special-expression runtime. It is **not** by itself a visual-quality or seam acceptance gate because the captures were temporally separated.

### Roll / eye registration dependency

The existing 11-pose parallax/eye-seam packet already established current eye-anchor authority and 22/22 valid matched captures at the conservative parallax amplitude, with no hard eye-patch edge inflation and no live mutation. Do not reopen that geometry authority without new executable counterevidence.

## Preserved negative / invalid evidence

1. Original semantic-shadow builder failure: **EVIDENCE/BUILDER DEFECT**, root cause repaired.
2. First repaired build invariant failure: **HARNESS ASSERTION DEFECT**; the regex escaped the `blinzeln()` body and matched later `_sonderLaeuft` state. Fixed by extracting the exact function body.
3. Shadow runtime v1: **EVIDENCE_INVALID / CDP TRANSPORT TIMEOUT** during one long `awaitPromise`; no product invariant had failed. A v2 validator now uses short synchronous CDP calls plus wall-clock sampling.
4. The temporally separated A/B changed a very large fraction of its crop. HTTP route falsification proved this was **not** caused by the old full-alpha eye asset being served. Therefore a matched frozen A/B is required before visual promotion.

## New durable discriminators

- `validate_shadow_blink_runtime_v2.py`
  - no long CDP promises;
  - exercises the real special-expression + real blink scheduler/player on the semantic shadow;
  - requires `halb1`, `zu`, `halb2`, multiple blink frames, glow hidden during lid activity, canonical eye opacity retained, return to frame 000, >=58 FPS, p95 <=18 ms, and unchanged live source.

- `validate_matched_eye_ab.py`
  - pauses Chrome virtual time after entering a real special expression;
  - captures eye-off, eye-on, eye-off-repeat from the exact same frozen state;
  - rejects non-eye drift, an old rectangular/full-patch footprint, and strong edge-energy inflation;
  - no live source write.

## Mutation authority / coordination fence

**No worker should live-write `buehne.html` for canonical eye identity yet.**

The current semantic boundary is single-owner/frozen until both remaining pre-live discriminators have executable receipts against the exact subject above:

1. robust shadow blink runtime v2;
2. virtual-time-frozen matched eye A/B.

A duplicate semantic successor before these results would create runtime-subject churn and is not useful work.

If another worker already owns either discriminator, overlap should become REVIEW_ONLY / FALSIFIER rather than a second mutation path.

## Live-promotion gate after both pre-live discriminators pass

Only then is a reversible live candidate justified:

1. re-read exact live hashes;
2. refuse on any drift;
3. preserve byte-exact rollback of `buehne.html`;
4. install exactly the accepted semantic-shadow bytes, atomically;
5. verify filesystem SHA and HTTP page readback;
6. exercise a real special expression + blink + gaze path;
7. measure FPS/jank and capture visual evidence;
8. run an independent post-write readback/falsifier;
9. rollback immediately on any gate failure and verify the original SHA is restored.

Promotion scope, if successful, is only **special-expression canonical eye identity**. It does not mint whole-avatar photorealism, GRID10/GWT/J-Space, effect, training, or whole-product credit.

## Parallel lanes

Body/shoulder WebGL evidence is currently positive at bounded runtime/performance scope (~60 FPS on the real AMD/ANGLE path), but live body microkinematics remains a separate perceptual/temporal promotion boundary.

Parallax `A=0.25` remains a safe pre-live candidate at measured geometry/seam scope but still lacks a positive perceptual-benefit discriminator. Do not promote merely because it is safe.
