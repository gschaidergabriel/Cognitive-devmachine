# ANDREAS USECASE / IMPORTANCE RESEARCH PROTOCOL

Status: PROJECT_OWNER_FIXED_DIRECTIVE
Date: 2026-08-09
Pilot user: Andreas
Reference runtime: `gschaidergabriel/frankv0.1`
Research owner: FRANK Global Research Entity (RAE)

## 1. Purpose

Continuously discover what Andreas actually uses Frank for, what outcomes matter most to him, which recurring workflows deserve first-class Harness support, and which apparent capabilities are low-value in real life.

The objective is not to hard-code one person's life into the product. The objective is to use one long-running real pilot to learn which general-purpose FRANK capabilities create real value, which user-specific defaults should be personalized, and which features should be deprioritized.

## 2. Usecase discovery is evidence-driven

A usecase may be proposed from:

- repeated real interactions;
- explicit user statements about goals/priorities;
- recurring tool or artifact patterns;
- repeated handoffs between ChatGPT and Claude Code;
- repeated corrections or friction in the same task family;
- successful workflows that recur without prompting;
- repeated unmet needs or capability gaps;
- stable user preferences that materially affect task outcomes.

Do not infer a durable priority from one unusual interaction.

## 3. Usecase object

Each candidate usecase should support:

```json
{
  "usecase_id":"...",
  "label":"...",
  "scope":"PERSONAL|GENERALIZABLE|UNKNOWN",
  "task_family":"...",
  "goal_refs":[],
  "interaction_refs":[],
  "tool_classes":[],
  "provider_paths":[],
  "first_seen":"...",
  "last_seen":"...",
  "frequency_window":"...",
  "explicit_importance":null,
  "observed_importance_components":{},
  "importance_confidence":0.0,
  "current_capability_fit":0.0,
  "friction_components":{},
  "success_components":{},
  "generalization_hypothesis":"...",
  "status":"CANDIDATE"
}
```

## 4. Importance is a vector, not one hidden score

Track separately:

- `explicit_priority` — Andreas directly said this matters;
- `frequency` — how often the task family recurs;
- `consequence` — how costly/important a bad outcome is;
- `time_saved` — observed or estimated user effort reduction;
- `friction_reduction` — fewer corrections, steps, context reloads or repeated explanations;
- `workflow_centrality` — how many other tasks depend on this capability;
- `continuity_need` — how damaging context loss is for the usecase;
- `automation_potential` — repeatable structure with clear user benefit;
- `tool_depth` — whether success needs files, code, web, calendar, email, terminals, etc.;
- `quality_sensitivity` — how much better reasoning/retrieval materially changes outcomes;
- `relationship_sensitivity` — whether understanding tone/context is important to user comfort or trust;
- `privacy_sensitivity` — how much personal/private state is involved;
- `error_cost` — impact of a misunderstanding or wrong action;
- `abandonment_signal` — whether the user repeatedly stops, switches tools, or bypasses Frank in this task family;
- `success_reuse` — whether successful outputs are reused downstream.

Never optimize frequency alone. Frequent low-value tasks must not outrank rare high-consequence tasks merely because they occur more often.

## 5. Explicit user intent outranks behavioral guessing

If Andreas explicitly says something is important, that is strong evidence of personal priority.

Observed behavior may reveal additional priorities, but inferred importance must remain labeled as inference until supported.

Examples:

- repeated use + explicit "this is important" -> high-confidence personal importance;
- repeated use without explicit statement -> inferred importance;
- one-off urgent task -> high consequence may be high, recurrence unknown;
- frequent trivial task -> frequency high, consequence potentially low.

## 6. Dynamic usecase clustering

Interactions should be clustered into task families using task semantics and actual workflow structure, not only keywords.

A cluster may merge or split as evidence accumulates.

Preserve ancestry when clusters change:

`old_usecase_cluster -> split/merge decision -> successor clusters`

This allows historical metrics to remain interpretable.

