# GO receipt — EntityOS artifact recovery blocker

Date: 2026-08-17  
Trigger: `go`  
Product endpoint: ClayVerse single OCI/Docker-compatible container image  
Scope: artifact recovery/provenance only; not whole-container PASS.

## Newest exact EntityOS evidence observed in this GO

Vercel deployment `dpl_Wr1eZgxbWsT8N39eiEE8JJ3h1Qdz` is bound by deployment metadata to `gschaidergabriel/Dr.-Unterweger` commit `79dc06eb4cba7aa3e3f4d1944bf3c2609ca0d21c`, which is a descendant of the older exact-evidence commit `92b629566452d8f45fd208fba943b823ddd37e8c`.

Its actually-started isolated Vercel build-internal Sandbox sequence recorded:

- exact source tree `d55d9d41f5a294a4a692cdee6fa46750652a390d`;
- full pytest PASS, zero skips, `207 passed`, `DENY_ALL`;
- twin one-file EntityOS builds byte-identical;
- EntityOS SHA-256 `32cd4587adbb45292c964b45f5efd4c38873ccd578792557fbf909f1953e1586`;
- size `9181696` bytes;
- runtime/self-test, no-host-Python and relocation/copy/rename gates PASS;
- source archive SHA-256 `4daf761a56164e43d332082e9357865a06d88035c54902f5adf99c204d773b8c`;
- source attestation SHA-256 `4e08e2ea96420d1671451af09601509013018807bdcd5b321be5b6620a0a3ce4`;
- Git bundle SHA-256 `948e53b78378a274366479888249076ed56d541be006cd63af4aa9df78930395`;
- successful Sandbox stop.

This is the identity currently tracked by `the artefact/entityos.lock.json`. It supersedes the older `92b62956...` / `a68eb0cc...` build only as the newest exact observed internal-substrate evidence; neither result is whole ClayVerse acceptance and neither transfers to later descendants without execution.

The built `32cd4587...` file existed only in the bounded Vercel Sandbox/build context. That execution evidence proves the bytes that were exercised, but it did not create a durable release/download location for those exact bytes.

## Older exact evidence retained, not promoted over the descendant

Vercel deployment `dpl_7CZDVst5XGJp67fKs1EeT9KNwiwg` remains valid bounded historical evidence for product commit `92b629566452d8f45fd208fba943b823ddd37e8c`: EntityOS SHA-256 `a68eb0cc2ac343d88421c9173e0d877f0f758b0ebd2e5918fd3e7a3c154b0c00`, size `9176080` bytes, full pytest/one-file/runtime/relocation/Batch-5 PASS and successful Sandbox stop. It is not the current ClayVerse artifact lock because `79dc06eb...` is a later exact-executed descendant.

## Recovery search

Current GitHub release inventory observed in this GO contained no release carrying the exact locked `32cd4587...` bytes. Search for a workflow artifact named for exact head `79dc06eb...` returned none.

A GitHub Actions artifact from earlier descendant-lane head `6c96c7606fe3bf2974b2e828531c28dd17c0d1c3` was downloaded as a possible transport source and rejected after byte verification: its extracted EntityOS was SHA-256 `cb698027bf383b7a0224c0f4dc5e010b03a37a469c7fe5804c55966c698052a4`, size `1217497`, so it is not the locked `32cd4587...` artifact.

No claim is made that the exact bytes are impossible to recover through provider-internal storage; only that no durable retrievable reference for the exact locked bytes was exposed by the authorized tool surfaces inspected in this `go`.

## Consequence for ClayVerse

The ClayVerse image path is source-ready to consume an exact EntityOS artifact without a runtime sidecar:

1. `stage-entityos.sh` binds exact bytes to a SHA-256 and fails closed on mismatch/symlink/observed TOCTOU source swap;
2. `entityos.lock.json` is the source-tracked authority for the admitted EntityOS identity instead of a caller-supplied digest;
3. Dockerfile embeds staged `EntityOS` and requires lock schema, digest, size and staged bytes to agree;
4. the manual OCI gate derives the build digest from the tracked lock and rejects missing/symlink/mismatched staged bytes;
5. runtime EntityOS execution remains fail-closed until accepted image/runtime evidence exists.

The missing input is therefore durable availability of the exact locked bytes plus an admitted exact-current-head isolated OCI execution surface, not another parallel embedding architecture.

## Precise blocker

`BLOCKED_LOCKED_ENTITYOS_BYTES_NOT_DURABLY_AVAILABLE_FOR_EXACT_OCI_GATE`

The current lock identifies SHA-256 `32cd4587adbb45292c964b45f5efd4c38873ccd578792557fbf909f1953e1586`, size `9181696`, from exact executed source `79dc06eb...`; those exact bytes are not currently available as a provenance-bound durable build input. Substituting a different artifact or silently rebuilding a descendant would destroy the artifact identity required by the lock and is forbidden.

GitHub-hosted ClayVerse OCI runs observed in this macro-cycle also failed before any job step executed (`runner_id=0` / no step logs), so they provide no build/test evidence and are not a substitute execution surface.

## Next executable regression-only step

When the exact locked EntityOS artifact becomes durably retrievable through an authorized path:

1. verify SHA-256, size and provenance against `entityos.lock.json` and the exact Vercel receipt;
2. stage those exact bytes through the existing fail-closed staging helper;
3. run the exact then-current ClayVerse source tests and OCI build in an authorized isolated environment;
4. verify the packaged `/opt/entityos/EntityOS` bytes against the lock, then exercise the bounded state-only restart/persistence/read-only-root gate;
5. only after that succeeds, run the normal-service Clerk + authenticated Claude Code + admitted EntityOS effect/re-entry gate;
6. persist exact research source SHA, EntityOS digest, OCI image ID/digest, commands, exit codes, logs and sandbox stop evidence;
7. keep unusual-experiment count at zero for all remaining descendant regression work in this macro-cycle.

The single unusual experiment for this `go` remains consumed by the parallel `STAGING_TOCTOU_SOURCE_SWAP` intervention; this reconciliation adds no new unusual experiment.

No VPS, self-hosted VPS runner, or production-host test is admitted as current acceptance evidence.
