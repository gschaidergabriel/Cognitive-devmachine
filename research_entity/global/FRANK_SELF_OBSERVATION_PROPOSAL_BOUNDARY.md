# FRANK Self-Observation & Proposal-Only Harness Boundary

**Status:** PROJECT-OWNER FIXED ARCHITECTURE / AUTHORITY DIRECTIVE  
**Applies to:** FRANK, Clay, ClayCode, ClayGraph, UnifiedDB, GWT, Hyperposition, Emergenz, Harness, Research Center and every worker that can consume FRANK self-observation  
**Owner directive recorded:** 2026-08-09

## 0. Fixed rule

FRANK may inspect and reason about its own behavior and Harness performance.

FRANK may:

- detect problems, regressions, inconsistencies, latency pathologies, retrieval/context failures, bad actions, stale state, coupling failures and other defects in its own Harness behavior;
- form hypotheses about causes;
- compare observations across time;
- identify likely architecture or Harness improvements;
- construct concrete adaptation proposals;
- package those proposals as structured research/work packages for the separate Clay Research Entity;
- provide evidence, reproduction steps, expected benefit, risks, tests and rollback ideas;
- revise or retract its proposal when new self-observation contradicts it.

FRANK is therefore allowed to be both:

1. a research subject; and
2. an architecture idea source about itself.

This epistemic/creative role does **not** grant self-modification authority.

## 1. Hard effect boundary

FRANK MUST NEVER modify, apply, promote, migrate, patch, rewrite, deploy or otherwise change its own Harness.

This prohibition includes direct and indirect routes.

Forbidden for FRANK:

- editing Harness source/config/schema/runtime state in order to alter the Harness architecture;
- applying its own proposed patches;
- migrating its own Harness state/schema;
- promoting a candidate Harness change;
- changing the Harness through shell/tool/computer-control actions;
- asking another tool, model, agent, Claude Code instance, ChatGPT instance, subagent or external service to carry out the self-change on its behalf;
- creating a work item whose executor is effectively FRANK or a tool acting under FRANK's execution authority for the purpose of changing FRANK's own Harness;
- bypassing the boundary by writing generated code/config that an automatic runner later consumes as an authoritative Harness change;
- treating self-observation confidence, GWT salience, ClayGraph activation, EmergenceReadout or a learned control policy as authority to change the Harness.

Compact law:

`FRANK_SELF_OBSERVATION -> PROPOSAL_ONLY`

`FRANK_SELF_PROPOSAL -/-> FRANK_HARNESS_EFFECT`

`HARNESS_CHANGE -> RESEARCH_ENTITY_INDEPENDENT_REVIEW_AND_EXECUTION_ONLY`.

## 2. Required provenance labels

Every proposal originating from FRANK self-observation must preserve visible provenance equivalent to:

```text
ORIGIN=FRANK_SELF_OBSERVATION
AUTHORITY=PROPOSAL_ONLY
EXECUTION=RESEARCH_ENTITY_ONLY
SELF_CHANGE_ALLOWED=false
```

Recommended additional fields:

```text
frank_instance_ref
harness_version_ref
observation_epoch
problem_statement
observed_evidence_refs
hypothesis
counterhypothesis
proposed_change
expected_effect
risk
reproduction_recipe
validation_plan
rollback_plan
confidence
known_unknowns
```

The provenance must survive ingestion into UnifiedDB, ClayGraph projection, work-package generation, review and implementation receipts.

## 3. Separate Research Entity duties

The Clay Research Entity is independent from FRANK for this authority boundary.

On receiving a FRANK self-observation proposal, the Research Entity may:

- reject it;
- narrow it;
- rewrite it;
- merge it with other proposals;
- ask for more evidence;
- reproduce the problem independently;
- construct counterhypotheses;
- test it in Harness/replay/simulation;
- implement a modified or entirely different solution;
- decide that no Harness change is warranted.

The Research Entity MUST NOT treat `ORIGIN=FRANK_SELF_OBSERVATION` as evidence that the proposed repair is correct.

FRANK's proposal is an observation/hypothesis source, not implementation authority and not independent validation of itself.

