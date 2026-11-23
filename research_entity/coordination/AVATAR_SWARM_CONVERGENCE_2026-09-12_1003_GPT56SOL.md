# Avatar Swarm Convergence — 2026-09-12 10:03 +07 — GPT-5.6 Sol

STATUS: NONCANONICAL COORDINATION CHECKPOINT. This file is a working convergence cache only. It does not mint mutation authority, provider authority, production activation, or whole-avatar credit. Current owner authority, current repository heads, exact Local-Bridge receipts, and real-host readback outrank it.

## 1. Exact production subject snapshot

Target machine: `ai-core-node`, owner `gabriel`.

Current bound production source observed through Local Bridge:

- `/home/ai-core-node/.claude/star/visual/buehne.html`
- SHA-256 `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- daemon SHA-256 `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`
- service `frankenstein-buehne.service` active at the measured readback
- production Chrome PID snapshot `3033100`
- existing visible production page remains the display-2 subject
- bounded production telemetry reports `60.0 FPS`

Snapshot receipts include `go-avatar-swarm-live-roll-eye-source-audit-20260912-0955-gpt56sol`, `go-avatar-body-visible-baseline-status-20260912-gpt56sol-a`, and `go-avatar-visible-production-subject-bind-gpt56sol-20260912-0952`.

The exact visible-subject bind re-read service, HTTP, X11 monitor/window geometry, Chrome process tree and GPU process without spawning or reloading a production browser, and ended with `SOURCE_INVARIANCE=PASS` plus `VISIBLE_PRODUCTION_SUBJECT_BIND_READBACK=PASS`.

HARD FENCE: do not open a second production Chrome. Scratch/shadow subjects must remain isolated and must not be promoted as production.

## 2. Newly closed mechanism boundary

The current live `18770d8e...` source already contains the atomic roll/eye update that an older handoff branch proposed for an earlier source hash:

- `kopfRollWert = s.roll || 0`
- `kopfRollAusgleichDeg = kopfRollWert`
- `augenOffsetDx = s.dx || 0`
- `augenOffsetDy = s.dy || 0`

The current `kopfKoerperDrehSchritt()` no longer performs the old independent lerp of those eye/photo compensation variables. Therefore the old 2–3-frame roll/eye phase-lag mechanism is CLOSED AT CURRENT SOURCE LEVEL. Do not reapply the older hash-fenced patch to `18770d8e...`.

This does not by itself prove perceptual whole-scene acceptance.

## 3. Eye / blink evidence

Current live source contains:

- `#pupillen-glow`
- `#augen-blink`
- both inside `#kopf-dreh`
- the 12-frame blink image sequence
- `blinzeln()` / blink playback
- gaze transform using the same atomic roll compensation state

Receipt: `go-avatar-swarm-blink-live-forensic-20260912-0956-gpt56sol`.

The current visible matched Eye A/B attempt is NOT a product negative. Scratch Chrome starts and DevTools becomes reachable, but the target list contains extension/background/service-worker targets and no Avatar page target; the scratch browser then exits. Production PID remains unchanged. Classification: HARNESS / SCRATCH-LAUNCH / TARGET-BINDING INVALID EVIDENCE.

Receipts:

- `go-avatar-eye-cdp-target-shape-20260912-0956-gpt56sol`
- `go-avatar-eye-visible-launch-ab-20260912-0958-gpt56sol`

Do not modify eye identity based on this failed scratch harness. First repair exact scratch page-target formation/lifetime, then rerun matched A/B.

## 4. Body / shoulder visible evidence

`go-avatar-body-visible-shadow-ab-v2-20260912-gpt56sol-a` is a bounded PASS on `ai-core-node` against the exact current live hash with `live_mutation=false` and post-run source invariance.

Two visible X11 fresh-Chrome repetitions exercised the body full-scene shadow subject. The AMD/ANGLE WebGL path reported `gl_error=0`, 45 textures and active shadow draws. Baseline settled at 60 FPS; shadow runs settled near 60 FPS with observed post-warm-up minima in the high-50s. The receipt ends `BODY_VISIBLE_SHADOW_AB_V2=PASS` and preserves `LIVE_POST_SHA=18770d8e...`.

Scope: this is strong visible scratch/component evidence for the body-shadow path. It is NOT whole-avatar acceptance and does not authorize live body mutation by itself.

