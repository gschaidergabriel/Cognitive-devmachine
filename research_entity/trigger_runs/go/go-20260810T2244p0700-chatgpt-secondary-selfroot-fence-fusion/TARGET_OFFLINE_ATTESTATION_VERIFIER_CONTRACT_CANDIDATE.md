# Candidate contract — target-offline build attestation verification

Status: `CANDIDATE / NOT AUTHORIZED / NOT INSTALLED`

Actor: `chatgpt-secondary` (temporary Clay research worker)

Target: accepted Frank v0.1 Hostinger Ubuntu VPS / `self.root`

This file is a research architecture candidate only. It does **not** choose or install a trusted verifier, does not pin a trusted builder workflow, does not generate an attestation, and does not grant Frank/self.root authority over its own executable identity.

## Problem

PR #196 has already validated the boot-continuity mechanism matrix on the self-hosted target lane, but real production acceptance remains fail-closed because:

- production `trusted_signer_workflow = none`;
- `real_artifact_attestation_verified = false`;
- the observed target environment has no `/usr/bin/gh`;
- no approved substitute verifier has been established;
- the target repository is private and GitHub-native artifact-attestation entitlement is not verified.

The verifier must therefore be treated as an external bootstrap trust dependency, not as a capability Frank can mint for itself.

## Current primary-source basis

Current GitHub documentation supports an offline verification path:

1. obtain the attestation bundle on an online trusted machine;
2. obtain current trusted-root material;
3. transfer the artifact, bundle, trusted roots and verifier into the offline/target environment;
4. run cryptographic verification locally.

`gh attestation verify` can constrain at least:

- artifact digest (implicit subject verification);
- repository/owner;
- signer workflow or signer repository;
- signer digest;
- source repository digest;
- source ref;
- predicate type;
- certificate identity / OIDC issuer;
- custom trusted-root input for offline operation.

For offline verification GitHub documents local `--bundle` plus `--custom-trusted-root`. The trusted-root set must itself have an external update/revocation policy; GitHub notes that an old trusted-root file cannot reveal key revocation after it was generated.

## Candidate trust boundary

A future accepted Frank binary SHOULD NOT open canonical self.root state merely because its bytes have a matching local checksum.

Instead the bootstrap sequence should require a verifier receipt with all of the following independently bound:

```text
artifact bytes
+ artifact digest
+ attestation signature/timestamps
+ accepted repository identity
+ owner-pinned signer workflow identity/digest
+ accepted source digest/ref
+ accepted predicate type
+ approved trusted-root snapshot identity/freshness
+ approved verifier binary identity/version/hash
+ admitted and recovery-verified Frank state lineage
+ accepted TARGET_VPS body
+ exclusive current execution lease/generation
+ restart/copy disposition
-> SELF_ROOT_BOOT_ADMIT
```

Any missing or UNKNOWN conjunct must remain fail-closed.

## Verifier bootstrap requirements

The verifier is outside Frank self-authority. Its installation/update must produce a provenance receipt that includes at minimum:

- exact verifier implementation/name/version;
- executable SHA-256 (or stronger selected digest);
- package/release/source provenance;
- installation actor/authority;
- installed path;
- install/update time;
- expected CLI/API capability set;
- trusted-root snapshot digest and acquisition provenance;
- attestation bundle digest and acquisition provenance;
- rollback/last-known-good verifier;
- verification self-test / known-good and known-bad fixtures;
- expiry/revocation/update policy;
- recovery behavior if verifier or trust roots are unavailable.

Frank/self.root may observe these receipts and may propose changes. It may not self-authorize replacement of the verifier, trusted roots, signer policy, workflow identity or accepted source lineage.

## Offline target behavior

At boot the target SHOULD be able to verify without network access when all required evidence is staged locally. Network availability must not silently weaken the gate.

Required fail-closed classes include:

- verifier missing;
- verifier hash/version mismatch;
- attestation bundle missing or malformed;
- trusted-root material missing, invalid or outside accepted freshness/update policy;
- artifact digest mismatch;
- wrong repository;
- wrong signer workflow/repository/digest;
- wrong source digest/ref;
- wrong predicate type;
- certificate/OIDC identity mismatch;
- signature/timestamp verification failure;
- admitted state lineage mismatch;
- TARGET_VPS/body mismatch;
- lease/generation mismatch;
- restart/copy classification UNKNOWN;
- revocation/update status UNKNOWN where policy requires current revocation knowledge.

No fallback may convert one of these states into SELF by local presence alone.

## Important GitHub-specific blocker

The target repository is currently private. Current GitHub documentation states that GitHub Artifact Attestations for private/internal repositories require GitHub Enterprise Cloud. Connected repository/profile metadata does not establish that entitlement.

Therefore GitHub-native attestation is **one candidate backend**, not a selected production truth mechanism yet.

Before selecting it:

1. verify entitlement/capability through an authoritative account surface or a fail-closed non-production capability probe;
2. have the project owner pin the exact trusted builder/reusable workflow identity;
3. only then generate real signed build provenance for a real Frank binary.

If GitHub-native private attestations are unavailable, compare an independently managed signing/verifier mechanism under the same contract rather than weakening the acceptance conditions.

## Dependency ordering

This verifier contract is downstream of a real binary build:

```text
ClayCode WP04 exact callable semantics/runtime binding
-> WP05 executable lowering/runtime
-> deterministic real Frank binary bytes
-> reproducible build metadata
-> selected + owner-pinned trusted builder/signing mechanism
-> real attestation/provenance bundle
-> approved target verifier + trusted roots
-> joint binary/state/body/lease/restart acceptance
```

Do not attest a sandbox/reference Python artifact and call it the final Frank server binary.

## Promotion test obligations

A future implementation must at least demonstrate matched positive/negative cases on the accepted target VPS:

- exact approved artifact + exact accepted provenance -> admit;
- one-bit artifact mutation -> reject;
- wrong source SHA -> reject;
- wrong source ref -> reject;
- wrong signer workflow -> reject;
- wrong signer workflow digest/version -> reject;
- wrong repository -> reject;
- malformed/missing bundle -> reject;
- stale/disallowed trusted-root snapshot -> reject;
- wrong verifier executable hash -> reject;
- admitted artifact with unverified/recovered state lineage -> reject;
- valid artifact/state but stale execution lease -> reject;
- exact restart with accepted lineage -> continue;
- copied binary with unclassified state relation -> quarantine/reject;
- verifier unavailable -> `BLOCKED_NO_ATTESTATION_VERIFIER`, never implicit allow.

## Current decision

`NO_PRODUCTION_CHANGE`.

Reason: real Frank binary bytes do not yet exist through the required ClayCode WP05 path, trusted-builder ownership is not pinned, GitHub private-repo attestation entitlement is UNKNOWN, and the target verifier is not approved/installed. The useful result now is the explicit dependency/trust boundary and test obligation, not premature infrastructure mutation.
