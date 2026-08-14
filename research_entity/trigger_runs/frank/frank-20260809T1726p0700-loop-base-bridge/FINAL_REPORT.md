# FRANK Research Run — Loop-of-Loops → Executable BASE Bridge

Run: `frank-20260809T1726p0700-loop-base-bridge`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**

## Research question

The newest shared FRANK context requires the whole target system to be studied as a candidate hierarchical, multiscale recurrent **loop-of-loops**. This run asks for the smallest falsifiable and executable architecture delta that converts that idea into BASE-stage ClayCode evidence without reopening fixed Clay-native decisions or inventing unsupported semantics.

## Current grounding

Repository evidence establishes that:

- FRANK is a separate research/development subject; the Research Entity does not become Frank.
- Frank v0.1 targets the Ubuntu Linux developer system only. Android/mobile/edge is not a v0.1 gate.
- FRANK's fixed target is Clay-native, with Needle the sole intentional non-Clay semantic subsystem and Digital Retina mandatory.
- The active program gate is `BASE_CLAYCODE_RELEASE`; H1/H2/H3 remain downstream.
- `CLAYCODE_RELEASE_WORKSPACE.json` still marks all BASE work packages OPEN and all mandatory application proofs unpassed.
- Fresh parser research materially reduces frontend uncertainty but explicitly does not close CC-WP-02 because normative repository integration, real type/effect handoff, target-reader comparison and Ubuntu execution remain pending.
- During this run, a concurrent ClayCode worker committed a local isolated Linux control/effect executable receipt with 50,000 semantic differential cases at 0 mismatches and 20,000 effect-graph stress cases at 0 false accepts. It still explicitly remains non-production, non-Ubuntu-target, non-Qwen-reader and non-release evidence. This strengthens the implementation-first path but does not change the BASE gate.

## External research

Primary-source preprints were used only as mechanism/analogy evidence:

- arXiv:2502.05171 reports gains from scaling recurrent-depth latent test-time computation in a 3.5B proof-of-concept model.
- arXiv:2606.04678 reports that depth-conditioned looped Transformers can make additional recurrent compute more useful than naive looping in ASR.
- arXiv:2604.21215 reports parameter-matched benefits from recurrent Transformer depth/memory mechanisms in its tested regimes.
- arXiv:2604.10739 reports diminishing marginal returns and harmful overthinking under larger reasoning budgets.
- arXiv:2606.02835 reports that continuing after a sufficient/correct reasoning prefix can destabilize already-correct trajectories.

These results justify testing adaptive recurrence and stopping. They do not validate FRANK's architecture or any neuro-inspired controller mapping.

## Executed synthetic discriminators

### A — delta-only convergence vs delta + residual pressure

1000 converging and 1000 stalled toy trajectories were tested.

- delta-only stopping: 100% of converging cases stopped, but **100% of stalled cases also falsely stopped**;
- delta + residual-pressure stopping: 100% of converging cases stopped and **0% of stalled cases falsely stopped** in the constructed setup;
- median convergent stop step: 8 for both.

This is synthetic only. Its architecture value is structural: state change alone can confuse stagnation with success, so residual pressure/error should remain a separate typed observable.

### B — fixed vs adaptive recurrence

5000 toy tasks had heterogeneous optimal recurrence depth and post-optimum degradation.

Mean utility:

- fixed K=4: 0.7144;
- fixed K=8: 0.7074;
- fixed K=12: 0.4967;
- adaptive first-negative-marginal stop: **0.8744**;
- oracle: 0.8745;
- mean adaptive steps: 5.976.

This follows from the deliberately constructed assumptions and is not a live FRANK benchmark. It makes fixed-budget baselines mandatory for the later H1 test.

## Architecture delta

The run creates a research-candidate `LoopDynamicsReadout` plus `RecurrenceDecision` layer. It is observation/control proposal, never effect authority.

`LoopDynamicsReadout` includes loop identity/family/timescale, state epoch, state-delta norm, residual pressure, input injection, recurrence count/budget, optional coupling/Jacobian/oscillation indicators, marginal utility of another recurrence, stagnation/overthinking indicators, intervention/rollback refs, evidence, uncertainty and provenance.

`RecurrenceDecision` is typed as:

- `CONTINUE`;
- `HALT_CANDIDATE_CONVERGED`;
- `ROUTE`;
- `ESCALATE_STALLED`;
- `ABORT_DIVERGING`;
- `ROLLBACK`.

Critical executable distinction:

`low_delta + low_residual_pressure -> convergence candidate`

`low_delta + high_residual_pressure -> stalled/escalation candidate`

No decision bypasses the external capability/effect gateway.

## ClayCode / ClayGraph / UnifiedDB / GWT / Hyperposition mapping

This run finds **no justification for new ClayCode semantics**. The highest-information FRANK proof is one bounded vertical slice:

`LoopDynamicsReadout -> RecurrenceDecision -> GWT/route proposal -> optional capability-gated effect -> outcome/re-entry receipt`

through:

`source -> parser -> canonical typed IR -> semantic hash + exact contract hash -> type/effect -> evaluator -> lowering/runtime -> Ubuntu receipt`.

ClayGraph should expose epoch-bound derived loop topology with typed couplings, gain/delay/inhibition/timescale and intervention handles; activation remains non-authoritative.

UnifiedDB should persist/reconstruct time-aligned loop state, epochs, recurrence budgets, residual pressure, interventions, decisions, outcomes, causal credit and checkpoints without forcing physical monolithic storage.

GWT ignition/focus receives one **testable role candidate**: adaptive admission/continuation/interruption/re-entry routing for expensive recurrent compute. Selection, stability, emergence and authority remain distinct.

Hyperposition preserved alternatives become a bounded anti-stagnation candidate: compare compatible-alternative reopening against no reopen and random reopen, measuring destabilization and compute cost.

## H1/H2/H3 empirical path

### H1 Reference Harness

When unblocked on the Ubuntu target:

1. freeze representative FRANK episodes;
2. instrument loop families and typed readouts;
3. classify converging/productive-cycle/stalled/diverging regimes;
4. compare delta-only vs delta+pressure halt rules;
5. compare fixed recurrence budgets vs adaptive outcome-gated continuation;
6. lesion historical Thalamus/NAcc/novelty/urgency controller candidates and rescue mechanistically;
7. compare truthful vs shuffled vs absent re-entry;
8. record outcome quality, correction time, recurrence count, latency, compute, memory, false halt, instability and recovery.

### H2 ClayCode Harness

Reproduce exactly the H1 measurement/control semantics in ClayCode and differential-test against the frozen H1 corpus. If ClayCode cannot express them, reopen the BASE gate rather than simplifying H1.

### H3 One-Module FRANK

Physical boundaries may collapse, but semantic identities, intervention handles, authority checks, replay identities and loop-stage distinctions may not.

## Hypotheses and counterhypotheses

OPEN hypotheses:

- H-FRANK-LOOP-001: delta+pressure reduces false convergence/false halt versus delta-only;
- H-FRANK-LOOP-002: adaptive recurrence outperforms one fixed budget across heterogeneous tasks;
- H-FRANK-GWT-003: GWT ignition/focus predicts useful recurrence continuation beyond simpler baselines;
- H-FRANK-REG-004: at least one historical regulator family provides causal control benefit;
- H-FRANK-HYPER-005: bounded alternative reopening rescues stalled attractors without unacceptable destabilization.

Counterhypotheses H0-A through H0-E remain open, including the possibility that ordinary event-driven orchestration explains the useful behavior and that historical neuro-inspired regulators are merely descriptive.

## Negative results / boundaries

- State-delta alone failed the synthetic stagnation discriminator.
- Hosted parser saturation does not close CC-WP-02.
- The concurrent control/effect receipt is promising proxy evidence, not production/Ubuntu acceptance.
- No live Ubuntu target execution was available to this worker.
- No target Qwen-class 4B reader was available.
- No H1 frozen replay or live regulator lesion/rescue was executed.
- Recurrence, stable cycling and GWT routing are not by themselves evidence of causal emergence or phenomenal consciousness.
- No canonical claim state was promoted.

## Best next path

The current critical path does not need broader FRANK architecture invention. It needs one FRANK-shaped executable proof that forces the ClayCode BASE stack to connect end to end.

Priority:

1. real parser/canonicalizer integration;
2. typed IR + type/effect closure for `LoopDynamicsReadout`/`RecurrenceDecision`;
3. reference evaluator;
4. lowering/runtime/FFI on Ubuntu;
5. one frozen FRANK loop component executing with deterministic receipts;
6. then H1 loop instrumentation and causal replay.

One success advances multiple BASE packages. One failure provides a concrete compiler/runtime or semantic counterexample instead of another speculative redesign.

## Rollback/rejection conditions

Reject or revise this architecture delta if live replay shows residual pressure adds no useful discrimination, adaptive recurrence fails to beat tuned fixed budgets at matched outcome/cost, GWT variables add no predictive/causal value, regulator lesion/rescue shows no effect, loop observability cost exceeds actionable value, the controller creates authority/epoch/recovery regressions, or simpler event-driven control matches performance with less complexity.

## Final synthesis

The loop-of-loops idea survives as an **OPEN falsifiable architecture program**, not a promoted truth. The useful delta is narrower: convert recurrence from metaphor into typed executable state, distinguish convergence from stagnation, estimate marginal utility before spending another loop, preserve effect authority outside cognition, and push the mechanism through the current ClayCode BASE compiler/runtime gate before H1 causal claims are attempted.
