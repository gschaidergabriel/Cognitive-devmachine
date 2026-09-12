# Avatar roll/eye atomic geometry candidate — 2026-09-12

Status: **CANDIDATE / NOT LIVE-PROMOTED**.

## Exact measured live subject

- host: `ai-core-node-projekt-frankenstein`
- live frontend: `/home/ai-core-node/.claude/star/visual/buehne.html`
- SHA256: `87cc0e3a94781f90a7533b129743597753876a8410b868767d243b753c5d3645`
- service: `frankenstein-buehne.service`
- measured roll-eye offsets are already encoded in `KOPF_ROLL_AUGEN_OFFSET` and originate from `rig2/messen_augenanker_exakt.py` / `rig2/augen_anker_exakt.json`.

## Root cause

The render loop calls `kopfRollTick(t)` before `kopfKoerperDrehSchritt()`.

`kopfRollTick()` makes the next 5-degree head-photo frame visible immediately and assigns `kopfRollWert = schritt.w`. The later eye/blink compensation then applies only 40% of that same new roll/translation state per RAF frame:

```js
kopfRollAusgleichDeg += (kopfRollWert - kopfRollAusgleichDeg) * 0.4;
augenOffsetDx += (zielOffset.dx - augenOffsetDx) * 0.4;
augenOffsetDy += (zielOffset.dy - augenOffsetDy) * 0.4;
```

This creates a deterministic temporal registration defect: the head photo is already at the new pose while the eye/blink/gaze overlay is deliberately left between old and new poses for 2-3 frames. It cannot be fixed by additional hand-fitting because it is a timebase mismatch, not a missing static offset.

Concrete `0° -> +5°` first visible frame:

- photo pose: `+5°`, measured eye offset `(10.5, -29.0)` native pixels;
- legacy overlay: `+2°`, `(4.2, -11.6)`;
- unapplied remainder on that frame: `3°`, `(6.3, -17.4)` native pixels.

The shared `#kopf-dreh` / `#koerper-dreh` spring is separate and should remain smooth. It affects head photo and overlay together and therefore does not create relative registration error.

## Candidate correction

Make only the local photo-specific compensation atomic with the already-visible photo step:

```js
kopfRollAusgleichDeg = kopfRollWert;
const zielOffset = KOPF_ROLL_AUGEN_OFFSET[String(kopfRollWert)] || {dx:0, dy:0};
augenOffsetDx = zielOffset.dx;
augenOffsetDy = zielOffset.dy;
```

`apply_atomic_roll_eye_geometry.py` is byte-hash guarded and refuses any subject other than the measured `87cc0e3a...` input by default.

`test_atomic_roll_eye_geometry.py` checks every adjacent 5-degree transition in the current `-25..+25` roll table. The acceptance invariant is zero relative state error on the first frame where the new photo is visible.

## Promotion gate

This branch does **not** authorize a live write by itself. Before promotion:

1. refresh local bridge ownership/activity;
2. require the exact live `buehne.html` subject hash or rebase/re-measure if bytes moved;
3. run the patch and deterministic test on a scratch copy;
4. apply only when no concurrent avatar mutator owns the same live frontend boundary;
5. reload/restart the live compositor;
6. exercise neutral and nonzero roll using the existing `k` diagnostic path or an equivalent deterministic trigger;
7. record screenshot/pixel or compositor-state evidence that blink/gaze remains registered;
8. preserve a byte-exact rollback copy.

No whole-avatar, blink-identity, GPU-performance, shoulder-articulation, physical-acceptance, HCU/J-Space, or training credit follows from this candidate.
