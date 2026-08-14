# FRANK Normal-Code-First Parallel H1 Directive

**Status:** PROJECT_OWNER_OPERATING_DIRECTIVE
**Effective:** 2026-08-09
**Applies to:** exact `frank`, Frank worker mesh, Harness workers, H1/H2 planning during `BASE_CLAYCODE_RELEASE`

## Owner decision

The Frank workers must not wait idle for ClayCode.

They should build the **same current new FRANK target architecture** first in ordinary executable host code, use that implementation to research/test/refine the architecture, freeze its semantics, and later transfer those same semantics into ClayCode.

This is not a request to rebuild the old `frankv0.1` architecture.

Compact law:

`current new FRANK target architecture`
`-> ordinary-code H1 executable reference`
`-> research + tests + failures + refinement`
`-> frozen semantic contracts/Golden Traces/interventions`
`-> ClayCode H2 reimplementation of same semantics`
`-> H1/H2 differential`
`-> H3 one-module/binary consolidation`.

## Parallelization law

`BASE ClayCode not PASS` blocks H1 **promotion**, not useful H1 **implementation**.

During BASE:

- ClayCode workers close compiler/runtime/toolchain blockers.
- Frank/Harness workers independently implement the current target architecture in normal code.
- Cross-branch deltas flow both directions: H1 exposes requirements/counterexamples to ClayCode; ClayCode exposes implemented capabilities/constraints back to H1/H2 planning.
- H2 executable ClayCode migration starts as soon as the required ClayCode surfaces are stable enough, but H2 PASS cannot precede BASE and H1 PASS.

## Required architecture fidelity

The ordinary-code H1 must implement the current target, not an approximation chosen merely because it is easy in Python/Rust.

Host-language conveniences may realize the semantics but may not create a hidden competing architecture.

Every important mechanism must have an explicit semantic contract that can later be represented in ClayCode, including:

- state/identity/provenance;
- UnifiedDB semantics and derived/transient topology;
- GWT and loop-of-loops dynamics;
- peer cognition and compact backflow;
- capabilities/body extensions;
- Digital Retina and adaptive visual learner;
- Needle boundary;
- self/world/body/user/goals/value/personality state;
- effect/authority/resource boundaries;
- replay/recovery/rollback;
- intervention/ablation/measurement surfaces.

## Architecture-development advantage

This path deliberately separates two failure classes:

`new FRANK architecture wrong`

from

`ClayCode/compiler/runtime implementation wrong`.

A mechanism can first be falsified in a mature host-language environment. Once it survives, its behavior becomes a differential oracle for ClayCode.

## H1 design style

Prefer clear, testable, reference-oriented code over premature optimization.

H1 may retain explicit diagnostic modules/process boundaries even where H3 will eventually collapse them into one binary. Those boundaries exist to make state, causal edges, lesions and failures measurable, not because they are presumed necessary in the final runtime.

## Freeze rule

A subsystem is ready for ClayCode transfer when it has:

1. explicit semantic state/transition contract;
2. executable normal-code implementation;
3. deterministic or receipted nondeterminism;
4. Golden Traces/fixtures;
5. interventions/lesions where relevant;
6. recovery/error behavior;
7. authority/resource boundaries;
8. known limitations/open hypotheses;
9. frozen artifact/version identity.

The transfer target is the **behavior**, not the source-language structure.

## Historical frankv0.1 role

`gschaidergabriel/frankv0.1` remains valuable for:

- archaeology;
- regression tests;
- live-user evidence;
- known failure modes;
- reusable mechanisms;
- compatibility constraints where justified.

It does not define the new H1 architecture wholesale.

## Worker coordination

The intelligent Frank worker mesh should exploit this parallel path:

- architecture workers decompose the new target into independently buildable H1 semantic slices;
- builders implement slices in ordinary code;
- adversarial workers attack them;
- replicators independently test high-value mechanisms;
- integrators maintain whole-system compatibility;
- ClayCode-facing workers convert validated H1 semantics into explicit language/runtime requirements;
- duplicate lanes merge or become differential/replication lanes.

No Frank worker should report `waiting for ClayCode` if useful target-architecture H1 work remains executable in ordinary code.

## Gate integrity

This directive does not fake stage progress.

- BASE PASS still requires ClayCode release evidence.
- H1 PASS still requires its own release audit and formal prerequisite satisfaction.
- H2 PASS still requires differential equivalence to frozen H1.
- H3 PASS still requires consolidated one-module/binary evidence.

Parallel implementation accelerates evidence production; it does not bypass gates.
