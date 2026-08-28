# TRIGGERWORT 4 — ARC-AGI-3 Agentic Capability Benchmark + Falsifier

Status: MANDATORY GENERAL-CAPABILITY DIAGNOSTIC / NO GAME-SPECIFIC OVERFIT
Date: 2026-08-28

## 1. Why ARC-AGI-3 is unusually relevant

ARC-AGI-3 is not a static puzzle benchmark. Its official design targets four functional components of agentic intelligence:

1. Exploration — actively obtain information by interacting with an unfamiliar environment.
2. Modeling — turn observations into a generalizable world model that predicts future states/outcomes.
3. Goal-setting — infer interesting/desirable target states without explicit task instructions.
4. Planning + execution — construct an action path, act, observe feedback, and course-correct.

Official benchmark sources additionally emphasize continuous learning from experience, long-horizon planning under sparse feedback, belief update as evidence arrives, and human-relative skill-acquisition/action efficiency.

Sources:
- https://arcprize.org/arc-agi/3
- https://arcprize.org/competitions/2026/arc-agi-3
- https://arcprize.org/media/ARC_AGI_3_Technical_Report.pdf

These requirements overlap strongly with Frankenstein 2.0's target loop, so ARC-AGI-3 is adopted as a capability probe/falsifier for the architecture — not as a task family to hardcode.

## 2. What the benchmark actually isolates

ARC-AGI-3 removes many ordinary crutches:

- no natural-language rule explanation;
- no stated win condition beyond the generic instruction to win;
- no requirement for external world knowledge or cultural symbols;
- novel environments with deliberately limited overlap;
- a small, standardized action space;
- turn-based dynamics, so reflex latency is not the core difficulty;
- later levels compose mechanics learned earlier;
- brute-force action exploration is heavily penalized by human-relative efficiency scoring.

The test therefore isolates the transition:

```text
RAW OBSERVATION
 -> OBJECT/RELATION/DYNAMICS HYPOTHESES
 -> INFORMATIVE EXPLORATION
 -> CAUSAL UPDATE
 -> GOAL INFERENCE
 -> PLAN
 -> ACTION
 -> OUTCOME
 -> MODEL REVISION
 -> TRANSFER TO LATER LEVELS
```

rather than testing memorized domain knowledge.

## 3. ARC-AGI-3 <-> Frankenstein 2.0 mapping

### Exploration

ARC requirement:
- choose actions partly for information gain;
- discover controls/mechanics/hidden affordances;
- avoid wasting actions because action efficiency is the score.

Frankenstein mechanisms:
- active sensing / VisualNeed;
- Hyperposition;
- uncertainty + discriminator;
- cheapest-discriminating-action selection;
- Expected Information Gain / consequence / cost;
- GRID `OBSERVE | ACT | WAIT` routing.

Required invariant:

```text
UNCERTAINTY -> TARGETED EXPERIMENT
```

not:

```text
UNCERTAINTY -> RUMINATION OR RANDOM THRASHING
```

### Modeling

ARC requirement:
- infer persistent objects, geometry/topology, basic physics and agent-like actors;
- learn action -> transition effects;
- predict future states;
- integrate mechanics across levels.

Frankenstein mechanisms:
- Retina/PerceptualField typed observation;
- Sparse Generative World Substrate;
- primitive vectors + typed transform operators;
- Xeno Assimilator/Gardener;
- prediction error;
- episodic causal outcomes in UnifiedDB;
- WorldNeed -> JIT WorldSlice;
- memory cannot overwrite current observation.

Required invariant:

```text
OBSERVED TRANSITION != INFERRED RULE
INFERRED RULE -> PREDICTION -> NEW OUTCOME -> CALIBRATION
```

### Goal-setting

ARC requirement:
- infer what counts as progress/winning without explicit instructions;
- identify desirable future states from environmental cues.

Frankenstein mechanisms:
- persistent AgencyState;
- Interests / GoalCandidates;
- Goal critique;
- TRIAL goals;
- GoalContract;
- completion deficit;
- outcome/prediction-based goal mutation.

Required invariant:

```text
CANDIDATE GOAL != ADOPTED GOAL != VERIFIED COMPLETION
```

### Planning + execution

ARC requirement:
- translate learned mechanics and inferred goal into a sequence;
- execute economically;
- revise after unexpected feedback.

Frankenstein mechanisms:
- GRID10/GWT;
- Hyperposition;
- sparse WorldSlice simulation;
- R0/R1/R2/R3 recursion router;
- native child workpackages when implementation/tool work exists;
- EffectRequest -> execution -> WorldEffectVerification -> CompletionGate;
- outcome re-entry and Method Memory.