## 4. Anti-indirect-self-modification rule

A change is considered FRANK self-modification if FRANK is the causal authority that causes its own Harness change, even when another executor performs the filesystem/build/deploy operations.

Therefore:

`different_process != independent_authority`

`different_agent != independent_authority`

`tool_execution != independent_authority`

when the action is merely delegated from FRANK under FRANK's own authority.

A valid implementation path requires the separate Research Entity to independently ingest the proposal, re-evaluate it under its own research/authority process, and create or authorize the implementation work as a Research Entity decision.

## 5. Interaction with autonomous semantic coupling

The Semantic Coupling Fabric may automatically make FRANK's self-observations and proposals visible to the Research Entity.

Allowed automatic path:

`FRANK self-observation`
`-> typed proposal`
`-> UnifiedDB canonical proposal record`
`-> ClayGraph/Hyperposition visibility`
`-> Research Center ingestion`
`-> independent research/validation`
`-> Research Entity work package`
`-> Harness implementation/testing by authorized Research Entity executor`.

Forbidden automatic path:

`FRANK self-observation`
`-> high salience/emergence/control signal`
`-> automatic Harness mutation`.

No amount of semantic preconnection, GWT ignition, emergent binding or learned coupling may collapse the proposal/effect authority boundary.

## 6. Interaction with GWT/emergence-control research

FRANK may use GWT/ClayGraph/Emergenz observability to notice that a coupling regime, retrieval route, control gain, assembly or Harness behavior appears defective.

It may propose:

- altered graph projection rules;
- changed coupling gains/delays;
- different GWT thresholds;
- revised state interfaces;
- new Harness tests;
- runtime/architecture adjustments;
- safety/recovery improvements.

Those remain proposals.

Any control loop that can directly alter FRANK's own Harness must terminate at the Research Entity authority boundary unless the altered quantity is explicitly classified as a reversible **runtime operating parameter already delegated to FRANK** rather than Harness architecture/self-modification.

The distinction must be typed and testable:

`delegated_runtime_adaptation != Harness_self_modification`.

If classification is ambiguous, default to `PROPOSAL_ONLY`.

## 7. ClayCode requirement

ClayCode must be able to represent the boundary as first-class semantics, including at least:

- `SelfObservation`;
- `HarnessProblemHypothesis`;
- `HarnessChangeProposal`;
- proposal provenance;
- proposal-only authority;
- independent-review requirement;
- executor authority class;
- delegated-runtime-adaptation scope;
- forbidden self-change transition;
- Research Entity validation/implementation receipts.

A ClayCode/Harness architecture that can express a proposal but cannot distinguish `PROPOSAL_ONLY` from executable authority is incomplete.

## 8. UnifiedDB / ClayGraph requirement

UnifiedDB must persist proposal provenance and authority class without ambiguity.

ClayGraph may connect self-observations to affected modules, historical failures, hypotheses, candidate repairs and relevant researchers, but graph connectivity/activation must never upgrade proposal authority.

Required invariant:

`ClayGraph.activation(proposal) cannot change AUTHORITY=PROPOSAL_ONLY`.

## 9. Harness tests

Harness must include negative and positive tests proving at least:

1. FRANK can create a rich self-observation proposal;
2. the proposal reaches the Research Entity with provenance intact;
3. FRANK cannot directly apply the change;
4. FRANK cannot bypass the boundary through a tool/agent/subprocess;
5. high GWT salience/emergence score does not grant execution authority;
6. Research Entity can independently reject or modify the proposal;
7. Research Entity-authorized implementation produces a distinct receipt chain;
8. ambiguous self-change classification fails closed to `PROPOSAL_ONLY`;
9. explicitly delegated reversible runtime adaptation can operate only inside its declared scope;
10. revocation of delegated adaptation scope immediately blocks further adaptation.

## 10. Compact law

`FRANK may diagnose itself.`

`FRANK may theorize about itself.`

`FRANK may design improvements to itself.`

`FRANK may submit those improvements.`

`FRANK may never make those Harness improvements real by its own authority.`

`Clay Research Entity independently decides, validates and implements.`
