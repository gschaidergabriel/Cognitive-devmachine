# Avatar Mouth/Roll Registration Finding — GPT-5.6 Sol — 2026-09-12

Status: **NEW NONDUPLICATE DEFECT CANDIDATE / EVIDENCE-BOUND / NO LIVE MUTATION**

## Exact subject

- machine: `ai-core-node`
- owner: `gabriel`
- live file: `/home/ai-core-node/.claude/star/visual/buehne.html`
- exact read receipt SHA-256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- live service/window boundary remains the one existing `frankenstein-buehne.service` + visible production Chrome on HDMI-A-0.

This note does not authorize a live write.

## Source-level asymmetry

The current live subject applies explicit roll geometry to `#augen-blink` and `#pupillen-glow`, while `#mund-effekt` remains a neutral-coordinate RGBA face/mouth patch.

- Mouth manifest geometry documented in live source: anchor `(622,352)`, patch `295x182`, canvas `1536x1024`.
- `#mund-effekt` is nested in `#kopf-dreh`, so it inherits the small shared spring `kDrehRot/kDrehTy`.
- `kopfRollTick()` switches the underlying head photograph to baked roll poses up to ±25°.
- `mundSchritt()` changes only `#mund-effekt.src`.
- No current live assignment applies `kopfRollWert`, a roll-specific translation, or an equivalent generated transform to `#mund-effekt`.

This makes mouth/rolled-photo registration a real unowned geometry boundary, but source inspection alone does not prove a visible defect.

## Exact generator readback — important correction

Local Bridge read the real host files:

- `rig2/messen_augenanker_exakt.py` SHA-256 `37d3768e440ba003774169823cd449015983597a3fea4a965c9d1a4312837ab0`
- `rig2/augen_anker_exakt.json` SHA-256 `4b3280dbf1acf72af377229ef5eadc798a9b48e2939ab1ca96b86c4e976bb8cb`

The script explicitly reproduces `build_rig_v2.py` geometry:

1. crop exact head alpha bbox;
2. `rotate(angle=-roll, expand=True)` about the crop image center;
3. bottom-center pin the expanded crop to fixed head/neck anchor `(768,600)`;
4. transform a marker at the real manifest eye anchor `(610,207)` through the same operation;
5. store **full marker displacement** relative to roll=0.

Therefore the current `KOPF_ROLL_AUGEN_OFFSET` source table is not established by this file as a mere post-CSS residual. An earlier candidate on this branch assumed that it could be reused directly as a common residual for the mouth. That assumption is **withdrawn**. The corresponding patcher/test were deleted from the branch before any live write.

This negative result is preserved deliberately: no production bytes were changed.

## Falsifiable prediction

If the mouth patch is visible while `kopfRollWert != 0`, its neutral-canvas patch may drift/rotate relative to the baked rolled head because no explicit photo-specific mouth transform exists. The strongest discriminator is the existing deterministic `k` roll diagnostic combined with a fixed mouth frame and matched 0° -> rolled -> 0° captures while the exact source hash remains invariant.

Reject the defect hypothesis if the mouth/head registration remains stable within a predeclared pixel/edge tolerance without roll-specific mouth geometry. Confirm it if displacement co-varies with roll and reverses at 0°.

## Exact mouth origin fact

If a CSS transform around the same fixed head/neck anchor is eventually part of the correct model, the exact origin relative to the mouth patch box is:

- X: `(768 - 622) / 295 * 100 = 49.49152542%`
- Y: `(600 - 352) / 182 * 100 = 136.26373626%`

This is a geometry fact only, not a complete correction.

## Highest-information next gate

Before creating a new mouth table or touching production:

1. recover the already-accepted live roll/eye discriminator that produced the current `18770d8e...` subject;
2. establish exactly how the current CSS `translate(...) rotate(...)` composition was evaluated against the generator marker path;
3. test mouth registration against the same geometric convention, not a newly invented convention;
4. only then build a scratch candidate and matched real-display A/B;
5. live promotion remains exact-hash guarded, single-mutator, rollback-protected, existing-window reload only, and independently read back.

## Scope fence

No mouth/roll result promotes blink identity, whole-avatar quality, body/GPU, parallax, HCU/GWT/J-Space, training, or whole-product acceptance.
