# Triggerword 4 — Recursive Cognitive Process Distillation and Method Evolution Addendum

Status: MANDATORY FRANKENSTEIN 2.0 COGNITIVE ARCHITECTURE LAW
Date: 2026-08-28

## 1. Why this exists

Frankenstein 2.0 must preserve an important mechanism learned from the long-running Clay Research Entity / worker process: repeated model calls did not improve model weights, but the surrounding processing system became materially sharper through persistent external state, source pinning, typed worker outputs, append-only evidence, contradiction preservation, reconciliation, quarantine, measurement, test gates, negative results, and repeated redesign of the next work selection.

The target is not to copy the historical swarm volume. The target is to internalize the useful processing improvements into Frankenstein 2.0 so that future cognition can learn **how to process a class of problems better** without requiring model retraining.

This layer is called **Recursive Cognitive Process Distillation (RCPD)**.

RCPD is not a second mind, not a free-running LLM swarm, and not a replacement for GRID10. It is the method-learning layer around and through GRID10.

## 2. Evidence from the worker process

The historical Research Entity demonstrates a recursive outer loop:

1. workers receive bounded work/questions;
2. workers emit typed deltas and open questions;
3. results are persisted outside the model window;
4. later workers re-read current state rather than trusting prior narration;
5. repeated observations are deduplicated rather than counted as independent proof;
6. contradictions remain explicit until stronger evidence resolves them;
7. malformed or under-evidenced packets are quarantined instead of silently normalized;
8. source commits / blobs / execution identities are pinned;
9. supervisor gates redefine the next exact discriminator after each result;
10. Distillery recursively decomposes unresolved research questions;
11. Evidence Forge attempts patch/test/reproduction and keeps negative outcomes;
12. only accepted evidence is eligible for later reinjection;
13. later cycles therefore inherit a changed processing policy even when the base model weights are unchanged.

The 2026-08-27/28 system dashboard reconstructed 5,555 successful historical GO worker outputs across 397 twelve-role macrocycles. Only a minority became machine-readable deltas and an even smaller fraction reached Forge-ready state. This is an important negative lesson: **raw recursion/parallelism is not the improvement mechanism; selection pressure, provenance, falsification and process-policy refinement are.**

## 3. Core distinction

Frankenstein 2.0 shall distinguish:

- FACT MEMORY — claims about the world/project;
- EPISODIC MEMORY — what happened in a particular run;
- METHOD MEMORY — reusable ways to solve/inspect/test;
- PROCESS POLICY — rules for selecting and composing methods;
- ARCHITECTURE POLICY — stable structural invariants of Frankenstein itself.

A successful answer does not automatically update Process Policy.
A failed answer does not automatically ban a method.
All method evolution requires evidence and applicability context.

## 4. The processing genome

Frankenstein 2.0 shall maintain a typed **Cognitive Process Genome** (CPG). This is a compact, evidence-bound collection of processing rules, not natural-language tips.

Minimum record types:

### MethodEpisode

- method_episode_id
- timestamp / monotonic interval
- task / situation fingerprint
- uncertainty profile
- goal / workpackage identity
- processing plan
- GRID cells used
- retrieval routes used
- world projections used
- recursion level R0/R1/R2/R3
- child count / child roles
- tool calls / simulators
- token / CPU / memory / latency / IO cost
- prediction before execution
- observed outcome
- completion evidence
- failure / bug links
- trace_id

### MethodHypothesis

- hypothesis_id
- proposed processing rule
- applicability signature
- expected benefit
- expected cost
- falsifier
- counterhypothesis ids
- source MethodEpisodes
- state: CANDIDATE / SHADOW / TRIAL / PROMOTED / DEGRADED / RETIRED / REFUTED

### MethodRule

- method_rule_id
- selector condition
- action / processing operator
- confidence
- evidence count
- independent-context count
- counterexample count
- measured benefit distribution
- measured cost distribution
- last_used
- decay / activation
- provenance
- rollback predecessor

### MethodCounterexample

- counterexample_id
- method_rule_id
- situation fingerprint
- expected result
- observed result
- failure signature
- trace / receipt

## 5. What can evolve

RCPD may learn or propose changes to processing choices such as:

- whether a task should be solved directly or delegated;
- child count and role decomposition;
- whether workers should be independent or sequential;
- recursion depth and stop conditions;
- retrieval route and retrieval breadth;
- context compilation strategy;
- whether to invoke Vector / QUBO / NeRD / Micro-Lab projection;
- whether to search for a counterexample before planning;
- which GRID functions need more or less budget;
- whether the next step should be observation, simulation, coding, testing or HOLD;
- how much evidence is enough for a particular class of claim;
- how to order cheap discriminators before expensive cognition;
- how to compress child results before GWT re-entry;
- when repeated failure means change method rather than retry;
- which prior processing patterns transfer to the current situation.

