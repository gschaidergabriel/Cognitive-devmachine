# Avatar GPU compositor — live evidence 2026-09-12

Status: **BOUNDED LIVE EVIDENCE**, not whole-avatar or whole-product acceptance.

This note prevents future agents from repeating the GPU-disable investigation or misclassifying the failed guard attempts. It records only evidence already emitted by the authorized `ai-core-node` local bridge.

## Subject

- Machine / bridge identity: `ai-core-node` (`hostname`: `ai-core-node-projekt-frankenstein`)
- Live app: `/home/ai-core-node/.claude/star/visual/`
- Service: `frankenstein-buehne.service`
- URL: `http://127.0.0.1:8788/`
- Live daemon SHA-256 after the change: `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`
- Previous daemon SHA-256: `0ab232f7112b046ced7e3e4ae454fe0d800eebd32d23bdac138c961bc069dff9`
- Reversible backup observed: `buehne_daemon.py.go-gpu-backup-20260912T0708` = previous SHA.

## 1. Shadow A/B established a large rendering-path difference

Receipt:

`local_bridge/results/receipts/go-avatar-c0dd67ea-gpu-ab.json`

Same avatar subject was exercised in two isolated Chrome profiles:

- software/disabled path: mean frame interval `53.6957 ms`, p50 `50.2 ms`, p95 `83.5 ms`, p99 `100.3 ms`;
- Chrome default GPU path: mean frame interval `17.3149 ms`, p50 `16.7 ms`, p95 `16.8 ms`, p99 `33.5 ms`.

This is bounded A/B evidence for the rendering path. It is not by itself production-runtime promotion.

## 2. First guarded live retry produced a false negative

Receipt:

`local_bridge/results/receipts/go-avatar-gpt56sol-live-gpu-enable-v2-20260912-0708.json`

The exact three daemon launch flags were removed and the restarted real Chrome process printed without those flags. The guard then returned exit `41` and rolled back because this check:

`pgrep -af '...--disable-gpu'`

matched the **shell command performing the check itself**, whose argv necessarily contained the literal `--disable-gpu` string.

Classification: `EVIDENCE_INVALID` / discriminator self-match, **not PRODUCT_NEGATIVE**.

## 3. Concurrent retry was killed after source mutation

Receipt:

`local_bridge/results/receipts/go-avatar-gpt56sol-live-gpu-enable-v3-20260912-0708.json`

It recorded:

- `OLD_SHA=0ab232...`
- `NEW_SHA=5527a1...`
- terminal bridge status `FAIL`, `exit_code=-9`.

Because termination occurred after the source write, this receipt alone could not establish whether source, service and process were mutually consistent. A subsequent exact live audit was therefore required.

## 4. Exact live post-kill audit closed the ambiguous state

Receipt:

`local_bridge/results/receipts/go-avatar-gpu-live-state-audit-after-kill-20260912-0715.json`

Observed together on the real host:

- daemon SHA = `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`;
- service = `active`;
- HTTP = `200`;
- actual kiosk Chrome argv contains none of `--disable-gpu`, `--disable-gpu-compositing`, `--disable-software-rasterizer`;
- Chrome GPU process exists and does not contain `--use-gl=disabled`;
- live renderer argv does not contain `--disable-gpu-compositing`.

This establishes that the production avatar is currently running on Chrome's default GPU/compositor path rather than the deliberately disabled path. It does **not** independently attest the exact physical graphics backend or long-run stability.

## 5. Dynamic visual smoke after enable

Receipt:

`local_bridge/results/receipts/go-avatar-gpu-live-visual-smoke-20260912-0716.json`

Five real X11 window captures of the running kiosk window were taken without mutating the app.

Observed:

- window: `746 x 449`;
- black fraction: `0.00904`;
- white fraction: `0.00761`;
- consecutive-frame `changed_gt2_frac`: `0.238..0.268`;
- consecutive-frame mean absolute differences: `2.63..4.63`;
- `dynamic_any=true`;
- main Chrome process snapshot: `2.4% CPU`, RSS `260680 KiB`;
- bridge result: `GPU_VISUAL_SMOKE_PASS`.

Therefore the compositor-enabled live app is not blank/frozen and exhibits measurable visual dynamics at the exact audited runtime boundary.

## Exact promotion

Promote only this statement:

> On 2026-09-12, the real `ai-core-node` avatar runtime was observed active with the GPU-disable launcher flags removed, Chrome's default GPU/compositor process path active, HTTP healthy, and a nonblank dynamically changing live window. The prior shadow A/B showed a large frame-interval advantage for that default path over the explicitly disabled software path.

## Explicit non-promotions

Still **not established by this packet**:

- formal production frame-time distribution after the live switch;
- exact hardware graphics backend identity / hardware utilization;
- long-duration thermal/resource stability;
- full visual identity correctness;
- formal multi-angle eye/head Gate-0 acceptance;
- blink identity acceptance;
- full-body biomechanics acceptance;
- whole Avatar dream-target acceptance;
- EntityOS/HCU whole-runtime, GRID10, GWT/J-Space, effect, training or whole-product credit.

## Next useful gates

Do not re-add the disable flags or repeat the already-closed launcher-owner search without new executable counterevidence. Prefer independent measurement of the now-live subject: production frame-time/jank over a longer interval, visual-regression checks for head/eye/blink identity, then the already-open unified head/eye anchor and motion-model work.
