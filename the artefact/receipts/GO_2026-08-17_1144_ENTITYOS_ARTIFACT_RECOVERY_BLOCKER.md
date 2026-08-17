# GO receipt — EntityOS artifact recovery blocker

Date: 2026-08-17  
Trigger: `go`  
Product endpoint: ClayVerse single OCI/Docker-compatible container image  
Scope: artifact recovery/provenance only; not whole-container PASS.

## Last promoted exact EntityOS evidence

Vercel deployment `dpl_7CZDVst5XGJp67fKs1EeT9KNwiwg` is bound by deployment metadata to `gschaidergabriel/Dr.-Unterweger` commit `92b629566452d8f45fd208fba943b823ddd37e8c`.

Its build logs record an actually-started isolated Sandbox sequence with:

- exact source tree `14f8196483f3579be4724f4bba7dad3ded146b20`;
- full pytest PASS, zero skips, `DENY_ALL`;
- twin one-file EntityOS builds byte-identical;
- EntityOS SHA-256 `a68eb0cc2ac343d88421c9173e0d877f0f758b0ebd2e5918fd3e7a3c154b0c00`;
- size `9176080` bytes;
- self-test / no-host-Python / relocation / Batch-5 / attested-vs-Git-clean identity PASS;
- successful Sandbox stop.

The logs show the built file at `/vercel/sandbox/out/entityos-b/EntityOS`. That is ephemeral Sandbox storage, not a durable release location.

## Recovery search

Current GitHub release inventory:

- `gschaidergabriel/clay-global-research-entity`: no releases;
- `gschaidergabriel/Dr.-Unterweger`: no releases.

The exact SHA-256 was not found as a committed binary path in the searched current EntityOS PR tree. The Vercel deployment remains available as a READY web deployment, but its served root is only the Clay Vercel Sandbox Bridge page and does not expose the stopped Sandbox output file.

No claim is made that the bytes are impossible to recover through provider-internal storage; only that no retrievable artifact reference is exposed by the authorized tool surfaces inspected in this `go`.

## Consequence for ClayVerse

The ClayVerse image path is now source-ready to consume an exact EntityOS artifact without a runtime sidecar:

1. `stage-entityos.sh` binds exact bytes to a supplied SHA-256 and fails closed on mismatch/symlink/observed TOCTOU source swap;
2. Dockerfile embeds staged `EntityOS` and verifies the same SHA-256 at build time;
3. runtime EntityOS authority stays disabled until accepted evidence exists;
4. the manual OCI workflow now stages a same-repository release asset `EntityOS`, passes the same digest to the Docker build, and re-hashes the embedded bytes inside the image.

The missing input is therefore concrete artifact availability, not another parallel embedding architecture.

## Precise blocker

`BLOCKED_ACCEPTED_ENTITYOS_BYTES_NOT_DURABLY_AVAILABLE`

The historical accepted digest/size are known, but the exact 9,176,080 bytes have not been recovered as a durable downloadable artifact. Substituting a synthetic binary or silently rebuilding a descendant would destroy provenance and is forbidden.

## Next executable regression-only step

When an authorized exact EntityOS artifact becomes available:

1. verify its SHA-256 and provenance against the accepted build receipt;
2. publish the exact bytes as research-repository release asset `EntityOS` under a provenance-bound tag;
3. run the repaired ClayVerse OCI staging/build gate with that tag + digest;
4. capture exact research source SHA, EntityOS digest, OCI image ID/digest, full tests, packaged byte verification, state probe, production fail-closed behavior, restart/persistence/read-only-root checks and sandbox stop evidence;
5. keep unusual-experiment count at zero for all descendant regression work in this macro-cycle.

No VPS, self-hosted VPS runner, or production-host test is admitted as current acceptance evidence.
