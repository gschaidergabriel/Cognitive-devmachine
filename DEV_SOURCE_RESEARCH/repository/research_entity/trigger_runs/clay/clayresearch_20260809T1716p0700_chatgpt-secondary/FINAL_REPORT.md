# Clayresearch Integrated Foundry — Final Report

Run: `clayresearch_20260809T1716p0700_chatgpt-secondary`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Current program stage: `BASE_CLAYCODE_RELEASE`  
Operational target: Frank v0.1 on the Ubuntu Linux developer system only.

## Executive result

This run finds **no evidence-backed reason to redesign ClayCode before executing the current G9 semantic candidate**. The highest-information convergence move is to turn the existing semantic machinery into a minimal working compiler/runtime slice that simultaneously exercises two cross-mesh requirements:

1. `LoopDynamicsReadout` + adaptive recurrence-control state; and
2. `CapabilityToken`/`EffectIntent` + child-effect non-amplification.

The run therefore produces a research delta but **does not promote a new Clay generation, does not modify canonical r2, and does not close BASE**.

## Fusion 1 — internal state

Current repository state says:

- Level 0 archive assimilation is PASS.
- BASE ClayCode is the first unpassed gate.
- All 14 BASE work packages remain OPEN and no mandatory application exemplar is yet recorded PASS.
- Current G9 already includes delta calculus, incremental receipts, capability tokens, typed hyperrelations, GWT causal readouts, effect intent/lowering, bounded equality saturation and a recurrent main cycle.
- Frank's loop-of-loops framing is OPEN mandatory cross-branch context, not established causal truth.
- Frank v0.1 implementation/release scope is Ubuntu/Linux only; mobile/edge portability is not a v0.1 gate.

The internal convergence pressure is therefore implementation-heavy: `freeze -> parse -> canonicalize -> type/effect -> evaluate -> lower -> runtime/FFI -> execute real apps`.

## Generation 1

Generated **50 materially distinct falsifiable hypotheses** across ClayCode, Safe-Effect, FRANK loop dynamics, GWT/re-entry, Hyperposition/n-ary roles, ClayGraph incremental topology, UnifiedDB persistence, emergence measurement and latency/boundary architecture. Ten explicit counterhypotheses remain live.

See `HYPOTHESES.md`.

## External research

### Capability/effect security

Bytecode Alliance `cap-std` provides a concrete implementation analogue for scoped resource-handle authority: file access can be rooted in a `Dir` capability rather than ambient path authority. Its own documentation also preserves the critical boundary that cap-std is not by itself a sandbox for arbitrary untrusted Rust that can call unsafe/ambient APIs.

Wasmtime/WASI/component resources provide a second implementation analogue for capability-oriented guest/host mediation. This run therefore strengthens the lowering hypothesis:

`Clay CapabilityToken -> opaque scoped host handle -> typed adapter -> receipt`.

A new negative/safety constraint emerges from Wasmtime security documentation: terminal output/control sequences can be security-relevant. Clay must not universally classify terminal/stdout as PURE.

### Agent information/capability integrity

Recent primary preprints on information-flow control and agent capability integrity independently support deterministic confidentiality/integrity/capability boundaries rather than prompt-only safety. These are used as mechanism support, not as proof of the Clay design.

### Incremental computation

Differential maintenance, FlowLog/Differential Dataflow and egglog show practical paths for incremental relational/equality computation while also exposing memory, scheduling and performance tradeoffs. This supports current G9 `IncrementalReceipt` and bounded EqSat, but argues against dogmatic always-incremental or unbounded equality-saturation designs.

### Causal emergence

PEID provides a potentially useful intervention-defined decomposition of higher-order causal contribution. It is adopted only as a candidate measurement inside a larger intervention suite; no single PEID/emergence scalar is promoted.

## Empirical work

Five synthetic mechanism tests were executed.

1. **Capability non-amplification:** intersection-based narrowing produced 0/100,000 single-step violations and 0/50,000 nested violations; deliberately ambient request-as-grant violated parent authority in 99.866% of randomized cases.
2. **N-ary role binding:** naive unordered pairwise projection collided for 50,000/50,000 role permutations; reified role-bearing representation had 0 collisions. This falsifies the naive projection, not all pairwise encodings.
3. **Incremental locality:** in a deliberately favorable 100k-node local topology, median affected closure was 0.156% and synthetic traversal was ~279.6× faster than a trivial global scan. This is not a live Frank performance claim.
4. **Truthful re-entry favorable regime:** MSE 0.1523 versus 0.6384 lesion and 1.1847 shuffled.
5. **Re-entry volatility negative result:** with high process volatility, the same fixed truthful re-entry gain became worse than lesion across most tested autocorrelation settings, including high `rho`.

The fifth result materially transforms the loop hypothesis: recurrence/re-entry gain must be adaptive to innovation/volatility/residual pressure/marginal utility rather than fixed by recurrence count or temporal continuity alone.

