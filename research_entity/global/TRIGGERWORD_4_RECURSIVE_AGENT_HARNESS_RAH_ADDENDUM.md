# TRIGGERWORT 4 — Recursive Agent Harness (RAH) Addendum

Status: MANDATORY ADDENDUM TO THE RECURSIVE HARNESS / CONTEXT VIRTUALIZATION LANE
Date: 2026-08-28

## 1. New evidence: recurse the harness, not only the model

`Recursive Agent Harnesses` (Lumer, Sen, Paul, Subbiah; arXiv:2606.13643, 2026-06-11) studies a stronger recursion unit than the original RLM abstraction.

RLM recursion:

```text
parent LM -> recursive LM call over a selected context slice
```

RAH recursion:

```text
parent agent/harness
  -> executable orchestration code
  -> child agent harness(es)
       each with model + filesystem/tools + code execution + planning
       and the ability to recurse again within a depth bound
```

The paper reports a controlled long-context evaluation on Oolong-Synthetic, 199 samples across context buckets up to 4M tokens. With the GPT-5 backbone held fixed, the reported scores are:

```text
full-context baseline        59.22%
RLM                          64.38%
Codex-style coding agent     71.75%
RAH, GPT-5                   81.36%
RAH, Sonnet 4.5              89.77%   # different backbone, not same-model ablation
```

The fixed-GPT-5 comparison from 71.75% to 81.36% is especially relevant to Frankenstein because it isolates a material harness-architecture delta while keeping the named backbone fixed. Important limitation: the paper uses previously published baseline point estimates rather than a fully paired rerun of every baseline under one new harness execution; cost/latency/branch-depth data are also incomplete. Treat the result as strong but not final evidence.

Source:
- https://arxiv.org/abs/2606.13643

## 2. Frankenstein must distinguish three recursion levels

Do not collapse all recursion into the word `subagent`.

### R0 — deterministic data recursion

```text
SQL / Python / graph traversal / map-reduce / exact transforms
```

No model call when deterministic computation is sufficient.

### R1 — model recursion (RLM)

```text
root model -> bounded recursive model call(s) over derived ContextViews
```

Useful when semantic processing is needed over many pieces but a full harness is unnecessary.

### R2 — harness recursion (RAH)

```text
root cognitive harness -> child harness(es)
child = bounded tool/code/context/planning environment + recursive capability
```

Useful when subtasks themselves require tool use, local state, iterative search, tests or multi-step work.

### R3 — GRID recursion

```text
GRID controller
 -> chooses R0/R1/R2 per subproblem
 -> allocates topology/fanout/depth/budget
 -> fuses typed results in GWT/J-Space
 -> retains Hyperposition when evidence conflicts
```

R3 is the Frankenstein-specific extension. GRID should not simply spawn ten identical full agents. It decides the cheapest recursion unit that can close the current uncertainty/completion deficit.

## 3. Required adaptive recursion router

Target conceptual interface:

```text
route_cognition(problem, context_refs, uncertainty, completion_deficit, budget)
    -> DETERMINISTIC
     | DIRECT_MODEL
     | RLM_SUBCALL
     | FULL_HARNESS_CHILD
     | PARALLEL_MIX
     | WAIT / OBSERVE / HOLD
```

Routing evidence should include:
- expected semantic difficulty;
- need for tools/code/tests;
- context size and information density;
- uncertainty/disagreement;
- whether the task is separable;
- predicted token/latency cost;
- coordination risk;
- authority/effect requirements;
- available deterministic solution.

The router itself is subject to ablation and cannot be justified only by intuition.

## 4. Extended ablation matrix

The main Recursive Harness directive's matrix is extended to include:

```text
A  direct/full-context
B  selective retrieval/ContextCompiler
C  external context + deterministic Python/SQL only
D  RLM: recursive model calls
E  full child harness recursion (RAH-like)
F  GRID, no recursive child harnesses
G  GRID + RLM only
H  GRID + full harness recursion only
I  GRID adaptive R0/R1/R2 routing
J  stronger-model direct baseline when legitimately available
```

For a valid harness attribution result, prefer exact same model/version/reasoning effort/task/scorer/tool authority/budget. When this cannot be held fixed, label the confound explicitly rather than calculating a fake harness delta.

## 5. Critical Frankenstein-specific hypothesis

### H-GRID-RAH-1

A variable GRID controller that chooses between deterministic computation, bare recursive LM calls and recursive full harnesses will dominate a fixed recursive strategy on a mixed workload because task structure varies.

Counterhypothesis:

The routing/controller overhead plus duplicated state management will erase the gains; a single strong harness with simple code-driven spawning will be more reliable and cheaper.

Cheapest discriminator:

Build a mixed benchmark with at least four task classes:
1. deterministic aggregation;
2. semantic aggregation;
3. tool-using repository/debugging subtask;
4. coupled task requiring cross-subproblem fusion.

Run fixed-budget matched-model A/B across RLM-only, RAH-only and GRID-adaptive routing. Measure score, tokens, wall time, child count, recursive depth, verifier success and coordination failures.

## 6. Coordination interaction with the UnifiedDB bug

RAH-style recursion increases the importance of the Frankenstein 2.0 P0 coordination repair.

A system that recursively spawns full harness children while still using session-only mutable pointers can amplify exactly the known failure mode:

```text
more parallel children
 -> more actor ambiguity
 -> more mutable-pointer overwrites
 -> mixed effect/result lineage
 -> stronger-looking but less trustworthy cognition
```

Therefore full R2/R3 parallelism is not allowed to receive whole-system credit before actor/task/turn/effect/generation lineage is repaired and tested.

Every recursive harness child must have stable identity at least:

```text
session_id
agent_id
parent_agent_id
task_id
recursive_call_id
turn_id / tool_use_id where applicable
causal_id
generation
```

## 7. Result fusion law

A parent receiving many child answers must not use majority vote as truth by default.

Fusion should preserve:
- evidence references;
- independent vs correlated derivation;
- contradiction;
- confidence calibration;
- negative results;
- tool/test receipts;
- unresolved alternatives.

Conceptual rule:

```text
MANY_RECURSIVE_RESULTS
 -> PROVENANCE_AWARE_FUSION
 -> HYPERPOSITION_IF_UNRESOLVED
 -> CHEAPEST_NEW_DISCRIMINATING_ACTION
 -> VERIFIED_CONVERGENCE_OR_EXPLICIT_UNKNOWN
```

## 8. Triggerword-4 consequence

This addendum is active whenever Triggerword 4 runs.

Workers must monitor and experimentally compare both RLM-style model recursion and RAH-style harness recursion. If full-harness recursion proves useful, implement it as a bounded GRID-controlled cognitive primitive, not as an independent uncontrolled swarm.

The target is:

```text
not MORE AGENTS
but THE RIGHT RECURSION UNIT AT THE RIGHT TIME
```
