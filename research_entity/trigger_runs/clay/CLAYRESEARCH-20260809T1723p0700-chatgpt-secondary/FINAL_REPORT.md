# CLAYRESEARCH Integrated Foundry — FINAL REPORT

Run ID: CLAYRESEARCH-20260809T1723p0700-chatgpt-secondary  
Actor: chatgpt-secondary / OpenAI GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346  
Program stage: BASE_CLAYCODE_RELEASE  
Scientific status: MATERIAL_OPEN_RESEARCH_DELTA  
Canonical promotion: NO

## 1. Executive result

The strongest cross-mesh delta is a sharper architecture hypothesis:

> FRANK should be modeled and tested as a **heterogeneous typed loop-of-loops recurrent dynamical system**, not as one monolithic reasoning loop and not as a synonym for chain-of-thought.

The loops are allowed to have different states, rates, delays, persistence, budgets and stopping conditions. Their higher-order behavior may arise from coupling, but every causal claim remains intervention-gated.

This does **not** imply that the current Qwen-class semantic kernel must itself become a looped/recurrent-depth neural architecture now. FRANK-level recurrence and model-internal recurrence are separate design axes. The current BASE program should implement/compile FRANK recurrence around a conventional model adapter first; looped/recurrent-depth model architectures become a later comparative optimization track.

The second strong result is a stage constraint: current ClayCode governance already says `preserve semantics -> freeze -> compile/lower -> execute -> test`. Therefore this run does not propose a syntax redesign. It proposes a concrete recurrent FRANK exemplar as a compiler counterexample test. Only missing semantics discovered by that executable exemplar may justify new IR fields or language changes.

## 2. Grounding and contradiction map

### Current internal evidence

- The first-principles coupling lens already treats FRANK as multi-timescale recurrent coupling among state variables, gates, feedback, memory, reward/resource constraints and timing.
- Current ClayCode requirements already include recurrent/re-entry loops, causal/dependency edges, multiple timescales, persistent epochs, intervention points and authority boundaries.
- Historical G2 ClayCode material already encoded a typed GWT sequence `COMPETE -> IGNITE -> BROADCAST -> RECONSTRUCT -> EFFECT -> OUTCOME -> REENTER`, plus parser/validator/compiler/fuzz scaffolding. This is prior engineering evidence, not current BASE PASS.
- The current BASE workspace still records 14/14 work packages OPEN and zero accepted application exemplars. Therefore strict stage progress remains 0 until execution receipts update the gate.
- The fresh same-day Emergenz branch report proposes a multi-axis `EmergenceEvidenceBundle`, PEID escalation, provenance-bound re-entry controls, n-ary parity fixtures, lag-resolved coupling, and H1/H2/H3 transfer. It is LOCAL_REPORT_ONLY / SYNC_PENDING and is imported here as OPEN branch evidence, not canonical truth.

### Main contradiction resolved

`FRANK is a complex loop system` and `looped LLMs can reason in latent recurrence` are compatible but non-identical claims.

- FRANK recurrence = architecture/runtime state transitions among organs/assemblies over multiple timescales.
- Model recurrence = repeated application of neural layers/latent state within one model inference.
- CoT = text-mediated reasoning trajectory.

The system can use the first without requiring the second or third. Later experiments can combine them.

## 3. External research synthesis

Primary research on looped/recurrent-depth language models supports treating recurrence as an independent compute axis. Ouro (arXiv:2510.25741) reports iterative latent computation and learned depth allocation; recurrent-depth controlled studies (arXiv:2604.07822) report improved systematic/depth generalization and explicitly identify overthinking when recurrence is excessive. A 2026 halting analysis (arXiv:2607.20519) finds learned exit gates can entangle trajectory formation with stopping and that simple post-hoc readouts can sometimes match or outperform learned gates. STARS (arXiv:2605.26733) explicitly targets fixed-point stability because LoopLM performance can peak and then degrade at excessive depth.

Google DeepMind's RecurrentGemma/Griffin provides independent implementation evidence that recurrent sequence processing can coexist with local attention and can target long-sequence memory/throughput characteristics. This is evidence for a future model-backbone comparison, not proof that RecurrentGemma-style recurrence is correct for FRANK.

