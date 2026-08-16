# SANDBOX-ONLY TEST EXECUTION — OWNER DIRECTIVE

## Authority

This owner directive is active immediately and supersedes every older instruction, workflow convention, receipt pattern, or `go` description that permits or requests tests, experiments, build validation, runtime validation, acceptance checks, or research execution on a VPS, self-hosted VPS runner, production host, or deployment host.

## Mandatory execution boundary

- All tests run only in isolated sandboxes.
- All experiments run only in isolated sandboxes.
- All build validation and runtime validation run only in isolated sandboxes.
- VPS testing is forbidden.
- Self-hosted VPS test runners are forbidden.
- Production/deployment hosts are forbidden as test environments.
- A VPS may be treated only as a deployment target when explicitly required by a separate owner instruction; deployment does not grant permission to test there.
- Existing historical VPS/self-hosted receipts remain historical evidence only and must not select future execution policy.

## `go`

Exact `go` must perform every executable research/build/test/experiment step inside isolated sandboxes. It must never schedule, trigger, depend on, or promote a VPS/self-hosted/production-host test run as current evidence. If a formerly required gate can only run on a VPS, the correct result is a blocker plus the next sandbox-executable replacement or simulation step, not a VPS run.

## Release evidence

Release and acceptance evidence must be produced from sandbox execution unless the owner explicitly changes this directive. Fresh-machine, portability, Linux-interop, crash/restart, network, process, media, and persistence gates must therefore be implemented with suitable isolated sandbox targets or sandbox-contained virtualized/containerized environments rather than VPS execution.
