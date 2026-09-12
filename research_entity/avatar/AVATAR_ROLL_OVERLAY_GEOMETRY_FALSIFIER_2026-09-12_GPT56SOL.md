# Avatar Roll Overlay Geometry Falsifier — GPT-5.6 Sol — 2026-09-12

Status: **CRITICAL FALSIFIER / REAL-HOST CONFIRMED / LIVE FIX NOT YET PROMOTED**

No live Avatar source was modified by this work.

## Exact production subject

- machine/owner: `ai-core-node` / `gabriel`
- live `buehne.html`: SHA-256 `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- live source currently sets the roll overlay state atomically, but composes the eye/blink overlay as:

```js
translate(KOPF_ROLL_AUGEN_OFFSET[roll]) rotate(roll)
```

around the fixed head/neck transform origin.

## Real-host generator authority

Local Bridge read exact `rig2/messen_augenanker_exakt.py` from `ai-core-node`, SHA-256:

`37d3768e440ba003774169823cd449015983597a3fea4a965c9d1a4312837ab0`

That script states and implements the actual roll-photo construction:

1. exact alpha head crop;
2. PIL `rotate(angle=-roll, expand=True)` about crop image center;
3. pin expanded crop bottom-center to fixed `(768,600)` neck anchor;
4. carry a marker at manifest eye anchor `(610,207)` through the same operation.

The accompanying real-host `augen_anker_exakt.json` SHA-256 is:

`4b3280dbf1acf72af377229ef5eadc798a9b48e2939ab1ca96b86c4e976bb8cb`

Its table is the **full generated marker displacement**, e.g.:

- roll `-25`: `(-32.5,+22.0)` px
- roll `-5`: `(-9.5,-1.0)` px
- roll `+5`: `(+10.5,-29.0)` px
- roll `+25`: `(+62.5,-112.0)` px

The generator file itself reports `0° -> (+0.5,+0.5)` because of the 5x5 marker/bbox-center discretization; live code normalizes 0° to `(0,0)`.

## Critical semantic distinction

Because those values are **full target displacement**, they cannot also be used unchanged as the translation operand of a second explicit CSS rotation around the neck anchor. The browser rotation already moves the neutral eye marker. Therefore:

`required_translation = generator_displacement - browser_rotation_displacement`

not the full generator displacement again.

## Independent + real-host Chromium result

The same scratch Chromium discriminator was executed twice:

1. independently outside the production host context;
2. through Local Bridge on the real `ai-core-node` host.

The real-host receipt is:

`local_bridge/results/receipts/avatar-roll-css-generator-falsifier-20260912-1012-gpt56sol.json`

Receipt facts:

- machine_id: `ai-core-node`
- owner: `gabriel`
- status: `PASS`
- exit_code: `0`
- execution boundary: `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`
- production browser/file mutation: `0`

The model uses:

- canvas `1536x1024`;
- marker neutral position `(610,207)`;
- transform origin at fixed neck `(768,600)`;
- exact live CSS order `translate(dx,dy) rotate(roll)`;
- current live table values.

Observed maximum anchor error using the current live composition:

`183.355405 px` native canvas at ±25°.

Representative real-host results:

| roll | generator target dx,dy | pure CSS rotation dx,dy | current-composition error norm |
|---:|---:|---:|---:|
| -25 | -32.5, +22.0 | -151.286, +103.595 | 183.355 px |
| -5 | -9.5, -1.0 | -33.651, +15.266 | 36.952 px |
| +5 | +10.5, -29.0 | +34.853, -12.275 | 36.952 px |
| +25 | +62.5, -112.0 | +180.892, -29.953 | 183.355 px |

Using the residual translation yielded maximum numerical anchor error:

`0.000015 px`.

Real-host residual table produced by the discriminator:

```text
-25: (+118.786, -81.595)
-20: ( +94.885, -65.740)
-15: ( +72.332, -49.285)
-10: ( +49.343, -33.407)
 -5: ( +24.151, -16.266)
  0: (  +0.000,  +0.000)
 +5: ( -24.353, -16.725)
+10: ( -48.644, -34.034)
+15: ( -72.100, -49.998)
+20: ( -96.443, -66.662)
+25: (-118.392, -82.047)
```

These values now have real-host Chromium support, but they are still **not live-authorized** because a matched actual-image visual gate and mutation-boundary reconciliation remain required.

## Mouth-marker instrumentation failure preserved

A separate command attempted to reuse the old `messen_augenanker_exakt.py` module directly for a mouth marker. It failed with:

`FileNotFoundError: /home/ai-core-node/.claude/star/visual/rig2/kopf/master/kopf_zero_mit_augen.png`

Reason: the script computes `VISUAL = dirname(__file__)`, so importing it from `rig2/` makes its internal asset path point under `rig2/kopf/...`. This is classified **HARNESS / INSTRUMENTATION FAILURE**, not a product negative. No replay is treated as accepted evidence until the path binding is repaired explicitly.

## Why this matters to mouth-roll work

The mouth path exposed the broader transform-ownership problem, but it must not copy the current eye table blindly. First resolve the eye table semantics in an exact-image matched gate. Once the correct `generator target -> browser transform` mapping is proven at visual scope, the mouth patch can be derived from the same generator operation at its exact manifest anchor `(622,352)`.

## Highest-information next gate

1. Build an exact-subject **scratch** candidate from live SHA `18770d8e...` that changes only the roll translation semantics from full displacement to validated residual displacement.
2. Run a deterministic actual-image matched browser gate over all 11 roll states with current vs corrected geometry.
3. Assert current geometry reproduces the known large anchor error and corrected geometry reaches the generator marker target within a strict native-pixel tolerance.
4. Verify neutral state byte/visual invariance and no changes to blink timing, gaze semantics, source image identity, body, parallax or production browser.
5. Reconcile with the currently active eye lane before any live mutation.
6. Only then exact-hash guarded live patch, rollback copy, reload the **existing** production page, and independent post-readback.

## Scope fence

This confirms a roll-overlay geometry defect at the measured anchor model. It does not yet promote a live fix, canonical eye identity, blink semantics, parallax, body/GPU, whole-avatar acceptance, HCU/GWT/J-Space, training, or whole-product completion.
