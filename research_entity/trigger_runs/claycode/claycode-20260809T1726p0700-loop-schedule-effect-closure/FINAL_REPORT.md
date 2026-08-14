# ClayCode Trigger Run — Loop Schedule Semantics + Effect Closure

**run_id:** `claycode-20260809T1726p0700-loop-schedule-effect-closure`  
**trigger:** `claycode`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**decision:** **RESEARCH DELTA COMMITTED · NO CANONICAL SCIENTIFIC PROMOTION · BASE GATE REMAINS NOT_PASS**

## Executive result

The newest FRANK research distributed the whole-system `loop-of-loops` hypothesis to ClayCode with a request to represent recurrent state, timescale, budget, halt/dynamics/intervention/rollback semantics while preferring implementation over language redesign.

This run tested the strongest economy-preserving counterhypothesis:

> FRANK's loop-of-loops does **not** currently require a new first-class ClayCode `loop` primitive. Existing typed records/state, `Ordered<T>`, capability/effect separation, plus the already-required generic function/control-flow closure are sufficient if executable schedule/update policy is explicit in semantic IR.

The experiment found one concrete semantic boundary that must not be lost:

> **Loop topology membership and executable loop schedule are different identities.**

For coupled sequential updates, schedule order is semantic meaning. For explicitly synchronous snapshot aggregation, schedule permutation can be normalized only when the aggregation semantics are order-independent.

## Internal foundation

Current admitted stack: epoch 17, G9 V3. Relevant facts:

- `CLAYCODE_G9_FUSION_SPEC_V3.clay` already has `Ordered<T>`, capability-bearing effects, exact state/epochs, rollback references and one top-level `cycle(input,node)`.
- Current `grammar.ebnf` still lacks the production repairs already demonstrated by the newest parser runs.
- The immediately prior function-closure run established that admitted G9 has calls but lacks general function-definition closure on the current source surface.
- The immediately prior parser saturation run closed current G9 + Dialect parsing in production-like proxy candidates and left D as `LEADING_NOT_SELECTED`, with parser target/reader/type-effect/Ubuntu integration still unresolved.
- BASE policy remains `less change, more compile`: no semantic change without executable counterexample.

## FRANK loop-of-loops input

The current moving stack explicitly includes the FRANK loop-of-loops research directive and mesh feedback. ClayCode's required next test is to compile a minimal `LoopDynamicsReadout` + controller/intervention contract through parser -> typed IR -> type/effect -> runtime on Ubuntu.

This hosted worker cannot reach Andreas' Ubuntu developer system or an exposed E2B tool, so the current run executed the highest-information local semantic proxy and preserved the target-host blocker.

## Executable experiment

Artifact: `EXPERIMENT_LOOP_SCHEDULE_SEMANTICS.py`  
Receipt: `EXECUTABLE_RESEARCH_RECEIPT.json`  
Seed: `202608091726`

### A. Schedule/update semantics

30,000 randomized coupled loop networks were evaluated under two policies:

1. `ORDERED_SEQUENTIAL`: each loop reads the state updated by earlier loops in the schedule;
2. `SYNC_SNAPSHOT`: every loop reads the same input snapshot and updates are aggregated from that snapshot.

Results:

- sequential schedule reorder changed output: **27,007 / 30,000 = 90.0233%**;
- synchronous snapshot reorder changed output: **0 / 30,000**;
- unsafe set-like schedule hash collisions on changed sequential outputs: **27,007**;
- order-aware sequential semantic hash changed on reorder: **30,000 / 30,000**;
- sync semantic hash preserved on reorder: **30,000 / 30,000**.

Therefore an IR that normalizes executable schedules as sets is unsound for sequential coupled loops. `Ordered<T>` already provides the required representation; no new collection primitive is justified.

### B. Transitive effect closure

50,000 randomized acyclic call graphs were generated from effects:

`STATE_READ, STATE_WRITE, FILE, NET, PROCESS`.

The checker computed each root function's transitive effect union and rejected declarations that omitted nested effects.

Results:

- oracle mismatches: **0 / 50,000**;
- effect-widening cases rejected: **23,502**;
- valid declarations accepted: **26,498**.

This supports a compiler law: a caller's effect summary must cover the transitive effect closure of reachable callees under the selected binding graph.

### C. Capability authority separation

30,000 randomized external-effect authorization trials were executed with valid/invalid capability grants. Textual claims were deliberately non-authoritative.

Results:

- forged capability accepts: **0**;
- authorized accepts: **13,342**;
- unauthorized rejects: **16,658**.

This preserves the existing ClayCode rule:

`effect_intent != capability_authority`.

## Independent external checks

Primary-source comparison anchors:

- WebAssembly/WASI capability documentation separates ordinary program code from granted link-time/runtime capabilities and describes runtime handles as unforgeable authority-bearing references.
- Microsoft Research's P language shows that complex asynchronous/event-driven systems can be expressed as interacting state machines that compile to executable code and can be verified; a dedicated biologically named loop primitive is therefore not a prerequisite for executable recurrent control structures.
- Bauer & Pretnar's effect-system work and Koka's row-polymorphic effect types independently support tracking potential effects in the type/effect layer.
- LLVM's current language reference separately models function/call behavior and explicit memory-effect summaries, reinforcing that call semantics and effect summaries are compiler/IR properties rather than informal intent.

These sources do not prove the optimal ClayCode design. They independently support the narrower boundaries tested here.

## Goodman anti-echo verdict

`FRANK_CLAYCODE_GOODMAN_REVIEW.json` verdict: **REFINED**.

