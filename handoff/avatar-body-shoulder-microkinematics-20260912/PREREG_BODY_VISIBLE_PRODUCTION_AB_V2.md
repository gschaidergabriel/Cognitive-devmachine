# Preregistration — visible production-shape body residual A/B v2

Date: 2026-09-12

## Purpose

Confirm, on the real `ai-core-node` X11/AMD display stack, whether the already-reviewed residual-body WebGL compositor can be added as hidden work without materially consuming the current 60 Hz avatar budget.

This is an execution-surface/runtime-cost gate only. It does **not** authorize a visible body replacement, live-file mutation, eye/head mutation, production enablement, or whole-avatar acceptance.

## Frozen subject

- live avatar HTML SHA-256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- parent evidence branch baseline: `14e1a18551dcee44fb79f372d2f48766eafa94b6`
- first visible adapter implementation: `95522e2d88613fd05423c29962073e8229646926`
- browser: `/opt/google/chrome/chrome`
- display: `:0`
- fresh Chrome profile for each BASE/SHADOW condition
- app window: 746x449, positioned away from the production avatar window

## Confirmatory acceptance rule

A later confirmatory run is `PASS_AT_VISIBLE_ADDITIVE_COST_SCOPE` only if **every** item below holds for two independent repetitions:

1. exact live HTML SHA is the frozen hash before and after the run;
2. each BASE and SHADOW summary has at least 8 valid post-warmup samples;
3. WebGL SHADOW metadata has no error and identifies the real AMD renderer path;
4. `shadow_fps_mean >= 58.0` for each repetition;
5. `shadow_fps_mean - base_fps_mean >= -1.0` FPS for each repetition;
6. `shadow_fps_min >= base_fps_min - 2.0` FPS for each repetition;
7. residual shadow draw count is non-zero and advances materially during measurement;
8. no residual `body-fullscene-visible-chrome-*` Chrome process remains after the gate;
9. no live avatar source file is written or replaced.

Any failed item is a `PRODUCT_OR_EXECUTION_NEGATIVE_AT_THIS_SCOPE` until classified. Missing samples/renderer/readback are `EVIDENCE_INVALID`, not a product failure.

## Explicit zero-credit boundaries

Even on PASS:

- visible residual-body visual quality credit: **0**
- seam/ghost/lifelikeness acceptance: **0**
- eye/head/roll acceptance: **0**
- live production feature enablement: **0**
- whole-avatar acceptance: **0**

The next boundary after a cost PASS is a deterministic, matched-image visible candidate-vs-baseline readback with seam/ghost registration checks, followed only then by a reversible dormant production feature gate.
