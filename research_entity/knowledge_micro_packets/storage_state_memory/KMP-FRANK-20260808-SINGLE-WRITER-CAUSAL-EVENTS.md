<!-- RAE_META
{"packet_id":"KMP-FRANK-20260808-SINGLE-WRITER-CAUSAL-EVENTS","title":"FRANK durable mutation should converge on a single-writer causal event path","domains":["storage_state_memory","frank_gwt","observability_recovery","security_capabilities"],"topics":["event sourcing","single writer","replay","causal receipts"],"epistemic_class":"OPEN_HYPOTHESIS","claim_status_hint":"OPEN","origin_class":"CODE_AND_EXTERNAL_RESEARCH_SYNTHESIS","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-08T05:20:00+07:00","updated_at":"2026-08-08T05:20:00+07:00","source_refs":["gschaidergabriel/Project-Frankenstein:core/app.py","gschaidergabriel/Project-Frankenstein:services/consciousness_daemon.py","https://arxiv.org/abs/2602.23193","research_entity/trigger_runs/frank/20260808T0520+0700-chatgpt-secondary-r2/FINAL_REPORT.md"],"evidence_refs":["E-G3-GWT-001"],"related_claim_ids":["H-G3-005","H-G3-006"],"related_experiment_ids":["EXP-LIVE-GWT-LESION"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.83,"verification_required":true,"falsifier_or_next_test":"Crash/fault-injection A/B between current direct cross-organ SQLite mutation and append-only single-writer event projection; require replay hash equality and no duplicate effects.","search_terms":["FRANK single writer","causal event log","event sourcing","replay","cross-organ SQLite"]}
RAE_META -->

### Core
FRANK should route durable state mutation through one validated append-only causal event/commit path, while specialized databases remain rebuildable or scoped projections where appropriate.

### Evidence / boundary
Current Core code directly writes the consciousness activity SQLite schema, creating a mutation path outside the owning subsystem. RAE H-G3-005/006 favor explicit causal receipts and an external authority boundary. Recent ESAA work independently explores deterministic event-sourced mutation for agent systems. This remains an architecture hypothesis until target crash/replay tests are run.

### Implication
One event envelope could unify persistence, GWT causal traces, observability, recovery and truthful outcome→reentry rather than implementing separate telemetry for each.

### Next test
Inject crashes between intention, validation, effect, outcome and reentry; replay from the log and compare projection hashes while checking idempotency and authority receipts.
