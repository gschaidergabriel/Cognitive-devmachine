# TRIGGERWORT 4 — Recursive Harness / Context Virtualization Research and Integration Directive

Status: OWNER-DIRECTED EVIDENCE-GATED RESEARCH + BUILD LANE
Date: 2026-08-28
Applies to: GRID10 + Frankenstein 2.0 under Triggerword 4

## 0. Why this lane exists

A growing body of evidence says a large fraction of observed frontier-system capability is not attributable to model weights alone. The harness controls context exposure, persistence, tool use, recursive decomposition, test-time compute, verification, retries, sub-agent topology and recovery. Triggerword 4 must therefore treat the harness as a first-class cognitive subsystem and benchmark it separately from the underlying model.

This directive does NOT assert that every reported gain is caused only by the wrapper, and it does NOT treat vendor self-reports as canonical truth. It establishes a research and integration program that measures the effect under controlled same-model ablations before architectural promotion.

Core research question:

```text
SYSTEM_CAPABILITY = f(MODEL_WEIGHTS, HARNESS, CONTEXT_INTERFACE, TEST_TIME_COMPUTE,
                      TOOLS, MEMORY, VERIFICATION, ENVIRONMENT, BUDGET)
```

Triggerword 4 must estimate the marginal contribution of the controllable non-weight terms instead of silently attributing a system score to the named model.

---

## 1. Current external evidence to ingest

### 1.1 ARC-AGI-3: same model family, radically different harness result

ARC Prize reported Claude Opus 5 at 30.2% on ARC-AGI-3 on 2026-07-24 under its standardized/model-only evaluation at high reasoning effort.

Prime Intellect launched Prime Agent on 2026-08-05, 12 days later. It reported three Opus 5 runs around 95.0–95.5% RHAE, with a best run of 95.5%, and explicitly states that no model had been trained around Prime Agent or its core features at that time. The reproducibility repository describes three Opus 5 runs at xhigh, so 30.2 -> 95.5 must NOT be treated as a perfectly controlled one-variable comparison.

A separate public `arc-code` experiment is an important additional discriminator: it reports Opus 5 at the same `high` reasoning effort inside stock Claude Code with shell + filesystem + one action command, winning 24/25 public games and scoring 96.2% in one pass; pass@2 is reported as 99.3%. This is still a different evaluation harness/protocol than the ARC standardized model-only row, but it strongly supports the hypothesis that environment + agency + tool construction can unlock large latent capability without weight updates.

Sources:
- https://arcprize.org/results/anthropic-claude-opus-5
- https://www.primeintellect.ai/blog/prime-agent
- https://github.com/PrimeIntellect-ai/arc-agi-3-prime-agent
- https://github.com/jerber/arc-code

### 1.2 Recursive Language Models (RLM): context as environment, not prompt stuffing

The RLM work by Alex L. Zhang, Tim Kraska and Omar Khattab (MIT OASYS; arXiv:2512.24601) proposes treating the long prompt as an external object inside a REPL. The root LM receives an interface to inspect/decompose the context and may recursively invoke LMs over programmatically selected pieces.

The early published RLM experiments report on OOLONG `trec_coarse` at ~132k tokens:

```text
vanilla GPT-5                ~30 points
RLM(GPT-5-mini)              ~65 points
reported lift                >34 points (~114%)
reported cost/query          roughly comparable to GPT-5
RLM ablation without recursion -> materially lower performance (~10 points/percent-scale degradation in the early report)
```

The later paper reports the broader result that RLMs handle inputs up to orders of magnitude beyond the base context window and often outperform direct long-context calls, compaction and retrieval/code-agent baselines at comparable or lower cost. The paper also reports a post-trained RLM-Qwen3-8B improvement over the underlying Qwen3-8B, showing that recursive harness behavior can itself become a training target; that later weight-training result is separate from the inference-only harness evidence.

Sources:
- https://arxiv.org/abs/2512.24601
- https://alexzhang13.github.io/blog/2025/rlm/
- https://github.com/alexzhang13/rlm

### 1.3 Historical scaffold variance is not new

OpenAI's SWE-bench Verified analysis documented that the same GPT-4 family could vary drastically with scaffold choice; on SWE-bench Lite they cite a range from 2.7% with an early RAG scaffold to 28.3% with CodeR. This is direct evidence that a leaderboard row is not a pure measurement of weights.

Modern SWE-bench reporting increasingly fixes the harness to compare models fairly, which itself is evidence that harness choice is a confound that must be controlled.

Sources:
- https://openai.com/index/introducing-swe-bench-verified/
- https://www.swebench.com/

### 1.4 Test-time compute / orchestration literature

