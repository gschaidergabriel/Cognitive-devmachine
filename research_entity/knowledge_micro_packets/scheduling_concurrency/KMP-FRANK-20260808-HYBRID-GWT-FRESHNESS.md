<!-- RAE_META
{"packet_id":"KMP-FRANK-20260808-HYBRID-GWT-FRESHNESS","title":"FRANK GWT should test hybrid heartbeat plus semantic-dirty query refresh","domains":["frank-gwt","scheduling-concurrency","synthetic-clay"],"topics":["freshness","event-triggered","heartbeat","re-entry"],"epistemic_class":"SYNTHETIC_ARCHITECTURE_HYPOTHESIS","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:59:00+07:00","source_refs":["user:Frank-Architektur.md sha256:98afa4eda69dbe0253ea482a5338cfbbed212af2fba5d45af0fd51786b17559c","research_entity/topic_packets/gwt-dual-workspace-causal-closure/SUMMARY.md","research_entity/trigger_runs/frank/20260808T0559+0700-chatgpt-secondary-r2/EXP_GWT_HYBRID_FRESHNESS_SYNTH_001.json"],"confidence":0.82,"verification_required":true,"falsifier_or_next_test":"Run fixed-60s versus hybrid shadow mode on real FRANK traces and compare focus changes, task outcome, later-state divergence, WAL contention and p99 latency."}
RAE_META -->

### Core
Keep the 60 s workspace tick as a spontaneous/idle heartbeat, but do not let it be the only freshness mechanism. Before a Core read, refresh if workspace-relevant channel revisions changed or if an age safety cap is exceeded; high-salience breakthrough events can trigger immediate refresh. This preserves spontaneous activity while preventing a fixed clock from imposing avoidable query-time staleness.

### Why dependency-scoped
ClayCode CC7 shows that dependency-scoped freshness can avoid broad false invalidation when scopes are complete, but hidden dependencies create missed conflicts. Therefore FRANK should track explicit channel/episode revisions and fail conservatively when relevance is unknown rather than treating age alone as truth.

### Synthetic result
A 100-replication constructed timing model found the hybrid policy used fewer refreshes than refresh-on-every-query in quiet, conversational and volatile regimes while eliminating stale reads by construction. Absolute stale rates are not live-FRANK estimates.
