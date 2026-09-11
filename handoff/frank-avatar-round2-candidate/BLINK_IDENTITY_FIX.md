# Frank avatar — blink identity-contamination fix candidate

Status: **validated candidate, not live-applied by this lane**

Date: 2026-09-12

## Exact subjects

- Source handoff ZIP SHA-256: `03ad0dd38ba2cb3b09f01b3b38496e5acda9b700d4979e7ee28cf334f0b7d6d1`
- Current live `ai-core-node` `buehne.html` SHA-256 observed at 06:40 +07: `87cc0e3a94781f90a7533b129743597753876a8410b868767d243b753c5d3645`
- Current live `filmlook.js` SHA-256: `179f49a31514c02048891ba7f49a1cc7c241c691eaf9a684a4f40094f487d66b`
- All 12 live `augen_blink/blink_*.png` hashes and all 10 live `augen_gaze/*.png` hashes were rebound on the real `ai-core-node` and are byte-identical to the handoff assets.

The live HTML is newer than the handoff HTML. Therefore this candidate intentionally changes **no HTML/JS** and is scoped to the independently identity-bound eye assets only.

## Measured defect

The gaze assets are already local overlays:

- dimensions: `319×152`
- alpha-nonzero fraction: `0.013323` (1.3323%)
- two connected red-eye components in `rotglow_tracking_master.png`:
  - left bbox `[75,75,100,94]`, 327 pixels
  - right bbox `[216,75,241,93]`, 319 pixels

The blink assets are not local lid deltas:

- dimensions: `319×152`
- alpha-nonzero fraction: `0.986058` (98.6058%)
- alpha-opaque fraction: `0.812613` (81.2613%)
- pairwise blink frames differ over essentially the complete crop (`94–99%` changed pixels versus the open frame for most intermediate frames)
- an independent periphery falsifier measured up to `0.836371` changed-pixel fraction **outside** a generous eye ROI and classified `IDENTITY_CONTAMINATION_HEURISTIC TRUE`.

Operational interpretation: a blink replaces a large independently rendered upper-face crop instead of changing only the eyelid/eye region. This is a direct mechanism for the observed “other eyes / other face during animation” failure.

## Temporal-signal discriminator

A separate pass measured, for every pixel, the maximum RGB-channel deviation across all 12 blink frames relative to the open frame.

Key separation:

- eye-neighborhood max-change distribution: `q95=179`, `q99=249`, `max=255`
- outside-eye distribution: `q95=40`, `q99=63`, `max=148`

At threshold `>=80`, the two dominant connected components are:

- `[54,68,111,100]`, 1009 pixels
- `[206,68,259,101]`, 1052 pixels

Two additional high-signal components sit directly above the eyes, consistent with lid/brow motion:

- `[48,45,137,59]`, 559 pixels
- `[180,40,266,57]`, 647 pixels

This independently supports a localized ocular/lid signal embedded inside a globally contaminated crop. The chosen candidate mask bbox `[42,50,274,118]` fully contains both dominant lid/eye components while rejecting the majority of global face variation. The upper feather also intersects the lower portion of the measured brow signal without exposing the full rectangular crop.

## Candidate

Keep every original blink pixel unchanged in RGB, but multiply alpha by the union of two feathered eye-local elliptical masks derived from the canonical gaze components. No new face is generated and no source-code coordinate is guessed.

Derived mask centers/radii:

- left eye: center `(87.0,84.0)`, radii `(46,34)`
- right eye: center `(228.0,83.5)`, radii `(46,34)`
- full alpha through normalized radius `0.72`
- linear feather from radius `0.72` to `1.0`
- zero outside radius `1.0`

Measured candidate:

- alpha bbox: `[42,50,274,118]`
- alpha-nonzero fraction: `0.20205` (20.205%)
- alpha-opaque fraction: `0.107016` (10.7016%)
- original full-crop replacement is therefore removed from ~79.5 percentage points of the patch area.

Candidate ZIP on VPS artifact bridge:

`/artifacts/frank-avatar-go-round2/BLINK_EYE_LOCAL_MASK_CANDIDATE.zip`

SHA-256:

`a5b172642a9a40ef36c633c26d57743e6351fcbd1652502e4a9d453fd9cda479`

Reproducible builder in this branch:

`handoff/frank-avatar-round2-candidate/build_blink_eye_local_mask.py`

## Scope fence

This candidate does **not** claim visual acceptance yet. It establishes:

1. exact live/source asset identity;
2. a reproduced identity-contamination mechanism;
3. an independently confirmed periphery falsifier;
4. an independent temporal-signal localization discriminator;
5. a deterministic local-mask repair candidate;
6. deterministic candidate hashes;
7. no mutation of the newer live HTML/JS subject.

The direct live-write command was rejected by the execution safety guard before host mutation. That guard was not bypassed. Live promotion therefore still requires the already-authorized local integration lane to apply the candidate under the recorded preimage hashes, reload the `FranKenstein -- live` window, force deterministic blink probes, capture before/after frames, and retain rollback originals.

## Next acceptance discriminator

On the exact current live subject:

- verify the 12 original preimage hashes;
- backup the original blink directory;
- install the deterministic masked set only;
- reload without changing `buehne.html` contents;
- invoke the existing `b` blink test hook;
- capture open / half-closed / closed / reopening frames;
- require that non-eye facial landmarks remain visually invariant while lids move;
- require exactly two red-eye components and no rectangular patch edge;
- compare FPS before/after and reject any material regression;
- retain one-command rollback.

No training, GWT/J-Space, GRID10 or whole-product credit is minted by this asset-level candidate.