<!-- RAE_META
{"packet_id":"KMP-G5-SELECTIVE-DISTRIBUTED-CLOSURE","title":"Synchronize effect boundaries rather than every cognitive transition","domains":["systems-architecture","ipc-distributed-systems","security-capabilities","synthetic-clay"],"topics":["distributed-closure","local-first","speculation","effect-gateway","latency"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_ARCHITECTURE_WITH_SYNTHETIC_SUPPORT","origin_class":"CLAY_G5_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:08:00+07:00","updated_at":"2026-08-08T05:08:00+07:00","source_refs":["Automerge external implementation evidence","Timely/Differential Dataflow external implementation evidence","clay-20260808T0508p0700-chatgpt-secondary:EXP-G5-DISTCLOSURE-006"],"evidence_refs":[],"related_claim_ids":["H-G5-029","H-G5-030","H-G5-049","H-G5-056"],"related_experiment_ids":["EXP-G5-DISTCLOSURE-006"],"predecessor_packet_ids":["KMP-G4-CLAY-SEMANTIC-CAUSAL-KERNEL"],"supersedes_packet_ids":[],"confidence":0.76,"verification_required":true,"falsifier_or_next_test":"Replay real FRANK multi-node traces under injected latency/partitions comparing all-transition consensus with local speculative cognition plus effect-only closure.","search_terms":["selective distributed closure","effect boundary synchronization","local speculative cognition","CRDT cognitive state"]}
RAE_META -->

### Core
G5 proposes that non-effectful cognition and reversible state proposals should remain local/speculative where possible, while externally effectful or causally conflicting transitions pay synchronous global authority/ordering cost. A synthetic distributed workload showed a large latency/availability advantage under its assumptions.

### Evidence / boundary
The proxy assumes only 10% effectful transitions and a specific network/partition distribution. It is not production evidence. CRDT/local-first systems support mergeable state, but convergence alone does not authorize real-world effects.

### Implication
FRANK can pursue near-zero-latency cognition without weakening the capability gateway by moving coordination to the effect boundary.

### Next test
Benchmark both designs on real/twin FRANK traces with partition injection, duplicate/reorder faults and external-effect safety checks.