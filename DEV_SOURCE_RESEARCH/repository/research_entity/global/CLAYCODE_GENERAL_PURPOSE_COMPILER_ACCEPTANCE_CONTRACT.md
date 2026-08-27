# ClayCode General-Purpose Compiler Acceptance Contract

**Status:** PROJECT_OWNER_FIXED_MILESTONE
**Purpose:** prove ClayCode is not merely a FRANK DSL but a general-purpose AI-native programming language/semantic IR with an executable compiler/runtime path.

## 0. Core law

ClayCode development is now in a **compile/realize** phase, not a language-reinvention phase.

Existing FRANK/XENO/ClayCode research is presumed to contain most required semantic concepts until an executable counterexample proves otherwise.

Default decision rule:

`preserve semantics -> freeze -> compile/lower -> execute -> test -> only change language when a real application/compiler counterexample forces it`

Do not add syntax/primitives merely because another language has them.

## 1. General-purpose target

ClayCode must be able to express and execute, directly or through typed FFI/lowering, all ordinary application classes including at minimum:

1. pure computation / algorithms;
2. CLI programs;
3. files/directories/processes;
4. HTTP client/server and network services;
5. static/dynamic websites and backend services;
6. GUI/desktop applications;
7. databases/storage engines and persistence clients;
8. concurrent/async applications;
9. games/simulation loops;
10. compilers/interpreters/JIT tooling;
11. GPU/ML workloads;
12. embedded/robotics/device applications;
13. system administration;
14. low-level/raw/device operations under explicit capability authority;
15. FRANK itself.

The language's safety model must constrain **authority**, not computational expressibility.

## 2. Existing evidence baseline

Existing ClayCode multiworker research already produced mechanism-level evidence that:

- a universal core proxy matched an independent reference interpreter on 20,000 bounded two-counter-machine cases with 0 mismatches;
- an effect/capability algebra covered 11/11 tested application classes;
- capability delegation/forgery fuzzing covered 100,000 cases with 0 oracle mismatches and 0 model-forged capability accepts.

These are design/mechanism results, not proof of the final compiler. Therefore the next milestone is executable realization.

## 3. Required compiler/runtime components

ClayCode BASE cannot PASS until the project has working versions of:

- frozen semantic spec;
- parser;
- deterministic canonicalizer;
- typed canonical IR;
- type/effect checker;
- evaluator/reference interpreter;
- compiler/lowering pipeline;
- runtime ABI;
- FFI boundary;
- capability/effect gateway ABI;
- module/package format;
- errors/exceptions/result semantics;
- async/concurrency/atomics semantics sufficient for target applications;
- memory/resource model sufficient for target backends;
- native and/or WASM/WASI backend sufficient for first acceptance;
- host interop sufficient for OS/network/UI/database/GPU access;
- minimal standard library/SDK;
- build/test toolchain;
- deterministic semantic hashes/receipts.

## 4. Application proof suite

The compiler gate requires executable application exemplars, not merely AST representability.

Mandatory first suite:

### APP-01 CLI
Read arguments, files/state, produce deterministic output.

### APP-02 Website
Build a small real website stack: HTTP server + routing + HTML/asset response + state/query interaction. A frontend-only static generator may be an additional test but cannot replace the HTTP/backend test.

### APP-03 Database-backed service
CRUD/query/transaction path through a real or reference DB adapter.

### APP-04 Concurrent service
Async/concurrent tasks, cancellation/error path and deterministic receipt semantics.

### APP-05 GUI or interactive application
Real event-loop/input/state/render path through a typed host adapter.

### APP-06 Compiler/tool
A small parser/compiler/interpreter implemented using ClayCode facilities.

### APP-07 GPU/ML or numerical backend
Typed host/backend lowering with explicit resource/capability handling.

### APP-08 Low-level/system effect
A harmless sandboxed representative of raw/admin/device-class authority proving expressibility without ambient authority.

### APP-09 FRANK component
Compile and execute at least one real frozen FRANK subsystem before full H2.

### APP-10 Full FRANK handoff
ClayCode BASE must expose everything needed for H2/H3 to implement the frozen FRANK architecture without semantic escape hatches.

## 5. Acceptance rule

For every exemplar:

- Clay source/IR hash recorded;
- compiler/runtime version recorded;
- generated target hash recorded;
- execution actually performed;
- expected-vs-observed semantic result recorded;
- positive and negative tests pass;
- no hidden authority escalation;
- host/FFI semantics explicit;
- any language change is linked to a concrete failing counterexample.

A source file that parses but cannot run does not satisfy the gate.

## 6. "Less change, more compile" invariant

Before changing ClayCode semantics, a worker must answer:

1. Which concrete application or FRANK program cannot be expressed/lowered now?
2. Is the missing piece actually language semantics, or only compiler/runtime/stdlib/FFI work?
3. Can an existing Clay primitive already represent it?
4. Can a typed host adapter solve it without semantic leakage?
5. What executable test proves the language itself must change?

If no such counterexample exists, implementation work wins over language redesign.

## 7. Gate output

Required artifacts:

- `CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json`
- compiler/runtime hashes;
- application proof suite receipts;
- unresolved-language-counterexample ledger;
- explicit `GENERAL_PURPOSE_GATE: PASS|FAIL`.

`GENERAL_PURPOSE_GATE = PASS` is mandatory for ClayCode BASE completion and therefore for Clay 0.1 / DOOMSDAY.
