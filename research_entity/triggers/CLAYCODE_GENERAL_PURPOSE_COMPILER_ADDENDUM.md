# ClayCode Trigger Addendum — General-Purpose Compiler Endgame

**Status:** PROJECT_OWNER_FIXED_ADDENDUM
**Applies to:** every exact `claycode` run and every ClayCode task spawned by `666`, Harness or Q12
**Acceptance contract:** `research_entity/global/CLAYCODE_GENERAL_PURPOSE_COMPILER_ACCEPTANCE_CONTRACT.md`
**Workspace:** `research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json`

## Mandatory law

ClayCode is no longer treated primarily as an open-ended language-design exercise.

Current default hypothesis:

> FRANK/XENO/ClayCode development has already forced most semantic concepts required for a general-purpose AI-native language. The dominant remaining task is to freeze, compile, lower, execute, test and package those semantics.

Therefore:

`existing semantics -> compiler/runtime/FFI/stdlib -> real applications -> FRANK -> only then redesign if a counterexample forces it`

## Required behavior on every run

Before proposing a new ClayCode semantic primitive:

1. inspect the General-Purpose Compiler Acceptance Contract;
2. inspect the current compiler workspace;
3. identify a concrete program/application/FRANK subsystem that fails;
4. determine whether the failure belongs to parser/compiler/runtime/ABI/FFI/stdlib/backend/tooling rather than language semantics;
5. attempt an executable fix without changing language semantics;
6. change semantics only if an executable counterexample remains.

## General-purpose proof obligation

ClayCode BASE requires executable proof across ordinary application classes, including a real HTTP/website stack, not just FRANK.

Representability alone is insufficient. Compilation/lowering + execution + semantic receipts are required.

## Research rule

New research remains welcome where implementation exposes a real gap. But novelty is not progress by itself. A compiler/runtime improvement that realizes existing semantics is preferred over a new concept when both solve the same problem.

## FRANK as requirements super-set

Treat FRANK as the most demanding integrated application currently known inside the project, not as evidence that no external application class can reveal a missing requirement.

The application proof suite exists specifically to search for those counterexamples.

If a website, GUI, DB service, concurrent service, compiler/JIT, GPU/ML workload, embedded/system task or other application exposes a missing capability, classify the gap before changing the language.