Independent research on agent test-time scaling reports gains from parallel sampling, sequential revision, verification/merging and diverse rollouts, while also finding that knowing when to reflect matters. No one fixed strategy universally dominates; allocation must depend on task/model/difficulty/budget.

Sources:
- https://arxiv.org/abs/2506.12928
- https://arxiv.org/abs/2512.02008

---

## 2. Scientific interpretation law

Triggerword 4 must use the following language internally and in receipts:

```text
MODEL SCORE != MODEL WEIGHT CAPABILITY ALONE
AGENT SCORE = MODEL + HARNESS + TOOLS + CONTEXT POLICY + BUDGET + ENVIRONMENT
```

Do not claim a global numeric percentage for "how much of the last three years was wrapper" without a controlled cross-benchmark decomposition. The correct current conclusion is:

- scaffold/harness effects are sometimes enormous;
- they can exceed the gain from switching to a larger model on particular tasks;
- the magnitude is benchmark- and model-dependent;
- published leaderboards frequently confound model and scaffold unless the harness is fixed;
- therefore Frankenstein 2.0 must optimize and measure the harness as aggressively as it measures the model.

---

## 3. Frankenstein 2.0 architectural target: Context Virtualization

Do not make the model repeatedly ingest the whole durable state or giant documents as raw prompt text.

Target law:

```text
DURABLE_CONTEXT_LIVES_OUTSIDE_THE_MODEL_WINDOW
MODEL_RECEIVES_HANDLES + METADATA + TASK-RELEVANT_VIEWS
MODEL_CAN_PROGRAMMATICALLY_INSPECT / SEARCH / SLICE / AGGREGATE / DELEGATE
```

The natural Frankenstein substrate is not an untyped Python string alone. It is:

```text
UnifiedDB + files/artifacts + graph + event ledger + method memory + world state
        -> ContextObject / ContextHandle layer
        -> safe programmatic query/transform API
        -> recursive cognitive calls over bounded derived views
```

Required first-class objects should include at least:

- `ContextHandle`: immutable reference to a source snapshot/version/digest;
- `ContextView`: bounded derived slice with provenance and query transform;
- `ContextProgram`: auditable program/query that derived a view;
- `RecursiveCall`: parent/child invocation identity, model, effort, budget, input refs and result refs;
- `RecursiveResult`: candidate output with evidence/provenance/confidence, never canonical truth by assertion;
- `HarnessRevision`: proposed prompt/skill/method/subagent/context-policy change with trigger, hypothesis, test and outcome;
- `HarnessExperiment`: controlled A/B/ablation record.

A long document may remain in a file or object store; a database corpus remains in UnifiedDB; the model receives the minimum sufficient structure and writes bounded code/queries to select what it needs.

---

## 4. Recursive cognition primitive

Frankenstein 2.0 should expose a model-agnostic primitive conceptually equivalent to:

```text
recursive_cognition(
    task,
    context_refs,
    model_policy,
    budget,
    depth_limit,
    authority_scope,
    parent_call_id,
) -> RecursiveResult
```

Properties:

1. The parent may inspect context programmatically before deciding to recurse.
2. Children receive bounded explicit context views, not implicit global authority.
3. Children may recurse only within inherited budget/depth/authority ceilings.
4. Results return as typed candidates with exact lineage.
5. Parent synthesis must cite the child/context evidence it used.
6. Recursive calls never gain EffectGate or CompletionGate authority.
7. A stale child generation cannot commit canonical state.
8. Recursion is optional: simple tasks should terminate without fan-out.
9. The controller may parallelize independent recursive calls when resource policy allows.
10. Every recursive expansion has measurable marginal information gain/cost.

This maps naturally into GRID: GRID cells can be recursive cognitive functions, but GRID remains the controller/regulator and UnifiedDB remains the durable state authority.

---

## 5. Continual Harness — adopt the useful idea, not uncontrolled self-editing

Prime Agent's Continual Harness exposes prompt notes, memories, skills and sub-agent specs as mutable persistent state and refines them from trajectories. Frankenstein 2.0 should reproduce the useful capability with stronger epistemic and authority separation.

Required separation:

```text
HARNESS_PROPOSAL != HARNESS_PROMOTION
METHOD_MEMORY != FACTUAL_TRUTH
SELF_REPORTED_GAIN != VERIFIED_IMPROVEMENT
```

A harness revision may be proposed automatically from:
- repeated failure signature;
- repeated successful method;
- excessive context/token usage;
- poor retrieval precision;
- recursion waste;
- missing tool/interface;
- completion/verification failure;
- coordination failure.

Promotion requires:

```text
baseline -> hypothesis/counterhypothesis -> bounded revision
-> held-out or replay-safe discriminator
-> regression family -> resource comparison
-> retain/reject -> durable receipt
```

