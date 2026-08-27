# GO receipt — OCI EntityOS release staging lane

Date: 2026-08-17  
Trigger: `go`  
Scope: workflow/provenance regression only; no OCI runtime PASS.

## Problem observed

The canonical `Dockerfile` now requires a staged `EntityOS` file plus `ENTITYOS_SHA256`, but `.github/workflows/clayverse-artefact-ci.yml` previously invoked `docker build` without staging the file and without passing the digest. That made the advertised manual OCI gate structurally incapable of building the current candidate.

## Repair

The manual workflow now requires two explicit inputs:

- same-repository release tag containing an asset named exactly `EntityOS`;
- expected 64-hex SHA-256.

The workflow uses its read-only repository token to download that same-repository release asset, stages it through `the artefact/stage-entityos.sh`, exports the normalized digest, passes the same digest to the Docker build, re-hashes `/opt/entityos/EntityOS` from inside the built image, and records source SHA + release tag + EntityOS digest with the image identity.

No arbitrary remote URL or runtime host bind mount was introduced.

## Exact regression identity

Reconstructed GitHub bytes before execution:

- `.github/workflows/clayverse-artefact-ci.yml`
  - Git blob: `fca90f784f0791e6459ae9f8a5a46929e6294610`
  - SHA-256: `c1010e3e9de5d17b6af17139cd682689b986a0a8fdfb0d8fe05ea04ef61909af`
- `the artefact/tests/test_oci_entityos_staging_workflow.py`
  - Git blob: `90f8770f5c09e8543e1dc0b79457cdad30cb52e0`
  - SHA-256: `ab2a7c22e6d515d425e02355e2b5bba94e6dc5313fe27448e3c1576dac7e7d88`

Both independently recomputed Git blob IDs matched GitHub exactly.

Authorized isolated non-production container regression result: `2 passed in 0.03s`.

Regression obligations:

1. explicit same-repo release tag + SHA-256 authority must exist before staging;
2. the same normalized digest must bind staging, Docker build and packaged EntityOS byte verification.

Unusual experiment accounting: `0 new`; the single unusual experiment for this user-triggered `go` was already consumed by `STAGING_TOCTOU_SOURCE_SWAP` and remains 1/1 total.

## Current blocker

Repository release inventory was checked after the repair:

- `gschaidergabriel/clay-global-research-entity`: no releases;
- `gschaidergabriel/Dr.-Unterweger`: no releases.

Therefore the workflow lane is now coherent but intentionally fail-closed until an owner-accepted EntityOS binary is promoted as a same-repository release asset with its exact digest. No synthetic binary is substituted and no current OCI build/runtime PASS is claimed.

GitHub-hosted Actions also remain described by current repository state as billing/spending blocked before job start. The preferred direct Vercel Sandbox start/exec operation is not exposed by the currently available Vercel connector surface.

## Next executable regression-only step

1. obtain the accepted EntityOS artifact bytes and exact SHA-256 from an authorized isolated build/acceptance lane;
2. promote those exact bytes as research-repo release asset `EntityOS` under a provenance-bound tag;
3. dispatch this manual OCI gate with that release tag and digest;
4. capture full pytest result, image ID/digest, embedded EntityOS digest, packaged runtime checks, state-only probe, fail-closed production startup and logs;
5. execute restart/persistent-state/read-only-root gates on the exact same image in an authorized isolated runtime;
6. persist the resulting exact-source/artifact receipt without upgrading component evidence to whole-product PASS.
