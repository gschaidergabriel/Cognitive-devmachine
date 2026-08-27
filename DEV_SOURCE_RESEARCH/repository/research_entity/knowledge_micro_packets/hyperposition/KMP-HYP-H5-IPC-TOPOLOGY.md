# KMP-HYP-H5-IPC-TOPOLOGY

- **epistemic class:** OPEN local systems mechanism result
- **claim:** Physical topology is an independent optimization dimension; semantic identity does not determine process/IPC placement.
- **H5 successful local rerun:** Pipe vs preallocated SharedMemory+copy+signal p50: 1 KiB 2.253 vs 1.763 us; 64 KiB 7.666 vs 3.135 us; 1 MiB 146.743 vs 31.286 us. Shared-memory advantage increased with payload in this local CPython mechanism proxy.
- **correction:** an earlier failed IPC attempt is discarded and is not evidence.
- **boundary:** benchmark omits realistic contention, cache coherence/visibility, lifecycle, crash recovery, multi-reader coordination, Rust/Android implementation and security fault domains.
- **architecture rule:** select same-process handles/shared memory/IPC/separate services by measured payload, contention, recovery, crash radius, energy and platform; do not alter semantic/authority identity.
- **falsifier:** target trace benchmarks show one physical route dominates all relevant workloads and fault regimes.
- **status:** OPEN/HOLD