For compiler/runtime optimization, the `egg`/egglog ecosystem provides a relevant analogy: e-graphs retain equivalent program forms and equality saturation can optimize without immediately choosing one representation. For Clay this is only an equivalence-optimization candidate; epistemic status, activation, causal necessity and execution authority must remain outside any equality relation.

For Safe-Effect, Wasmtime/WASI provides a concrete candidate enforcement substrate: filesystem/network access can be host-scoped/capability-mediated, and Wasmtime treats use of a WASI resource without its capability as a security fault class. Its own security documentation also highlights denial-of-service and terminal side-effect channels, so WASI is not equivalent to full Clay Safe-Effect closure.

Reddit/community search was attempted as required but produced no strong, directly relevant implementation evidence suitable for promotion; it was not used to support scientific claims.

## 4. First-generation hypothesis matrix

60 materially distinct falsifiable hypotheses were generated across recurrence, GWT, ClayCode, Hyperposition, Assemblies, ClayGraph, UnifiedDB, Safe-Effect, model architecture, emergence and governance.

See `HYPOTHESES_G1.md`.

Key families:
- heterogeneous timescale loops vs one global loop;
- adaptive/local halting vs fixed-depth recurrence;
- gain/delay sweeps and overcoupling;
- provenance-bound re-entry;
- event-driven incremental scheduling;
- causal GWT receiver closure;
- current-semantics-first ClayCode compilation;
- recurrence/resource identities in IR/runtime;
- n-ary-vs-pairwise higher-order reductions;
- versioned loop topology and event cursors;
- child-effect non-amplification and cumulative budgets;
- conventional-4B-first vs recurrent-model-later;
- intervention/transfer-based emergence measurement.

## 5. Empirical work

All four tests are synthetic instrument sanity checks. They are **not FRANK runtime evidence**.

### SYN-LOOP-HALT-001
Noisy mixed-difficulty scalar recurrence:
- adaptive local halt: mean 9.148 steps, p95 19, MSE 0.005444;
- fixed 12: MSE 0.016233;
- fixed 16: MSE 0.008343;
- fixed 24: MSE 0.002725;
- fixed 32: MSE 0.001116.

Interpretation: adaptive stopping occupied a useful accuracy/compute point and beat fixed-16 accuracy with substantially fewer mean steps, while longer fixed runs still achieved lower absolute error. This supports measuring Pareto fronts, not declaring one stopping policy universally best.

### SYN-MULTISCALE-002
Synthetic slow+fast latent process:
- best one-state EMA test MSE: 0.102789;
- two-timescale state test MSE: 0.095984;
- relative MSE improvement: 6.62%.

Interpretation: positive-control evidence that heterogeneous timescale state can matter when the environment truly contains heterogeneous dynamics. No FRANK percentage claim follows.

### SYN-INCREMENTAL-DAG-003
Sparse 10,000-node dependency DAG, 1,000 random source updates:
- mean affected nodes: 30.25;
- median: 2;
- p95: 64.05;
- full-sweep/mean-affected operation-count ratio: ~330.6x.

Interpretation: incremental scheduling can be enormous in sparse graphs, but actual FRANK affected-set density and maintenance overhead must be measured before speedup promotion.

### SYN-SAFE-EFFECT-004
100,000 random child-effect requests:
- ambient requested-effects baseline violated parent-subset in 93.4% of generated cases;
- explicit intersection broker: 0 subset violations;
- 93.4% requests were partially/fully rejected.

Interpretation: the non-amplification invariant is mechanically testable. This toy broker enforces it by construction; it does not establish compiler/FFI/OS completeness.

See `EXPERIMENT_RESULTS.json`.

## 6. Fusion 2 — transformed architecture

The 60 first-generation hypotheses compress into 14 higher-value transformed hypotheses in `HYPOTHESES_G2.md`.

The proposed executable architectural core is:

