# GO Avatar Convergence Packet — 2026-09-12

Status: `CANDIDATE_FALSIFIER + MECHANISM/QA LANE`  
Owner goal: push the live FranKenstein avatar toward lifelike/photoreal motion while keeping runtime load bounded and without duplicating the active host-mutation lane.  
This packet does **not** claim host mutation or runtime acceptance.

## 1. Current exact evidence boundary

Round-1 handoff evidence says the live avatar is `/home/ai-core-node/.claude/star/visual/buehne_daemon.py` + `buehne.html`/`filmlook.js`, not `frankenstein-repo`. The live renderer is a Vanilla HTML/CSS/JS alpha-layer rig on `127.0.0.1:8788`.

Observed live DOM uses two transition layers for body and head (`koerper-schicht{,2}`, `kopf-schicht{,2}`), plus expression, gaze, blink and mouth layers. Dual layers are intended as cross-fade machinery and must not be called the bug without a discriminator.

Round-1 is structurally strong but still lacks: 30–60 s animation capture, requestAnimationFrame/long-task/memory trace and full console-event trace. Therefore no performance or motion-quality promotion is allowed yet.

## 2. External mechanism refresh

### LivePortrait — borrow control ideas, not necessarily runtime dependency
Official project: https://github.com/KwaiVGI/LivePortrait

Useful mechanisms for this rig:
- relative motion around a source/reference state rather than independent absolute layer motion;
- stitching/retargeting as an explicit correction stage;
- smoothing of motion trajectories before render;
- separate eye/lip retargeting instead of replacing the whole identity image.

Important counterevidence from its own config: eye retargeting is marked WIP/not recommended and source-video eye retargeting may cause inter-frame jitter. Therefore `AI eye retargeter` is **not** an automatic quality win. Frank should first make eye geometry deterministic and temporally stable.

### DWPose — measurement / offline synthesis tool, not renderer
Official project: https://github.com/IDEA-Research/DWPose

DWPose provides whole-body/face/hand keypoints with small model variants (the published table includes a tiny 256x192 model at ~0.5 GFLOP). Good use here: low-rate/offline pose extraction, reference-clip analysis and generated-asset QA. Bad use: inserting a high-rate detector into every render frame without evidence it is needed.

### MuseTalk 1.5 — optional mouth lane, not default compositor
Official project: https://github.com/TMElyralab/MuseTalk

MuseTalk reports 30fps+ on a Tesla V100 and uses a single-step latent inpainting path, but it modifies a 256x256 face region and its project documents identity-detail limitations/jitter in the pipeline. Treat as an optional GPU mouth/face experiment only after current deterministic rig baseline exists.

### EchoMimicV2 — offline asset/storyboard generator only for this target
Official project: https://github.com/antgroup/echomimic_v2

It can produce semi-body human animation, but published acceleration is still on A100-class hardware (~50 s / 120 frames after acceleration) and tested GPUs include A100/4090D/V100. That is incompatible with the desired low-load live path. Use only to synthesize reference motion/assets if useful; never make it the default live renderer without matched-host evidence.

## 3. Root architecture correction: one pose state, many render layers

The next live implementation should introduce one frame-authoritative `AvatarPoseState` (or equivalent) and derive all layer transforms from it. No visual layer may independently invent head/body motion.

Minimum state:

```text
root_x, root_y, root_scale
camera_scale, camera_y
pelvis_x, pelvis_y
spine_lean, torso_twist
shoulder_lift_l, shoulder_lift_r
shoulder_roll_l, shoulder_roll_r
head_yaw, head_pitch, head_roll
head_tx, head_ty
gaze_x, gaze_y
blink_l, blink_r
mouth_viseme, mouth_open
expression_mix
breath_phase
```

Frame transaction:

```text
intent/speech/input
 -> target pose
 -> physically bounded temporal solver
 -> ONE committed pose state
 -> derive body/head/eye/mouth transforms
 -> pairwise transition compositor
 -> film look
 -> instrumentation
```

This directly attacks the current failure class where a head can visually drift independently of its torso/neck or two semantic states can coexist incoherently.

## 4. Kinematic invariants

Implement/falsify these before adding more effects:

1. **Neck anchor:** head base follows torso neck socket. Independent head translation is limited to a few pixels of soft tissue/camera residual, not a second body trajectory.
2. **Shoulder decoupling:** left/right shoulders have independent bounded DOFs but share torso root. No mirror-locked shrug unless the target motion requests it.
3. **Camera/body coupling:** when more body becomes visible, solve primarily through `camera_scale/camera_y/root_scale`, not by sliding only the head upward/downward.
4. **Pose continuity:** target changes pass through critically damped/spring-damper motion with bounded velocity/acceleration/jerk. Random noise may modulate micro-motion only after the deterministic trajectory.
5. **Cross-fade exclusivity:** for a semantic pair (e.g. `kopf-schicht` + `kopf-schicht2`), opacity weights should sum to ~1 during a transition and only one asset generation may be fully opaque at a time.
6. **Atomic layer generation:** all layers rendered for frame N must refer to the same pose generation/state revision.

