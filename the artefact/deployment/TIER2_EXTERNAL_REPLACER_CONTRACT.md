# ClayVerse external Tier-2 Kubernetes replacer

Status: **SOURCE CANDIDATE / STACKED ON THE DURABLE SAME-POD FENCE / NOT RUNTIME ACCEPTED**

This is deployment infrastructure for the Tier-2 law in `MICROVM_DEPLOYMENT_CONTRACT.md`. It is not a second ClayVerse application, state authority, recovery ledger, identity, effect path or cognition service.

## Dependency

The reference controller consumes the narrow Tier-2 application signal reserved by the durable same-Pod fence candidate: ClayVerse exit code `86`. It must not be promoted as a complete Tier-2 path unless that signal/fence law is present on the canonical product path.

## Deletion admission

Before deleting anything, `tier2_kubernetes_controller.py` requires all of the following on the exact named Pod:

- namespace and Pod name match the configured target;
- Pod UID is present and bounded;
- `app=clayverse` is present;
- exactly one controller owner exists and is `StatefulSet/clayverse`;
- the admitted Kata RuntimeClass is unchanged;
- the ClayVerse application Pod still has `automountServiceAccountToken: false`;
- Pod spec image and runtime `imageID` both match the exact accepted immutable OCI digest;
- current or previous ClayVerse container termination carries the reserved Tier-2 exit code `86`.

Only then may the controller issue a graceful Pod delete with `DeleteOptions.preconditions.uid` bound to the observed old Pod UID. A missing Pod or a UID-precondition conflict is safe convergence; the controller never broadens deletion to a successor that reused the stable StatefulSet Pod name.

## Authority boundary

The controller is stateless with respect to ClayVerse cognition. It does not import UnifiedDB, effects, memory, recovery or inference modules and does not use a shell/process execution path. It reads Kubernetes Pod state and requests deletion only.

`tier2-controller-rbac.template.yaml` is an optional cluster-local credential binding. It grants only `get` and `delete` on the exact named Pod `clayverse-0`. That credential MUST NOT be mounted into the ClayVerse application Pod. A platform-native external controller may replace the reference implementation only if it preserves the same fail-closed identity and UID-precondition contract.

## What this does not prove

A changed Pod UID is necessary evidence for leaving the old Pod identity, but it does not by itself prove a fresh Kata VM/guest-kernel boundary. Final Tier-2 acceptance still requires observed old sandbox termination plus new Pod UID and independently attested new Kata sandbox/VM identity, the same accepted OCI digest, declared persistent-volume reattachment, canonical recovery with generation advance, stale-writer rejection, UNKNOWN preservation and no blind external-effect replay.

Source/unit success for this controller is mechanism evidence only. Kubernetes API/RBAC behavior, actual Pod deletion/recreation, CSI/CNI, Kata/microVM replacement and whole ClayVerse acceptance remain runtime gates.
