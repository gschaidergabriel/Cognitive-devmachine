# CLAYRESEARCH Final Report — Loop-of-Loops Control Fusion

Run: `clayresearch-20260809T1653p0700-chatgpt-loopcontrol-fusion`  
Actor: chatgpt-secondary / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Moving stack: epoch 17  
Program stage: BASE ClayCode Release  
Operational target: Frank v0.1 on Andreas' Ubuntu Linux developer system only.

## Executive result

The distributed `FRANK as loop-of-loops` hypothesis survives integrated review, but the control model is refined materially.

The key new result is that **loop regulation cannot safely be reduced to convergence/stability alone**. A useful FRANK loop controller needs at least three separately typed signals:

1. **state-space dynamics** — delta, gain, coupling, periodicity, Jacobian/spectral proxies;
2. **residual problem pressure** — unresolved error, uncertainty, contradiction, failed effect, unmet commitment;
3. **marginal verified utility** — whether another recurrence is actually improving the task/outcome per cost.

This yields a stronger classification:

- low delta + low residual + non-degrading utility -> candidate successful convergence;
- low delta + high residual -> STALLED;
- bounded periodic trajectory + positive causal utility -> PRODUCTIVE_LIMIT_CYCLE;
- growing state/error/cost -> DIVERGING;
- numerically stable or converging state + falling task utility after a peak -> OVERTHINKING.

Therefore:

`numerical stability != cognitive usefulness`

and

`residual-aware convergence != sufficient halting rule`.

## Synthetic discriminating experiment

Five controlled traces were generated: convergence, stagnation, productive limit cycle, divergence, and numerically stable overthinking.

A delta-only halt rule falsely halted both convergence and stagnation. Adding residual pressure fixed that distinction, but still treated the numerically stable overthinking trace as successful convergence. Adding marginal utility separated `HALT_SUCCESS` from `HALT_OVERTHINKING` and identified the stalled trace for escalation.

This is synthetic mechanism evidence only, not FRANK runtime evidence.

## External research triangulation

Primary-source mechanism evidence supports the refinement:

- `Loop, Think, & Generalize` (arXiv:2604.07822): recurrent depth enables deeper test-time computation but excessive recurrence can degrade predictions through overthinking.
- `A Mechanistic Analysis of Looped Reasoning Language Models` (arXiv:2604.11791): looped models can approach cyclic fixed points and stabilize attention behavior; input injection and normalization affect these dynamics.
- `Parcae` (arXiv:2604.12946): looped LMs can be treated as nonlinear time-varying dynamical systems, with instability linked to injection-parameter spectral behavior; constrained injection improves stability.
- `Mixture-of-Recursions` (NeurIPS 2025 / arXiv:2507.10524): adaptive recursion routes different computation depth to different tokens and motivates stepwise adaptive compute allocation rather than uniform depth.

These papers support transfer of mathematical tools, not a claim that FRANK and a looped Transformer are the same mechanism.

## FRANK architecture implication

FRANK should continue to be studied as an OPEN candidate hierarchical/multiscale recurrent system, but its controller/readout plane should be explicitly tri-axis.

Historical readouts remain causal hypotheses:

- Thalamus gain -> possible route/loop gain;
- habituation -> possible anti-repetition damping;
- NAcc phasic/tonic -> possible short/long-horizon continuation utility;
- GWT ignition/focus -> possible expensive-compute admission/continuation routing;
- novelty -> possible stale-attractor escape;
- urgency -> possible recurrence budget/time pressure.

No neuro-inspired mapping is promoted without H1 lesion/rescue evidence.

## GWT / Emergenz implication

GWT should test adaptive recurrence admission/continuation using receiver causal-use and outcome utility, not broadcast alone. Emergence research must keep recurrence, stability, causal emergence and task utility separate.

A stable loop may be useless. A useful loop may be cyclic. A recurrent system may be complex without being emergent. Emergence claims still require interventions, lesion/rescue, shuffled/no re-entry, null models and transfer.

## Hyperposition implication

Preserved alternatives become a specific candidate anti-stagnation tool: reopen an evidence-supported alternative when a loop is `STALLED`, not merely because novelty is high. This must be compared against no-reopen and novelty-only controls because branch reopening can destabilize healthy convergence.

## ClayGraph implication

