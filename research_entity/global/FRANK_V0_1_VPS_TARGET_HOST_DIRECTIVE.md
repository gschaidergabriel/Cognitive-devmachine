# FRANK v0.1 — VPS Target Host Directive

**Status:** PROJECT_OWNER_FIXED_DIRECTIVE
**Effective:** 2026-08-10
**Scope:** Frank v0.1 / Clay 0.1 staged build program

## Exact change

Everything in the current Frank/Clay v0.1 programme remains unchanged **except the target system**.

The former v0.1 target host `Ubuntu Linux on Andreas' developer system` is replaced by:

**the persistent VPS.**

This is a replacement, not an additional target.

## Fixed target semantics

Frank v0.1 is built, researched, compiled, executed, benchmarked, integrated, deployed and release-gated for the VPS as the operative target host.

Andreas' PC is no longer a Frank v0.1 release target, acceptance target or required execution target. It may still act as an ordinary client/development access point where useful, but no v0.1 gate depends on reproducing Frank there.

## Persistent deployment requirement

The target VPS hosts the finished Frank continuously (24/7) with:

- authenticated API-token access for authorized clients;
- restart/reboot recovery;
- health/readiness/version/build/model identity;
- versioned build/deployment history;
- bounded searchable telemetry/state-history database;
- recurring versioned UnifiedDB backups and tested recovery candidates;
- controlled non-destructive Research-Entity execution via MCP or successor interface.

## Programme invariance

This target-host replacement does not otherwise change:

- Clay architecture;
- ClayCode semantics or staged compiler/runtime work;
- H1 Reference Harness semantics;
- H2 ClayCode Harness semantics;
- H3 One-Module Frank semantics;
- Digital Retina / adaptive visual learning requirements;
- GWT, Hyperposition, ClayGraph or UnifiedDB research semantics;
- data/training gates;
- evidence, falsification, receipt or recovery standards;
- Frank/Research-Entity identity and authority separation.

Existing work remains valid unless it depended specifically on Andreas-PC-only hardware/runtime assumptions.

## Host-specific reinterpretation rule

Any older current document that says:

- `Ubuntu developer system`;
- `Andreas PC` as v0.1 target;
- `UBUNTU_LINUX_DEVELOPER_SYSTEM`;
- `final release truth -> Andreas Ubuntu target`;

is interpreted, for v0.1 target-host purposes only, as:

`PERSISTENT_FRANK_VPS`

until that document is mechanically updated.

## Acceptance consequence

All host-dependent build/test/performance/recovery/boot/service/API acceptance receipts for Frank v0.1 must ultimately be generated on the VPS.

Proxy/synthetic/other-machine evidence can guide development but cannot substitute for a required target-host receipt.

## Compact invariant

`FRANK_V0_1_TARGET_HOST = PERSISTENT_FRANK_VPS`

and

`ALL_OTHER_PROGRAMME_SEMANTICS = UNCHANGED`
