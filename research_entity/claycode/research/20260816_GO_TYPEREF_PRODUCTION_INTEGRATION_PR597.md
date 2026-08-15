# GO 2026-08-16 — ClayCode TypeRef production integration (PR #597)

## Scope / active program framing

This delta is ClayVerse / Clay Machine work. It advances the ClayCode compiler/runtime substrate needed by the Clay Machine. Legacy workflows and paths that still carry FRANK/self.root names are used only as inherited regression/compatibility evidence; they are not treated here as the active project goal or as Frank-v0.1 promotion.

Actor: temporary Clay research/build worker (OpenAI GPT-5.6 Sol)
Trigger: exact `go`
Research parent before write: `3aed29ec304996b960cf0f8863f2e3734beefc5c`
Product repository: `gschaidergabriel/Dr.-Unterweger`
Fresh product base: `7fbcb5f64798d919859dc0b664ab5f29559f9d5a`
Candidate branch: `chatgpt/go-claymachine-typeref-production-20260816`
Candidate exact head: `2626a45e53e9943c19cf88bc1ae3b7836cfb5799`
Review object: draft PR #597, mergeable at last refresh, not merged.

## R0 — observed reality

The current ClayCode supervisor frontier required a fresh-main production integration of the detached TypeRef totality mechanism rather than merging stale PR #583. On fresh product main, productive `runtime/claycode_typecheck_v1/typecheck.py` still:

- recursively traversed parameterized `TypeRef.params` in `_canonical`;
- delegated canonical equality to recursive dataclass equality;
- rendered diagnostic TypeRefs through recursive `TypeRef.__str__`.

The prior detached mechanism had executable evidence but deliberately did not mutate production `typecheck.py`.

## R1 / retained hypothesis

Replacing only those three host-recursive TypeRef operations with explicit work stacks can remove Python-stack dependence while preserving current nominal ClayCode rules, alias-cycle fail-closed behavior, diagnostics, admission authority, and downstream compiler/runtime behavior.

## R3 — strongest counter-realities

1. Iterative alias provenance could leak across sibling parameter branches and create false `TYPE_ALIAS_CYCLE` diagnostics.
2. Stack-safe canonicalization could still leave recursive diagnostic rendering and fail only on mismatch paths.
3. The local TypeRef repair could perturb WP04 admission, post-admission snapshot protection, C/Python lowering, runtime nominal behavior, parser fidelity, ABI, or repository integrity.
4. A detached candidate could appear green while fresh-main production bytes regress; therefore evidence must bind the exact fresh-main successor SHA.

## R4 — intervention

Product branch changes are intentionally narrow:

- add `runtime/claycode_typecheck_v1/typeref_ops.py` with explicit-stack canonicalization, structural equality, and diagnostic rendering;
- wire those operations into productive `NominalTypeChecker`;
- keep the existing rule that only non-parameterized alias names resolve;
- add no generic semantics and mint no effect/execution authority;
- add one focused production integration regression gate and exact-head self-hosted workflow.

Product commits:

- `facf4ef0ff8f5716fe709a2793e4040b56b2fada` — production TypeRef stack-safe primitives;
- `bf91eecadba9919f817bcd1a82f02003c177b36b` — productive checker integration;
- `5dba7c2cf82b0674c5bb3c44a34d6ecb4a9c3668` — regression + one unusual falsifier;
- `2626a45e53e9943c19cf88bc1ae3b7836cfb5799` — exact-head VPS integration gate.

Branch comparison at the measured head: 4 commits ahead, 0 behind the fresh base; only checker, TypeRef helper, test, and dedicated workflow changed.

## Exactly one bounded unusual experiment

Experiment: `TYPEREF_ALIAS_SIBLING_PROVENANCE_BRAID`

Construction: an acyclic alias graph deliberately makes two sibling parameters share an alias downstream. If mutable active-alias provenance leaks from one sibling traversal to the other, the second sibling is falsely diagnosed as cyclic.

Prediction if integration is right: `Pair<Int, Int>` and zero cycle diagnostics.
Prediction if counter-reality is right: false `TYPE_ALIAS_CYCLE` on `Right -> Left`.
Observed exact-head result: `Pair<Int, Int>`, zero cycle diagnostics.
Outcome: RETAIN the branch-local provenance mechanism; counter-reality not observed in this discriminator.

