# FRANK Goals / Intent Queue / Project Engine — deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: archaeology + current target synthesis

## GIP-0 — separate intention, goal, plan, action and authority

FRANK history contains several mechanisms that all dealt with “what should happen next,” but at different levels:
- persistent goals extracted from cognition;
- Intent Queue for unresolved inner resolutions;
- action-intent detector for user/model proposed actions;
- autonomous research plans;
- Project Engine goal/world/policy/task system.

The current architecture keeps these semantic distinctions explicit. A goal or intent is not an EffectPermit.

## GOAL-1 — persistent goal structure

Commit `f300491dfcfa5766e56f3a11fc2842f6bb69f55c` (2026-02-15) added Persistent Goal Structure together with perception, experience space and AST.

Historical behavior:
- goal extraction from reflections;
- persistent storage;
- ACT-R-like decay;
- goal conflict detection;
- goals became an additional workspace/consciousness channel.

The following day's expansion `7fb267399...` explicitly described goal emergence, decay and conflict detection as part of the 10-loop consciousness architecture.

Current reusable principle:
- goals are slow persistent cognitive state with provenance and lifecycle;
- goals may influence attention/planning but do not directly authorize external effects.

## GOAL-2 — novelty/experience coupling

64D experience vectors marked novelty/drift/cycles and later influenced reflection/goal formation candidates. This creates a useful hypothesis:
- sustained novelty or unresolved discrepancy can modulate goal proposal priority.

Current correction:
- novelty score is a routing/priority signal, not evidence that a goal is valid;
- shuffled-novelty controls are required before claiming causal benefit.

## INTENT-1 — Intent Queue creation

Commit `ccebdc78f3c08013e08758c7386984cc5e70386f` (2026-03-03):
- regex-based capture of inner resolutions from reflections;
- stores unresolved intentions instead of requiring immediate action;
- intended to reconnect later cognition with earlier commitments.

Architectural value:
`thought expresses resolution -> persistent intent candidate -> later resurfacing`, rather than `thought -> immediate effect`.

## INTENT-2 — domain migration

Entities->Rooms migration `b3df2f988...` changed `entity_message -> room_intent` patterns.

This reinforces that intent type/category is versioned semantic schema. String/category renames can alter surfacing logic and must migrate historical rows explicitly.

## INTENT-3 — contamination negative result

`475652157...` found Intent Queue contamination:
- 38 whisper/room-themed pending intents were purged;
- contamination filters added at insertion and surfacing;
- lazy cleanup auto-cancelled contaminated intents.

`083ba1a...` connects this to the broader room-prose feedback loop.

Current law:
- model-generated ambient prose cannot automatically become a persistent commitment;
- intent admission needs epistemic/source/quality gates and ancestry awareness.

## PLAN-1 — autonomous research plans

`d2c08bac...` created bounded autonomous research:
- current thought evaluated for research worthiness;
- plan with max 10 tool calls;
- restricted/read-only tools;
- findings synthesized and stored.

This is a useful precursor of typed planning, but historical LLM-generated plan text remains proposal state rather than deterministic authority.

## PROJ-1 — persistent project truth file

`91b983a...` (2026-04-01) made `PROJECT.md` the persistent base-of-truth for project chats, with status/goal/metrics/architecture/progress and auto-applied update blocks.

Useful idea:
- project state should survive conversation context and be explicitly inspectable.

Historical risk:
- LLM-generated `[UPDATE PROJECT.md]` blocks could mutate that base directly; final FRANK uses typed proposals/authority boundaries rather than treating model text as trusted mutation.

## PROJ-2 — tool-use project agent

`62a661f...` gave project Claude five sandboxed tools (bash/read/write/edit/list) and a tool-use loop, max 15 iterations.

`1c5c682...` added:
- context compaction;
- SSE streaming;
- persistent task tracking;
- max 25 iterations.

This is a separate agentic-project lineage, useful for plan/task/world mechanics but not automatically part of the core cognitive FRANK organism.