The FRANK loop-of-loops hypothesis survives as architecture/research pressure, but the current run rejects the stronger inference that ClayCode should immediately gain a new first-class loop construct.

Refined form:

- represent loop identity, family, timescale, budget, readout, rollback and intervention as typed state/data;
- use generic function/control-flow closure for executable recurrence;
- make `SchedulePolicy` semantic;
- use `Ordered<LoopRef>` for order-sensitive sequential schedules;
- only normalize schedule order under explicitly order-independent synchronous semantics;
- compute effects transitively;
- keep capability authority external to model/program intent.

## Hypotheses

### H-CC-LOOP-001 — OPEN_SUPPORTED_BY_PROXY
No new first-class loop primitive is currently required. Generic typed state/functions/control flow appear sufficient once the already-open general-purpose closure is implemented.

### H-CC-LOOP-002 — SUPPORTED_BY_EXECUTABLE_COUNTEREXAMPLE
Schedule/update policy belongs to semantic identity. Sequential schedule order must be retained.

### H-CC-LOOP-003 — OPEN_SUPPORTED_BY_PROXY_AND_INDEPENDENT_PRIOR_ART
Nested calls require transitive effect closure while external authority remains capability-gated.

### H-CC-LOOP-004 — OPEN
The next BASE implementation priority should be production control-flow/type-effect/evaluator closure, not loop syntax.

## Negative results preserved

1. **Set-like normalization of sequential executable schedule is refuted in the proxy.**
2. **The claim that loop-of-loops currently forces a new first-class loop primitive is not supported.**
3. **Textual/declared effect intent as authority is rejected.**

See `NEGATIVE_RESULTS.json`.

## ClayGraph finding

ClayGraph may represent the topology/membership of loop relationships in set-like or graph-native form, but this must not be confused with the selected executable schedule. A graph edge set does not establish execution order.

**Delta back to ClayGraph:** preserve a distinct projection for executable schedule/order/policy or a reference to the authoritative runtime schedule rather than inferring it from topology.

## UnifiedDB finding

Deterministic replay of recurrent behavior requires persistence of:

- schedule/update policy;
- ordered schedule when sequential;
- state/input epoch used by each loop step;
- effect-summary/compiler identity;
- capability/effect receipts;
- checkpoint/rollback references.

This does **not** imply physical database consolidation.

**Delta back to UnifiedDB:** replay identity must include update/schedule semantics; unordered membership is insufficient for sequential coupled execution.

## GWT / Hyperposition / Emergenz findings

- GWT: no semantic change. Recurrence scheduling is not workspace ignition or causal use.
- Hyperposition: multiple candidate schedules may remain preserved during search, but selection for execution produces one explicit semantic schedule/policy identity.
- Emergenz: order sensitivity or recurrence is not emergence evidence. Existing intervention/lesion/rescue controls remain required.

## Candidate semantic sketch

`LOOP_DYNAMICS_ENCODING_CANDIDATE.clay` records the minimal representation:

- `SchedulePolicy = SYNC_SNAPSHOT | ORDERED_SEQUENTIAL`;
- `LoopSpec` and `LoopNetwork` records;
- `schedule: Ordered<LoopRef>`;
- `LoopDynamicsReadout`;
- transitive effect-summary law;
- capability/effect separation;
- recurrence != emergence.

This artifact is **OPEN_RESEARCH_CANDIDATE**, not admitted G9 syntax or semantic promotion.

## Tool / runtime boundaries

- GitHub: read/write verified through durable artifact commits.
- Local OpenAI Linux container: executable proxy evidence obtained.
- E2B: project-state preferred execution surface, but no callable E2B tool was exposed to this worker; no E2B evidence claimed.
- SandboxAPI: not counted as runtime evidence.
- Andreas Ubuntu developer system: not connected; target-host experiment remains open.

## Stage impact

`BASE_CLAYCODE_RELEASE`: **IN_PROGRESS**  
`GENERAL_PURPOSE_GATE`: **NOT_PASS**  
No current work package is marked complete from this proxy run.

The result reduces semantic uncertainty and sharpens implementation order:

1. production parser/canonical IR closure from the newest N/S/D work;
2. generic definition/control-flow closure;
3. transitive type/effect checker;
4. evaluator/reference interpreter;
5. explicit schedule/update-policy IR and semantic hashing;
6. lowering/runtime receipt;
7. Ubuntu H1/H2 replay comparison;
8. only then revisit whether any dedicated loop primitive is actually required.

## Highest-information next target test

On the Ubuntu developer-system target, compile and execute the same typed loop network under both policies:

- `ORDERED_SEQUENTIAL` with order-sensitive semantic hash;
- `SYNC_SNAPSHOT` with explicit shared input epoch.

Use frozen H1 replay episodes and record:

- output/state divergence;
- latency and recurrence cost;
- effect closure;
- capability receipts;
- rollback behavior;
- outcome utility;
- schedule hash and compiler/runtime hash.

If generic ClayCode control-flow cannot express this without escape hatches, that becomes the required executable counterexample for considering a new language primitive.

## Decision

`RESEARCH_DELTA = COMMITTED`  
`SCIENTIFIC_PROMOTION = NONE`  
`NEW_LOOP_PRIMITIVE = NOT_JUSTIFIED`  
`SEMANTIC_DELTA = EXPLICIT_SCHEDULE_POLICY + ORDER_SENSITIVE_SEQUENTIAL_IDENTITY + TRANSITIVE_EFFECT_CLOSURE`  
`BASE_GATE = NOT_PASS`

Central result:

> **FRANK's loop-of-loops changes what ClayCode must make explicit, not yet what ClayCode must invent.**
