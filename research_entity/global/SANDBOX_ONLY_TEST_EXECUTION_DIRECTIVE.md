# SANDBOX-ONLY TEST EXECUTION — OWNER DIRECTIVE

## Authority

**Updated by explicit owner instruction: 2026-08-18 01:58 +07:00.**

All Clay/ClayVerse executable testing remains isolated-sandbox-only. The categorical ban on every VPS-hosted test is superseded by `VPS_DISPOSABLE_GUEST_TEST_EXECUTION_DIRECTIVE.md`.

The operative distinction is now:

- **direct test/build/experiment execution on a VPS host remains forbidden**;
- **a VPS may act as trusted orchestration substrate for a freshly created disposable independent-kernel guest test sandbox**, subject to the newer VPS disposable-guest directive;
- a self-hosted VPS runner may orchestrate such a guest but may not execute the code-under-test on the host itself.

## Mandatory execution boundary

- All tests run only in isolated sandboxes/guests.
- All experiments run only in isolated sandboxes/guests.
- All build validation and runtime validation run only in isolated sandboxes/guests.
- Direct VPS-host execution of product/test commands is forbidden.
- Direct self-hosted-runner execution of product/test commands is forbidden.
- Production application processes and production host namespaces are forbidden as test environments.
- Vercel Sandbox and Daytona remain admitted isolated execution providers when available.
- VPS-hosted disposable guests are admitted when they satisfy `VPS_DISPOSABLE_GUEST_TEST_EXECUTION_DIRECTIVE.md`.
- Existing historical direct-VPS/self-hosted receipts remain historical evidence only and do not become current evidence merely because the new guest lane is authorized.

## `go`

Exact `go` must perform every executable research/build/test/experiment step inside an admitted isolated environment. It may now use the real VPS as an orchestrator for a disposable independent-kernel guest when the newer VPS directive is satisfied.

`go` must never treat the host runner, host shell, host Docker daemon, host filesystem or host kernel namespace as the ClayVerse test target.

If KVM/nested virtualization is unavailable, `go` may use the explicitly hardened QEMU/TCG independent-kernel lane for development/runtime evidence, but must not promote that run to the separate hardware-virtualized final MicroVM acceptance gate.

## Release evidence

Release and acceptance evidence must come from the environment that actually executed the exact bound source/artifact. Source inspection, orchestration success and deployment readiness do not substitute for guest execution.

Final ClayVerse whole-product acceptance continues to require the same exact accepted OCI digest behind the independent hardware-virtualized VM/microVM guest-kernel boundary specified by the current ClayVerse MicroVM directive. A VPS QEMU/TCG test guest is a powerful development/validation surface, not automatic final MicroVM credit.