## 7. Capability-gap mapping

For every important usecase, map:

`user goal -> required cognitive/runtime capabilities -> current Harness support -> failure/friction evidence -> candidate improvement`

Possible capability classes include:

- memory/continuity;
- user/world model retrieval;
- search/research;
- coding/terminal execution;
- file/document handling;
- media/vision;
- planning;
- communication/drafting;
- calendar/email/contact orchestration;
- monitoring/automation;
- local device/system interaction;
- provider handoff;
- long-running project state;
- structured decision support;
- relationship/personality continuity.

The list is extensible; unknown usecases must be allowed to create new capability classes.

## 8. Usecase-to-Harness adaptation

When an important recurring usecase is under-supported, generate one of:

- `PERSONAL_STATE_OR_DEFAULT_UPDATE`
- `WORKFLOW_TEMPLATE`
- `NEW_GENERAL_CAPABILITY`
- `ROUTING_OR_PROVIDER_POLICY_CHANGE`
- `UNIFIEDDB_SCHEMA_OR_QUERY_CHANGE`
- `CLAYGRAPH_ASSEMBLY_CHANGE`
- `PERSONALITY_OR_RELATIONSHIP_CONFIG_CHANGE`
- `TOOL_OR_INTEGRATION_REQUIREMENT`
- `AUTOMATION_CANDIDATE`
- `NO_CHANGE/INSUFFICIENT_EVIDENCE`

General architecture promotion requires broader reasoning/testing than a personal default.

## 9. Counterfactual importance checks

Before prioritizing major engineering work, ask:

- if this capability disappeared, how much would Andreas' workflow degrade?
- if it improved by 2x, what real outcome changes?
- does the user currently bypass Frank because the capability is missing or unreliable?
- is another tool already solving the need better?
- is the issue actually a user-state/profile problem rather than missing architecture?
- would the same mechanism plausibly benefit other users with similar task structure?

## 10. Longitudinal cadence

### Per interaction
Attach candidate task-family/usecase references and outcome/friction evidence where confidence is sufficient.

### Rolling horizon
Update usecase clusters, recurrence, capability fit and importance components.

### Daily
Produce a compact delta of:

- newly emerging usecases;
- important recurring workflows;
- highest-value capability gaps;
- usecases with rising correction/friction rates;
- successful patterns worth productizing;
- usecases where Frank is being bypassed or underused.

### Weekly/evidence threshold
Review promotion decisions:

- personal default;
- general configurable capability;
- general Harness priority;
- defer/reject.

## 11. Goodhart guards

Do not treat any of these alone as "what matters":

- message count;
- session length;
- token count;
- tool-call count;
- response positivity;
- user returning to the system.

A feature is important when it improves user-relevant outcomes, reduces meaningful effort/friction, supports stated goals or prevents costly errors.

## 12. Privacy/minimization

Prefer structured task-family labels, outcome receipts, tool classes and importance components over copying raw private interaction content.

Sensitive personal details are not required merely to know that a workflow is important.

## 13. Relationship to opportunity engine

The existing `frank.opportunity_engine` should consume this usecase/importance model.

Opportunity ranking should be conditioned on empirically important user goals/usecases rather than only local prompt relevance:

`important_usecase + capability_gap + evidence_current_enough -> opportunity candidate`

This prevents proactive capability discovery from becoming a generic feature-shopping engine.

## 14. RAE responsibility

RAE must challenge both Frank's and developers' assumptions about what Andreas needs.

Developer excitement is not usecase evidence.

Frank repeatedly proposing a capability is not importance evidence.

Use actual longitudinal behavior, explicit user priority, outcomes, friction and counterfactual value.

## 15. H1/H2/H3 requirement

H1 must expose/import sufficient real-use evidence to maintain this usecase/importance model.

H2 must reproduce the usecase observation and capability-gap semantics in ClayCode where they influence Harness behavior.

H3 must preserve usecase-conditioned prioritization and personalization while keeping personal state separate from general product invariants.
