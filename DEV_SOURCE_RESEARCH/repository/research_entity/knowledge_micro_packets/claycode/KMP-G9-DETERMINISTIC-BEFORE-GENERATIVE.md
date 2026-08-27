<!-- RAE_META
{"packet_id":"KMP-G9-DETERMINISTIC-BEFORE-GENERATIVE","title":"Resolve deterministic state semantics before small-model projection","domains":["claycode","frank_gwt","formal_methods_testing"],"topics":["projection_compiler","small_model","deterministic_semantics","otcc"],"epistemic_class":"HOSTED_MODEL_PROXY_PLUS_ARCHITECTURE_METHOD","origin_class":"CLAY_G9","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T17:40:00+07:00","source_refs":["research_entity/runtime/tool_results/g9-groq-rawprojection-20260808T1716.json","research_entity/runtime/tool_results/g9-groq-compiledprojection-20260808T1716.json","research_entity/trigger_runs/claycode/claycode-20260808T1723p0700-chatgpt-secondary/EXPERIMENT_RESULTS.json"],"verification_required":true}
RAE_META -->

### Core
On G9's fixed 10-query state-reader corpus, direct raw-output audit gives 6/10 for raw state and 8/10 for trusted candidate projection while prompt tokens fell 487→324. Yet the compiled arm still made a wrong deterministic min/max choice and omitted a unique answer.

### Rule
If a trusted runtime can soundly execute filter/join/min/max/uniqueness/version/capability semantics, it should execute them before the LLM. The model should receive only unresolved semantic alternatives plus required witnesses. Model output remains a proposal.

### Cross-branch audit
CC9 reports different derived scores (5/10 and 9/10) for the same G9 refs. G9 retains its explicit per-query gold audit and treats the score mismatch as method memory: derived metrics must remain traceable to raw outputs.
