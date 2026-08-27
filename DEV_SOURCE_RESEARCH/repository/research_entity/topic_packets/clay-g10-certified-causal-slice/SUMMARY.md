# COVE-G10 — Certified causal slice

COVE-G10 refines EPOCH-G9 by compiling a **Certified Operation View Envelope** for each consequential operation. The envelope binds only the consistency domains the trusted operation semantics actually depend on, then adds authenticated selection provenance and deterministic projection receipts before model use. The model may propose but cannot narrow trusted closure or mint authority.

Current evidence is mixed-class: seven-branch RAE synthesis, six local synthetic mechanism experiments, one registered Groq 8B proxy experiment, and 2026 external research. The strongest independent convergence is Selection Integrity for graph memory (`arXiv:2606.12290`): authenticated records can still be misselected through writable structure, so record provenance alone is insufficient.

Key runtime objects: `CausalSlicePlan`, `ConsistencyDomainWitness`, `SelectionReceipt`, `ProjectionProofReceipt`, `CertifiedOperationView`, `EffectReceipt` and `M.REVOCATION_DEPENDENCY_INDEX`.

COVE-G10 remains OPEN/HOLD. It is not live-FRANK proof and is not target-Qwen3-4B or Android production evidence.