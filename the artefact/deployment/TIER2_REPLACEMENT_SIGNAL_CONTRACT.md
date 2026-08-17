# ClayVerse Tier-2 replacement signal contract

Status: **SOURCE CANDIDATE / FINAL RUNTIME UNVERIFIED**

This contract defines the narrow signal by which the ClayVerse application can tell an external deployment controller that the **entire Pod/Kata sandbox/VM must be replaced**. It does not itself implement the external replacer and therefore does not close the `TIER2_REPLACEMENT_BLOCKED` final-acceptance gate.

## Signal

The reserved ClayVerse Tier-2 process exit code is:

`86`

Current admitted producer scope is deliberately narrow:

- `RecoveryIntegrityError` while reconstructing the canonical recovery spine -> exit `86`;
- emitted stderr status is bounded JSON with `status=tier2_replacement_required` and `reason=RECOVERY_INTEGRITY_UNTRUSTED`;
- the underlying exception text is not copied into the signal;
- generic startup/configuration/readiness errors are **not** translated into exit `86`.

This prevents ordinary recoverable or configuration failures from silently becoming full-appliance replacement authority.

## External controller law

A future admitted external Tier-2 controller MUST:

1. observe the exact ClayVerse Pod through Kubernetes list/watch or an equivalently lossless controller mechanism;
2. treat only the explicitly admitted Tier-2 signal as replacement authority; generic readiness loss and arbitrary nonzero exits are insufficient;
3. bind the triggering Pod UID, container identity, observed exit code and resourceVersion into its receipt before deletion;
4. delete/replace the whole Pod so the old Kata Pod sandbox/VM becomes terminal; restarting only the container is insufficient;
5. fail closed if the old Pod UID or old sandbox identity can still rejoin;
6. verify a new Pod UID and a new Kata sandbox/VM identity;
7. verify the replacement runs the exact same accepted ClayVerse OCI digest;
8. reattach only declared persistent volumes;
9. require ClayVerse recovery to advance the canonical global generation, reject stale pre-crash results and preserve ambiguous effects as UNKNOWN rather than replaying them;
10. reopen ingress only after full runtime readiness and the MicroVM deployment attestation gates pass.

The controller is deployment infrastructure only. It MUST NOT become a second state, memory, identity, cognition or effect authority and MUST NOT run as a companion ClayVerse application container.

## Watch/replay law

Kubernetes watch streams can be interrupted and historical resource versions can expire. An admitted controller must therefore use a standard list-then-watch/relist discipline and make Pod deletion idempotent against the exact triggering Pod UID. A reconnect or duplicate watch event must not cause deletion of a later healthy replacement Pod.

## Acceptance boundary

Source wiring of exit `86` is only the first discriminator. Final Tier-2 acceptance still requires live proof on the admitted Kubernetes/Kata target that:

- the controller actually observes the signal before/through any kubelet in-place restart race;
- the exact old Pod/Kata sandbox is deleted;
- new Pod and new sandbox/VM identities are observed;
- the same OCI digest is running;
- state recovery and generation fencing complete;
- no ambiguous external effect is blindly replayed;
- ingress remains closed until the replacement has passed readiness and outer-isolation attestation.

Until that live controller path exists and is exercised, final status remains `TIER2_REPLACEMENT_BLOCKED`.
