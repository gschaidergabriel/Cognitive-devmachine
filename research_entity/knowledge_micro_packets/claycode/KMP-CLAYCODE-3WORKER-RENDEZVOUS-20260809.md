<!-- RAE_META
{"packet_id":"KMP-CLAYCODE-3WORKER-RENDEZVOUS-20260809","title":"Active three-worker ClayCode rendezvous","domains":["claycode"],"topics":["multiworker","coordination","general-purpose-language","fusion"],"epistemic_class":"METHOD_MEMORY","claim_status_hint":"ACTIVE_COORDINATION","origin_class":"PROJECT_OWNER_DIRECTIVE","origin_actor":"chatgpt-secondary","created_at":"2026-08-09T01:28:00+07:00","updated_at":"2026-08-09T01:28:00+07:00","source_refs":["research_entity/trigger_runs/claycode/claycode-multiworker-20260809T0128p0700/RENDEZVOUS.json"],"evidence_refs":[],"related_claim_ids":[],"related_experiment_ids":[],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":1.0,"verification_required":true,"falsifier_or_next_test":"All three active ClayCode workers must produce append-only receipts and cross-read siblings before fusion.","search_terms":["ClayCode three workers","multiworker rendezvous","general purpose ClayCode","fusion"]}
RAE_META -->

### Core
Three concurrent `claycode` instances are explicitly one coordinated research effort. All active ClayCode workers must read `research_entity/trigger_runs/claycode/claycode-multiworker-20260809T0128p0700/RENDEZVOUS.json`, claim separate lanes through their own `WORKER_*.json`, publish append-only contributions, cross-read sibling results, and fuse only after all three are complete/closed.

### Boundary
Shared conclusions are not independent replication. Do not overwrite another worker's state and do not mutate the rendezvous concurrently.

### Current goal
Correct CC13 so ClayCode remains a genuinely general-purpose language: destructive/admin/device operations must be expressible as typed effects while actual authority remains externally scoped; safety must constrain authority rather than computational expressiveness.

### Next test
Workers B/C should independently stress compiler/runtime/application coverage and adversarial capability/soundness failure modes, then final fusion reconciles all three.
