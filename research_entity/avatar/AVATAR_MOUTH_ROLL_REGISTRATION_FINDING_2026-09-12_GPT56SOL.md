# Avatar Mouth/Roll Registration Finding — GPT-5.6 Sol — 2026-09-12

Status: **NEW NONDUPLICATE DEFECT CANDIDATE / EVIDENCE-BOUND / NO LIVE MUTATION YET**

## Exact subject

- machine: `ai-core-node`
- owner: `gabriel`
- live file: `/home/ai-core-node/.claude/star/visual/buehne.html`
- exact read receipt SHA-256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- live service/window boundary remains the one existing `frankenstein-buehne.service` + visible production Chrome on HDMI-A-0.

This note does not authorize a live write.

## Why this is not duplicate eye work

The swarm already isolated and corrected the temporal eye/roll registration class. In the current live subject, `kopfKoerperDrehSchritt()` atomically binds the photo roll to `KOPF_ROLL_AUGEN_OFFSET`, `kopfRollAusgleichDeg`, `augenOffsetDx`, and `augenOffsetDy`; both `#augen-blink` and `#pupillen-glow` receive roll-specific translation + rotation.

The mouth path is structurally different:

- `#mund-effekt` is a neutral-coordinate RGBA face/mouth patch anchored at canvas coordinate approximately `(622,352)` via CSS `left:40.49%; top:34.38%; width:19.21%; height:17.77%`.
- It is nested in the same `#kopf-dreh` wrapper, so it inherits the small shared spring `kDrehRot/kDrehTy`.
- `kopfRollTick()` switches the underlying head photograph to baked roll poses up to ±25°.
- `mundSchritt()` changes only `#mund-effekt.src`.
- No current live assignment applies `kopfRollWert`, a per-roll translation table, or an equivalent generated transform to `#mund-effekt`.
- No `MUND_ROLL_*` geometry exists in the exact live source.

Therefore the shared wrapper handles only the small common spring, while the photo-specific baked roll still has an apparently unowned registration requirement for the mouth patch.

## Falsifiable prediction

If the mouth patch is visible while `kopfRollWert != 0`, its neutral-canvas patch should drift/rotate relative to the baked rolled head unless some asset-internal transform not visible in the current source happens to compensate it. This must be tested; it is not promoted from source inspection alone.

The strongest deterministic discriminator is the existing `k` roll diagnostic combined with a fixed mouth frame and matched screenshots/state captures at 0°, +5°, +10°, +15° and return-to-zero, with the current source hash held invariant.

Reject the defect hypothesis if the mouth/head seam remains registered to measurement tolerance without any roll-specific mouth transform. Confirm it if mouth-patch edge/landmark displacement co-varies with roll and returns at 0°.

## Geometry path — do not hand-fit

The eye fix already established the correct generator-level method: derive offsets through the same `transform_crop_about_anchor()` geometry used to produce the rolled head photographs. Reuse that generator math for the mouth anchor; do not invent another hand-tuned table.

The current neutral mouth box implies a neck-anchor transform origin of approximately:

- X: `(768 - 0.4049*1536) / (0.1921*1536) ≈ 49.5%`
- Y: `(600 - 0.3438*1024) / (0.1777*1024) ≈ 136.3%`

Those numbers are only a derived candidate for reproducing the existing eye strategy. Final values must come from exact source dimensions/anchor data and the same generator transformation, not from rounded CSS percentages.

## Next gate

1. Read the exact live `rig2/messen_augenanker_exakt.py` and `rig2/augen_anker_exakt.json` through Local Bridge.
2. Extend the geometry calculation on a scratch/repo artifact to the mouth anchor without touching production.
3. Generate `MUND_ROLL_OFFSET` mechanically for the same `-25..+25` ladder and prove zero-state identity.
4. Build a scratch copy of exact live `18770d8e...` with only mouth geometry changed.
5. Run matched 0°/rolled/0° screenshots and edge/landmark metrics; simultaneously verify eyes remain byte/behavior unaffected.
6. Only if that passes and no other worker owns the frontend mutation boundary: exact-hash guarded live patch, rollback copy, existing-window reload only, independent readback, FPS/HTTP/service/visible-window check.

## Scope fence

A mouth-roll fix would not promote blink identity, whole-avatar quality, body/GPU, parallax, HCU/GWT/J-Space, training, or whole-product acceptance.
