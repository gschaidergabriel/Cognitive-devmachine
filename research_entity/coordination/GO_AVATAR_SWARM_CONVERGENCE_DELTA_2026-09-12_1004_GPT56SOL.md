# GO Avatar Swarm Convergence Delta — 2026-09-12 10:04 +07 — GPT-5.6 Sol

Status: NONCANONICAL coordination/evidence delta. This file does not mint production authority or whole-avatar credit.

## Exact production subject preserved

Target: `machine_id=ai-core-node`, `owner=gabriel`.

Read-only production preflight and body-baseline receipts bind the existing display-2 subject to:

- live source `/home/ai-core-node/.claude/star/visual/buehne.html`
- live SHA-256 `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- daemon SHA-256 `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`
- service `frankenstein-buehne.service` active
- existing production Chrome PID observed as `3033100`
- `/api/status` measured `fps=60.0` at `2026-09-12T02:56:36Z`
- pre/post live HTML hash remained identical in the body-baseline probe.

Evidence:

- `local_bridge/results/receipts/go-avatar-visible-subject-preflight-20260912-0952-gpt56sol.json`
- `local_bridge/results/receipts/go-avatar-body-visible-baseline-status-20260912-gpt56sol-a.json`

No live Avatar source mutation was performed by this lane.

## Dedup correction: roll/eye geometry is newer than the handoff text

Current live source plus an independent line-forensic receipt show that the old description "eye glow/blink still uses hand-fitted roll compensation" is stale at the implementation level.

Current live implementation contains:

- measured per-roll `KOPF_ROLL_AUGEN_OFFSET` values in native 1536x1024 coordinates;
- `kopfRollAusgleichDeg = kopfRollWert`;
- atomic assignment of the measured dx/dy offset when the photo-roll pose changes;
- the same roll translation/rotation basis applied to `#augen-blink` and `#pupillen-glow`;
- both eye layers inside `#kopf-dreh`.

The source comments identify `rig2/messen_augenanker_exakt.py` and `rig2/augen_anker_exakt.json` as the measurement lineage. This is stronger than the older hand-fitted-Lerp description, but it is not yet a proof that every angle / expression combination is perceptually accepted.

Independent receipt:

- `local_bridge/results/receipts/avatar-hardcore-20260912T0255Z-roll-eye-forensic-gpt56sol.json`

Dedup consequence: do NOT dispatch another worker merely to replace the old hand-fitted constant. The next useful geometry work must target a still-open discriminator (multi-angle Gate-0, manifest unification, or exact parallax provenance).

## Scratch Chrome A/B classified as harness failure, not Avatar negative

`go-avatar-eye-visible-launch-ab-20260912-0958-gpt56sol` tested isolated Chrome launch modes `app`, `plain`, and `newwindow` while preserving production PID `3033100`.

All three scratch processes exposed only extension background/service-worker targets and died after roughly 3 seconds. The production subject survived unchanged.

Classification: `HARNESS / EVIDENCE_INVALID`, NOT Avatar product negative.

Evidence:

- `local_bridge/results/receipts/go-avatar-eye-visible-launch-ab-20260912-0958-gpt56sol.json`

Do not reuse that launcher as a visual A/B evidence path without first repairing target-page readiness.

## Parallax / Gate-0 frontier

A dedicated read-only provenance audit was dispatched:

- command: `go-avatar-parallax-provenance-gate0-audit-20260912-0959-gpt56sol`
- command commit: `fedd4df4384996c4f31ea82237745277300df283`

The receipt returned exit `141` because the shell used `set -o pipefail` together with bounded `... | head` discovery output. This is a harness termination, not a parallax scientific negative. Partial output is still usable as bounded evidence.

Verified from that output:

- live source hashes stayed unchanged;
- `kopf_rgba_parallax/` exists;
- `kopf_rgba_tiefe/parallax/` exists;
- `rig2/` exists;
- `rig_v2_incoming/FRANK_AVATAR_RIG_V2/` exists;
- `rig_referenz/build_rig_v2.py` exists and declares `head_neck_anchor = {x:768,y:600}`;
- `kopf_rgba_parallax/` contains 48 RGBA PNGs, all exactly 1536x1024;
- 44 unique SHA-256 image hashes were measured, structurally consistent with 11 roll poses x 4 slices plus a 4-slice zero reference duplicating the +0 pose;
- historical handoff inventories mark both parallax families as `inactive/experimental`;
- no current live `buehne.html` parallax wiring was found in the prior exact source read.

Evidence:

- `local_bridge/results/receipts/go-avatar-parallax-provenance-gate0-audit-20260912-0959-gpt56sol.json`
- `local_bridge/results/logs/go-avatar-parallax-provenance-gate0-audit-20260912-0959-gpt56sol.stdout.txt`

New exact manifest reads have been queued as separate `read_file` operations:

- `go-avatar-read-depth-parallax-manifest-20260912-1002-gpt56sol`
- `go-avatar-read-rig2-manifest-20260912-1002-gpt56sol`
- `go-avatar-read-rigv2-incoming-manifest-20260912-1002-gpt56sol`
- `go-avatar-read-build-rig-v2-20260912-1002-gpt56sol`

Until their receipts prove lineage, do NOT label the 4-slice assets as Depth-Anything-V2 output and do NOT wire them into production.

## Provider authority fence

Current Clay authority says FreeSwarm/provider admission is `HARD_OFF` unless newer explicit authority reopens that provider lane.

A concurrent control-branch commit attempted to enqueue `harness_aider.py fallback-start --kandidaten nvidia-nemotron` for an Avatar anchor falsifier. Because general swarm coordination is not equivalent to reopening FreeSwarm/provider execution, the command was removed from the current control tree before any receipt for it was visible.

Historical command commit is intentionally preserved as audit/negative evidence:

- `1276d1ac9fd67a052e4de1b26dce5e046995bc08`

Fence commit removing it from the current control tree:

- `4fe9e6012becc02844e07b09d03a44345aa3469b`

Any late receipt from that provider command must be classified as an authority/concurrency incident and must not create Avatar promotion credit.

## Current highest-information nonduplicate sequence

1. Consume the four exact manifest/builder receipts.
2. Determine whether either parallax family has explicit source-image + algorithm/model + parameters + output-hash provenance.
3. If provenance is absent or ambiguous: keep assets experimental and close the gap with lineage evidence before rendering tests.
4. If provenance is exact: run an isolated Gate-0 reconstruction/alignment discriminator against canonical `kopf_rgba/roll` poses; no production wiring.
5. Only after exact geometry PASS, build one shadow parallax renderer and compare it to the current production visual path.
6. Production mutation remains a separate admitted step: exact pre-hash -> isolated candidate evidence -> live write -> reload existing production subject only -> same display/runtime readback -> screenshot/FPS/hash receipt.

## Promotion vector from this delta

- production health/readback: bounded positive evidence
- roll/eye measured-anchor implementation: bounded positive source/runtime evidence
- eye scratch-launch A/B: invalid harness, zero product credit
- parallax provenance: OPEN / not promoted
- parallax live activation: 0 / not promoted
- whole-avatar acceptance: 0 / not promoted
- FreeSwarm/provider execution: HARD_OFF
