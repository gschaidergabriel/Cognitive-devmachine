# HCU / physical GRID / coordinators

Status: `SOURCE_READY_RUNTIME_UNOBSERVED`

Fused physical GRID10 source now uses ten overlapping Popen children, distinct parent-observed PIDs, shared read-only S1 snapshot barrier and atomic cohort fan-in at source level. Exact repository-bound runtime receipt is still missing; physical GRID10 credit remains 0.

Next: prove runtime quiescence, re-enter execution authority, then execute the exact fused pin and persist a clean bound receipt.

Evidence: `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`

> Cache only.
