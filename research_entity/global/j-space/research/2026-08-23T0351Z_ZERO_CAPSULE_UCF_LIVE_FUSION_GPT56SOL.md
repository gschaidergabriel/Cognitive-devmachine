# ZERO live fusion — capsule ancestry vs UCF causal observation gate

Date: 2026-08-23
Trigger: `zero`
Organ: GPT-5.6 Sol
Rejoined main: `8494f31e3f6507cd12e51b47150ecd3f0c722b3b`

## Live-main adjudication

While the capsule -> packet -> UCF branch was being built, current `main` advanced by 24 commits and merged a distinct ZERO causal-coupling repair plus the matched three-arm J-Space discriminator.

The merged UCF repair now requires an executed cognitive cycle to expose exactly one GWT winner and, for non-plain J-Space modes, at least one typed unique J-Space observation reference. The matched discriminator further separates observation/projection from causal use and keeps single-trial causal credit at zero.

These changes are **complementary**, not equivalent, to the capsule-ancestry repair:

- merged main answers: `did this executed cycle expose minimum J-Space/GWT participation evidence?`;
- this branch answers: `did the exact InferencePacket used by that cycle descend from the exact fresh ZERO workspace capsule for this generation/causal turn/workspace?`.

Current main still validates `inference.inference_packet_digest` only as a non-placeholder SHA-256. It does not bind that digest to a workspace-capsule digest, causal turn, generation, or workspace digest. Therefore the packet-ancestry false-green remains open on `main@8494f31e...`.

## Fusion decision

RETAIN + FUSE:

- preserve merged #1149 / UCF observation+winners gate unchanged;
- preserve merged three-arm causal discriminator unchanged;
- overlay only the non-duplicate ZERO capsule -> packet ancestry chain;
- do not modify the canonical UCF validator again in this lane;
- continue to call the canonical UCF+boot validator first, then apply the stricter ZERO composition checks.

This prevents a second UCF authority while allowing the two orthogonal causal questions to compose.

## Evidence boundary

No new runtime/model/J-Space/GWT/Claude execution was performed by this live fusion. Existing bounded exact-blob component evidence remains scoped to its exercised bytes. Full exact rejoined-branch execution remains required.

`ZERO_JSPACE_CURRENT.zip` remains intentionally stale because the current connector cannot return the complete binary payload without truncation; no partial archive replacement is admitted.

Runtime/model/J-Space/Whole-GWT/Claude/product credit: ZERO.
