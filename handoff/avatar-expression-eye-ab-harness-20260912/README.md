# Special-expression eye A/B harness

Status: **SOURCE-READY TEST HARNESS / NOT RUNTIME CREDIT**

This lane exists to close one narrow gate: whether the already accepted localized eye identity can remain visually coherent while a special-expression frame is active.

## Current exact subject

- live `buehne.html`: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- live `buehne_daemon.py`: `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`
- productive localized open-eye plate (`augen_blink_relief2/blink_000.png`): `8ab1a11c6f8a738e34c516bbf65c00e0f48de70c7341bfa970f236e002c94fc9`
- localized Blink live gate: PASS on real `ai-core-node`, 15/15 FPS samples = 60.0.

## Critical route law

Do **not** change browser URLs to `/augen_blink_relief2/...`, `/augen_gaze_relief2/...`, or `/kopf_rgba_relief2/...`.

The live daemon intentionally exposes stable public routes such as `/augen_blink/...`, `/augen_gaze/...`, and `/kopf_rgba/...`, then `_vielleicht_ai()` resolves the currently admitted backing directory (`_relief2` > `_ai` > original). The current real-host HTTP authority already resolves Head and Gaze to relief2 assets.

A previous shadow-HTML attempt tried to hard-code `/augen_blink_relief2/...`; that bypasses the existing routing authority and is not the candidate carried forward here.

## Why v2 harness exists

The earlier isolated-browser run successfully loaded the page, entered `_sonderLaeuft`, and observed the expected native suppression (`GLOW_OPACITY_BASE=0`), but then timed out in `Page.captureScreenshot`. Its CDP websocket itself had a 5-second timeout.

`expression_eye_ab_harness.py` changes only the test harness:

- per-CDP-call deadlines instead of one 5-second socket limit;
- `Page.captureScreenshot` deadline 30 s;
- three bounded screenshot retries with explicit error markers;
- capture clipped to the eye neighborhood instead of the entire animated viewport;
- the existing productive `/augen_blink/blink_000.png` is reused as the canonical open-eye plate;
- no second eye DOM layer is introduced;
- live source hashes are checked before and after;
- the forced-glow phase is explicitly geometry/compositing-only, not a claim that gaze may ignore the real presence signal.

## Productive expression caveat

The daemon also runs `AUSDRUCK_ERWEITERT_DIR` through `_vielleicht_ai()`. On this host `ausdruck_erweitert_relief2` exists and has 308 frontal `stufe_*.png` files. Therefore any offline 308-frame identity statistic against plain `ausdruck_erweitert` is method evidence only until repeated against the actual relief2 tree or bound by HTTP hash.

The next accepted evidence should therefore bind all three subjects together:

1. stable public expression URL -> exact relief2 expression bytes;
2. stable public `/augen_blink/blink_000.png` -> exact accepted localized open-eye plate;
3. isolated browser A/B -> expression native vs canonical-eye overlay vs canonical-eye+gaze geometry, with no source write.

Only after those pass should a minimal live HTML behavior patch be considered. No asset-tree rewrite is required merely to test this hypothesis.
