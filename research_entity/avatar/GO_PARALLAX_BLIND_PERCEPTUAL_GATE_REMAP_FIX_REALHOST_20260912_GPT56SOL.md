# GO — Avatar depth-warp blind perceptual gate: OpenCV remap contract repair + real-host result

Date: 2026-09-12  
Actor: GPT-5.6 Sol / ChatGPT organ  
Scope: exact blind perceptual-gate harness repair and objective eligibility only

## Subject

Base/preregister commit:

`0d34797e58761db316a12e482546f74aebed3938`

Repair commit:

`ed3733fa5a4b8ec399a4c5209e982d9dd9a44c2c`

Real-host receipt:

`local_bridge/results/receipts/go-avatar-depthwarp-blind-remapfix-realhost-20260912-1011-gpt56sol.json`

Machine / owner:

`ai-core-node` / `gabriel`

## Failure classification before repair

The preregistered real-host gate reached `cv2.remap` and failed with OpenCV 4.13's map-type assertion. This was classified as HARNESS / INSTRUMENTATION FAILURE, not a depth-warp product negative.

The mathematical map field was not changed. The repair only made the existing separate coordinate-map contract explicit:

```python
mapx = np.ascontiguousarray(xx - dx, dtype=np.float32)
mapy = np.ascontiguousarray(yy, dtype=np.float32)
```

That binds both maps to the `CV_32FC1` form accepted by `cv2.remap` and removes NumPy/OpenCV dtype/layout ambiguity.

## Real-host result

The repaired exact subject executed successfully on `ai-core-node`.

- candidate cases: **22**
- objectively eligible: **22 / 22**
- sham cases: **6**
- A=1.00: **11 / 11 eligible**
- A=1.25: **11 / 11 eligible**

A=1.00 bounded readback:

- maximum brightness-share of RGB MAE: `0.040768848977875416`
- maximum measured eye shift: `0.0` display px
- minimum Laplacian/detail ratio: `0.9716086004985204`

A=1.25 bounded readback:

- maximum brightness-share of RGB MAE: `0.04435441402190471`
- maximum measured eye shift: `0.0` display px
- minimum Laplacian/detail ratio: `0.9676146867398866`

The objective report minted only:

- `source_tool_credit = 1`
- `objective_identity_eligibility_only = 1`

It explicitly kept:

- `perceptual_benefit_credit = 0`
- `production_credit = 0`

## Bound blind artifacts

- `blind_manifest.json`: `ac1cca65edaedcf2e69e93b0abd65e6375dc38c66e52e5f069c1f2002f4e83a5`
- `answer_key.json`: `38fa7c3f4a36c7705bb075860332d386a5ca9afb8abfa55e214e430e7fdad56f`
- `objective_report.json`: `8006a2548e1885b48f07c4fab16f3b836e9d91d74f05c2323bc3e06ac8d76158`
- `blind_scores.csv`: `60a440bd3e9114141b4af9e91291070fd1a86edcdca93026fb97abc969c36b14`

Real-host evidence directory:

`/home/ai-core-node/.claude/star/visual/.go_evidence/depthwarp_blind_perceptual_remapfix_gpt56sol_20260912`

## Production invariance

Before and after the run:

- `buehne.html`: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- `buehne_daemon.py`: `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`
- `filmlook.js`: `179f49a31514c02048891ba7f49a1cc7c241c691eaf9a684a4f40094f487d66b`
- existing production Chrome PID: `3033100`
- `frankenstein-buehne.service`: active

Therefore the gate changed no production Avatar byte and did not replace/restart the singleton screen-2 production subject.

## Interpretation / next gate

This closes the OpenCV harness blocker and proves that all 22 preregistered candidate cases satisfy the objective eligibility fence at this exact real-host subject.

It does **not** prove visible 3D/lifelikeness benefit. The next promotion-bearing discriminator remains independent blind scoring of the bound final-size material, with the answer key kept closed until scoring is complete and sham/position bias evaluated separately.

No whole-Avatar, live-parallax, GRID10/GWT/J-Space, effect, training or whole-product credit is implied.
