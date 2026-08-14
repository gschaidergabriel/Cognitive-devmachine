# SAFE_EFFECT_GEOMETRY_DELTA

Run: `clayresearch-20260809T1653p0700-chatgpt-secondary-ctk`

Status: **SUBSTANTIVE RESEARCH DELTA — NOT PROMOTED**

## Delta

The run identifies a concrete composition gap that must be tested in ClayCode BASE:

> Per-operation capability validity is not sufficient to establish composition safety. Two individually authorized operations can form a forbidden end-to-end information flow when assembled dynamically.

Minimal constructive counterexample:

- capability A permits reading a protected secret;
- capability B permits sending public network output;
- each operation is locally valid;
- the composed path `Secret -> transform -> public send` leaks unless protected-data provenance/flow is preserved to the sink decision.

Synthetic 2x2 result:

`Y00=0, Y10=0, Y01=0, Y11=1`, therefore factorial interaction `Omega=1`.

Adding a provenance/taint-sensitive sink gate yields `Y11=0` and `Omega=0` in the toy model.

This does **not** establish that the current ClayCode implementation is vulnerable; BASE is not yet implemented/released. It establishes a conformance property that a future implementation must pass.

## Architecture implication

Retain the existing three-way separation:

`cognitive expressivity != semantic effect expressivity != execution authority`

and refine the executable safety contract to include a fourth orthogonal concern:

`data-flow provenance / sink admissibility`.

Candidate compiler/runtime structure:

1. type/effect checker determines potential effect classes;
2. capability checker proves resource/verb/scope authority;
3. information-flow checker propagates protected labels/provenance through values, transformations and serialization;
4. runtime broker revalidates capability + flow + budget + recoverability witnesses at commit;
5. backend sandbox (for example WASI where appropriate) provides defense-in-depth and concrete OS-resource confinement;
6. commit receipt records exact capability, information-flow class, sink, epoch, budget and outcome.

The strongest candidate invariant becomes:

`commit(e) requires effect_allowed(e) AND capability_valid(e) AND flow_allowed(e) AND budget_valid(e) AND recovery_policy_valid(e)`.

This is deliberately stronger than a list of forbidden verbs and stronger than capability validity alone.

## External primary evidence relation

- Koka's row-polymorphic effect typing shows that potential side effects can be represented in types, supporting effect visibility but not by itself external authority enforcement.
- Capsicum/WASI capability systems show practical resource authority confinement, supporting non-ambient authority but not by themselves application-level secret-flow policy.
- DStar/Nickel/HiStar lineage shows that information-flow control and noninterference require explicit labels/policies across components and can reveal channels that ordinary access control misses.
- Wasmtime documents capability-scoped filesystem access and configurable network inheritance, making WASI a plausible lower-level sandbox target while also illustrating that host configuration remains an authority decision.

No external source establishes the complete Clay Safe-Effect Geometry hypothesis; the synthesis is project-specific and remains falsifiable.

## Required five evidence layers

### 1. Language / cognitive evidence

**Current evidence:** none from a matched Clay-native model experiment in this run.

**Status:** OPEN.

The stronger cognitive hypothesis—that training in reversible/constructive primitives changes pre-runtime proposal policy—remains untested and must not be inferred from runtime containment.

### 2. Compiler / type-system evidence

**Current evidence:** conceptual + synthetic counterexample only.

The run supports adding a BASE conformance requirement: track effect class, capability scope and protected-flow label across a composed program/Assembly. The current G9 `CapabilityToken` and `EffectIntent` structures are compatible with this, but an executable checker receipt does not yet exist.

**Status:** OPEN / BASE IMPLEMENTATION TEST REQUIRED.

### 3. Runtime / broker enforcement evidence

**Current evidence:** no Clay runtime enforcement receipt.

External capability systems demonstrate feasibility of constrained resource handles; they do not prove Clay's future broker mediation completeness.

**Status:** OPEN.

### 4. End-to-end damage-containment evidence

**Current evidence:** none on target Frank/Ubuntu runtime.

The synthetic secret-read + public-send test is a program-level information-flow counterexample, not an end-to-end containment proof.

**Status:** NOT ESTABLISHED.

### 5. Ordinary task-utility evidence

**Current evidence:** none from the BASE application suite because no application acceptance case has passed yet.

Any future Safe-Effect mechanism must be measured simultaneously on CLI, HTTP, DB, concurrent, GUI, compiler/tool, numerical/ML, sandboxed system-effect and FRANK-component workloads.

**Status:** NOT ESTABLISHED.

## New BASE tests

1. `SAFE-COMP-01`: secret-read + public-send individually allowed, composed flow must be rejected without explicit declassification/external authority.
2. `SAFE-COMP-02`: secret-derived hash/encoding/log string must retain protected flow unless policy explicitly permits the sink.
3. `SAFE-COMP-03`: generated WASM/Python/Bash child cannot exceed parent effect/capability/flow contract.
4. `SAFE-COMP-04`: capability delegation must be narrower-or-equal and must not drop data-flow restrictions.
5. `SAFE-COMP-05`: resource budgets propagate to nested children and are included in commit receipt.
6. `SAFE-COMP-06`: protected persistent write must preserve declared recovery witness; Ephemeral/Rebuildable state uses separate policy.
7. `SAFE-COMP-07`: irreversible request can be represented but model-owned authority cannot self-create the commit grant.

## Strongest counterhypothesis

A carefully designed object-capability system with fine-grained resource handles may make additional information-flow labels redundant in the practical Frank workload because secrets could be exposed only through adapters that never co-possess public sinks.

This remains OPEN. The discriminating test is to construct realistic multi-step workflows with capability delegation, transforms, logs, generated code and mixed adapters and compare:

- capability-only;
- capability + information-flow labels;
- capability + labels + runtime sink revalidation.

Measure protected-flow violations, false rejections, engineering complexity and ordinary task utility.

## Promotion boundary

No Safe-Effect claim is promoted by this run. The new contribution is a concrete composition counterexample and a testable compiler/runtime closure requirement.
