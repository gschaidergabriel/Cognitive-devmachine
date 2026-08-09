# FRANK v0.1 — Ubuntu Target Host Directive

**Status:** PROJECT_OWNER_FIXED_DIRECTIVE
**Scope:** Frank v0.1 / Clay 0.1 staged build program
**Effective:** 2026-08-09

## Fixed target

Frank v0.1 is built, researched, compiled, executed, benchmarked, integrated and release-gated for exactly one operative target host:

**Ubuntu Linux on the developer system.**

## Explicit out-of-scope targets for v0.1

The following are not current Frank v0.1 research targets, implementation targets, portability gates or release gates:

- Android
- mobile platforms
- generic edge-device deployment
- Windows
- macOS
- BSD
- cross-platform portability work that is not required to make Frank v0.1 run correctly on the Ubuntu developer system

They may be reconsidered only after a new explicit project-owner directive.

## Research and implementation law

For every current branch (`clayresearch`, `frank`, `claycode`, `harness`, `gwt`, `emergenz`, `hyperposition`, `claygraph`, `unifieddb`):

1. optimize current architecture and implementation decisions for the Ubuntu developer system;
2. use Ubuntu/Linux-native execution, filesystem, process, IPC, sandbox, GPU/accelerator, packaging and service semantics as the concrete v0.1 environment;
3. do not spend current research budget on Android/mobile/edge portability;
4. do not block BASE/H1/H2/H3/UDB/DATA progression on non-Ubuntu portability;
5. preserve semantic abstractions only where they are useful for correctness, testing, safety or future optional portability, but do not turn future portability into current work;
6. any prior document mentioning Android/mobile/edge as a v0.1 target is superseded by this directive for the v0.1 program scope.

## ClayCode consequence

ClayCode BASE remains a general-purpose language/runtime, but the first compiler/runtime release path and all mandatory Frank v0.1 acceptance execution are targeted and validated on Ubuntu Linux. Additional backends are optional research only after the Ubuntu v0.1 path is complete or the owner explicitly reopens portability work.

## Harness consequence

H1, H2 and H3 acceptance evidence must be reproducible on the Ubuntu developer system. No Android/mobile/edge harness is required for Frank v0.1 PASS.

## Priority consequence

When a choice exists between:

- improving Ubuntu v0.1 correctness/performance/integration, and
- enabling another operating system or mobile/edge target,

Ubuntu v0.1 work wins unless the other work is strictly necessary for the Ubuntu implementation itself.
