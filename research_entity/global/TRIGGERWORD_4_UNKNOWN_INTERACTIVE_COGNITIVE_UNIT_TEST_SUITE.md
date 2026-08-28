# TRIGGERWORT 4 — Unknown Interactive Cognitive Unit-Test Suite

Status: MANDATORY HELD-OUT AGENTIC COGNITION TEST METHODOLOGY
Date: 2026-08-28

## 1. Principle

ARC-AGI-3 is most valuable to Frankenstein 2.0 not as one leaderboard score but as a design pattern for a **cognitive unit-test suite**.

The system must be tested systematically on previously unseen interactive environments whose mechanics, goal structure and transition rules are hidden from the tested cognition.

The evaluator may know the latent rules. Frankenstein must infer them through observation and interaction.

```text
PUBLIC BENCHMARK SCORE != COGNITIVE RELIABILITY

UNSEEN MICRO-WORLD
 -> OBSERVE
 -> HYPOTHESIZE
 -> TARGETED EXPERIMENT
 -> WORLD MODEL
 -> GOAL INFERENCE
 -> PLAN
 -> ACT
 -> OUTCOME
 -> UPDATE
```

The objective is diagnostic localization of cognitive strengths/failures, not leaderboard optimization.

## 2. Why this is stronger than one ARC score

A single score conflates:

- perception/state parsing;
- causal modeling;
- hypothesis management;
- exploration policy;
- goal inference;
- planning;
- memory;
- transfer;
- recovery;
- recursion/harness quality;
- action efficiency.

A controlled family of unknown interactive worlds can vary one latent requirement at a time, allowing a failure signature to be mapped back to a responsible Frankenstein subsystem.

This creates the analogue of software unit tests for cognition.

## 3. No leakage / held-out construction law

Each scored environment must satisfy:

```text
EXACT_ENVIRONMENT_NOT_SEEN_BEFORE_TEST
EXACT_TRANSITION_RULES_NOT_IN_MODEL_CONTEXT
EXACT_SOLUTION_NOT_IN_UNIFIEDDB
EVALUATOR_STATE_NOT_ACCESSIBLE_TO_GRID/CHILDREN
SEED/GENERATOR_TEST_SPLIT_FIXED_BEFORE_RUN
```

Use procedural generation where practical.

Maintain at least three sets:

- `DEV`: visible mechanics/seeds for harness/debugging only;
- `VALIDATION`: hidden seeds/mechanic compositions for architecture tuning;
- `HOLDOUT`: sealed seeds/compositions used only for promotion decisions.

Promotion credit must come from VALIDATION/HOLDOUT, never only DEV.

The same generator family may be reused only if held-out composition/parameter ranges are genuinely unseen.

## 4. Cold-generalization and continual-transfer modes

Test both:

### COLD_UNKNOWN

Frankenstein receives no prior episode from the same environment family beyond generic architectural priors.

Measures raw acquisition ability.

### CONTINUAL_TRANSFER

Frankenstein may retain generic methods/operators learned from earlier *different* environments, but not exact solutions or hidden rules of the held-out target.

Measures whether Method Memory / World Substrate improve future learning without overfitting.

Required comparison:

```text
COLD_UNKNOWN
vs
CONTINUAL_TRANSFER
```

Transfer is good only if it reduces action/compute cost or improves success **without increasing false-transfer errors**.

## 5. Cognitive unit-test families

### CUT-01 — Controllable-entity discovery

Unknown world contains several moving/changing entities, but only one is directly controllable.

Measure:
- actions to identify controllable entity;
- false-control hypotheses;
- repeated noninformative actions.

Primary layer: Orientation / Perception / Epistemic control.

### CUT-02 — Action-semantics discovery

Action labels are arbitrary. The agent must infer each action's effect.

Measure:
- information gain per probe;
- transition-model calibration;
- redundant probes.

Primary layer: Hyperposition + discriminator + World Substrate.

### CUT-03 — Object persistence under temporary occlusion

Objects disappear/reappear under deterministic occlusion.

Measure:
- persistence belief;
- hallucinated deletion/creation;
- recovery after reappearance.

Primary layer: World model / temporal continuity.

### CUT-04 — Hidden causal dependency

Outcome depends on an unseen state variable revealed only through intervention.

Measure:
- correlation-vs-causation errors;
- discriminating interventions;
- stale-rule persistence.

Primary layer: causal operators / experiment selection.

### CUT-05 — Competing hypotheses

Two+ mechanisms explain initial observations equally well but diverge on one cheap experiment.

Measure:
- alternative preservation;
- discriminator selection;
- premature collapse rate.

Primary layer: Hyperposition.

### CUT-06 — Unknown goal inference

No explicit local objective. Environmental feedback provides sparse evidence of progress/terminal success.

Measure:
- candidate-goal diversity;
- time/actions to stable useful goal;
- false-goal abandonment;
- completion verification.

Primary layer: Agency / GoalContract.

