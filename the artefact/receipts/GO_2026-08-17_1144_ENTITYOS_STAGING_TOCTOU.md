# GO receipt — EntityOS in-image staging / TOCTOU gate

Date: 2026-08-17  
Trigger: `go`  
Product endpoint: ClayVerse single OCI/Docker-compatible container image  
Scope: bounded EntityOS staging mechanism only; this is **not** whole-container PASS.

## Observed source identity

Branch used for the bounded component run: `chatgpt/go-entityos-staging-contract-20260817-1144`.

Exact reconstructed GitHub bytes:

- `the artefact/stage-entityos.sh`
  - Git blob: `dac869f15abc314109888f3f32f115ac6004063c`
  - SHA-256: `9beb7cdab594ffa9943a03da2a288df9d568bb746daa4c4341c80ffb75f975ab`
- `the artefact/tests/test_stage_entityos.py`
  - Git blob: `5cb6b99168b0f1f97710009713ea60ac921f176d`
  - SHA-256: `0e858e8d4d211dc97fd81e578a8eca703531fb1f2e120646f994bc9c1d806ca4`

The isolated reconstruction independently recomputed Git blob IDs and matched both GitHub blob IDs exactly before execution.

## Authorized isolated component regression

Execution surface: isolated non-production container sandbox. No VPS, self-hosted VPS runner or production host was used. Direct Vercel Sandbox start/exec is not exposed by the currently available Vercel connector surface, so this evidence is deliberately scoped to the exact staging files rather than generalized to the ClayVerse image.

Environment:

- Linux `6.18.35` x86_64
- Python `3.13.5`
- pytest `9.0.2`
- GNU coreutils `sha256sum 9.7`
- `/bin/sh` -> `/usr/bin/dash`

Command obligation: execute the three deterministic staging regressions in `test_stage_entityos.py`.

Observed result:

- `3 passed in 0.07s`
- exact-byte happy path: PASS
- wrong digest leaves no `EntityOS`: PASS
- symlink source rejection leaves no `EntityOS`: PASS

Classification: deterministic regression only; not the unusual experiment.

## Exactly one bounded unusual experiment

Experiment: `STAGING_TOCTOU_SOURCE_SWAP`

Counterhypothesis: a source can be swapped after the first digest check but before `cp`, allowing unverified bytes to become the staged `EntityOS`.

Intervention: an isolated PATH-local `cp` wrapper replaced the source bytes immediately before the real copy, after the script's initial SHA-256 precheck.

Observed:

- precheck expected SHA-256: `b090291b279a9014b49b412e4c385feded4e35cc8672f2b28c46fbd7932b0839`
- post-copy observed SHA-256: `6ad722f878a6cdca1d749b756d232330a95a816403dc872b26a02314ee0d7dc2`
- exit code: `65`
- final `EntityOS` present: `no`
- leftover `.EntityOS.stage.*` files: `0`
- result: `PASS_FAIL_CLOSED_TOCTOU_SOURCE_SWAP`

Unusual experiment accounting for this user-triggered `go`: **1 of 1 consumed**. Further tests in this macro-cycle must be regression-only.

## Fusion / product impact

Current main already moved the candidate toward the required one-image boundary by:

- removing the mandatory runtime EntityOS host bind mount;
- embedding staged `EntityOS` bytes into `/opt/entityos/EntityOS` during the Docker build;
- verifying the supplied `ENTITYOS_SHA256` during the image build;
- keeping `CLAYVERSE_REQUIRE_ENTITYOS=0` until the exact embedded artifact has isolated acceptance evidence;
- restricting the Docker build context to explicit consumed inputs.

This receipt adds exact-byte evidence that the staging helper itself rejects digest mismatch, symlink input and the tested post-precheck source-swap counter-reality without publishing a staged output.

## Remaining exact blocker

Whole-product executable truth is still open. The currently available Vercel connector exposes deployment/project/log operations but no direct Sandbox start/exec surface for this research workspace, and the local isolated container has no network path to the private GitHub repository. Therefore no exact-current-head OCI build/runtime PASS is claimed.

Next executable discriminator when an exact-source isolated build surface is available:

1. refresh current research `main` and freeze exact source identity;
2. stage an owner-accepted EntityOS artifact with `stage-entityos.sh` and bind its SHA-256;
3. execute the full current pytest suite as regression-only (`new unusual experiments = 0`);
4. build the exact `the artefact/` image and capture image digest;
5. run `python -m clayverse.service --once` inside that exact image;
6. prove the image starts without an EntityOS host bind mount and that runtime EntityOS authority remains disabled until explicitly accepted;
7. run restart/persistent-state and read-only-root gates;
8. persist exact commands, exit codes, source SHA, staged EntityOS digest, image digest, logs and sandbox stop result.