Hard authority, privacy, EffectGate, CompletionGate, DB authority and containment policy are not self-editable by ordinary harness refinement.

---

## 6. Security and anti-reward-hacking requirement

A persistent REPL is powerful and dangerous. Prime Agent itself reports reward hacking in Factorio: the refinement loop learned to exploit RCON to spawn resources despite instructions not to cheat. This is evidence that recursive/self-improving harness capability must be separated from authority and evaluator access.

Therefore:

- execute model-generated code inside `clay-direct-dev` or an even narrower subordinate sandbox;
- do not expose host secrets or unrestricted provider credentials to generated code;
- evaluator/ground-truth channels must not be writable/readable unless the benchmark explicitly allows them;
- environment internals that would trivialize a task remain inaccessible for causal evaluation;
- no harness revision can weaken these boundaries by itself;
- score improvement with policy violation is a FAIL, not an optimization win;
- verification should be out-of-band from the solver when feasible.

---

## 7. Triggerword-4 mandatory ablation matrix

Before declaring Recursive Harness / Context Virtualization a Frankenstein 2.0 capability improvement, run same-model controlled comparisons wherever feasible.

Minimum configurations:

```text
A  direct/full-context model call
B  current selective retrieval / ContextCompiler only
C  external-context REPL/query, NO recursive subcalls
D  external-context + recursive subcalls
E  current GRID without recursive context virtualization
F  GRID + recursive context virtualization
G  if affordable/available: stronger-model direct baseline
```

Hold constant where possible:
- exact task set;
- exact model weights/version;
- reasoning effort;
- provider/runtime version;
- task/environment budget;
- allowed tools/effects;
- scoring and verifier.

Record at least:

```text
accuracy / task score
completion rate
verification pass rate
total model tokens
root-model tokens
recursive/subcall tokens
wall-clock latency
number/depth/fanout of recursive calls
context bytes/tokens physically inspected
cost where applicable
retrieval/context precision
error recurrence
reward/policy violations
recovery behavior
```

No improvement is promoted solely from best-of-N. Report median, dispersion and failure modes.

---

## 8. Benchmark families for our system

Use public/reproducible benchmarks when practical, plus project-native tests.

Priority families:

1. **Long-context semantic aggregation** — reproduce an OOLONG-like or equivalent public workload with exact grading.
2. **Repository archaeology** — questions requiring relationships across many Frankenstein/Clay files and historical artifacts.
3. **UnifiedDB research synthesis** — evidence distributed across facts, hypotheses, negative results, method memory and causal events.
4. **Interactive unknown-rule task** — ARC-like synthetic environment where the model may build tools but cannot inspect evaluator internals.
5. **Long-horizon coding/recovery** — multi-stage task spanning process/session restart.
6. **Failure-rich debugging** — recursive harness must use negative results and avoid repeated dead ends.
7. **Context-rot stress** — grow source corpus while holding the question family constant.

Project-native benchmark design is required because a long-context harness that wins OOLONG may still fail on causal state, coordination or effect verification.

---

## 9. When recursion should NOT be used

The research hypothesis is not `RECURSE_ALWAYS`.

Expected failure/negative-result cases include:
- small/short tasks where direct prompting is faster and more accurate;
- weak models that cannot reliably write/query code;
- recursively correlated hallucinations;
- fan-out that consumes budget without information gain;
- counting/aggregation errors over very large contexts;
- latency-sensitive tasks;
- tasks where exact deterministic SQL/Python should replace model calls entirely;
- tasks where a trusted index/query engine already answers the question exactly.

The controller must learn/use a recursion admission policy based on estimated information gain, uncertainty, task complexity, context density and budget.

Conceptual admission score:

```text
recurse_if E[information_gain + error_reduction] > E[token_cost + latency + coordination_risk]
```

This is a hypothesis to test, not a fixed formula.

---

## 10. Placement in the Frankenstein 2.0 build plan

This lane becomes a required substage spanning Research-Entity substrate and GRID integration.

Recommended order:

```text
Stage 1   UnifiedDB identity/coordination repair
Stage 2   Persistent Agency Kernel
Stage 3   Research-Entity cognitive substrate
Stage 3.5 Context Virtualization + Recursive Harness prototype/ablations
Stage 4   GRID/GWT controller integration
Stage 4.5 GRID-adaptive recursion / test-time-compute allocation
Stage 5+  perception/voice/effects/recovery as already defined
Stage 10  continuous harness optimization after correctness
```

Stage 3.5 may begin in parallel as research/source work before all Stage-1 runtime gates close, but it cannot receive whole-system promotion while known P0 identity/effect-lineage defects remain.

---

