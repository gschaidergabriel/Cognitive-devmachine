# Live Probe — ai-core-node — 2026-09-12

Status: `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`, read-only probe.  
No visual source was mutated by these measurements.

## Exact live subject

At 2026-09-12 06:38 +07, the real avatar host reported:

- host: `ai-core-node-projekt-frankenstein`
- user: `ai-core-node`
- `frankenstein-buehne.service`: active/running
- main PID: `2665680`
- exec: `/usr/bin/python3 /home/ai-core-node/.claude/star/visual/buehne_daemon.py`
- HTTP `127.0.0.1:8788/`: `200 OK`

Live/served identity:

```text
buehne.html      87cc0e3a94781f90a7533b129743597753876a8410b868767d243b753c5d3645
buehne_daemon.py 0ab232f7112b046ced7e3e4ae454fe0d800eebd32d23bdac138c961bc069dff9
filmlook.js      179f49a31514c02048891ba7f49a1cc7c241c691eaf9a684a4f40094f487d66b
zustand.json     f98e76440cf8968076ff5f9ee8096ce7bfdd91063afbc442b9cee6a8f5e2a8c4
```

The HTTP body SHA-256 equals the live `buehne.html` SHA-256 exactly. The HTML has advanced beyond the earlier round-1 handoff snapshot; the daemon and film-look hashes match the earlier inventory.

## Historical fixes are present in the live source

The live HTML contains the implemented mechanisms described in the 2026-09-11 report:

- camera shake on one whole-scene wrapper;
- real RGBA head/body layers;
- separate head/body motion wrappers;
- neck-centered head transform origin (`50% 58.59%`);
- expression RGBA layers replacing the old opaque/full-frame ghost-head path;
- 12-state body breathing crossfade;
- neck seam opacity mask;
- eye/blink overlays moved inside the head transform;
- roll compensation for the eye overlays.

Therefore those historical bugs remain regression tests unless a new capture reproduces them.

## Current eye-identity defect in architecture

A current target mismatch remains in live source.

`sonderausdruckZeigen()` uses full RGBA expression frames which carry their own eyes and mouth. During those sequences `_sonderLaeuft=true`. `gazeSchritt()` then explicitly sets the canonical `#pupillen-glow` opacity to zero:

```js
$("pupillen-glow").style.opacity = _sonderLaeuft ? "0" : String(ziel.opazitaet);
```

The source comment states the reason: special-expression frames contain their own eyes. This conflicts with the current owner target that the red eyes are the stable identity anchor across all poses/expressions. This is a current implementation/target mismatch, not merely a visual preference.

Current eye assets include one `rotglow_tracking_master.png`, 12 blink frames, and multiple gaze-direction assets. Expression sequences have their own 1536x1024 RGBA frames. The correct repair should make expression geometry and the canonical eye identity composable rather than introduce a third independent eye system.

## Current measured performance regression candidate

The page already contains a real browser-side FPS meter. Every animation frame enters a rolling 1-second window and the page posts `window.__buehneFps` to `/api/fps` every 5 seconds. The daemon stores and exposes that value through `/api/status`.

A real-host sample at ~06:43 +07 returned browser-measured values including:

```text
48 fps
46 fps
46 fps
45 fps
```

The exact same sample showed approximately:

```text
buehne_daemon.py          ~51% process CPU, ~105 MB RSS
active Chrome renderer    ~62-63% process CPU, ~750 MB RSS
Chrome gpu-process        ~75% process CPU, ~100 MB RSS
```

These process percentages are not additive whole-machine CPU utilization; they are per-process CPU observations. They are sufficient to identify a high-load boundary but not to infer total system CPU by summation.

The running Chrome command line contains:

```text
--disable-gpu
--disable-gpu-compositing
--disable-software-rasterizer
```

and the renderer is also marked `--disable-gpu-compositing`. The process named `gpu-process` reports `--use-gl=disabled`.

This is current counterevidence to treating the earlier ~58–60 fps report as still current. It does **not** yet prove which subsystem caused the regression.

## Hot-path facts visible before mutation

The main `requestAnimationFrame` loop currently performs, every frame:

```text
atmen
koerperSchritt
kopfRollTick
mundSchritt
kopfKoerperDrehSchritt
kameraWackeln
gazeSchritt
rain particle creation
regenZeichnen
fpsMessen
```

The adaptive rain fallback only enters its throttled state below 24 fps and exits again at 28 fps. A system sitting around 45–48 fps therefore receives no adaptive quality relief even though it misses a 60 fps target substantially.

This is a candidate mechanism, not yet the accepted root cause.

## Next discriminators

1. locate the owner of the Chrome `--disable-gpu*` launch flags;
2. inspect rain/body hot-path code and daemon CPU loops;
3. measure canonical-eye versus expression-eye geometry/pixel differences;
4. make one-variable A/B candidates in a reversible test subject before touching the live files;
5. accept a performance change only if browser FPS rises materially while CPU/RSS and visual regressions do not worsen;
6. accept an eye change only if canonical red-eye identity survives neutral, gaze, blink and special-expression sequences without double-eye/edge artifacts.

No current whole-avatar acceptance is claimed.