`event/input`  
`-> affected-loop discovery`  
`-> loop-local state update`  
`-> candidate/assembly competition`  
`-> bounded workspace`  
`-> transform/proposal`  
`-> deterministic authority/effect gate`  
`-> effect receipt/outcome`  
`-> provenance-bound re-entry`  
`-> dependency-triggered next loop updates`  
`-> local stability / global budget halt`

Each loop should be able to expose at least:
- `loop_state_id`;
- `epoch/cursor`;
- `timescale/rate`;
- `dependency/re-entry edges`;
- `delay/gain`;
- `budget`;
- `local halt/stability rule`;
- `cancellation/revocation state`;
- `intervention handle`;
- input/output/event provenance.

This is a **semantic contract candidate**. It should first be expressed with existing ClayCode constructs. New syntax is not warranted yet.

## 7. BASE-stage implementation consequence

Highest-information current-stage action:

**Compile one real frozen FRANK recurrent subsystem as a loop-of-loops exemplar before changing ClayCode semantics.**

The exemplar should force:
1. at least two different timescales;
2. one feedback/re-entry edge;
3. one delayed dependency;
4. one cancellation/restart path;
5. one UNKNOWN/CONFLICT path;
6. one effect proposal crossing the external gateway;
7. one duplicate/out-of-order replay;
8. one edge lesion and rescue;
9. deterministic canonical/source/target hashes;
10. no opaque host semantic escape.

If current ClayCode can compile/lower/execute this, recurrence is implementation work. If it cannot, the failing executable trace becomes the legitimate language-change counterexample.

This action directly advances CC-WP-02/03/04/05/06/07/09/11/13 rather than creating a new speculative branch.

## 8. Safe-Effect delta

Material delta: recurrent systems need **cumulative epoch budgets**, not only per-call capability checks. A loop can remain inside an allowed per-call effect yet cause damage by repetition.

Candidate recurrence-safe invariants:
- authority non-amplification across iterations;
- cumulative resource/effect budget per loop epoch;
- idempotent effect receipts across retries/restarts;
- revocation checked before every commit;
- child effects remain a subset of parent Clay contract;
- protected-state recoverability is not silently reduced.

See `SAFE_EFFECT_GEOMETRY_DELTA.md`.

## 9. Negative results / non-promotions

- No live FRANK loop benefit is established.
- No live Qwen-4B recurrent-model result was obtained.
- No current BASE application proof passed in this run.
- No claim that a looped neural model should replace the current 4B is promoted.
- No claim that e-graphs are ClayGraph or Hyperposition is promoted.
- No claim that WASI proves Safe-Effect closure is promoted.
- No single emergence scalar is recommended.
- No phenomenal-consciousness inference is supported.
- Current room hot-state paths expected from the repo-native protocol were not fetchable on this hosted surface; no JOIN/PULSE event was fabricated.
- Full repository provider-router orchestration was not executed; native web/GitHub/local-execution fallbacks were used and recorded.

## 10. Cross-branch feedback

Explicit deltas were generated for `clayresearch`, `frank`, `claycode`, `gwt`, `emergenz`, `hyperposition`, `claygraph`, `unifieddb`, `harness`.

See `BRANCH_FEEDBACK.md`.

## 11. Next discriminating experiments

1. BASE compiler counterexample: compile/execute the two-timescale recurrent FRANK exemplar above.
2. Frozen-model loop lesion: truthful/no/shuffled/provenance-broken/delayed re-entry with identical model outputs.
3. Real dependency-density trace: measure affected-set size before adopting incremental scheduling optimizations.
4. Coupling sweep: gain x delay x timescale with oscillation and utility readouts.
5. Ubuntu Safe-Effect child escape matrix: WASM + host-language subprocess, cumulative budgets, cancellation/restart, revocation and effect receipts.
6. Only after BASE/Harness evidence exists: matched conventional-4B vs looped/recurrent-depth model study.

## 12. Research decision

**OPEN research delta, durable run report warranted.**  
No canonical scientific generation/revision is justified by this run alone.

The key program decision is intentionally conservative:
**recognize FRANK's loop-of-loops semantics now; compile and measure it now; do not prematurely redesign ClayCode or the 4B model architecture.**
