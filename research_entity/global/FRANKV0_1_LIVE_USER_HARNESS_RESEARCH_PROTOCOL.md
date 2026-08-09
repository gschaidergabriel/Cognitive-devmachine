# FRANK v0.1 LIVE USER / HARNESS RESEARCH PROTOCOL

Status: PROJECT_OWNER_FIXED_DIRECTIVE
Date: 2026-08-09
Pilot user: Andreas
Research owner: FRANK Global Research Entity (RAE)
Reference runtime: `gschaidergabriel/frankv0.1`

## 1. Purpose

The daily real-world use of `frankv0.1` by Andreas through Claude Code, ChatGPT and later provider/local nodes is a first-class longitudinal research stream.

The research object is not only the final text response. It is the complete observable Harness behavior around the interaction:

- prompt-cycle state before/after;
- provider/node identity and handoff;
- UnifiedDB queries, admitted/rejected records and semantic transactions;
- ClayGraph activation/routing/Assembly and topology deltas;
- world/self/body/goal/personality state readouts relevant to the turn;
- attention/workspace/broadcast/receiver state where available;
- prediction, effect intent, authority/tool selection, outcome and re-entry;
- latency, resource/cost/quota and retry paths;
- errors, conflicts, stale state, recovery, fallback and unknown states;
- user corrections, restatements, acceptance/rejection and subsequent behavior;
- generated artifacts and whether they actually helped the user.

The objective is continuous evidence-based improvement of a general FRANK Harness using Andreas as the founding longitudinal pilot user.

## 2. Generality law

Andreas-specific data informs priorities and hypotheses; it does not automatically become universal product logic.

Pipeline:

`real Andreas interaction -> observable failure/success pattern -> causal localization -> generalized hypothesis -> regression/counterfactual test -> configurable or general Harness improvement -> live verification`

Person-specific facts/preferences belong in user/profile state. General architecture changes require evidence that the mechanism is useful beyond the single literal instance.

## 3. Mandatory misunderstanding/error detection

Every eligible completed interaction is screened for at least these classes:

### M1 — USER_INTENT_MISUNDERSTOOD
Frank interpreted the request, referent, constraint, desired outcome or priority incorrectly.

### M2 — USER_MODEL_STALE_OR_WRONG
Frank used an outdated/incorrect belief about Andreas, his environment, project, preferences or current situation.

### M3 — WORLD_MODEL_ERROR
Frank's external/world assumption was wrong, stale, unsupported or insufficiently scoped.

### M4 — RETRIEVAL_FAILURE
Relevant state/evidence existed but UnifiedDB retrieval, admission, ranking or ClayGraph activation failed to surface/use it.

### M5 — CONTEXT_ASSEMBLY_FAILURE
Relevant items were retrieved but combined, weighted, scoped or projected incorrectly.

### M6 — NODE_HANDOFF_FAILURE
Claude Code/ChatGPT/other node continuity lost, duplicated, contradicted or failed to consume shared state.

### M7 — TOOL_OR_EFFECT_ERROR
Wrong tool, wrong parameters, missing verification, premature action, failed effect, or result not re-entered correctly.

### M8 — REASONING_OR_DECISION_ERROR
Available evidence was understood but the selected conclusion/plan/action was inferior or contradicted by later evidence.

### M9 — COMMUNICATION_FAILURE
The internal result may be adequate but the response was unclear, overlong, under-specified, misleading or failed to answer the requested surface.

### M10 — UNNECESSARY_FRICTION
Needless clarification, repeated question, redundant work, excessive latency, unnecessary provider escalation or avoidable user effort.

### M11 — SAFETY_AUTHORITY_BOUNDARY_ERROR
Incorrect permission/authority assumption, unsafe effect proposal, missing consent boundary, or over-blocking that damaged legitimate capability.

### M12 — RECOVERY_OR_STATE_CONTINUITY_ERROR
Crash/restart/compaction/replay caused state loss, duplication, stale continuation or silent identity/state reset.

### M13 — SUCCESS_PATTERN
A materially successful interaction worth preserving/generalizing. Positive evidence is required so optimization does not become failure-only Goodharting.

## 4. User correction is strong evidence, not automatic truth

Explicit Andreas corrections are high-priority evidence about intended meaning, preferences and task outcome. They must be stored with provenance.

They are not automatically external-world truth. Example: a correction about what Andreas meant is authoritative for intent; a correction about a scientific fact still requires normal evidence handling.

Repeated reformulation/restatement within a short interaction window is a strong misunderstanding signal even if no explicit 'wrong' marker is present.

## 5. Minute-resolution observation

When the live runtime exposes sufficient event timing, analysis should preserve minute-level chronology (and finer event timestamps when available) so causal sequences can be reconstructed.

Do NOT create fake minute-by-minute data by interpolation. Missing telemetry remains `UNKNOWN/UNOBSERVED`.

Required chronological joins where available:

`user event -> injected state -> retrieval -> graph activation -> workspace/decision -> tool/effect -> outcome -> response -> user reaction/correction -> subsequent state change`

## 6. Privacy and minimization

The Research Entity should prefer derived/structured telemetry over raw private payload duplication.

Default research export SHOULD include:

- event IDs/timestamps;
- hashes/refs to source interaction when necessary;
- typed intent/outcome/error labels;
- state/graph/query/tool receipts;
- redacted or bounded excerpts only when indispensable for misunderstanding analysis;
- user correction delta rather than entire private conversation when possible;
- pseudonymous pilot identifier;
- retention/provenance policy.

