# ClayVerse Tier-2 replacement signal and Pod-UID fence

Status: **SOURCE CANDIDATE / NOT FINAL TIER-2 ACCEPTANCE**

This contract refines `MICROVM_DEPLOYMENT_CONTRACT.md`. UnifiedDB remains canonical state authority; the deployment layer does not become a second recovery or effect authority.

## Narrow application signal

Exit code `86` is reserved for `tier2_replacement_required` / `tier2_replacement_blocked` states. Generic startup, configuration, dependency or readiness failure is not automatically Tier-2.

The currently admitted trigger is `RecoveryIntegrityError` from the canonical boot recovery spine.

## Durable same-Pod fence

The Kata workload injects Kubernetes `metadata.uid` as `CLAYVERSE_POD_UID` through the Downward API while `automountServiceAccountToken: false` remains in force.

On a recovery-integrity Tier-2 request ClayVerse:

1. atomically writes and fsyncs `/var/lib/clayverse/tier2-replacement.json`;
2. binds the current Pod UID, typed reason and global entity generation;
3. exits with code `86` without opening ingress/readiness;
4. on restart, refuses to open UnifiedDB when the persisted fence names the same Pod UID;
5. permits replacement recovery only when the Pod UID differs;
6. requires canonical recovery to advance the one global entity generation beyond the fenced generation;
7. writes a Tier-2 replacement checkpoint and only then removes/fsyncs the fence.

Malformed, oversized, symlinked/non-regular or identity-invalid fence material fails closed. A repeated Tier-2 request from the same Pod is idempotent and preserves the first fence.

## External full-sandbox replacement remains mandatory

The application does not receive Kubernetes API credentials and does not delete its own Pod. Final deployment requires an external fail-closed orchestrator that:

- observes reserved exit code `86` on the exact `clayverse` container and the exact triggering Pod identity;
- verifies that the Pod is still owned by `StatefulSet/clayverse`, still uses the admitted Kata RuntimeClass, still denies application ServiceAccount-token automount and still references/runs the exact accepted immutable ClayVerse OCI digest;
- uses the old Pod UID as a Kubernetes delete precondition so a stale controller cannot delete a successor that reused the stable StatefulSet Pod name;
- treats Pod disappearance or a UID-precondition conflict as safe convergence and never broadens deletion to a replacement Pod;
- does not treat `RestartAllContainers`, `PodRestartInPlace`, kubelet container restart or another same-Pod reset as Tier-2;
- proves the old Pod/Kata sandbox terminal and proves a new Pod UID plus new Kata sandbox/VM identity;
- preserves the same accepted immutable ClayVerse OCI digest;
- reattaches only declared persistent state/workspace volumes;
- keeps ingress closed until canonical recovery/readiness plus outer-isolation attestation succeed;
- proves the global generation advanced and stale pre-replacement writers/results are rejected;
- preserves UNKNOWN for ambiguous external effects and never blindly replays them.

`deployment/tier2_kubernetes_controller.py` is the bounded reference implementation for the deletion discriminator. It is deployment infrastructure, not a second ClayVerse application/state authority. It does not import UnifiedDB, effect or cognition code and uses no generic process/shell execution. `deployment/tier2-controller-rbac.template.yaml` is an optional cluster-local credential binding limited to `get` and `delete` on the exact named Pod `clayverse-0`; that credential MUST NOT be mounted into the ClayVerse application Pod. A platform-native controller may replace this reference only if it preserves the same fail-closed identity/precondition contract.

The reference controller intentionally does **not** claim that a changed Pod UID proves a new Kata VM. Pod-UID replacement is a necessary discriminator; final Tier-2 acceptance must separately attest the new sandbox/guest-kernel identity and the exact accepted OCI digest after replacement.

Force deletion is not the baseline path because uncertain old-instance termination can violate single-instance safety. Final acceptance must exercise the selected controller on the admitted Kubernetes/Kata target.

## Evidence boundary

Source/unit success for this protocol is mechanism evidence only. It does not prove Kubernetes deletion/watch semantics, Pod/Kata sandbox replacement, CNI enforcement, CSI persistence, exact OCI execution, Clerk/PTY/Claude/Mistral paths or whole-product PASS.

Final Tier-2 acceptance remains `TIER2_REPLACEMENT_BLOCKED` until the same accepted OCI digest survives an observed full appliance/Sandbox destruction and recreation with new outer identity, recovered canonical state, advanced generation and no blind effect replay.
