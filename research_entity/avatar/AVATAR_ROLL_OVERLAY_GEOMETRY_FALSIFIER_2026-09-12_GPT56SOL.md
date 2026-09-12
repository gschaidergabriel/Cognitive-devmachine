# Avatar Roll Overlay Geometry Falsifier — GPT-5.6 Sol — 2026-09-12

Status: **CRITICAL FALSIFIER / REAL-HOST GENERATOR BOUND / LOCAL CHROMIUM CONFIRMED / REAL-HOST CHROMIUM RECEIPT PENDING**

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

Because those values are **full target displacement**, they cannot automatically also be the translation operand of a second explicit CSS rotation around the neck anchor. If the browser rotation already moves the marker from the neutral position, the translation operand required to reach the generator target is:

`required_translation = generator_displacement - browser_rotation_displacement`

not the full generator displacement again.

## Independent Chromium scratch result

A scratch Chromium geometry model was run outside production using:

- canvas `1536x1024`;
- marker neutral position `(610,207)`;
- transform origin mapped to fixed neck `(768,600)`;
- exact live transform order `translate(dx,dy) rotate(roll)`;
- current live table values.

No production page/browser/window/file was touched.

Observed maximum anchor error using the current composition:

`183.3554 px` native canvas at ±25°.

Representative results:

| roll | generator target dx,dy | pure CSS rotation dx,dy | current-composition error norm |
|---:|---:|---:|---:|
| -25 | -32.5, +22.0 | -151.286, +103.595 | 183.355 px |
| -5 | -9.5, -1.0 | -33.651, +15.266 | 36.952 px |
| +5 | +10.5, -29.0 | +34.853, -12.275 | 36.952 px |
| +25 | +62.5, -112.0 | +180.892, -29.953 | 183.355 px |

Using the residual translation instead yielded maximum numerical error about `1.5e-5 px` in the scratch Chromium model.

Provisional residual table from that browser geometry:

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

These numbers are **not authorized for live use yet**. They are a falsifier output pending same-host Chromium confirmation and a matched visual gate.

## Why this matters to mouth-roll work

The mouth path exposed the broader transform-ownership problem, but it must not copy the current eye table blindly. First fix/resolve the semantic meaning of the eye table versus CSS rotation. Once the correct `generator target -> browser transform` mapping is proven, the mouth patch can be derived from the same generator operation at its exact manifest anchor `(622,352)`.

## Real-host confirmation dispatched

A read-only/scratch Local Bridge command has been dispatched:

`avatar-roll-css-generator-falsifier-20260912-1012-gpt56sol`

It runs isolated Playwright/Chromium geometry only and explicitly does not open or reload a production browser or mutate the live file.

Promotion remains blocked until that receipt is PASS and the current active eye worker lane is reconciled.

## Scope fence

Even if confirmed, this is a roll-overlay geometry defect/fix only. It does not promote canonical eye identity, blink semantics, parallax, body/GPU, whole-avatar acceptance, HCU/GWT/J-Space, training, or whole-product completion.
