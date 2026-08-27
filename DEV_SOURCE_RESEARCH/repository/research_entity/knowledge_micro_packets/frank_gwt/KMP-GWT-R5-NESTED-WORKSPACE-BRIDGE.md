<!-- RAE_META
{"packet_id":"KMP-GWT-R5-NESTED-WORKSPACE-BRIDGE","title":"System WorkspaceEpisode and model-internal workspace are distinct causal stages","domains":["frank_gwt","model_runtime","synthetic_clay","storage_state_memory","observability_recovery"],"topics":["global-workspace","J-space","WorkspaceEpisode","uptake","re-entry","Qwen","causal-intervention"],"epistemic_class":"OPEN_SYNTHESIS_WITH_PRIMARY_EXTERNAL_CAUSAL_EVIDENCE_AND_SYNTHETIC_METHOD_CALIBRATION","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T21:40:00+07:00","source_refs":["research_entity/trigger_runs/gwt/gwt-20260808T2140p0700-chatgpt-secondary-r5/FINAL_REPORT.md","research_entity/trigger_runs/gwt/gwt-20260808T2140p0700-chatgpt-secondary-r5/EXPERIMENT_RESULTS.json","https://www.anthropic.com/research/global-workspace","https://transformer-circuits.pub/2026/workspace/","https://github.com/anthropics/jacobian-lens"],"confidence":0.86,"verification_required":true,"falsifier_or_next_test":"On target Qwen-4B, fit/apply a Jacobian lens or equivalent hidden-state intervention and independently cross system WorkspaceEpisode ON/OFF, model-internal workspace lesion, truthful/shuffled re-entry and ClayGraph field while pinning candidate set, projection and token budget."}
RAE_META -->

### Core
FRANK should not collapse the system-wide GWT `WorkspaceEpisode` and a possible workspace-like representation inside its reader model into one mechanism. Primary 2026 Anthropic intervention evidence shows a compact internal J-space in Claude whose contents are reportable, task-modulated, causally load-bearing for multi-step reasoning and flexibly reused by downstream computations. The released Jacobian-lens reference implementation explicitly supports Qwen examples and HuggingFace decoder models.

### R5 causal bridge
Use the stage chain:

`ClayGraph/UnifiedDB candidate formation -> system competition/WorkspaceEpisode -> reader projection -> model-internal uptake/workspace -> model proposal/effect -> outcome -> provenance-bound re-entry`.

A downstream effect is attributable to system GWT only if graph/query candidate formation, projection, internal uptake and re-entry are separately controlled or measured. Internal workspace activity remains model state, not execution authority.

### Externalization hypothesis
Anthropic reports that standard transformers can extend deliberation beyond one feedforward pass by writing intermediate state into tokens and later re-ingesting it. Therefore FRANK's external Clay/re-entry loop is a plausible recurrence scaffold, but it counts as support only if truthful re-entry selectively rescues multi-step performance while shuffled/revoked re-entry does not.

### Boundary
Anthropic establishes this mechanism in Claude, not FRANK/Qwen. R5's numeric nested-workspace experiment is a constructed identifiability calibration, not a target-model effect measurement. No GWT/J-space result establishes phenomenal consciousness.