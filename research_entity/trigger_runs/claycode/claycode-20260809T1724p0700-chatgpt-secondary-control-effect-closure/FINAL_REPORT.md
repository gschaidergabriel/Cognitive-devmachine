# ClayCode Trigger Run — Control-Flow + Effect Closure

**run_id:** `claycode-20260809T1724p0700-chatgpt-secondary-control-effect-closure`  
**trigger:** `claycode`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**decision:** **RESEARCH DELTA COMMITTED · NO SCIENTIFIC PROMOTION · BASE GATE REMAINS NOT_PASS**

## Executive result

The immediately preceding ClayCode wave already narrowed two major frontend problems:

1. production-like parser saturation now has executable N/S/D surface candidates and shared parser repairs, with D locally `LEADING_NOT_SELECTED` rather than promoted;
2. a minimal typed definition→call bridge executed 20,000 randomized composed calls with zero differential mismatches, but explicitly left branching, recursion, structured failure/pattern match and typed effect closure open.

This run therefore did not repeat parser or function-definition work. It attacked the next closure boundary:

> **Can ClayCode represent bounded recursive control and structured failure while computing function effects compositionally, without allowing effect declarations to become execution authority?**

A compact executable candidate was tested in the hosted Linux sandbox. In the tested proxy subset:

- 50,000 randomized branch + recursive-call + Result/match cases produced **0 differential mismatches** against a direct Python reference;
- 20,000 randomized effect-call-graph mutations produced **0 false accepts** after removing an actually inferred transitive effect from a caller declaration;
- an undeclared transitive effect failed closed;
- a statically valid effectful call with no runtime permit failed closed;
- the same call with the matching runtime permit succeeded;
- runaway recursion exceeded an explicit step budget and failed closed;
- an undefined static call failed closed.

The strongest current candidate law is:

```text
potential_effect_summary != runtime_effect_authority
```

and for recurrent FRANK/GWT execution:

```text
semantic/dependency lineage may continue
runtime effect authority does not automatically continue
```

This is a typed IR/type-effect/evaluator candidate, not a syntax promotion.

## Internal grounding and non-duplication

### Current BASE stage

The current stage is `BASE_CLAYCODE_RELEASE`. The target for Frank v0.1 is the Ubuntu Linux developer system. The project law is `less change, more compile`: existing semantics should be preserved unless an executable counterexample proves them insufficient.

### Parser wave

The latest production-like parser saturation run established executable N/S/D candidates across G9 + Dialect material after shared repairs including typed blocks, interface method signatures, `if`, comparisons and contextual identifier handling. D has the lowest measured migration cost in that local proxy, but target reader, normative compiler integration and Ubuntu execution remain missing. This run therefore does not select a surface dialect.

### Function closure wave

The preceding definition→call run showed a small typed function surface can close pure composed calls in a local proxy, but left control flow, recursion, structured errors, effects, lowering and Ubuntu execution open. This run consumes that boundary rather than duplicating it.

## Nine-branch mesh synthesis

`INTERCONNECT_MANIFEST.json` records all registered research foundations.

### FRANK

The current fused FRANK target is a multi-plane, multi-rate recurrent runtime whose logical components may later collapse physically but remain semantically testable. It already requires external effect authority. The present result therefore argues against a FRANK-specific recursion/effect primitive: ordinary general-purpose control and effect closure should be solved by ClayCode generically.

### ClayResearch

The latest synthetic Safe-Effect experiment produced 0/100,000 authority-amplification violations for capability intersection and 0/50,000 across nested delegation, while unsafe ambient/request-as-grant amplified in 99,866/100,000 cases. This is synthetic mechanism evidence, but it reinforces structural authority narrowing as the correct adversarial direction.

### ClayGraph

Associative activation may store or retrieve dependency/effect ancestry, but it must not resolve exact compiled function/effect authority. Exact typed compiler identity remains authoritative for closure.

### UnifiedDB