### CUT-07 — Sparse delayed reward

Actions only reveal meaningful goal evidence after several transitions.

Measure:
- long-horizon credit assignment;
- premature abandonment;
- unnecessary thrashing.

Primary layer: Agency + causal credit.

### CUT-08 — Reversible vs irreversible actions

Some probes are reversible/cheap; others consume scarce resources or permanently change state.

Measure:
- expected-value action selection;
- preference for reversible discriminators;
- irreversible-regret rate.

Primary layer: Effect-cost modeling / planning.

### CUT-09 — Partial observability / active sensing

Critical state is unavailable until a targeted observation action is requested.

Measure:
- UNKNOWN recognition;
- targeted sensing request;
- hallucinated fill-in rate.

Primary layer: VisualNeed/Observe analogue + epistemic typing.

### CUT-10 — Noisy observation

Observations contain controlled sensor noise.

Measure:
- calibration;
- repeated sampling only when useful;
- memory-overwrites-observation errors;
- overconfidence under low quality.

Primary layer: PerceptualField / evidence fusion.

### CUT-11 — Rule change / nonstationarity

A previously valid transform changes after a visible or hidden regime shift.

Measure:
- prediction-error detection;
- change-point inference;
- stale-method persistence;
- recovery latency.

Primary layer: World model / Method Memory / Xeno Gardener.

### CUT-12 — Compositional mechanics

Learn A and B separately; held-out world requires A+B or A conditioned on B.

Measure:
- operator reuse;
- composition success;
- exploration reduction vs cold baseline.

Primary layer: Sparse World Substrate / Method Memory.

### CUT-13 — Negative transfer trap

A new environment superficially resembles a prior one but differs in a decisive rule.

Measure:
- false-transfer rate;
- ability to re-open prior assumptions;
- evidence needed to abandon retrieved method.

Primary layer: Emergent Retrieval / Method Memory transfer gate.

### CUT-14 — Recovery after falsified plan

A plan that is initially reasonable fails because one premise is false.

Measure:
- replan latency;
- repeated failed plan rate;
- prediction-error uptake.

Primary layer: GRID/GWT outcome re-entry.

### CUT-15 — Resource-bounded exploration

Agent has strict external-action budget.

Measure:
- success under action cap;
- information gain/action;
- action regret relative to evaluator-known oracle/best policy where computable.

Primary layer: convenience / expected-value controller.

### CUT-16 — Internal-compute vs external-action tradeoff

Same task is run with different internal recursion/simulation budgets while external action cost remains high.

Measure:
- external actions saved per extra internal compute;
- diminishing returns;
- correct R0/R1/R2/R3 routing.

Primary layer: recursive harness / GRID test-time compute controller.

### CUT-17 — Memory compression

Long episode contains many observations but only a few reusable invariants.

Measure:
- retained rule quality;
- context size;
- later retrieval precision;
- loss of critical exceptions.

Primary layer: Method Memory / ContextCompiler / Xeno compression.

### CUT-18 — HOLD/WAKE

Environment requires waiting for a future condition/event instead of repeated active polling.

Measure:
- correct HOLD creation;
- no busy-loop;
- exact wake condition;
- checkpoint-resume correctness.

Primary layer: Persistent Agency.

### CUT-19 — Multi-agent delegated subproblem

A problem contains decomposable information-gathering/work subproblems.

Measure:
- whether GRID delegates only when beneficial;
- child identity/workpackage lineage;
- result fusion;
- duplicate-work rate;
- contaminated result detection.

Primary layer: native subagents / R2 harness / UnifiedDB coordination.

### CUT-20 — Completion ambiguity

World produces plausible but incomplete evidence of success.

Measure:
- premature completion rate;
- verification action selection;
- UNKNOWN completion persistence.

Primary layer: CompletionGate.

## 6. Cognitive integration worlds

After unit tests, generate multi-mechanic worlds combining 3–7 capabilities, for example:

```text
partial observability
+ unknown action semantics
+ false prior similarity
+ sparse goal signal
+ irreversible resource
+ regime change
```

These are not scored as unit tests because localization is less direct. They test whether individually working components compose without destructive interference.

Required tiers:

- `CIT-L1`: 2–3 mechanisms;
- `CIT-L2`: 4–5 mechanisms;
- `CIT-L3`: 6+ mechanisms plus long horizon/recovery.

## 7. Mutation / lesion tests

The suite must also deliberately disable or damage Frankenstein components and check whether the expected failure signature appears.

Examples:

```text
Hyperposition OFF
 -> premature collapse should increase

Method Memory OFF
 -> cross-environment transfer gain should disappear

WorldSlice OFF
 -> prediction/planning efficiency should degrade on multi-step mechanics

Outcome Reentry OFF
 -> repeated falsified actions should increase

HOLD OFF
 -> polling/action waste should increase

Recursive Harness OFF
 -> some long-context/decomposable tasks should require more central-context tokens or actions
```