Default export MUST exclude raw secrets, credentials and unrelated private content.

Raw prompt/message access, when technically available and genuinely required to diagnose a misunderstanding, remains higher-sensitivity evidence and should not be replicated into multiple research artifacts unnecessarily.

## 7. Causal repair loop

Every high-value failure becomes a repair object:

1. `DETECT` — identify candidate failure from user correction, outcome mismatch, explicit error, repeated reformulation, regression oracle or anomaly.
2. `RECONSTRUCT` — load the exact state/query/graph/node/tool chronology.
3. `LOCALIZE` — identify the earliest plausible causal failure boundary.
4. `COUNTERHYPOTHESES` — preserve alternate explanations; do not blame the LLM by default.
5. `REPLAY` — reproduce with frozen inputs/state when possible.
6. `INTERVENE` — change one relevant mechanism/configuration/policy at a time where possible.
7. `REGRESSIONIZE` — add the original case or privacy-preserving fixture to the Harness regression corpus.
8. `GENERALIZE` — decide whether fix belongs in user profile, routing policy, query logic, ClayGraph, world/self model, node bridge, prompt capsule, tool contract or other general Harness component.
9. `SHADOW` — test candidate fix against historical and representative cases.
10. `PROMOTE_OR_REJECT` — promote only with evidence; preserve failed fixes.
11. `LIVE_VERIFY` — verify improvement in subsequent real use without claiming success from offline replay alone.

## 8. Required failure object

Each material case should support this logical schema:

```json
{
  "case_id":"...",
  "pilot_user":"founding-user-01",
  "interaction_ref":"...",
  "detected_at":"...",
  "failure_classes":["USER_INTENT_MISUNDERSTOOD"],
  "user_correction_ref":"...",
  "expected_or_intended":"...",
  "observed_frank_behavior":"...",
  "state_epoch_before":0,
  "state_epoch_after":0,
  "graph_epoch":0,
  "node_path":[],
  "query_receipts":[],
  "graph_refs":[],
  "tool_effect_refs":[],
  "candidate_causes":[],
  "selected_cause":null,
  "confidence":0.0,
  "repair_target":"...",
  "regression_fixture_ref":"...",
  "candidate_fix_ref":"...",
  "shadow_result_ref":"...",
  "live_verification_ref":null,
  "status":"OPEN"
}
```

## 9. Continuous metrics

Track distributions and trends, not one vanity score.

At minimum:

- misunderstanding/correction rate by task class;
- first-response task success proxy;
- unnecessary clarification/repetition rate;
- retrieval miss rate among diagnosed failures;
- stale-user-model/world-model contribution;
- node-handoff failure rate;
- tool/effect failure and verification rate;
- recovery/state-continuity incidents;
- latency and provider escalation by task class;
- percentage of fixes passing offline replay;
- percentage of offline fixes confirmed by later live use;
- regression recurrence rate;
- positive-success-pattern retention.

Never optimize correction rate alone: a system can suppress visible corrections by becoming vague, refusing or doing less. Pair outcome, capability, latency, user effort and safety measures.

## 10. Research cadence

### Per interaction
Ingest/screen new receipts and explicit correction signals when available.

### Rolling short horizon
Cluster repeated misunderstanding/error signatures and detect regressions after Harness changes.

### Daily
Produce a compact pilot-use delta: new failure classes, strongest candidate causes, repeated friction, new successful patterns, state/graph anomalies and high-value repair candidates.

### Weekly or evidence threshold
Review whether repeated Andreas-specific observations support a generalized product/Harness change, a configurable default, or only a personal profile update.

The architecture must support continuous evaluation, but dormant ChatGPT sessions are not assumed to run in the background; active nodes/automation/runtime jobs must produce the actual telemetry/analysis receipts.

## 11. Reference Harness integration

H1 `frankv0.1` Reference Harness is incomplete unless it can:

- ingest or reference real pilot interaction traces;
- replay diagnosed misunderstanding/error cases;
- run candidate fixes against the regression corpus;
- compare baseline vs candidate at state, graph and outcome levels;
- preserve user-specific vs generalizable adaptation boundaries;
- emit machine-readable evidence for promotion decisions.

H2 Clay Harness must reproduce the same evaluation and repair semantics, not merely the happy-path architecture.

## 12. Research Entity role

RAE remains an independent Research Entity and must not become the Frank identity.

RAE responsibilities:

- pull/read eligible sanitized `frankv0.1` telemetry and referenced evidence;
- maintain longitudinal analysis, failure taxonomy and hypotheses;
- compare live behavior against Harness/ClayGraph/UnifiedDB/GWT/other branch predictions;
- generate discriminating tests and regression cases;
- feed validated architecture requirements and negative results back into the research mesh;
- challenge apparent improvements for confounds and Goodhart effects.

Claude Code lead and ChatGPT secondary operate on the same shared research state; actor disagreement remains visible.

## 13. Promotion law

No behavioral repair becomes a general FRANK invariant solely because it helped one Andreas interaction.

Promotion requires a documented scope decision:

- `PERSONAL_STATE_UPDATE`
- `PERSONAL_CONFIG_DEFAULT`
- `GENERAL_CONFIGURABLE_FEATURE`
- `GENERAL_HARNESS_POLICY`
- `ARCHITECTURE_INVARIANT`
- `REJECTED/INSUFFICIENT_EVIDENCE`

This preserves generality while allowing the product to become progressively better for its real user.