Program semantic identity and runtime permit/execution-attempt identity should remain separately representable. Nothing here requires physical database consolidation.

### GWT

Fresh R7 research separates workspace admission from recurrence continuation and explicitly sets `authority_carried_forward=false` through outcome/re-entry. The ClayCode candidate aligns with this: recurrence may preserve semantic decision/dependency ancestry while delayed effects revalidate current permission separately.

### Hyperposition

Set-valued alternatives may exist during research/search, but concrete compiled execution cannot treat fuzzy alternatives as authority. Effect execution is an explicit typed decision.

### Emergenz

Branching, recursion, universal computation or effect closure do not constitute emergence evidence.

### Harness

The latest H-WP-02 oracle candidate separates `semantic_state_hash`, `state_version_hash` and `trace_root_hash` and passes local idempotency/replay/stale-epoch regressions. This supports, within shared project ancestry, the analogous compiler separation between program semantic meaning and runtime attempt/permit identity.

### ClayCode

Route the current delta to `CC-WP-03-IR-TYPES`, `CC-WP-04-TYPE-EFFECT` and `CC-WP-05-EVALUATOR`, then into `CC-WP-06-COMPILER-LOWERING`. Do not mark any work package complete from this proxy alone.

## Independent external comparison

Three primary comparison anchors were checked. They are independent design references, not evidence that ClayCode should copy their syntax.

1. **WebAssembly Core Specification 3.0** — structured `block`/`loop`/`if` control and calls are explicit validated execution constructs. Transfer: structured control belongs to deterministic runtime semantics rather than model interpretation.
2. **LLVM Language Reference** — call/control semantics and memory-effect properties are explicit IR/compiler properties; call-site effects can be refined from function and call-site information. Transfer: effect information can be a compiler semantic property distinct from runtime environmental authority.
3. **Daan Leijen, Koka / row-polymorphic effect types (2014)** — potential side effects can be reflected in function types and inferred compositionally. Transfer: compositional function-effect summaries are a credible language design family, not a ClayCode-specific invention.

None of these sources proves the optimal ClayCode surface, authority model or target-reader efficiency.

## Executable experiment

Durable artifacts:

- `EXPERIMENT_CONTROL_EFFECT_CLOSURE.py`
- `EXECUTABLE_RESEARCH_RECEIPT.json`
- `HYPOTHESIS_MATRIX.json`
- `NEGATIVE_RESULTS.json`

Reproducer SHA-256:

`2cd3574914f37dc39910e303c1233e3cacaeebe24dcc9353e871733d8074301c`

Runtime evidence class:

`LOCAL_ISOLATED_LINUX_EXECUTION_NOT_TARGET_UBUNTU_ACCEPTANCE`

Seed: `202608091724`.

### Control-flow differential

The proxy implements:

- conditional branch;
- recursive call with explicit step budget;
- `Ok` / `Err` structured result;
- result matching;
- ordinary function composition.

Randomized cases: **50,000**.  
Differential mismatches: **0**.

### Transitive effect closure

Each function has:

- direct effects;
- call dependencies;
- declared potential-effect set.

The checker computes a fixed point over the call graph and requires inferred effects to be a subset of declared effects.

Randomized effect graph mutations: **20,000**.  
False accepts after deleting one actually inferred effect: **0**.  
Maximum fixed-point rounds observed: **2**.

### Authority adversarial test

A wrapper around `log.write` was statically effect-closed. Execution without a runtime permit containing `log.write` was rejected. The same call with the matching permit returned `7`.

Therefore, in this tested model:

```text
static effect validity != execution authorization
```

### Semantic identity

The candidate program semantic hash:

`c8e06e5f63adda1db0e55428205d43b2c92a47d5c65992ef6a9202dc39f1940e`

Observed invariants:

- set-order-equivalent effect representation -> same semantic hash;
- changed effect meaning -> changed semantic hash;
- changed control meaning -> changed semantic hash;
- runtime permit identity -> intentionally excluded from program semantic hash.

