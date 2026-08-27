<!-- RAE_META
{"packet_id":"KMP-CR-20260809-INCREMENTAL-LOCALITY","title":"Dependency-local recomputation can be tiny under local topology","domains":["claygraph","unifieddb","claycode","clayresearch"],"topics":["incremental","dependency-closure","derived-view","performance"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN","origin_class":"EXECUTED_SYNTHETIC_EXPERIMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-09T17:16:00+07:00","updated_at":"2026-08-09T17:16:00+07:00","source_refs":["research_entity/trigger_runs/clay/clayresearch_20260809T1716p0700_chatgpt-secondary/EXPERIMENTS.md"],"evidence_refs":["EXP-INCR-001"],"related_claim_ids":["H-CR-029","H-CR-030","H2-CR-009"],"related_experiment_ids":["EXP-INCR-001"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":"LOW_TO_MEDIUM_SYNTHETIC","verification_required":"REAL_DEPENDENCY_TOPOLOGY_BENCHMARK","falsifier_or_next_test":"Measure affected closure, bookkeeping and memory on real BASE/H1 dependency traces.","search_terms":["incremental dependency closure","ClayGraph delta","derived view","selective recompute"]}
RAE_META -->

### Core
In a deliberately local 100,000-node synthetic dependency graph, updates touched a median 0.156% of nodes and local closure traversal was ~279.6× faster than a trivial full scan.

### Evidence / boundary
The topology was intentionally favorable: 1,000 mostly isolated 100-node components. The result demonstrates possibility, not expected Frank speedup. Broad fan-out, index maintenance and retained differential-state memory may erase the benefit.

### Implication
Keep `IncrementalReceipt`/affected-dependency recomputation as the leading hot-path hypothesis, but permit selective drop/rebuild and measure real closure size rather than assuming locality.

### Next test
Capture dependency fan-out and update locality from the first executable BASE/H1 traces; compare incremental, batch recompute and hybrid drop/recompute under latency+memory shadows.
