# GO receipt — EntityOS in-image staging / TOCTOU gate

Date: 2026-08-17  
Trigger: `go`  
Product endpoint: ClayVerse single OCI/Docker-compatible container image  
Scope: bounded EntityOS staging mechanism only; this is **not** whole-container PASS.

## Exact source bytes exercised

- `the artefact/stage-entityos.sh`
  - Git blob: `dac869f15abc314109888f3f32f115ac6004063c`
  - SHA-256: `9beb7cdab594ffa9943a03da2a288df9d568bb746daa4c4341c80ffb75f975ab`
- `the artefact/tests/test_stage_entityos.py`
  - Git blob: `5cb6b99168b0f1f97710009713ea60ac921f176d`
  - SHA-256: `0e858e8d4d211dc97fd81e578a8eca703531fb1f2e120646f994bc9c1d806ca4`

The isolated reconstruction independently recomputed Git blob IDs and matched both GitHub blob IDs exactly before execution.

## Authorized isolated regression

Execution surface: isolated non-production container sandbox. No VPS, self-hosted VPS runner or production host was used. The currently exposed Vercel connector surface has project/deployment/log operations but no direct Sandbox start/exec action for this workspace, so evidence is deliberately scoped to the exact staging files.

Environment:

- Linux `6.18.35` x86_64
- Python `3.13.5`
- pytest `9.0.2`
- GNU coreutils `sha256sum 9.7`
- `/bin/sh` -> `/usr/bin/dash`

Observed regression result: `3 passed in 0.07s`.

Covered deterministic obligations:

1. exact bytes + uppercase digest stage successfully and output mode is `0555`;
2. wrong digest exits `65` and publishes no `EntityOS`;
3. symlink source exits `66` and publishes no `EntityOS`.

Classification: regression only; not the unusual experiment.

## Exactly one bounded unusual experiment

Experiment: `STAGING_TOCTOU_SOURCE_SWAP`.

Counterhypothesis: source bytes can be replaced after the first SHA-256 check but before `cp`, allowing unverified bytes to become the staged `EntityOS`.

Intervention: a PATH-local `cp` wrapper replaced the source immediately before the real copy, after the script's initial precheck.

Observed:

- expected SHA-256: `b090291b279a9014b49b412e4c385feded4e35cc8672f2b28c46fbd7932b0839`
- post-copy SHA-256: `6ad722f878a6cdca1d749b756d232330a95a816403dc872b26a02314ee0d7dc2`
- exit code: `65`
- final `EntityOS`: absent
- leftover `.EntityOS.stage.*`: `0`
- outcome: `PASS_FAIL_CLOSED_TOCTOU_SOURCE_SWAP`

Unusual experiment accounting for this user-triggered `go`: **1 of 1 consumed**. Any further execution in this macro-cycle is regression-only.

## Product fusion

At the observed current program frontier, the ClayVerse candidate has converged from a mandatory host-side EntityOS bind mount toward the single-image law:

- staged EntityOS is an explicit build-context input rather than a runtime mount;
- Dockerfile verifies `ENTITYOS_SHA256` and embeds the bytes at `/opt/entityos/EntityOS`;
- Compose has no EntityOS host bind mount;
- runtime EntityOS authority remains disabled until the exact embedded artifact receives isolated acceptance evidence;
- Docker build context is default-deny and allowlists only consumed product inputs.

This receipt strengthens only the staging/embedding provenance mechanism. It does not prove the full OCI build, Clerk, Claude runtime, state recovery, or whole ClayVerse behavior.

## Remaining executable blocker

No exact-current-head OCI build/runtime PASS is claimed. The direct Vercel Sandbox execution operation required for the preferred whole-image gate is not available in the current connector surface, and the isolated local container cannot resolve/access the private GitHub repository to reconstruct the entire exact head automatically.

Next regression-only discriminator on the next exact-source isolated build surface:

1. refresh/freeze current research `main` SHA;
2. stage an owner-accepted EntityOS binary with this helper and bind its SHA-256;
3. run the full current pytest suite with zero new unusual experiments;
4. build exact `the artefact/` and record OCI image digest;
5. run the exact image's `clayverse.service --once` gate;
6. verify no mandatory EntityOS runtime mount, non-root/read-only-root controls, restart and persistent state;
7. persist exact source SHA, staged EntityOS digest, image digest, commands, exit codes, logs and sandbox stop result.