## 5. Eye identity lock

The eyes are an identity anchor and must stop being replaced by visually different eye sources.

Recommended decomposition:

```text
base eye/face identity pixels
+ gaze transform/mask
+ eyelid/blink mask
+ optional emission/glow mask
```

Do not swap to a second full eye image merely to change gaze/glow. Establish one canonical eye identity source per head-generation and transform only the minimum region required.

Acceptance measures:
- pupil/iris center relative to eyelid landmarks remains continuous;
- left/right inter-pupil distance changes only under head pose/perspective, not asset swaps;
- no one-frame eye-source hash/generation jump without an explicit expression transition;
- blink modifies eyelid aperture without changing surrounding face identity.

## 6. Compositor discriminator for the suspected double-head/body bug

Do not diagnose from DOM node count. Instrument actual per-frame visibility.

For every transition frame emit a compact record:

```json
{
  "frame": 0,
  "pose_generation": 0,
  "head_a_src": "...",
  "head_b_src": "...",
  "head_a_opacity": 0.0,
  "head_b_opacity": 0.0,
  "body_a_opacity": 0.0,
  "body_b_opacity": 0.0,
  "head_weight_sum": 0.0,
  "body_weight_sum": 0.0,
  "neck_anchor_error_px": 0.0
}
```

Fail if, outside explicitly admitted artistic overlays:
- `abs(head_weight_sum - 1) > 0.02` while visible;
- `abs(body_weight_sum - 1) > 0.02` while visible;
- both full head images are near-opaque simultaneously;
- head/body generations differ in one committed frame;
- neck-anchor error exceeds the baseline-derived tolerance.

## 7. Performance instrumentation before optimization claims

Add a zero/low-cost in-browser profiler that can be enabled for acceptance runs:

- `requestAnimationFrame` frame interval histogram;
- p50/p95/p99 frame time;
- dropped/late frame count against chosen 30 or 60 fps target;
- Long Task API count/duration where available;
- asset decode/load timings;
- number of DOM/style writes per frame;
- compositor transition count;
- browser JS heap where supported;
- host CPU/RSS sampled externally during the same capture.

User target from current direction: spikes around 60% CPU are acceptable, but sustained load should stay materially below that. Do not optimize by deleting lifelike motion; optimize duplicated work, unnecessary decodes, repeated style/layout work and overly frequent expensive inference.

## 8. Acceptance ladder

`A0 baseline`: unchanged current render, screenshot + 30–60 s capture + trace.  
`A1 compositor`: cross-fade invariants pass; no double semantic head/body.  
`A2 kinematics`: neck/root/camera/shoulder invariants pass on scripted motion suite.  
`A3 eyes`: eye identity lock + gaze/blink continuity pass.  
`A4 natural motion`: reference-trajectory comparison; velocity/acceleration/jerk outliers reduced versus A0 without freezing motion.  
`A5 photoreal polish`: film/vignette/color only after A1–A4; polish may not hide geometry failures.  
`A6 live load`: matched 30–60 s run with CPU/frame-time evidence; peak/sustained constraints reported separately.  
`A7 user-visible`: screenshot/video comparison against the owner-selected dream target and storyboard.

Every stage must retain the previous stage’s regression fixtures. No scalar `looks better` promotion without the measured evidence plus visual review.

## 9. Worker split — no collisions

- `HOST-AUDIT`: exact live source/process/capture on ai-core-node; read-only until baseline captured.
- `COMPOSITOR`: dual-layer visibility/generation instrumentation + fix only if discriminator fails.
- `POSE`: AvatarPoseState + temporal solver + neck/root/camera/shoulder invariants.
- `EYES`: canonical eye source + gaze/blink/emission decomposition.
- `ASSET-SYNTH`: optional new body/face/expression assets; offline only; may use generative tools but must match identity/anchor contract.
- `PERF`: rAF/long-task/CPU/RSS trace and regression thresholds.
- `FALSIFIER`: tries to reproduce ghosting, head drift, eye identity swap, shoulder coupling and load spikes with scripted state sequences.

Only one worker owns each mutation boundary. Other workers remain review/falsifier lanes.

## 10. Next exact action

The highest-information next executable action is **not** adding a new AI renderer. It is:

1. recover a correctly attributed execution channel to the real `ai-core-node` host;
2. capture current live 30–60 s baseline + profiler trace;
3. instrument the dual-layer compositor and pose generation without changing visuals;
4. reproduce/falsify the double-head/head-drift hypotheses;
5. only then mutate the smallest proven failing boundary.

Current blockers are transport/attribution plus missing baseline traces, not lack of candidate rendering technology.
