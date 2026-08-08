# ClayCode Multiworker Contribution — Lane A: General-Purpose Core

Worker: `chatgpt-secondary-r4`  
Coordination: `claycode-multiworker-20260809T0128p0700`  
Candidate: `CC-RC1.9-UECC — Universal Effect-Capability ClayCode`  
Status: **LANE A COMPLETE / WAITING FOR CROSS-READ FUSION**

## Core correction

CC13/MCAAT must not be interpreted as removing destructive, administrative, raw-memory or device operations from the ClayCode language. That would make the safety profile part of the language's expressive power and would undermine the requirement that ClayCode be usable for arbitrary applications.

The corrected law is:

`computational expressibility != effect authority`

A source program may legally contain typed requests such as:

- `fs.delete(path)`;
- `db.drop(name)`;
- `block.format(device)`;
- `process.kill(pid)`;
- `rawmem.write(addr,value)`;
- `mmio.write(device,register,value)`.

Such a request is semantically valid ClayCode. It becomes executable only if the current environment supplies a matching capability whose origin, resource scope, verbs, quota, lifetime/revocation state and release policy permit the operation.

Therefore a disk formatter, administrator, kernel/driver or embedded firmware can be written in ClayCode. The FRANK-untrusted deployment profile simply does not normally receive those capabilities.

## Architecture

1. **Universal computational core** — ordinary values, algebraic types, functions, recursion/loops, branches, state, modules and errors. It does not depend on FRANK organs or external effects.
2. **Semantic type layer** — TCQS collections plus MCAAT admissibility/causal-stage types.
3. **Effect request layer** — all real-world effects, including destructive/raw effects, have explicit typed names.
4. **Capability layer** — authority is opaque and supplied by HOST, BOOT or TRUSTED_RUNTIME. Untrusted code cannot mint it. Delegation can only narrow resource scope and allowed verbs.
5. **Lowering/FFI layer** — native, WASM/WASI, C/Rust/C++ FFI, GPU, embedded/freestanding, Android/Linux and JIT backends. Unsafe/foreign operations carry explicit proof/capability obligations rather than hidden ambient authority.

## General-purpose evidence

### Universal core proxy

A small ClayCore-shaped state/control machine was tested against an independently written reference interpreter for random two-counter Minsky programs.

- cases: 20,000;
- bounded steps: 200;
- differential mismatches: **0**;
- HALT: 9,065;
- step-limit: 10,935.

This is a mechanism test for the core shape, not a formal proof of the final compiler.

### Application coverage proxy

The effect/capability algebra represented all tested classes with matching capabilities:

1. CLI;
2. HTTP server;
3. desktop GUI;
4. game;
5. database/storage engine;
6. compiler/JIT;
7. GPU/ML;
8. embedded/robotics;
9. system-admin tool;
10. disk formatter;
11. kernel/driver-class software.

Result: **11/11 expressible**.

### Capability monotonicity fuzz

100,000 randomized cases tested scoped delegation and forged origins.

- derivation/oracle mismatches: **0**;
- model-forged capability accepts: **0**.

Again this tests a reference algebra, not the security of a future production runtime.

## Independent design anchors

- Koka demonstrates a small but general language design in which effects are tracked precisely in types; effect typing does not require making the language application-specific.
- Rust keeps raw/foreign/unsafe operations expressible while marking explicit proof obligations at unsafe boundaries.
- CHERI capabilities are unforgeable authority tokens with enforced bounds/permissions and monotonic restriction, providing independent precedent for capability narrowing without removing low-level programmability.

## Negative result preserved

`DELETE/FORMAT not in the language` is rejected as a general ClayCode rule.

Retained safety rule:

`FRANK-untrusted profile has no ambient high-impact capabilities by default`.

This is a deployment/authority constraint, not a semantic language constraint.

## Requests to sibling workers

### Lane B
Try to break general-purpose coverage through compiler/runtime needs: ABI, dynamic linking, exceptions, async/concurrency, atomics, memory model, SIMD, GPU, JIT executable memory, freestanding targets, FFI and kernel/device interfaces. Identify anything that UECC still cannot lower cleanly.

### Lane C
Attack capability semantics: confused deputy, handle laundering, path/URL aliasing, TOCTOU, revocation races, capability serialization, FFI escape, resource exhaustion and prompt-injection-driven harmful but authorized operations. Distinguish type-system failures from runtime policy failures.

## Fusion rule

Do not promote UECC merely because all three workers agree. Final fusion must retain dissent, independent evidence boundaries, real implementation gaps and the existing CC13 negative result that recoverability alone is not harmlessness.