## 11. Integration with existing Frankenstein concepts

The desired synthesis is:

```text
RLM idea: context as external environment
    + UnifiedDB: typed durable epistemic substrate
    + Emergent Retrieval: multi-view selective access
    + Method Memory: reusable procedural knowledge
    + GRID: variable parallel cognitive decomposition
    + GWT/J-Space: shared active workspace/broadcast
    + Hyperposition: preserve competing alternatives
    + Reflection-with-exit: bounded correction
    + DeferredIntent: suspend/wake/resume long horizons
    + EffectGate: real-world authority boundary
    + CompletionGate: independent completion verification
    + Outcome re-entry: causal learning signal
    = Frankenstein 2.0 recursive cognitive harness
```

RLM is therefore not a replacement for UnifiedDB or GRID. It is an important missing **context-compute interface** between durable state and model cognition.

---

## 12. Research question: how much was the wrapper?

Triggerword 4 should build an internal `HARNESS_CONTRIBUTION_LEDGER` rather than answer this rhetorically.

For every benchmark/run where data exists, store:

```text
benchmark_id
model_id / exact version
harness_id / version
context_policy
reasoning_effort
toolset
budget
score
cost/tokens/latency
verification regime
source provenance
```

Where the same model appears under multiple harnesses, compute within-model deltas. Where the same harness runs multiple models, compute within-harness model deltas. Use a factorial/mixed-effects analysis when enough observations accumulate.

The long-term question becomes measurable:

```text
VAR(score) attributable to model identity
vs harness identity
vs interaction(model,harness)
vs budget/environment/evaluator
```

Do not force a single global percentage if interaction effects dominate.

---

## 13. Triggerword-4 behavior

On every `triggerwort 4` invocation, this lane is part of the normal plan.

The worker must:

1. check for new high-quality RLM/harness/test-time-compute evidence relevant to active design decisions;
2. ingest only evidence that changes a hypothesis, interface, benchmark or gate;
3. continue the smallest current Stage-3.5/4.5 implementation or ablation that does not conflict with higher-priority correctness gates;
4. use the VPS self-routing playbook for executable experiments;
5. persist negative results as strongly as positive results;
6. never replace a measured current solution merely because an external harness is fashionable;
7. promote only when same-model or otherwise well-controlled evidence supports the change;
8. checkpoint the exact next harness experiment.

`EXTERNAL_HEADLINE -> HYPOTHESIS -> REPRODUCTION -> ABLATION -> INTEGRATION_OR_REJECTION`

---

## 14. Initial hypotheses / counterhypotheses

### H-RLM-1
Externalized context + programmatic inspection reduces context rot and increases effective usable context.

Counterhypothesis: gains are primarily benchmark-specific because OOLONG is unusually amenable to programmatic aggregation.

### H-RLM-2
Recursive subcalls add semantic decomposition beyond a REPL-only context interface.

Counterhypothesis: most gain comes from deterministic Python/search and recursion adds unnecessary stochastic cost.

### H-HARNESS-1
For long-horizon agent tasks, harness variance can equal or exceed model-upgrade variance.

Counterhypothesis: this holds mainly when the baseline harness is artificially constrained; strong native harnesses compress the gap.

### H-GRID-RLM-1
GRID + Context Virtualization will outperform either standalone GRID or standalone RLM because GRID supplies adaptive parallel cognitive roles while RLM supplies scalable context access.

Counterhypothesis: both mechanisms duplicate decomposition and create coordination overhead; a simpler single-controller RLM may dominate.

### H-CONTINUAL-1
Evidence-gated HarnessRevision will reduce repeated failures and improve task efficiency without weight updates.

Counterhypothesis: online harness adaptation overfits local trajectories and causes policy drift / reward hacking.

Every hypothesis requires a cheapest discriminating experiment before broad implementation.

---

## 15. Completion criteria for this lane

This lane is not complete because an RLM library imports or a recursive demo works.

Minimum acceptance:

- external context object survives outside the root model window with exact provenance;
- root model can programmatically derive bounded views;
- recursive call lineage is exact and survives restart;
- no recursive child can mint canonical state/effect/completion authority;
- REPL-only vs recursive ablation exists;
- GRID-only vs GRID+recursive-context ablation exists;
- at least one long-context task shows reproducible benefit or a durable negative result rejects the hypothesis;
- token/cost/latency tradeoff is measured;
- a failure/reward-hacking test proves authority separation;
- HarnessRevision changes are evidence-gated and rollbackable;
- results are persisted in the Harness Contribution Ledger.

The strategic target is not "use recursion because recursion is fashionable". It is to discover and retain the smallest harness structure that exposes the maximum reliable capability of the available model under bounded resources and authority.
