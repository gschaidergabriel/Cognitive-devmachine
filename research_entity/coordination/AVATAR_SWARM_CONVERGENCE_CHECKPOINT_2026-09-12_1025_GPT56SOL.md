# Avatar Swarm Convergence Checkpoint — 2026-09-12 10:25 +07 — GPT-5.6 Sol

## Authority / exact live subject

- repo: `gschaidergabriel/clay-global-research-entity`
- work branch: `chatgpt/gpt56sol-avatar-swarm-convergence-20260912-0952`
- production host/owner: `ai-core-node` / `gabriel`
- production HTML: `/home/ai-core-node/.claude/star/visual/buehne.html`
- exact current SHA-256: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- production singleton remains existing `frankenstein-buehne.service` + existing visible Chrome on HDMI-A-0.

**NO LIVE WRITE has been made by this lane.**

## Swarm assimilation / dedup

Observed parallel Avatar convergence lanes are disjoint:

- `chatgpt/avatar-swarm-convergence-20260912-1003`: Body/Depth-Warp convergence and harness classification.
- `chatgpt/avatar-swarm-convergence-20260912-1004`: Parallax convergence/dedup; redundant Gate-0 verifier removed after stronger prior closure.
- Eye scheduler/canonical-mask/body-perf/parallax audit branches remain occupied by their own workers.

This lane therefore owns no body/parallax implementation. It focuses on the previously unowned roll-overlay transform semantics and mouth follow-on geometry.

## Confirmed critical defect

Real-host receipt:

`local_bridge/results/receipts/avatar-roll-css-generator-falsifier-20260912-1012-gpt56sol.json`

PASS/0 on `ai-core-node`, owner `gabriel`, boundary `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`.

Current live eye/blink composition uses:

`translate(full_generator_marker_displacement) rotate(roll)`

although the translation table was generated as the **full marker displacement** through the rolled-head generator. Browser rotation therefore double-counts a large part of the motion.

Measured native-canvas anchor errors current vs generator target:

- 5°: 36.952 px
- 10°: 73.833 px
- 15°: 110.574 px
- 20°: 147.105 px
- 25°: 183.355 px

Using `generator_target - browser_rotation_displacement` as the translation residual produces max numerical error `0.000015 px` in the same real-host Chromium discriminator.

## Evidence inputs

Real-host generator script receipt:

`avatar-mouth-roll-read-geometry-script-20260912-1004-gpt56sol`

- script SHA: `37d3768e440ba003774169823cd449015983597a3fea4a965c9d1a4312837ab0`
- generator: exact head crop -> PIL rotate(expand=True) -> bottom-center repin to neck `(768,600)`.

Real-host exact eye-marker JSON receipt:

`avatar-mouth-roll-read-eye-geometry-data-20260912-1004-gpt56sol`

- data SHA: `4b3280dbf1acf72af377229ef5eadc798a9b48e2939ab1ca96b86c4e976bb8cb`
- eye anchor: `(610,207)`.

## Preserved negative / invalid evidence

1. A first mouth-roll candidate incorrectly assumed the current eye table already represented a residual. Real-host generator readback falsified that assumption. Candidate patcher/test were deleted before any live write.
2. `avatar-mouth-roll-exact-marker-20260912-1008-gpt56sol` failed because the legacy measurement module binds its visual root to `rig2/` and therefore looked for nonexistent `rig2/kopf/...`. Classification: HARNESS/INSTRUMENTATION FAILURE, not product negative.
3. A provider-side NVIDIA/Nemotron body falsifier timed out; partial prose is not accepted evidence.

## Candidate artifacts on this branch

- `research_entity/avatar/AVATAR_ROLL_OVERLAY_GEOMETRY_FALSIFIER_2026-09-12_GPT56SOL.md`
- `research_entity/avatar/AVATAR_MOUTH_ROLL_REGISTRATION_FINDING_2026-09-12_GPT56SOL.md`
- `research_entity/avatar/apply_roll_overlay_residual_candidate.py`
- `research_entity/avatar/test_roll_overlay_residual_candidate.py`
- `research_entity/avatar/roll_overlay_actual_asset_gate.py`
- `research_entity/coordination/AVATAR_SWARM_ALERT_ROLL_OVERLAY_GEOMETRY_2026-09-12_GPT56SOL.md`

## Dispatched but not yet receipt-promoted at this checkpoint

- `avatar-roll-residual-candidate-static-gate-v2-20260912-1024-gpt56sol`
- `avatar-roll-actual-asset-gate-20260912-1019-gpt56sol`

The earlier static-gate command without `v2` has an identified module filename/import mismatch and must be classified as harness failure if/when its receipt arrives.

## Exact next decision boundary

**Do not patch production from the geometric receipt alone.**

Required closure order:

1. static candidate v2 PASS with exact live SHA guard and source-invariance proof;
2. actual real-asset Chromium A/B PASS using real rolled-head PNG + real `blink_000.png`, with corrected transformed eye anchor <= 0.35 native px and current path reproducing the large error;
3. reconcile result with active eye lane / no competing live writer;
4. only then consider an exact-hash-guarded live mutation;
5. if admitted: rollback copy -> patch exact live SHA -> reload EXISTING production page only -> independent source hash/service/HTTP/window/GPU/screenshot/readback;
6. derive mouth roll path only after the eye transform convention is closed.

No whole-avatar, body, parallax, GWT/HCU/J-Space, training or product credit is implied.
