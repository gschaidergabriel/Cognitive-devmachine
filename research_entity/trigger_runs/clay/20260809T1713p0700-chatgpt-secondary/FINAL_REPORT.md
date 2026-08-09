# CLAYRESEARCH FINAL REPORT

Run ID: `20260809T1713p0700-chatgpt-secondary`  
Actor: `chatgpt-secondary` / OpenAI GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Operational target: Frank v0.1 on the Ubuntu Linux developer system only  
Promotion: **NO_CANONICAL_PROMOTION**

## Executive synthesis

The strongest current-stage result is not a new ClayCode semantic invention. It is a concrete realization blocker: the admitted G9 V3 research surface and admitted grammar are not currently surface-conformant. The spec uses `>`, `<`, `>=`, `if { ... }`, and `receipt? or residual` forms that the grammar does not represent. Under the project's `less change, more compile` law, this should be closed before CC-WP-01 SPEC-FREEZE and CC-WP-02 PARSER-CANON can truthfully PASS.

The run therefore narrows the BASE critical path to:

`admitted surface/spec conformance -> real parser -> deterministic canonical typed IR -> type/effect legality -> reference evaluator -> legality-gated progressive lowering -> runtime/ABI/FFI/stdlib -> executable app suite -> FRANK handoff`

This is deliberately smaller than redesigning ClayCode.

A READY append-only work event was created:

`CC-WORK-G9-SPEC-GRAMMAR-CONFORMANCE-001`

It requires a real Ubuntu full-spec parser/roundtrip receipt. The event is queued work, not executed work.

## Fusion 1 — current internal state

Current project evidence already supports a rich semantic basis: typed semantic state/provenance, capability-bearing effects, Delta/ViewDelta incremental state, ClayGraph epochs, GWT causal-use axes, EffectIntent/Needle separation, bounded rewrite search and reader/context economics. Historical acceptance evidence also contains universal-core and capability mechanism proxies. The active project law is therefore implementation-first, semantic-change-only-on-executable-counterexample.

The current loop-of-loops result was already distributed to all nine branches before this run. It remains one OPEN ancestry family, so this run did not count repeated branch agreement as independent evidence.

## External triangulation

### Recurrent computation

Recent primary research on recurrent-depth transformers supports the plausibility that repeated computation can improve reasoning/generalization, while also reporting an overthinking regime at excessive recurrence depth. Separate attractor-style work explores adaptive recurrent computation/convergence. These papers support testing outcome-gated recurrence in FRANK; they do not validate FRANK's architecture and do not imply emergence or consciousness.

**Implication:** keep `continue iff expected marginal verified outcome gain > compute/resource/instability cost AND unresolved pressure remains material`, and preserve productive cycles/stalls as distinct from fixed-point convergence.

### Incremental computation

DBSP and its practical Feldera implementation show that rich incremental view maintenance is technically viable. Current incremental-view research also emphasizes that cost depends on query/algebra structure rather than being universally constant.

**Implication:** Clay `Delta/ViewDelta` is a plausible implementation direction; preserve an adaptive switch to batch/full recomputation when affected dependency closure becomes dense.

### Compiler lowering

LLVM MLIR's official dialect-conversion architecture uses explicit legal/illegal conversion targets and progressive lowering.

**Implication:** ClayCode should adopt the principle, not copy MLIR wholesale: after each lowering stage, undeclared residual operations/effects are errors rather than silently accepted host escapes.

### Capability sandboxing

WASI/Wasmtime provides capability-oriented resource mediation and is attractive as one Ubuntu backend/sandbox boundary. However, a 2026 Wasmtime security advisory documents a WASI path operation that bypassed an intended host restriction.

**Implication:** sandbox/backend capability systems are defense-in-depth. Clay's deterministic effect/capability broker and protected-invariant verification remain the semantic authority root.

### Equality saturation

Current e-graph work and `egg` support equality saturation as a powerful optimization/search technique, but also reinforce the need for bounded search, extraction and verification.

**Implication:** retain G9 bounded equivalence search as optional optimization research, not a prerequisite for BASE parser/compiler correctness.

### Higher-order causal measurement

Intervention-based information-decomposition work provides candidate methods for testing synergistic causal contribution.

**Implication:** such metrics belong only after controlled intervention/lesion/rescue/null experiments; recurrence, graph complexity and observational synergy remain insufficient for emergence promotion.

## Fusion 2 — transformed architecture decisions

### Decision D1 — close surface/spec conformance before semantic freeze

The first executable question is: what is the authoritative ClayCode input surface? If the G9 V3 `.clay` file is intended to be admitted parser input, grammar/parser must accept its constructs. If it is not, the project must explicitly define a different executable surface and stop using the research surface as parser acceptance corpus. Either outcome is preferable to hidden parser exceptions.

### Decision D2 — use legality-gated lowering

Every compiler stage should declare what Clay operations/effects are legal after that stage. Complete lowering succeeds only when no illegal/unmediated operation remains. This makes host escape visible and supports Safe-Effect closure.

### Decision D3 — keep Safe-Effect authority outside model and sandbox

Model output, GWT selection, graph activation, compiler success and sandbox execution are not authority. Authority must be explicit, narrowed and independently committed through capability/resource rules and protected-state checks.

### Decision D4 — do not put loop-of-loops on BASE critical path beyond representability

BASE must be able to encode recurrent state, timescale, budget, intervention, halt/escalate reasons and receipts. Actual regulator benefit, adaptive recurrence and emergence are later executable H1/H2 questions. No new loop syntax is justified without a compile counterexample.