RCPD may not silently rewrite canonical truth, effect authority, completion truth, user goals, or architecture invariants.

## 6. Recursive processing loop

Every material cognitive/work cycle can produce a method-learning opportunity:

```text
SituationFingerprint
        |
        v
Method Retrieval
        |
        v
GRID selects ProcessingPlan
        |
        v
Execute / Observe / Delegate / Simulate
        |
        v
Trace + Outcome + PredictionResidual
        |
        v
Processing Credit Assignment
        |
        +--> no useful process delta -> archive episode
        |
        +--> MethodHypothesis + Counterhypothesis
                    |
                    v
                SHADOW
                    |
                    v
          replay / held-out / future trial
                    |
                    v
       promote / degrade / refute / retire
                    |
                    v
             Cognitive Process Genome
                    |
                    v
              future GRID cycle
```

This is the intrinsicized successor to the historical worker -> distillery -> forge -> supervisor -> next-worker loop.

## 7. Processing Credit Assignment

A method shall not receive positive credit merely because the final task succeeded.

Credit must distinguish at least:

- outcome quality delta;
- time/latency delta;
- resource/token delta;
- error rate delta;
- uncertainty reduction;
- prediction calibration;
- robustness across perturbations;
- child/retrieval/simulation contribution where causally testable;
- whether the result would have succeeded under a cheaper baseline.

Preferred evidence hierarchy:

1. matched ablation / intervention;
2. replay under identical frozen inputs;
3. held-out repeat on comparable situations;
4. repeated observational correlation;
5. single anecdotal episode.

Only 1-3 normally justify PROMOTED Process Policy.

## 8. Shadow learning before promotion

New process rules begin as CANDIDATE.

Where possible, Frankenstein should evaluate them in SHADOW without changing the live decision:

- compute alternate retrieval ranking;
- compute alternate GRID budget;
- simulate alternate child decomposition;
- compare alternate context compilation;
- compare alternate world projection route;
- run a cheap replay after task completion.

Only after useful discriminating evidence may a rule enter TRIAL and later PROMOTED.

A promoted rule must retain predecessor and rollback path.

## 9. Contradiction and reconciliation law

The historical worker system improved because later workers did not need to pretend earlier workers were right.

Frankenstein 2.0 shall therefore preserve:

- hypothesis and counterhypothesis simultaneously;
- old and new MethodRule lineage;
- explicit SUPERSEDES / CONTRADICTS / SUPPORTS edges;
- exact evidence that caused promotion or retirement;
- unresolved conflicts as UNKNOWN/CONTRADICTION.

Repeated identical observations are consistency evidence, not independent replication.
Consensus count alone cannot promote a method.

## 10. Dedupe and provenance

Every MethodEpisode and MethodHypothesis must be bound to exact source/execution identity sufficient to prevent accidental double counting.

Recommended dedupe inputs include:

- task/situation fingerprint;
- source version / model version;
- processing plan digest;
- input data identity;
- trace identity;
- run/workpackage generation;
- output/evidence digest.

No timestamp-only joins.
No session-order joins.
No natural-language similarity joins for causal credit.

## 11. GRID10 integration

RCPD is distributed across GRID rather than implemented as an eleventh agent.

- G1 Orientation exposes SituationFingerprint and relevant prior MethodEpisodes.
- G2 Goal/Value defines what improvement means for the current task.
- G3 Epistemic Gap identifies the cheapest discriminator.
- G4 Hypothesis/Counterhypothesis includes MethodHypotheses when processing itself is uncertain.
- G5 World Projection can simulate consequences of alternate plans.
- G6 Planning builds candidate ProcessingPlans.
- G7 Retrieval/Transfer retrieves MethodRules by applicability, not only semantic similarity.
- G8 Micro-Lab runs cheap method ablations/replays where useful.
- G9 Delegation/Harness Router applies learned child/recursion/context policies.
- G10 Critic/Stop detects rumination, poor marginal information gain, over-recursion and premature method promotion.

The GWT broadcast may carry a MethodRule candidate, but broadcast is not promotion.

## 12. Persistent Pulse integration

The cheap Persistent Pulse may use promoted Process Policy for wake/admission decisions, but may not run expensive method evolution itself.

Examples:

- known low-value repeated state -> HOLD rather than GRID;
- known stagnation signature -> wake with `METHOD_CHANGE_REQUIRED`;
- high prediction residual -> wake with `METHOD_REVIEW_REQUIRED`;
- familiar task fingerprint with stable promoted method -> compile a smaller SituationFrame.