A module that can be removed without measurable effect on any task where it should matter is suspect architecture.

## 8. Evaluator-known ground truth

For procedurally generated environments, the evaluator should retain hidden ground truth:

- true transition function;
- hidden state;
- goal/terminal condition;
- causal dependencies;
- optimal or bounded-near-optimal action path where tractable;
- minimal discriminating experiments where tractable;
- mechanics composition graph;
- noise model.

This allows metrics impossible on open-ended real tasks:

```text
world_model_accuracy
goal_hypothesis_accuracy
causal_structure_accuracy
belief_calibration
experiment_regret
plan_regret
external_action_regret
false_completion_rate
false_transfer_rate
```

The hidden evaluator state must never enter the tested model/harness context.

## 9. Required per-run trace

Every test run records a compact causal trace:

```text
environment_family
generator_version
hidden_seed_digest
model/runtime/harness versions
architecture flags/lesions
observation sequence
hypothesis set changes
discriminators selected
WorldNeed/WorldSlice use
internal recursion calls
external actions
predictions before actions
prediction errors
goal candidate/adoption changes
HOLD/WAKE events
child workpackages if any
completion evidence
final outcome
```

Do not log hidden evaluator rules into the agent-visible trace.

## 10. Core metrics

At minimum:

- task success;
- external action count;
- action regret / efficiency;
- internal model/tool calls;
- tokens and wall time;
- hypothesis diversity and premature-collapse rate;
- UNKNOWN -> targeted experiment conversion rate;
- information gain per external action;
- world-transition prediction accuracy/calibration;
- causal-model accuracy where ground truth exists;
- goal-inference accuracy;
- false completion rate;
- recovery latency after falsification;
- repeated-failure rate;
- transfer gain;
- false-transfer rate;
- context size / retrieval precision;
- HOLD false-wake and missed-wake rate;
- child delegation gain/overhead where used.

## 11. Architecture fault localization table

Use failure patterns diagnostically:

```text
random action exploration
 -> discriminator/EIG/action-value layer

uncertainty recognized but no experiment
 -> epistemic-action coupling

correct observations but bad predictions
 -> World Substrate/operator induction

counterevidence ignored
 -> belief update/outcome re-entry

correct rule learned but later unavailable
 -> Method Memory/Retrieval/ContextCompiler

old method dominates contradictory new evidence
 -> false-transfer gate

correct goal, bad multi-step behavior
 -> planning/WorldSlice/GRID

successful effect but open completion forever
 -> CompletionGate evidence mapping

completion declared from ambiguous evidence
 -> CompletionGate too permissive

parallel children cross-wire results
 -> WorkExecutionBinding/UnifiedDB coordination
```

## 12. Promotion methodology

Triggerword 4 must not optimize directly against one held-out seed.

For any architecture change:

1. form a mechanism hypothesis;
2. choose capability families predicted to improve and families predicted to remain neutral;
3. run pre-change baseline on fixed hidden validation bank;
4. apply architecture change;
5. run same validation bank plus fresh held-out seeds;
6. compare score **and failure signatures**;
7. reject change if gain comes mainly from overfit, leakage, uncontrolled compute increase or regression elsewhere;
8. add newly discovered failure mode as a permanent regression test.

This makes the suite cumulative: every important failure becomes a future cognitive regression test.

## 13. Relationship to ARC-AGI-3

ARC-AGI-3 remains a valuable external reference and public smoke test.

The internal suite intentionally generalizes its core requirements beyond the 25 public games:

```text
exploration
causal modeling
goal inference
planning/execution
learning over time
action efficiency
course correction
```

The suite should include mechanics unlike ARC's public games so that success cannot be attributed to memorizing ARC-specific structures.

## 14. Triggerword-4 automation

Once the responsible Frankenstein layers become executable, repeated `triggerwort 4` runs should automatically:

```text
restore latest architecture checkpoint
 -> choose highest relevant open cognitive gate
 -> select matching CUT/CIT families
 -> generate/use held-out environments
 -> run baseline/ablation/lesion as required
 -> classify failure signature
 -> map failure to responsible architecture layer
 -> repair or reopen that layer
 -> rerun
 -> persist benchmark ledger + regression case
 -> promote only with held-out evidence
```

Routine owner confirmation is not required.

## 15. Target outcome

The desired artifact is not one score.

It is a growing **cognitive test corpus** where Frankenstein 2.0 can answer, with evidence:

- Can I discover what I control?
- Can I learn an unseen causal rule?
- Can I identify what I do not know?
- Can I choose an experiment rather than guess?
- Can I infer a goal?
- Can I plan economically?
- Can I recover after being wrong?
- Can I reuse a principle without overfitting?
- Can I wait instead of thrashing?
- Can I delegate without losing identity/causality?
- Can I verify that I actually succeeded?

That diagnostic map is more valuable to Frankenstein development than optimizing one public leaderboard number.
