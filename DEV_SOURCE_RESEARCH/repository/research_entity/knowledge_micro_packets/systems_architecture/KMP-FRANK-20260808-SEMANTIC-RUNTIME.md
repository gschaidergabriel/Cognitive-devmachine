<!-- RAE_META
{"packet_id":"KMP-FRANK-20260808-SEMANTIC-RUNTIME","title":"FRANK semantic runtime is not synonymous with one OS process","domains":["systems_architecture","frank_gwt","model_runtime","security_capabilities"],"topics":["module collapse","semantic runtime","fault isolation"],"epistemic_class":"ARCHITECTURE_DECISION_SUMMARY","claim_status_hint":"OPEN","origin_class":"MODEL_RESEARCH_SYNTHESIS","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-08T05:20:00+07:00","updated_at":"2026-08-08T05:20:00+07:00","source_refs":["gschaidergabriel/Project-Frankenstein:services/global_workspace.py","gschaidergabriel/Project-Frankenstein:services/thalamus.py","gschaidergabriel/Project-Frankenstein:router/app.py","gschaidergabriel/Project-Frankenstein:gateway/app.py","research_entity/trigger_runs/frank/20260808T0520+0700-chatgpt-secondary-r2/FINAL_REPORT.md"],"evidence_refs":["E-G3-GWT-001"],"related_claim_ids":["H-G3-005","H-G3-006"],"related_experiment_ids":["EXP-LIVE-GWT-LESION"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.82,"verification_required":true,"falsifier_or_next_test":"Instrument target-host latency/recovery and compare selective collapse against process-isolated baseline under crash/resource faults.","search_terms":["FRANK semantic runtime","module collapse","single process","fault isolation","capability boundary"]}
RAE_META -->

### Core
“FRANK as one module” should currently be interpreted as one semantic runtime and causally coherent active state, not as a requirement that all model, gateway, tool and persistence functions occupy one OS process.

### Evidence / boundary
Current code already co-locates GlobalWorkspace and Thalamus in-process while retaining a separate inference HTTP endpoint and authenticated Gateway. RAE H-G3-005/006 require causal receipts and external authority. This supports selective collapse but does not yet measure the target-host optimum.

### Implication
Collapse deterministic hot-path cognition, scheduling and active projections. Keep privileged effects and, by default, accelerator-heavy model execution independently restartable/resource-governed.

### Next test
A/B selective collapse on the FRANK host while injecting inference crashes/OOM and measuring p99 latency, state survival and recovery.