### Decision D5 — incremental semantics remain benchmark-gated

The synthetic sparse-DAG proxy strongly supports the possible efficiency of dependency-closure recompute but does not establish real workload sparsity. The architecture should retain both incremental and full/batch plan choices and measure the crossover.

## Empirical results

### EXP-CR-001 — G9 spec/grammar conformance

Concrete static mismatch found for comparison operators, conditional blocks and optional/coalescing-like expression syntax. Status: `STATIC_CONFORMANCE_RESEARCH_EVIDENCE`. Required next step: real parser execution on Ubuntu.

### EXP-CR-002 — incremental DAG proxy

5000-node synthetic DAG, 100 single-node updates:
- 100/100 exact matches with full recomputation;
- median incremental/full op ratio ~0.0893%;
- p90 ~1.55%.

Status: `SIMULATION_ONLY`.

### EXP-CR-003 — capability attenuation proxy

100000 random delegation cases:
- `parent ∩ request`: 0 authority amplifications;
- `parent ∪ request`: 93580 authority amplifications (93.58%).

Status: `SIMULATION_ONLY`.

## Hypothesis programme

This run materialized 54 materially distinct falsifiable hypotheses and 10 counterhypotheses across:
- compiler/runtime realization;
- recurrent/GWT control;
- incremental state/UnifiedDB/ClayGraph;
- Safe-Effect Geometry;
- causal emergence and optimization architecture.

Highest-information near-term hypotheses:
1. current G9 mismatch is surface-level and can close without semantic redesign;
2. legality-gated progressive lowering prevents silent host/effect escape;
3. typed FFI/resources can satisfy broad application classes without ambient authority;
4. sparse incremental recomputation will transfer only if real dependency closure remains sparse;
5. capability narrowing transfers from algebraic proxy to real nested runtime only if ambient authority is eliminated;
6. adaptive recurrence beats fixed depth only on some heterogeneous episodes and must be outcome-gated.

## Safe-Effect Geometry delta

A dedicated `SAFE_EFFECT_GEOMETRY_DELTA.md` was produced. It separately records:
1. language/cognitive evidence — no new live model evidence;
2. compiler/type-system evidence — legality-gated effect lowering recommendation;
3. runtime/broker evidence — attenuation proxy, live runtime unverified;
4. end-to-end containment — not established;
5. ordinary utility — not established.

The strongest current architecture constraint is:

`EffectiveEffects(child_program) subseteq Effects(parent_Clay_contract)`

must be tested across WASM, native FFI, generated code, tools and subprocesses. A runtime sandbox does not replace this contract.

## Cross-branch feedback

Explicit feedback was written to all nine currently registered scientific branches. Key effect on each:
- `clayresearch`: integrate around minimal compiler realization path;
- `frank`: provide one frozen executable FRANK component for APP-09;
- `gwt`: provide representable control/readout semantics without new syntax by default;
- `emergenz`: keep intervention constructs representable, no promotion;
- `claycode`: close G9 spec/grammar blocker first;
- `hyperposition`: preserve conflict/alternatives through canonicalization;
- `claygraph`: live-test incremental/epoch claims;
- `unifieddb`: benchmark sparse/dense crossover and avoid premature physical monolith;
- `harness`: execute the queued full parser conformance test on Ubuntu before H1 advancement.

## Negative results and limitations

- No full current G9 parser execution occurred in this hosted worker.
- No local Ubuntu compiler/runtime receipt was available.
- Expected `research_entity/rooms/rooms/clay/ROOM_STATE.json` was absent, so full same-room worker reconciliation could not be performed.
- The run does not establish end-to-end Safe-Effect containment.
- The run does not establish live UnifiedDB incremental speedup.
- The run does not establish adaptive recurrence benefit in FRANK.
- The run does not establish causal emergence or phenomenal consciousness.
- No Android/mobile/edge implementation work is admitted for Frank v0.1.

## Current-stage impact

`BASE_CLAYCODE_RELEASE` remains `NOT_PASS`; all 14 workspace packages were still OPEN at read time. This run does not manufacture percentage completion from research activity.

It does, however, reduce uncertainty about the first implementation sequence and creates a concrete READY work item. The next discriminating local action is now unambiguous:

**Execute the complete admitted G9 surface through a real Ubuntu parser, close the surface/grammar discrepancy with the smallest semantic-preserving change, and produce canonical roundtrip + negative-test receipts.**

Only after that should the parser/canonical-IR/type-effect/lowering chain be considered frozen enough for the application proof suite.

## Durable artifacts

- `RUN_MANIFEST.json`
- `HYPOTHESIS_MATRIX.md`
- `EXPERIMENT_REPORT.md`
- `SAFE_EFFECT_GEOMETRY_DELTA.md`
- `TOOL_EXECUTION_MANIFEST.json`
- `INTERCONNECT_MANIFEST.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `MICRO_PACKETS.json`
- work event `CC-WORK-G9-SPEC-GRAMMAR-CONFORMANCE-001`
- this `FINAL_REPORT.md`

## Final epistemic disposition

**Research delta: yes. Canonical scientific promotion: no.**

The run produced a current-stage executable counterexample, architecture narrowing, proxy experiments, external primary-evidence triangulation and explicit branch feedback. The highest-value next evidence is a local Ubuntu compiler/parser receipt, not another speculative redesign.