No second unusual experiment was executed in this macro-cycle. All other checks below are ordinary regression/compatibility tests.

## Exact-head measured evidence

Dedicated run: `31908520503`, job `95069970925`, self-hosted runner `clay`, machine `clayverse`.
Tested SHA: `2626a45e53e9943c19cf88bc1ae3b7836cfb5799`.
Result: `PASS_CLAYCODE_TYPEREF_PRODUCTION_INTEGRATION`.

Ordinary checks: 7/7 PASS:

1. 4096-depth canonicalization stack-safe;
2. 4096-depth equality stack-safe;
3. 4096-depth leaf mismatch detected;
4. direct alias cycle fail-closed once;
5. structural alias cycle visible and fail-closed;
6. shallow diagnostic text preserved exactly;
7. deep diagnostic rendering stack-safe.

Measured file SHA-256:

- `runtime/claycode_typecheck_v1/typecheck.py`: `c4fddc9735fc7733fd8db6970372d70503dc1881f850ad732565d702958a3a7c`
- `runtime/claycode_typecheck_v1/typeref_ops.py`: `c33be84e9c6fc49aa628910a4e649363ff211eb87611b730c0a2669ad8b52871`
- `tests/claycode_typeref_production_integration_gate.py`: `23a6716bcc311d870e7955cad15b94f6abba9d36e798d78367aef90659edcbed`

Repository static integrity: PASS.
`generic_semantics_widened=false`.
`authority_minted=false`.

## Independent triggered regression envelope on the same candidate head

All completed SUCCESS:

- ClayCode TypeRef Production Integration VPS — run `31908520503`;
- ClayCode Nominal Typecheck V1 VPS — run `31908520489`;
- ClayCode WP04 to WP06 Python admission barrier VPS — run `31908520485`;
- ClayCode WP04 WP06 C Admission Barrier VPS — run `31908520436`;
- ClayCode runtime nominal boundary repair VPS — run `31908520491`;
- ClayCode Alias Totality VPS — run `31908520361`;
- ClayCode opaque parser fidelity V1 — run `31908520464`;
- ClayCode WP06 ABI Manifest Guard v1 VPS — run `31908520504`;
- Deep Integrity legacy compatibility workflow — run `31908520520`.

Additional legacy Frank-named workflows also went green on the candidate head; they are not used to promote the active Clay Machine program and are intentionally not interpreted as Frank-v0.1 acceptance.

## External primary-source boundary

Python 3.13 documentation states that the interpreter recursion limit protects against C-stack overflow and that raising the recursion limit is platform-dependent and must be done carefully because too-high values can crash the process. Python's built-in exception documentation defines `RecursionError` as the exception raised when maximum recursion depth is exceeded.

Primary references:
- https://docs.python.org/3.13/library/sys.html
- https://docs.python.org/3/library/exceptions.html

This supports removing host recursion from finite ClayCode TypeRef processing rather than treating `sys.setrecursionlimit()` as the semantic fix.

## Collapse / evidence state

Outcome: SUPPORTED_INTEGRATION_CANDIDATE, not canonical promotion yet.

Supported:
- fresh-main production bytes can use iterative TypeRef operations without observed regressions in the triggered envelope;
- deep finite TypeRefs no longer inherit the tested Python call-stack limit on the productive checker path;
- the tested sibling-provenance counter-reality did not occur;
- current nominal/generic-open and authority boundaries remained intact in the measured gates.

Not established:
- ClayCode language/compiler completion;
- complete resource totality of parser/analyzer/evaluator/compiler/VM surfaces beyond the tested TypeRef path;
- Clay Machine VM or ClayOS completion;
- any whole-system release acceptance;
- independent semantic replication merely because multiple clay-family self-hosted workflows agree.

## Promotion / next frontier

PR #597 remains review-gated. The current product main did not drift during the measured cycle, and the PR became mergeable, but canonical merge should still respect the supervisor law requiring review before semantic promotion.

After review/promotion, the next high-information Clay Machine language frontier should be re-resolved from fresh main rather than assumed here. Current inherited supervisor fallback priorities include unresolved Call ownership (429 unique / 464 occurrences), 22 MethodChain/member segments, and productive WP04 admission/private-state non-bypassability. Re-resolve these counts before acting because a merge or concurrent worker can change the frontier.

Rollback: close/reject PR #597; no product-main bytes were changed by this run.