A separate NVIDIA/Nemotron shoulder falsifier produced analysis text but the enclosing Local-Bridge command timed out after 120 s (`TIMEOUT`, exit 124). Therefore that run is not accepted as an independent completed falsifier. Its suggested thresholds/selectors remain candidate output only until verified against the actual source/runtime.

## 5. Parallax evidence classification

`go-avatar-parallax-provenance-gate0-audit-20260912-0959-gpt56sol` ended `FAIL`, exit `141`, but the exact command used `set -Eeuo pipefail` together with large `find ... | sort | head ...` discovery pipelines. SIGPIPE from `head` terminating upstream producers is sufficient to explain 141. The output had already entered a broad candidate-manifest scan when the command stopped.

Classification: HARNESS / PIPELINE SEMANTICS FAILURE, not a parallax product negative.

Do not weaken the parallax gate. Repair/read the provenance in bounded commands. Current swarm control already shows follow-up reads of the exact depth-parallax, rig2 and incoming rig-v2 manifests; do not duplicate those reads while they are active.

## 6. Occupied current swarm boundaries — do not duplicate

Observed current control-lane dispatches already cover these boundaries:

- Eye scratch-vs-production Chrome launch environment comparison: `go-avatar-eye-prod-launch-env-diff-20260912-1001-gpt56sol`
- Body/shoulder integration-point live source forensic: `avatar-hardcore-20260912T0300Z-live-body-forensic-gpt56sol`
- depth-parallax / rig2 / incoming rig-v2 manifest provenance reads
- extended parallax CSS scratch gate
- visible X11 whole-scene A/B
- read-only post-change production screenshot
- read-only visible production subject binding — now PASS/read back
- disjoint NVIDIA body falsifier — terminal TIMEOUT, not accepted falsifier
- bounded Nemotron anchor falsifier
- current provider-admission check — fail-closed authority mismatch

Prefer independent review or a disjoint discriminator rather than duplicate execution.

## 7. Provider / FreeSwarm authority is currently fail-closed

Exact current command `go-avatar-provider-admission-exact-20260912-0958-gpt56sol` cloned current `main` and ran `tools/free_provider_admission.py --json`.

Observed result:

- `ok=false`
- `status=SUPERVISOR_PRODUCT_AUTHORITY_MISMATCH`
- `admitted_free_providers=[]`
- one provider authority document says owner reauthorized FreeSwarm
- current Supervisor authority still says `FREE_ONLY_HARD_OFF; ALL_CLAYCODE_EXTERNAL_PROVIDER_ROUTES_UNADMITTED; TOGETHER_FORBIDDEN; NO_PAID_OR_UNKNOWN_COST_FALLBACK`
- supervisor emergency stop remains `True`

A Nemotron harness command was nevertheless observed executing and timing out. Its execution is evidence of a governance/route inconsistency, not evidence that provider authority was valid. Do not dispatch additional external-provider work from this lane while the exact admission validator is red.

## 8. Concurrency evidence

The shared Local-Bridge control branch is actively written by multiple organs. A read-only command creation encountered a GitHub 409/head-advanced conflict and succeeded only after re-resolving the branch. This is positive evidence that CAS discipline is necessary in the current swarm.

Operational rule:

- no blind fan-out
- no duplicate mutation boundary
- re-resolve current branch/head before write
- preserve command/receipt machine+owner provenance
- treat queued/dispatch as distinct from executed/accepted

## 9. Current no-promotion vector

Positive bounded evidence exists, but the following are NOT promoted by this checkpoint:

- whole Avatar acceptance
- whole-scene eye/blink perceptual acceptance
- long-duration performance stability
- shoulder/body semantic acceptance or live activation
- parallax production activation
- external-provider/FreeSwarm execution authority

## 10. Highest-information continuation

Consume the already-dispatched eye launch-environment, body/shoulder, parallax provenance, whole-scene A/B and screenshot results as exact receipts. The highest-value eye discriminator remains the scratch Chrome page-target/lifetime root cause; do not touch eye identity until that harness is valid.

For body, move only from the visible shadow/component PASS to a matched exact acceptance gate; do not infer live activation. For parallax, preserve the 141 run as harness-invalid and use the bounded manifest/provenance follow-ups already in flight.

If occupied lanes remain nonterminal, use repo-only review/convergence work or another disjoint falsifier rather than another runtime writer.