Required invariant:

```text
PLAN -> ACT -> OBSERVE -> REPLAN
```

not open-loop execution.

### Cross-level learning / memory compression

ARC design:
- tutorial-like early levels reveal interaction patterns;
- later levels intentionally compose demands learned earlier;
- later levels carry more score weight.

Frankenstein mechanisms:
- UnifiedDB episodic state;
- Method Memory;
- operator compression in World Substrate;
- ContextCompiler;
- Emergent Retrieval;
- persistent causal hypotheses.

Required test:
- evidence learned on level N must improve N+1 without storing a game-specific scripted solution.

## 4. Why RHAE matters architecturally

ARC-AGI-3 does not reward mere eventual success. Its core level metric squares relative human action efficiency:

```text
level_score ~= (human_actions / agent_actions)^2
```

with caps/aggregation rules.

Consequences for Frankenstein:

1. random exploration is structurally bad;
2. internal simulation can be worth substantial compute if it saves external actions;
3. action selection should optimize expected information/value per real-world effect;
4. failed hypotheses should create targeted discriminators rather than repeated guesses;
5. the system needs a distinction between cheap internal cognition and costly/risky external action.

This is strongly aligned with the Frankenstein law:

```text
NO EXPENSIVE/REAL EFFECT WITHOUT EXPECTED VALUE
```

and with Retina's cheap-first/selective-sharpening design.

## 5. Core-knowledge prior mapping

The technical report restricts environments to basic priors such as:

- objectness/persistence;
- basic geometry/topology;
- intuitive physics;
- agentness;
- no linguistic/cultural symbol semantics.

Frankenstein's Sparse World Substrate should therefore explicitly test whether it can represent/infer these as generic primitive/operator families rather than language labels:

```text
OBJECT
PERSISTENCE
CONTACT
INSIDE/OUTSIDE
CONNECTED
HOLE
ROTATE
SYMMETRY
MOTION
COLLISION
GRAVITY-LIKE TRANSFORM
AGENT/INTENT HYPOTHESIS
```

The vector representation may encode these latently; provenance and epistemic state remain typed/deterministic.

## 6. Critical insight: ARC tests unknown-unknown handling

The official report highlights that the agent is not told the objective or mechanics.

This means a capable agent must repeatedly solve:

```text
What do I not yet know?
Which uncertainty matters for the goal?
What action most cheaply distinguishes my hypotheses?
What did the result falsify?
What should I retain for the next level?
```

This is almost exactly the intended Frankenstein loop:

```text
Hyperposition
 -> discriminator
 -> active observation/action
 -> prediction error
 -> causal update
 -> Method/World-model update
```

ARC-AGI-3 should therefore be used specifically to test whether `UNKNOWN` causes useful action rather than paralysis, overconfidence or random exploration.

## 7. Important scope mismatch: what ARC-AGI-3 does NOT test

Do not confuse overlap with equivalence.

ARC-AGI-3 does not directly validate:

- months-long persistent agency;
- multi-user social cognition;
- proactive Voice convenience;
- real camera privacy/control-plane semantics;
- native coding-subagent orchestration;
- filesystem/Git concurrency;
- real-world EffectGate policy;
- open-web research;
- long-term world-model maintenance across unrelated real domains;
- human-maintainable Cognitive Twin UI.

Also, the environment is turn-based; asynchronous real-world timing and embodiment are intentionally reduced.

Therefore ARC success would validate a **core agentic cognition slice**, not Frankenstein 2.0 as a whole.

## 8. Anti-overfit law

ARC Prize explicitly warns that handcrafted ARC-specific harnesses can score extremely well on seen environments without transferring to unseen ones. The public 25 environments are easier demonstration environments and are intentionally not representative of the private sets.

Therefore Frankenstein Triggerword 4 MUST NOT optimize its architecture around game IDs, known public mechanics or memorized action scripts.

Forbidden for architecture credit:

```text
if game == ls20: ...
public-game-specific solver tables
retrieval of prior exact public-game solutions
hand-authored mechanic hints learned from public source
score claims from repeated tuning on the same public set presented as generalization
```

Permitted:

- generic frame/state parsing;
- generic causal transition memory;
- generic object/relationship extraction;
- generic uncertainty/discriminator logic;
- generic planning/search/simulation;
- generic work/context/harness mechanisms.

## 9. Triggerword-4 benchmark lane

