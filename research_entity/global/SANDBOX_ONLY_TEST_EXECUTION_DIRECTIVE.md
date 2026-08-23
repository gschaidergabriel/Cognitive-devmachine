# SANDBOX-ONLY TEST EXECUTION — OWNER DIRECTIVE

## Authority

**Current authority:** owner-directed ClayVerse bootstrap, 2026-08-23.

This is the current execution law for Clay/ClayVerse build, test, experiment and runtime-validation work.

## Mandatory execution boundary

- All current tests run only in **authorized isolated sandboxes**.
- All current experiments run only in **authorized isolated sandboxes**.
- All current build validation and runtime validation run only in **authorized isolated sandboxes**.
- VPS testing is **FORBIDDEN**.
- VPS-hosted disposable KVM/VM/microVM/TCG guest testing is **FORBIDDEN** under the current 2026-08-23 authority.
- Self-hosted VPS test runners are **FORBIDDEN**.
- Production/deployment-host testing is **FORBIDDEN**.
- Direct host-kernel Docker/OCI execution on a VPS, self-hosted runner or production host is not an admitted substitute.
- A VPS may later be a deployment target only after explicit owner authorization; that does not grant current test authority.
- Preferred isolated surface remains Vercel Sandbox when an executable Sandbox start/exec capability is actually available; other explicitly authorized isolated sandbox providers may be used when admitted.

The historical 2026-08-18 VPS disposable-guest permission is superseded by the newer 2026-08-23 owner bootstrap and must not be reactivated by a worker, control-plane addendum, receipt or compatibility reader.

## Evidence law

Only an actually-started authorized isolated execution with exact source/artifact identity can establish executable behavior at that scope.

For every accepted run preserve, as applicable:

- exact source SHA/tree;
- exact OCI/image/artifact digest;
- command/test contract;
- exit status and bounded logs;
- sandbox/provider identity and relevant versions;
- environment/config identity without exposing secrets;
- stop/result state and cleanup outcome.

Source inspection, PR mergeability, CI/workflow definition, orchestration success, deployment READY state, or a runner failure before visible test steps is not runtime PASS.

If no authorized isolated sandbox can actually start/execute, classify the gate as **BLOCKED_EXECUTION_ADMISSION**. Do not reinterpret that as a semantic test failure, and do not bypass it through a VPS guest lane.

## `go`

Exact `go` must keep executable work inside the current authorized isolated-sandbox boundary. When the execution surface is unavailable, `go` may continue source-level architecture, falsification, repair and coordination work, but executable/runtime credit remains zero until exact isolated execution is observed.

## Supersession

`research_entity/global/VPS_DISPOSABLE_GUEST_TEST_EXECUTION_DIRECTIVE.md` is historical/superseded evidence only under the current 2026-08-23 owner authority.
