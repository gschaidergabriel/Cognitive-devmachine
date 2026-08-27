# GO 2026-08-16 — Release-manifest trust boundary

Status: SUPPORTED CANDIDATE / NEXT FALSIFIER OPEN
Trigger: go
Observed repository anchor before intervention: clay-global-research-entity `900e29095cd164681b98c477299561e319de6619`; Dr.-Unterweger main `7b54a420172e1d4a8099071eb49352f895943636`.

## Executed repository delta

1. PR #630 (`1c9bcb51401d6657cceb9f80cf7b07e62771748f`) reviewed as mergeable on exact current main. Its exact-head self-hosted workflows for ClayVM provenance, ClayEnv, strict ClayOS, single VM, VM bootstrap, parser/runtime and Deep Integrity were green. It was marked ready and merged with merge commit `4643ee5f77d9c3ea75b4c5ba620a44e5963544c1`.
2. After refetch, PR #632 (`70ee97ecbb7a9ffaf2814298c2f3f129f7c534c8`) compared against the new main. Merge-base was exactly PR #630 head and the remaining delta was limited to six ClayOS/policy/test files. Its exact-head self-hosted ClayOS/provenance/ClayEnv/single-VM/VM-bootstrap/parser/runtime/Deep-Integrity workflows were green. It was marked ready and merged with merge commit `44fdf86474e32cd976f3d071df97078c544d24d1`.

Resulting supported mechanism:
- public ClayOS admission is artifact-only at the package facade;
- raw `exec_blob`/unbound-bootstrap launch surfaces are removed from the production-facing ClayOS API;
- trusted `vm_blob_sha256` is checked before process admission;
- internally self-consistent substituted VM blobs fail when the expected VM identity is independently fixed by the caller/manifest.

Do not infer physical Python sandboxing, release authenticity, whole Clay Machine PASS, Frank-v0.1 PASS or provider capability from these merges.

## GRF candidate and counter-reality

Generated reality: binding source/grammar/executable-IR/VM/artifact hashes is enough to establish release identity.

Strongest counter-reality: if the expectation/manifest is selected by the same untrusted actor that selects the artifact, the attacker can replace both artifact and manifest with a second internally self-consistent world. Hash equality then proves consistency only, not authority.

## Exactly one bounded unusual experiment: MANIFEST_DOUBLE_WORLD

Purpose: discriminate consistency from release authority without changing production code.

Baseline model:
- legitimate world: program `main->42`, VM `CLAYVM-good`, manifest contains their hashes;
- substituted world: program `main->666`, VM `CLAYVM-evil`, manifest contains the substituted hashes;
- verifier checks only equality between caller-selected manifest hashes and supplied artifact identities.

Observed baseline result:
- legitimate world accepted: TRUE;
- substituted self-consistent world accepted: TRUE.

Intervention in the same experiment:
- generate an independent Ed25519 release key;
- pin the release public key in the verifier;
- sign the legitimate canonical manifest with the release key;
- sign the substituted manifest with an attacker key.

Observed intervention result:
- legitimate signed manifest accepted: TRUE;
- substituted attacker-signed manifest accepted: FALSE.

Outcome: RETAIN counter-reality. A non-self-selected trust root is required before release-authenticity promotion.

Rollback: none required; experiment was isolated and production repository bytes were not modified by the experiment.

## Primary external evidence

TUF official documentation: trusted roles sign metadata; root metadata names trusted keys/thresholds; targets metadata binds target hashes/sizes; snapshot/timestamp metadata prevent mixed/stale repository views. This directly supports separating trusted release metadata from artifact self-description.

in-toto official documentation: project-owner-signed layouts name authorized functionaries and signed link metadata, supporting an explicit owner/release authority boundary rather than artifact-selected provenance.

Sigstore official documentation: verification checks signatures against a trusted key or certificate identity and binds the signed payload to an artifact digest; this supports signature/identity verification as the authority layer above hash consistency.

## Next highest-information implementation candidate

Introduce a minimal `ClayReleaseManifest/v1` boundary ahead of `ClayEnvManifest/v1` consumption:
- manifest binds artifact SHA-256, VM blob SHA-256, source/grammar/executable-IR identities, release/version and expiry/epoch;
- verifier trust root must come from an independently provisioned/pinned release root, never from the artifact or caller-selected manifest itself;
- fail closed before `ClayOS.exec_artifact` on unknown root, bad signature, expired/stale epoch, artifact/VM mismatch or manifest rollback;
- keep current `ProvenanceExpectation` checks as the second-stage semantic/integrity gate;
- do not add a second VM or bypass artifact-only launch.

Prefer standards-aligned verification (TUF/in-toto/Sigstore-compatible concepts) over inventing custom cryptography. A small bootstrap implementation may pin one offline release root, but key rotation/rollback protection must remain explicit follow-up obligations.

## Next falsifiers

1. Prove a substituted artifact + substituted unsigned/untrusted manifest cannot reach PID admission.
2. Prove stale but correctly signed release metadata is rejected after a newer accepted epoch/version.
3. Prove changing VM hash, artifact hash or executable-IR identity under an otherwise valid signed manifest fails before admission.
4. Crash/restart: prove last accepted release epoch/root state survives restart without rollback acceptance.
5. Re-run strict ClayOS, provenance, ClayEnv, single-VM, VM-bootstrap, runtime/parser and Deep Integrity on the exact implementation head.

No Together API used. No paid training authorized or started.
