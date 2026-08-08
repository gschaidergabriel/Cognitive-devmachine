<!-- RAE_META
{"packet_id":"KMP-UDB-U1-CANONICAL-SPINE","title":"UnifiedDB default is canonical event spine plus replayable derived planes","domains":["unifieddb","frank","clay","claygraph","claycode"],"topics":["event spine","outbox","derived views","replay","physical placement"],"epistemic_class":"OPEN_ARCHITECTURE_REFINEMENT_WITH_LOCAL_MECHANISM_EVIDENCE","status":"OPEN","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","source_refs":["research_entity/trigger_runs/unifieddb/unifieddb-20260808T2044p0700-chatgpt-secondary-r2/EXPERIMENT_RESULTS.json","research_entity/trigger_runs/clay/clay-20260808T2033p0700-chatgpt-secondary-r3/MOSAIC_G11.claycode.json"],"verification_required":true}
RAE_META -->

### Core
UnifiedDB should default to one authoritative transactional Clay event/state/effect spine plus versioned replayable derived graph/vector/FTS/activation planes. Logical/semantic unification is first-class; physical colocation is a per-subplan optimization, not the definition of unity.

### Mechanism evidence
A local injected-failure test produced silent cross-store partial state for unsynchronized specialized stores, explicit recoverable lag for a canonical commit + durable outbox, and atomic rollback for a physical monolith. A separate read microbenchmark found the monolith slower on the cache-hot mixed read path, while it had a better write p50 in the tested run.

### Falsifier
A representative live FRANK workload shows a physically consolidated store strictly dominates the hybrid design across exact correctness, p99, write amplification, recovery and common-mode risk.