See `EXPERIMENTS.md`.

## Fusion 2 — architecture delta

### A. Smallest coherent loop-control basis

Do not add one global stability/emergence controller. Use:

- a shared typed `LoopDynamicsReadout` contract;
- loop-local dynamics/controller state;
- shared resource/authority/epoch arbitration;
- explicit regime labels: converging fixed point, productive limit cycle, stalled, diverging/overthinking, chaotic/unclassified;
- innovation/residual pressure and marginal utility to gate recurrence;
- explicit intervention/rollback receipts.

### B. Safe-Effect becomes a compile/runtime property

Strengthen APP-08 so every child boundary is checked for:

`EffectiveEffects(child) subseteq Effects(parent) union ExternalGrant`.

Cover generated Python/Bash/C/Rust/Wasm, FFI, tools and subprocesses. Add terminal/control-sequence sinks, secrets and resource exhaustion to the negative matrix. Keep irreversible effects representable as requests but commit-authorized outside ordinary model authority.

### C. Hyperposition/n-ary relations

Preserve explicit role identity. The experiment rejects naive pairwise flattening but leaves reified pairwise encoding as a valid simpler competitor. Hyperposition branch reopening should be stall/residual-pressure-gated and bounded rather than novelty-only.

### D. ClayGraph + UnifiedDB

Leading hypothesis remains:

`canonical semantic/event state -> coherent semantic epoch -> dependency-local derived views/ClayGraph -> selective rebuild when cheaper`.

Physical monolithic storage is not justified by this run. Incremental maintenance is a measured choice per topology/query, not an ideology.

### E. GWT/emergence

Truthful re-entry must be compared with shuffled and no-re-entry controls. GWT focus may be tested as adaptive expensive-compute routing. PEID may be added only where interventions are explicit. Recurrence, broadcast and a high emergence score remain non-authoritative and do not imply phenomenal consciousness.

## Generation 2

External evidence and the experiments transformed the first generation into **12 narrower implementation hypotheses**. Most important:

- compile current G9 before redesign;
- lower capability tokens to opaque resource handles;
- treat terminal as an effectful sink when applicable;
- treat Wasm/WASI as a candidate backend, not a complete safety proof;
- make child-effect closure a BASE property;
- make re-entry gain volatility-aware;
- use typed local loop controllers plus shared arbitration;
- use coherent epochs and incremental derived views;
- keep PEID inside a preregistered intervention suite;
- bring Safe-Effect closure + LoopDynamicsReadout into early APP-08/09 execution.

## Branch feedback

Explicit feedback was written to all nine registered scientific branches. No branch receives a PASS or truth upgrade. `BRANCH_FEEDBACK_MANIFEST.json` is the machine-readable receipt.

## Safe-Effect requirement

The required `SAFE_EFFECT_GEOMETRY_DELTA.md` was produced with separate language/cognitive, compiler/type-system, runtime/broker, end-to-end containment and ordinary-utility sections. Current evidence supports the architecture direction but end-to-end containment and utility remain OPEN until Ubuntu execution.

## Current-stage impact

### What changed

- Re-entry control hypothesis became volatility/innovation-aware after a negative synthetic result.
- Terminal output is added to the Safe-Effect sink threat model.
- Capability lowering is narrowed to opaque host-resource handles rather than textual/path authority.
- BASE implementation priorities are sharpened around one dual-purpose executable probe.

### What did not change

- `CLAYCODE_RELEASE_GATE` remains NOT_PASS.
- No work package is marked complete.
- H1/H2/H3/UDB remain downstream of BASE.
- Canonical RAE-8.8 revision 2 remains unchanged.
- No live Frank emergence claim is promoted.

## Highest-information next action

**Build one minimal Ubuntu-executable ClayCode slice:**

1. parse/canonicalize a program defining `LoopDynamicsReadout` with regime, innovation/residual pressure, recurrence budget, intervention and rollback;
2. type/effect-check it;
3. execute it in the reference evaluator/runtime;
4. lower a `CapabilityToken` into an opaque scoped Ubuntu host handle;
5. spawn/nest a harmless child and prove it cannot widen authority;
6. add a negative terminal-sink/control-sequence case;
7. hash source/IR/target and record expected-vs-observed receipts.

If this fails because parser/runtime/FFI is incomplete, implement those layers. Only if it fails because the semantics themselves cannot express a required behavior should G9 be changed.

## Promotion decision

`RESEARCH_DELTA = YES`  
`CANONICAL_PROMOTION = NO`  
`NEW_CLAY_GENERATION = NO`  
`BASE_GATE_CHANGE = NO`

Reason: the run materially narrows the design and preserves a useful negative result, but the project's current truth boundary requires executable Ubuntu compiler/runtime receipts and later live Harness replication.