ClayGraph should expose loop phase/timescale/gain/delay/inhibition and tri-axis readouts as derived epoch-bound topology. Repeated recurrence must not inflate association into truth. Incremental projection remains preferred over global rebuild.

## UnifiedDB implication

UnifiedDB must support time-aligned reconstruction of loop state, residual pressure, verified utility, controller version, effect attempts, interventions and rollback/checkpoint identity. Logical semantic unification remains sufficient; loop research does not justify premature physical database consolidation.

## ClayCode / BASE implication

The immediate BASE task is not a new language generation. Existing semantics should first attempt to encode and execute:

`LoopDynamicsReadout`
`LoopControlDecision`
`RecurrenceBudget`
`HALT_SUCCESS | HALT_OVERTHINKING | ESCALATE_STALLED | CONTINUE | ROUTE_ALTERNATIVE`
`InterventionReceipt`
`RollbackRef`

with explicit separation between readout/control and effect authority.

The first required proof is a minimal parser -> canonical IR -> type/effect -> runtime execution on Ubuntu. Reopen language semantics only if that executable attempt exposes a genuine inadequacy.

## Safe-Effect Geometry delta

Recurrence introduces an additional safety dimension: repeated wrong or compromised intent can multiply effect attempts and resource cost even if the capability set does not widen.

New invariant candidate:

`recurrence budget must never imply capability widening`.

Every recurrent effect path should eventually expose attempt count, cumulative resource/cost budget, capability identity, retry reason and rollback identity.

Current Ubuntu evidence supports studying a layered confinement design:

- Linux Landlock can let unprivileged processes add restrictions and requires runtime ABI detection;
- Ubuntu AppArmor supplies per-program mandatory profiles and is loaded by default on Ubuntu;
- Sandlock (arXiv:2605.26298) is a recent AI-agent sandbox example separating static kernel-enforced policy from a narrow dynamic supervisor using Linux primitives and reversible effects.

This is implementation-direction evidence, not end-to-end FRANK containment evidence.

## Governance negative results

Two governance drifts remain open and block strong promotion from this run:

1. `research_interconnect_preflight.py` still uses `clay` in its explicit governance maps while the authoritative registry renamed the peer branch to `clayresearch`; its fail-closed guard therefore cannot pass current registry state.
2. `CLAY_RESEARCH_PROTOCOL.md` still contains stale text naming exact `clay` as the foundry trigger, describing an eight-branch mesh and requiring Android/edge cross-platform work. Current registry/stack and the Ubuntu target directive supersede those statements.

The run therefore uses a verified manual fail-closed interconnect manifest and makes **no strong promotion**.

## Hypothesis output

- 50 first-generation falsifiable hypotheses across GWT, FRANK, Emergenz, ClayCode, Hyperposition, ClayGraph, UnifiedDB, Harness, latency and Safe-Effect.
- 10 transformed second-generation hypotheses after external research.
- 4 preserved negative results, including delta-only and two-axis halting failures.

## Highest-information next experiment

On the Ubuntu H1 Reference Harness:

1. freeze representative episodes;
2. log typed state delta, residual pressure/error and verified outcome utility per material recurrence;
3. classify convergence / productive cycle / stalled / divergence / stable overthinking;
4. compare fixed depth, upfront predicted depth and stepwise adaptive continuation;
5. lesion historical candidate regulators independently;
6. rescue each lesion with the predicted regulator;
7. test truthful, shuffled and no re-entry;
8. keep capabilities fixed while recurrence budgets vary;
9. measure task success, correction latency, recurrence count, wall-time, CPU/GPU/RAM, effect-attempt count, false halt, false continue, protected-state damage and rollback success;
10. reproduce the same semantics in H2 ClayCode before any H3 consolidation claim.

## Research decision

`FRANK_LOOP_OF_LOOPS`: KEEP_OPEN_AND_REFINE  
`TRI_AXIS_LOOP_CONTROL`: PROMOTE_TO_SHARED_RESEARCH_REQUIREMENT, NOT RUNTIME TRUTH  
`NEW_CLAY_GENERATION`: NO  
`BASE_STAGE_ADVANCEMENT`: NO  
`ANDROID_MOBILE_EDGE_V0_1`: OUT_OF_SCOPE  
`NEXT`: executable Ubuntu ClayCode contract + H1 instrumentation after BASE prerequisites.