This is a candidate identity split, not a production hash contract.

## Goodman anti-echo review

Verdict: **REFINED**.

The FRANK-derived requirement for recurrent control plus external authority survives, but the architecture conclusion is narrowed:

- do not add a FRANK-specific control/effect primitive;
- do not treat recurrence or re-entry as authority inheritance;
- do implement ordinary control/effect semantics generically in canonical typed IR;
- do compute transitive potential-effect summaries compositionally;
- do keep runtime permission/capability validation separate and fail closed;
- do require fresh permission validation for delayed/recurrent effects.

The adversarial counterhypothesis — that a static effect summary can itself authorize execution — failed in the executable proxy.

## Hypotheses

The strongest open hypotheses are:

- `H-CC-CF-20260809-01`: existing G9 + typed IR control nodes can close branching/recursion/Result-match without a FRANK-specific primitive;
- `H-CC-EFF-20260809-02`: transitive fixed-point function-effect summaries provide the lowest-risk compositional effect closure;
- `H-CC-AUTH-20260809-03`: effect summaries and runtime authority must remain separate, including across recursion/re-entry;
- `H-CC-ID-20260809-04`: control/effect meaning belongs in program semantic identity, while permit/attempt identity belongs in contract/execution receipts.

All remain `OPEN`.

## Negative results

Preserved explicitly:

- `static effect summary = runtime authority` — negative in the tested proxy;
- `direct effects only are enough` — negative in the tested proxy;
- unbounded recursion is acceptable — negative in the tested proxy;
- local proxy closure is sufficient for BASE PASS — false.

## Architecture / implementation delta

Candidate compiler chain:

```text
source
 -> deterministic parse
 -> canonical typed control IR
 -> exact symbol/signature binding
 -> call graph
 -> transitive potential-effect fixed point
 -> declared-effect validation
 -> program semantic identity
 -> lowering contract
 -> executable artifact
 -> fresh external EffectPermit/capability validation
 -> effect
 -> execution/effect receipt
```

Hard boundaries:

```text
ClayGraph activation != symbol/effect authority
UnifiedDB proximity != symbol/effect authority
GWT selection/reentry != effect authority
model output != effect authority
static effect summary != runtime permit
program semantic hash != runtime attempt/permit identity
```

## Highest-information next tests

1. Integrate the smallest control/result/recursion/effect candidate into the production parser + canonical typed IR + type/effect checker rather than a side proxy.
2. Differentially lower the same corpus to the selected Ubuntu-native backend; optionally use WASM as an independent semantic shadow.
3. Add resource/effect polymorphism only if real application code demonstrates monomorphic summaries are too costly or inexpressive.
4. Execute capability revoke/regrant during delayed/recurrent calls and require fresh failure/success behavior.
5. Run FFI/subprocess/ambient-host escape fixtures; static ClayCode safety is insufficient if host paths bypass the gateway.
6. Feed compiler/effect semantic-oracle fixtures into Harness H2 preparation without changing the H1 gate.
7. Only after this closure is production-integrated, advance toward the CLI/HTTP/DB/concurrent/FRANK mandatory application proofs on the Ubuntu target.

## Decision

`RESEARCH_DELTA = COMMITTED`  
`SCIENTIFIC_PROMOTION = NONE`  
`CLAYCODE_SURFACE_PROMOTION = NONE`  
`CANDIDATE_DELTA = CONTROL_FLOW + TRANSITIVE_EFFECT_IR_CLOSURE`  
`AUTHORITY_LAW = EFFECT_SUMMARY != EFFECT_PERMIT`  
`ROUTE = BASE canonical IR + type/effect checker + evaluator + lowering`  
`BASE_GATE = NOT_PASS`

The main result is deliberately narrow:

> **ClayCode does not need more cognitive syntax to solve this gap yet. It needs executable, compositional control/effect semantics whose static meaning remains rigorously separate from runtime authority.**
