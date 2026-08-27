<!-- RAE_META
{"packet_id":"KMP-HYP-ZEROCOPY-BOUNDARY-COST","title":"Zero-copy removes copies but not synchronization and coherence cost","domains":["ipc-distributed-systems","systems-architecture","performance"],"topics":["zero-copy","shared memory","cache coherence","ring buffers","near-zero latency"],"epistemic_class":"SYNTHESIS_ARCHITECTURE_CONSTRAINT","claim_status_hint":"CURRENT_MECHANISM_OPEN_TARGET_TRANSFER","origin_class":"HYPERPOSITION_H1_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:26:00+07:00","updated_at":"2026-08-08T05:26:00+07:00","source_refs":["Linux io_uring zero-copy Rx documentation","eclipse-iceoryx/iceoryx2","OSDI 2026 Generalized Cache Coherence Protocol","OSDI 2025 Tigon","hyperposition-20260808T0526p0700-chatgpt-secondary"],"evidence_refs":[],"related_claim_ids":["H-HYP-012","H-HYP-013","H-HYP-016"],"related_experiment_ids":[],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.82,"verification_required":true,"falsifier_or_next_test":"Benchmark FRANK target hardware using serialization/socket, shared-memory ring and iceoryx2 paths while measuring p50/p95/p99 latency, CPU, cache misses/coherence proxies, context switches and crash recovery.","search_terms":["zero-copy boundary cost","cache coherence IPC","shared memory latency","iceoryx2","io_uring zero copy"]}
RAE_META -->

### Core
Zero-copy/shared-memory IPC can eliminate serialization and memory-copy work from critical paths, but it does not make communication free. Ownership transfer, atomics, cache-line movement/coherence, wakeups, reclamation and recovery remain first-order costs under contention.

### Evidence / boundary
Linux `io_uring` and iceoryx2 provide implementation evidence for zero-copy paths. Current systems work on cache-coherence synchronization and coherent shared memory shows why tighter sharing shifts the bottleneck rather than deleting it. Exact FRANK target costs are still unmeasured.

### Implication
Define near-zero latency as minimizing a boundary-cost vector — copies, serialization, syscalls, wakeups, atomics/cache transfers, reclamation and authority/recovery overhead — while preserving isolation and deterministic recovery.

### Next test
Run a target-hardware IPC factorial and retain zero-copy only where end-to-end p99 and recovery improve, not merely payload-copy microbenchmarks.
