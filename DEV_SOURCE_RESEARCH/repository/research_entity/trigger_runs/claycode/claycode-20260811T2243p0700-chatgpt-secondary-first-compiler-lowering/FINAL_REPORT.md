# ClayCode run — bounded compiler/lowering frontier

Run: `claycode-20260811T2243p0700-chatgpt-secondary-first-compiler-lowering`

## Result

The ClayCode compiler frontier now has three deliberately separate lanes:

- PR #369: bounded nominal type admission;
- PR #364: CPython-AST reference/differential backend;
- PR #366: native C11/shared-object backend candidate.

This separation is intentional. ClayCode remains semantic authority. The Python and C artifacts are compiled projections, not independent semantic architectures.

## Accepted evidence

The existing executable evaluator substrate from PR #310 already has target evidence for 200,576 `decide_effect` comparisons with zero mismatch.

PR #369 reached `PASS_CLAYCODE_NOMINAL_TYPECHECK_V1_GATE` on the accepted Linux/X64 target with 12/12 checks. It statically rejects Bool-vs-Int equality, comparison chains, wrong argument/return/condition types, ambiguous variants and untyped host intrinsics. It is a bounded type-admission candidate, not WP04 completion.

PR #364 produced a real target-supported Python-AST lowering mechanism on run `31510276958`: 12/12 checks, 200,576 three-way comparisons, zero mismatch, capability-surface audit PASS, adversarial host-capability AST graft detected, comparison chains and Bool/Int host coercion fail closed. The paired warm shadow measured 15,777.25 ns/call for the evaluator versus 7,196.48 ns/call for the compiled backend, about 2.192x evaluator/compiled ratio. This speed shadow is not a promotion gate.

PR #366 independently produced native C11 lowering evidence on run `31509419897`: 8/8 checks, 200,576 comparisons, zero mismatch, deterministic generated C and shared-object identities. It is a bounded WP06 mechanism candidate, not WP06 completion.

## No backend winner yet

The accepted Python-AST and C runs do not share identical source/grammar/analyzer/evaluator ancestry and their performance scopes are not matched. Therefore no honest backend winner can be selected yet. The next discriminating comparison must run both backends behind the same accepted nominal type boundary, source ancestry, target, request corpus and matched warm benchmark.

## Python-backend counterhypothesis hardening

The strongest counterhypothesis is that a Python-AST backend imports host semantics or host capabilities and becomes a second architecture.

The run therefore hardened #364 beyond simple result equality:

- cross-runtime Bool/Int equality is refused instead of inheriting Python `True == 1` behavior;
- multi-relation comparison chains remain unresolved/fail-closed;
- intrinsic-reachable entries fail closed;
- emitted AST/global capability surface is audited;
- an adversarial `os.system` AST graft must be detected;
- semantic sabotage must turn the differential red;
- source parameters/locals using reserved backend prefix `__clay_` are rejected;
- unbound Clay paths must never fall through to Python globals;
- Clay local bindings must resolve before same-spelled sum variants;
- conditional branch-local bindings are conservatively not promoted to definite outer bindings.

## Preserved negative result

Fresh-current target run `31511909950` tested synthetic merge `a46cb8abf8e99b645a7a9261c83348ed7fcafdd5`, binding the PR into target main `9085f0b3e2be364759d5d8a9d3a08bb71ca06b44`.

The reserved-binding gate passed and rejected both helper-parameter and generated-function-local shadowing. The next path-resolution gate failed before semantic execution with `ModuleNotFoundError: No module named 'runtime'`. This is classified as a test-harness path bug, not compiler counterevidence; the main differential gate was consequently skipped.

The repair is intentionally minimal: the test now inserts the repository root into `sys.path`, and the workflow additionally invokes the scope gate with `PYTHONPATH=$TREE` and Python `-P`. Current repaired head observed during this report is `06051ce66e02361238987e250fbc3b2f02e8f95f`.

## Current replay

Current target main at refresh: `9085f0b3e2be364759d5d8a9d3a08bb71ca06b44`.

Fresh-current repaired target run: `31512274848`, job `93848790327`.

State at report refresh: `QUEUED`.

Until that exact current composition passes, #364 remains draft and the hardened reference backend is not promoted as current-main merge evidence. The earlier green run remains valid mechanism evidence only.

## Research consequence

The architecture delta is `SUPPORTED_DUAL_BACKEND_MECHANISMS_WITH_HARDENED_REFERENCE_BACKEND_PENDING_FRESH_CURRENT_REPLAY`.

No ClayCode language semantic change was selected. No canonical UnifiedDB/ClayGraph state was mutated. No external effect or authority was minted. No WP04/WP06/general compiler/runtime/FFI completion, whole Frank v0.1 acceptance, or training authorization is claimed.

## Next falsifier

Require the repaired exact current #364 replay to pass reserved-binding 2/2, path/scope 5/5, compiler 12/12 and 200,576/0 differential cases. Then compare Python-AST and C only on one matched accepted type/source/base ancestry before choosing any backend.
