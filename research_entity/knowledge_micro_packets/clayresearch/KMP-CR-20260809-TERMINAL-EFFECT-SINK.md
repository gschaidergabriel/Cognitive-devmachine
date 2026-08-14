<!-- RAE_META
{"packet_id":"KMP-CR-20260809-TERMINAL-EFFECT-SINK","title":"Terminal output may be an effectful sink","domains":["clayresearch","claycode","harness"],"topics":["safe-effect","terminal","output","control-sequences"],"epistemic_class":"WEB_RESEARCH_SYNTHESIS","claim_status_hint":"OPEN","origin_class":"PRIMARY_DOCUMENTATION_SYNTHESIS","origin_actor":"chatgpt-secondary","created_at":"2026-08-09T17:16:00+07:00","updated_at":"2026-08-09T17:16:00+07:00","source_refs":["Wasmtime official security documentation","research_entity/trigger_runs/clay/clayresearch_20260809T1716p0700_chatgpt-secondary/SAFE_EFFECT_GEOMETRY_DELTA.md"],"evidence_refs":["official runtime security documentation"],"related_claim_ids":["H-CR-012","H2-CR-003"],"related_experiment_ids":[],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":"MEDIUM_ENVIRONMENT_DEPENDENT","verification_required":"TARGET_TERMINAL_TEST","falsifier_or_next_test":"Characterize the actual Ubuntu terminal/UI sink and execute a bounded control-sequence negative suite.","search_terms":["terminal control sequence","stdout effect","safe effect sink","Wasmtime terminal security"]}
RAE_META -->

### Core
`stdout`/terminal output must not be globally typed as PURE. In environments that interpret control sequences, output can alter terminal/application state and may trigger security-relevant effects.

### Evidence / boundary
The constraint comes from official Wasmtime security documentation and is environment-dependent. It does not imply every log/file/string sink is dangerous.

### Implication
ClayCode effect typing should distinguish inert text construction from emission to an effectful terminal/UI sink. APP-08 should include control-sequence negatives and sanitization/bounding policy.

### Next test
Identify Frank v0.1's exact Ubuntu terminal/UI path, then run harmless adversarial control-sequence tests and classify the minimal required sink effect type.