## 13. Memory evolution integration

Method Memory follows the same activation/degradation principle as other memory:

- frequently useful, transferable rules become easier to retrieve;
- old low-value rules lose activation but remain recoverable;
- contradicted rules are not erased; they become counterexamples / retired lineage;
- context-specific rules must not become global defaults merely through repetition.

## 14. Why the current Frankenstein / Claude Code harness cannot do this yet

The current donor contains important pieces but not this closed meta-processing loop:

1. The Claude Code install route treats Claude primarily as the native host/installer and asks it to follow a fixed plugin integration path; it is not itself a long-running method learner.
2. The versioned hook configuration routes SessionStart/UserPromptSubmit/PreToolUse/PostToolUse/Stop/SessionEnd/PreCompact into one short-lived `stern.py hook` dispatcher and explicitly has no permanent process.
3. The donor can create handoff packages/capsules, but `stern.py` itself does not spawn the child.
4. The current source does not persist the complete `paket_id -> Agent tool_use_id -> child agent_id -> result` WorkExecution join, so child outcomes cannot yet receive robust method-level credit.
5. Current donor hooks drop useful child identity fields that the host may expose.
6. There is no integrated Distillery/Forge-equivalent that turns child/task traces into falsifiable MethodHypotheses, tests them against baselines, and promotes only reproducible process improvements.
7. There is no explicit Cognitive Process Genome whose rules alter future task decomposition, recursion, retrieval, simulation and context compilation based on measured outcomes.

Therefore the missing capability is not merely "spawn more Claude Code agents". It is **persistent method-level learning plus causal process attribution around native agents**.

## 15. High-value lesson from the historical swarm

Do not copy the swarm's inefficiency.

Historical funnel measurements show that thousands of worker outputs can still yield very few accepted architecture improvements. Frankenstein 2.0 should push selection pressure earlier:

```text
cheap situation classification
-> retrieve proven MethodRules
-> identify uncertainty
-> choose minimum discriminating computation
-> use parallel workers only when independence adds information
-> require typed evidence
-> ablate before promotion
-> preserve negative results
-> update Process Policy only when transfer is measured
```

The target is higher **accepted cognitive improvement per unit compute**, not maximum worker count.

## 16. Required tests

At minimum Frankenstein 2.0 must eventually pass:

1. PROCESS_TRANSFER_TEST — a method learned on one task family improves held-out related tasks without rule leakage.
2. PROCESS_COUNTEREXAMPLE_TEST — a promoted rule is degraded/retired after reproducible counterexamples.
3. PROCESS_ABLATION_TEST — the claimed improvement disappears when the learned method component is removed.
4. PROCESS_COST_TEST — a higher-quality method is rejected when its marginal benefit does not justify cost under policy.
5. PROCESS_OVERFIT_TEST — a rule useful on one micro-world is not incorrectly generalized to structurally different held-out worlds.
6. PROCESS_REPLAY_TEST — exact frozen inputs reproduce the recorded processing-plan comparison.
7. PROCESS_CONCURRENCY_TEST — parallel child results are attributed to the correct processing plan without timing inference.
8. PROCESS_RUMINATION_TEST — repeated low-information cycles trigger method change/HOLD rather than blind recursion.
9. PROCESS_ROLLBACK_TEST — a bad promoted method can be deterministically rolled back to its predecessor.
10. PROCESS_LINEAGE_TEST — every current MethodRule can be traced to episodes, hypotheses, counterhypotheses, tests and promotion receipts.

## 17. Telemetry requirements

All RCPD events must be captured in the Frankenstein-2.0 test/telemetry spine:

- method episode DB records;
- process-plan traces/spans;
- child/retrieval/simulator attribution;
- CPU/RAM/GPU/token/latency costs;
- hypothesis/counterhypothesis DB links;
- bug/root-cause links;
- promotion/degradation/rollback receipts;
- GRID10 decision metadata;
- test-series run package snapshots.

This makes the build itself a dataset for post-build analysis.

## 18. Triggerword 4 operational rule

Every Triggerword-4 build cycle shall treat RCPD as a required architecture concern:

- preserve and ingest worker/process lessons;
- do not mistake worker volume for learning;
- identify reusable processing rules;
- bind them to evidence and applicability;
- build the MethodEpisode/MethodHypothesis/MethodRule substrate;
- test process transfer with matched baselines and held-out tasks;
- route successful method learning into GRID10/Method Memory rather than into untyped prompts.

The end-state is a Frankenstein 2.0 that does not only remember **what** happened. It accumulates evidence about **how it should think, search, simulate, delegate, recurse and stop** for different classes of situations.