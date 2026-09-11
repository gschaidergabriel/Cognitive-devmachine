# Owner Target Delta — 2026-09-12

Status: `CURRENT_TARGET_CORRECTION` for PR #2153.  
This file narrows/supersedes any part of `PACKET.md` that could be read as claiming the already-repaired 2026-09-11 visual bugs are still current product negatives.

## Evidence correction

The current 2026-09-11 coordinator report records these as **already found, repaired and visually re-verified** on the real avatar host:

- neck seam caused by body/head breathing at different rates;
- ghost head caused by an old flat expression layer blending over the real head;
- transient eye-region slip during fast head motion, caused by double angle correction plus a hard rotation step;
- frame-rate fall to roughly 35–45 fps, restored to roughly 58–60 fps without default GPU compositing.

Therefore these are now **regression falsifiers**, not presumed open root causes. A later baseline may reopen them only if executable evidence reproduces them.

## Current owner visual target

The authoritative visual target is not generic photorealism. It is the existing FranKenstein identity made maximally lifelike while preserving the coarse digital voxel/pixel sculpture aesthetic.

Measured/style constraints from the current owner material:

- near-black/navy Matrix-like background; cyan/magenta accents;
- face remains a visibly quantized/pixel-block sculpture, not smoothed into a conventional face;
- red eyes remain the only warm identity anchor;
- same person, same lighting and stable registration across every generated pose;
- no waterline, fog bank or horizontal translucent strip;
- shared global film look (grain/color/vignette) is allowed only after geometry remains correct.

## Mandatory default pose

The canonical zero pose is **not upright/leaned back**. It is:

- looking directly toward camera/person;
- head slightly forward;
- chin slightly lowered;
- approximately 8–12 degrees forward pitch as a descriptive range, with the actual owner reference image outranking the numeric estimate.

This pose is `yaw=0, pitch=0, roll=0` in the avatar coordinate system. Every motion must return naturally toward this owner-selected neutral pose.

## Anchor contract

Head frames:

- same canvas;
- neck/base anchor registered to the same coordinate across head frames;
- no hidden crop/scale shift that moves the neck during head-only rotation.

Body frames:

- the body is allowed to move the neck anchor as the torso leans/rotates;
- **every body pose must carry its own measured neck-anchor coordinate in the manifest**;
- the head is placed against that per-body-pose anchor, not a single global constant.

This is stricter and more accurate than treating `neck_anchor` as fixed across all body poses.

## Required motion coverage for generated/selected assets

Head target coverage:

- yaw: -80..+80 degrees in <=10-degree steps;
- pitch: -30..+30 relative to the owner neutral in <=10-degree steps;
- roll: -25..+25 in <=5-degree steps;
- common combined yaw/pitch poses, especially yaw {-40,-20,0,+20,+40} x pitch {-10,0,+10}.

Body target coverage:

- breathing with >=12 intermediate states;
- forward/back lean -20..+20 in <=5-degree steps;
- lateral weight shift -15..+15 in <=5-degree steps;
- shoulder/torso rotation -35..+35 in <=5-degree steps;
- shrug sequence with >=8 states;
- slouch-to-upright with >=6 intermediate states;
- common lean/shoulder-rotation combinations.

These are target-coverage requirements for asset generation/selection, not evidence that the live asset inventory already satisfies every point.

## Eye identity contract

The eyes are an explicit identity and tracking anchor. The target material requires them as a tiny independent RGBA layer.

Hard rules:

1. One canonical red-eye identity for the current head generation.
2. Gaze changes move/warp/mask that identity; they must not silently substitute a visually different eye pair.
3. Blink uses lid/aperture states over the same identity; it must not change face identity.
4. Eye anchor coordinates are bound to head pose and are transformed exactly once.
5. A new eye asset generation must be an explicit transition with provenance, not an incidental frame choice.
6. At least open/half/closed plus >=4 intermediate blink states for generated target material.

The current live rig already has independent `pupillen-glow`/`augen-blink` paths, so the next task is identity/anchor validation and regression control, not adding a third competing eye system.

## Full-body coupling contract

The body may not be a static pedestal for a moving head.

Use a single frame-authoritative pose transaction, but preserve physically meaningful lag:

- head can lead a turn;
- torso follows with smaller amplitude and delay;
- left/right shoulders remain independently controllable;
- breathing remains low-amplitude and may not tear the neck seam;
- camera/root framing handles gross apparent-body movement; head-only translations stay small;
- neck anchor is resolved from current body pose before final head transform.

Suggested deterministic render order:

```text
pose_target
 -> temporal solver
 -> body_pose + body_neck_anchor
 -> head_pose relative to body_neck_anchor
 -> eye_anchor from transformed head
 -> gaze + lids
 -> mouth/viseme
 -> expressions
 -> pairwise compositor
 -> film look
 -> instrumentation
```

## Baseline priority after GO

Because the 2026-09-11 report claims the major visual defects were repaired, the next baseline must test for **regression and remaining puppet-like motion**, not assume the historical defects are still present.

Highest-information checks:

1. 30–60 s capture of the untouched current live render;
2. rAF p50/p95/p99 + late/dropped-frame histogram;
3. synchronized host CPU/RSS during that capture;
4. per-frame body/head generation + opacity + neck-anchor coordinates;
5. per-frame eye source/generation + final anchor coordinates;
6. scripted neutral -> yaw -> combined lean -> neutral trajectory;
7. explicit default-pose screenshot and numeric anchor record.

Only if these reproduce a defect is that boundary reopened for mutation.

## V3 artifact note

A File-Library sidecar now records:

`635ae5e94a9d414c237819f1e57904206f839fa186a8e5dc39fcd07463becfc0  /mnt/data/FRANK_CLAUDE_HANDOFF_GUIDE_V3_2026-09-12.zip`

At this GO cycle, the ZIP bytes themselves are not available through the active File Library/GitHub connection; only the checksum sidecar is visible. Do not claim the V3 ZIP was inspected until the exact archive becomes accessible and its checksum matches.

## Promotion rule

`historically_fixed != currently_regressed`

and

`target_specified != live_implemented != measured_pass`

Current next promotion requires a correctly attributed `ai-core-node` runtime receipt for the untouched baseline and instrumentation before live visual mutation.
