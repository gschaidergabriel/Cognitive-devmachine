# ClayVerse Tier-2 Pod-UID replacement fence

Status: **SOURCE CANDIDATE / NOT FINAL TIER-2 ACCEPTANCE**

This file refines the mandatory `MICROVM_DEPLOYMENT_CONTRACT.md` without weakening it. Final Tier-2 acceptance still requires replacement of the complete Pod/Kata sandbox/VM, new workload/sandbox identity, the same accepted ClayVerse OCI digest, persistent-state recovery, global-generation advance, stale-writer rejection and no blind external-effect replay.

## Purpose

A Kubernetes StatefulSet may restart a terminated application container inside the same Pod and therefore inside the same Kata sandbox. That is useful for ordinary Tier-1 process recovery, but it is not ClayVerse Tier-2 recovery.

The source candidate adds a durable application-side fence so a fatal recovery-integrity event cannot be followed by a normal in-place container restart that silently reopens the same sandbox.

## Protocol v1

The Kata workload injects Kubernetes `metadata.uid` into the ClayVerse process as `CLAYVERSE_POD_UID` through the Downward API. This supplies object identity only; it does not grant ClayVerse Kubernetes API credentials or orchestration authority.

On an admitted fatal recovery-integrity failure:

1. ClayVerse writes `/var/lib/clayverse/tier2-replacement.json` atomically and fsyncs the file plus containing directory.
2. The fence records schema `clayverse.tier2-replacement/v1`, the current Pod UID, typed reason and current global entity generation.
3. ClayVerse exits with dedicated exit code `86` and never reports readiness.
4. Any later process start that sees the fence and the **same** Pod UID exits fail-closed before opening UnifiedDB.
5. A start with a **different** Pod UID may enter canonical restart recovery, but the fence remains until the recovered global entity generation is strictly greater than the fenced generation and all normal pre-readiness checks have succeeded.
6. Only then is a durable `tier2-replacement-admitted:<old uid> -> <new uid>` checkpoint written and the fence removed with directory fsync.

Malformed, oversized, symlinked/non-regular or identity-invalid fence material is fail-closed. Repeating the request from the same Pod UID is idempotent and preserves the first durable fence.

## External orchestrator obligation remains open

This source candidate deliberately does **not** embed a Kubernetes controller, service-account token or second application container into ClayVerse.

Final deployment still requires a separately admitted fail-closed orchestration mechanism that observes the Tier-2 condition and deletes/replaces the **whole Pod/Kata sandbox**. That mechanism must:

- bind the exact old Pod UID before deletion;
- use Kubernetes delete preconditions for that UID/resource identity so a stale controller cannot delete a replacement Pod;
- prefer normal/graceful deletion and never treat force deletion as the baseline path;
- wait for terminal evidence for the old Pod/sandbox before accepting the replacement identity;
- prove a new Pod UID and a new Kata sandbox/VM identity;
- preserve the accepted immutable ClayVerse image digest and only declared persistent volumes;
- keep ingress closed until ClayVerse recovery/readiness plus the Tier-2 fence admission succeed;
- preserve UNKNOWN for ambiguous pre-crash external effects and reject stale generation writers.

Kubernetes' `RestartAllContainers` action is not a ClayVerse Tier-2 substitute because it is explicitly an in-place restart that preserves Pod UID and Pod sandbox.

## Evidence boundary

A green source/unit test of this protocol establishes only a bounded fail-closed application mechanism. It does not prove Kubernetes API deletion behavior, StatefulSet recreation, Kata sandbox/VM replacement, CNI enforcement, storage/CSI semantics, exact OCI execution or whole-product PASS.

Final empirical gate remains `TIER2_REPLACEMENT_BLOCKED` until the protocol is exercised end-to-end on an admitted VM/microVM deployment using the same accepted OCI digest.

## Primary upstream behavior references

- Kubernetes StatefulSet API: https://kubernetes.io/docs/reference/kubernetes-api/apps-stateful-set-v1/
- Kubernetes Pod lifecycle/restart behavior: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
- Kubernetes v1.35 RestartAllContainers: https://kubernetes.io/blog/2026/01/02/kubernetes-v1-35-restart-all-containers/
- Kubernetes DeleteOptions/Preconditions: https://kubernetes.io/docs/reference/kubernetes-api/definitions/delete-options-v1-meta/
- Kubernetes StatefulSet force-deletion warning: https://kubernetes.io/docs/tasks/run-application/force-delete-stateful-set-pod/