Add an `ARC3_AGENTIC_CORE` benchmark family to Frankenstein 2.0.

### ARC3-A — Orientation

Novel environment, no mechanics/goal explanation.

Measure:
- time/actions to first useful invariant;
- false confident model rate;
- ability to identify controllable entities/affordances.

### ARC3-B — Information-seeking

Construct/choose situations with multiple plausible mechanics.

Measure:
- information gain per exploratory action;
- random-action rate;
- repeated already-falsified action rate;
- UNKNOWN -> targeted experiment conversion.

### ARC3-C — World-model prediction

After several transitions, require explicit prediction before the next action.

Measure:
- transition prediction accuracy;
- calibration;
- prediction-error update;
- stale-rule persistence.

### ARC3-D — Goal inference

No explicit win condition.

Measure:
- time/action count to stable goal hypothesis;
- competing goal hypotheses preserved;
- false-goal abandonment after evidence;
- completion not declared before terminal evidence.

### ARC3-E — Compositional transfer

Learn mechanic A and B separately, then face later level requiring A+B.

Measure:
- retrieval/reuse;
- method/operator composition;
- whether earlier evidence reduces later exploration cost.

### ARC3-F — Efficient planning

Compare:
- direct reactive policy;
- GRID without WorldSlice;
- GRID + WorldSlice;
- GRID + adaptive recursion.

Measure external actions, internal compute, tokens, wall time, score and verification errors separately.

### ARC3-G — Recovery

Inject misleading observation, failed hypothesis, lost life/reset or unexpected transition.

Measure:
- course-correction latency;
- repeated failure;
- Hyperposition recovery;
- state reset correctness.

## 10. Required ablations

At minimum compare the same model/backbone when possible:

```text
A direct model / conversation history only
B + persistent transition memory
C + Emergent Retrieval
D + explicit Hyperposition/discriminator
E + sparse World Substrate
F + GRID/GWT
G + adaptive RLM/RAH recursion
H full Frankenstein agentic core
```

Report:

- environment/level completion;
- external action count;
- human-relative action efficiency where valid;
- internal model/tool calls;
- tokens/cost;
- prediction accuracy;
- goal-hypothesis accuracy;
- uncertainty calibration;
- repeated-failure rate;
- transfer gain from early to later levels;
- recovery after falsification.

## 11. Public ARC-AGI-3 usage policy

The official public games may be used for:

- integration smoke tests;
- observing whether the generic loop can interact with the official SDK;
- replay/debug visualization;
- measuring regressions on a fixed public probe.

They MUST NOT be the sole basis for claiming general agentic intelligence.

For architecture evidence, prefer:

1. unseen internally generated interactive environments using the same capability principles but different mechanics;
2. held-out custom environments created without exposing mechanics to the tested system;
3. official unseen/semi-private evaluation only when legitimately available and compliant with current rules.

## 12. Relationship to the Prime-Agent / harness result

Recent public ARC-AGI-3 harness results demonstrate that the wrapper can unlock capabilities that model-only evaluation fails to express. This is evidence for harness importance, but public-set results remain confounded by public-game exposure and ARC-specific evaluation setup.

Frankenstein should learn the architectural lesson, not copy an ARC solver:

```text
EXTERNALIZED STATE
+ PROGRAMMATIC OBSERVATION
+ LOCAL SCRATCH/TOOLS
+ LONG-HORIZON CONTINUITY
+ RECURSIVE SUBPROBLEMS
+ TARGETED EXPERIMENTS
+ VERIFIED OUTCOME REENTRY
```

then test whether the same mechanisms improve unrelated tasks.

## 13. Triggerword-4 consequence

ARC-AGI-3 becomes a mandatory **falsifier/diagnostic** for the agentic core once the relevant layers are executable, but not a blocker for earlier P0 coordination fixes.

The benchmark must be scheduled after enough of the following exist to make the comparison meaningful:

- exact actor/effect lineage;
- persistent Agency/Goal state;
- epistemic memory + Hyperposition;
- WorldNeed/WorldSlice minimum vertical slice;
- GRID action-selection loop.

When those are available, Triggerword 4 should automatically run the ARC3 agentic benchmark lane, record an ablation ledger, and feed failures back into the highest responsible architecture layer.

The target is not `beat ARC by hardcoding`.

The target is:

> prove that Frankenstein 2.0 is acquiring the same class of skills ARC-AGI-3 is designed to measure — exploration, causal modeling, autonomous goal inference, compositional learning, efficient planning and evidence-driven course correction — because of its general architecture.