## PROJ-3 — Project Engine v3

Commit `cfa7062ba62bc9d83fffada29dcc03a75c4f4050` (2026-04-05) rebuilt Project Engine as a goal-driven autonomous platform.

Reported architecture:
- tiered decision engine T0 code -> T1 free LLM -> T1.5 scripts -> T2 Claude;
- action chaining up to five actions/cycle;
- nightly dream cycle;
- persistent goals with metrics/targets/decomposition/confidence;
- entity-relation world model;
- evolving agent profile;
- hard/soft policy engine;
- tool outcome -> strategy log -> profile learning;
- 27 tools;
- checkpointing and collision-safe heartbeat.

Reported project-specific results included a 39 s autonomy cycle with 0 Claude tokens and a real outreach workflow. These are historical reported measurements, not direct evidence for core FRANK cognition.

## GIP-1 — strongest reusable Project Engine ideas

1. Goal state is explicit and measurable, not hidden in chat prose.
2. Goals decompose into tasks with lifecycle/status.
3. World model and goal state are linked.
4. Tool outcomes update strategy/profile only through receipts.
5. Cheap deterministic decisions should precede expensive model calls when soundly possible.
6. Checkpoint/recovery is part of the agent loop.

These map naturally into current Clay/UnifiedDB semantics.

## GIP-2 — distinctions the current target adds

### GoalProposal
Desired future state, priority, source evidence, dependencies, conflict status.

### Commitment
Owner/policy-accepted persistent goal state. Still non-authoritative for external effects.

### Plan
Ordered/partially ordered candidate operations with assumptions/resources.

### Intent
Operation/effect request scoped to current episode/goal.

### EffectIntent
Typed external-effect proposal.

### EffectPermit
Opaque host-minted authority, never a goal/plan property.

### Outcome/Re-entry
Observed result updates goals/strategy/value only with exact causal linkage.

## GIP-3 — current fused target

Persistent self/world/goals live in Unified Memory/typed state. Active goal subsets enter bounded Assembly/GWT based on current relevance, conflict, deadlines and action opportunity.

Goals can arise from:
- explicit user/owner instruction;
- persistent commitments;
- unresolved errors/conflicts;
- trusted experiment/result state;
- bounded novelty/curiosity proposals.

Goals cannot arise as durable commitments merely from decorative/model-generated recurrence.

Project Engine remains a useful agentic-application reference, not a hidden second architecture beside Clay.

## Mandatory regressions

- GIP-REG-01 repeated ambient/reflection phrase becomes persistent intent;
- GIP-REG-02 renamed intent category makes old rows surface under wrong semantics;
- GIP-REG-03 stale completed goal remains active after outcome;
- GIP-REG-04 conflicting goals are simultaneously executed without arbitration;
- GIP-REG-05 novelty signal alone creates/authorizes goal;
- GIP-REG-06 model-generated project update mutates canonical state without permit;
- GIP-REG-07 plan/tool outcome not linked to goal/episode and corrupts strategy learning;
- GIP-REG-08 cheap tier changes semantics/authority relative to expensive tier;
- GIP-REG-09 crash/restart executes same task/effect twice;
- GIP-REG-10 goal/intent state physically collapsed in H3 but no longer independently lesionable;
- GIP-REG-11 H1/H2/H3 goal-conflict/task/outcome differential equivalence.

## Fusion decision

- Persistent Goals: `REUSE_AS_TYPED_SLOW_COGNITIVE_STATE`.
- Intent Queue: `REUSE_COMMITMENT_MEMORY_IDEA; REBUILD_ADMISSION/PROVENANCE/QUALITY_GATES`.
- Project Engine: `REUSE_GOAL/WORLD/TASK/STRATEGY/CHECKPOINT_PATTERNS_AS_APPLICATION_AND_ARCHITECTURE_REFERENCE; NOT_SECOND_CORE_SEMANTIC_ARCHITECTURE`.
