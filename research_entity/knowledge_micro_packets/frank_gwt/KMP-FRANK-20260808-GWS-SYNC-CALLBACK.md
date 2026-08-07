<!-- RAE_META
{"packet_id":"KMP-FRANK-20260808-GWS-SYNC-CALLBACK","title":"Current GlobalWorkspace publish path synchronously executes subscribers","domains":["frank_gwt","scheduling_concurrency","performance_economics","observability_recovery"],"topics":["GlobalWorkspace","broadcast","latency","subscriber isolation"],"epistemic_class":"COMPRESSED_SOURCE_SUMMARY","claim_status_hint":"OPEN","origin_class":"CODE_INSPECTION","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-08T05:20:00+07:00","updated_at":"2026-08-08T05:20:00+07:00","source_refs":["gschaidergabriel/Project-Frankenstein:services/global_workspace.py","research_entity/trigger_runs/frank/20260808T0520+0700-chatgpt-secondary-r2/FINAL_REPORT.md"],"evidence_refs":[],"related_claim_ids":["H-G3-005"],"related_experiment_ids":["EXP-LIVE-GWT-LESION"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.96,"verification_required":true,"falsifier_or_next_test":"Register a controlled slow subscriber and measure publish latency on the target runtime; inspect all subscribers for blocking work.","search_terms":["GlobalWorkspace synchronous subscriber","publish non-blocking","slow subscriber","GWT broadcast latency"]}
RAE_META -->

### Core
The current `GlobalWorkspace.publish()` implementation copies subscribers under an `RLock` and then invokes each callback synchronously in the publisher thread. This contradicts its docstring’s “non-blocking” description for subscriber execution latency.

### Evidence / boundary
This is direct source-code inspection of the accessible Project-Frankenstein default branch, not target-runtime timing evidence. Exceptions are isolated, but callback duration is not.

### Implication
A slow subscriber can become a hidden global-workspace latency coupling. A two-lane design is indicated: bounded pure causal reducers may remain synchronous, while I/O/expensive side effects use queued execution with visible receipts.

### Next test
Inject a 50 ms subscriber and measure publisher p50/p99 before/after an async side-effect lane while checking event ordering and causal receipt completeness.
