# G10 source ledger

## Canonical/internal RAE evidence

- `research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json` — RAE-8.8 r2 / `04234efd...`.
- Clay G9 `EPOCH` final report — shared-ancestry predecessor, HOLD.
- FRANK C5 final report/run manifest — operation-specific Certified Basis, selection provenance, Reader ABI; OPEN.
- GWT R4 `CSOC` — causal stage orthogonality; OPEN.
- ClayCode CC9 `CBCC` — certified basis/compositional closure; OPEN.
- Hyperposition H3 — epoch-pinned adaptive topology; OPEN.
- ClayGraph G1d — epochal latent field; HOLD; accepted graph remains G0.
- Emergence Certificate — CURRENT method boundary.

Shared RAE ancestry is not independent replication.

## Registered provider evidence

- OpenAlex request/result: `research_entity/runtime/tool_results/clay-g10-1751-openalex.json` — SUCCESS, scholarly metadata/discovery; broad/noisy result set used only for discovery support.
- arXiv: `research_entity/runtime/tool_results/clay-g10-1751-arxiv.json` — SUCCESS. Relevant current items included `Are We Ready For An Agent-Native Memory System?` (2606.24775), `Causal Agent Replay` (2606.08275), and current graph/agent-memory work.
- Semantic Scholar: `research_entity/runtime/tool_results/clay-g10-1751-semscholar.json` — HTTP 429/RATE_LIMITED; covered by OpenAlex/arXiv/native primary-source research.
- Tavily: `research_entity/runtime/tool_results/clay-g10-1751-tavily.json` — SUCCESS, web discovery only.
- Exa: `research_entity/runtime/tool_results/clay-g10-1751-exa.json` — SUCCESS. Surfaced the key independent Selection Integrity paper and memory-poisoning/security work.
- Groq: raw and compiled `clay-g10-1751-groq-*.json` — SUCCESS; `llama-3.1-8b-instant` strictly labeled `8b_proxy_for_4b`.

## Key independent external sources

- Fei et al. 2026, `Selection Integrity for LLM Graph Memory: An Accumulability Criterion for Information-Flow-Blind Retrieval`, arXiv:2606.12290 — external preprint; key independent convergence for `record provenance != selection integrity` and correction against global novelty.
- Current 2026 agent-memory system/evaluation work — external preprints; supports lifecycle decomposition and localized maintenance as research direction.
- ACL 2026 prompt-order work — peer-reviewed conference evidence that reader projection/order can alter behavior.
- FoundationDB developer guide — authoritative implementation documentation for strict serializability, snapshot reads and narrow conflict ranges.
- Qwen3-4B GGUF model material and MLC Android SDK docs — authoritative/model-runtime implementation context for target-reader identity and memory controls.
- TimelyDataflow/differential-dataflow — implementation evidence for localized incremental recomputation.
- Practitioner Reddit discussions — hypothesis/implementation discovery only, never promotion evidence.

## Experiment provenance

- EXP-G10-001..006: `SYNTHETIC_LOCAL_EXECUTION`; mechanisms calibrated locally, not live-FRANK incidence/effect estimates.
- EXP-G10-007: `EXTERNAL_MODEL_RUNTIME_PROXY`; Groq 8B proxy, not target Qwen3-4B evidence.

## Boundary

Preprints, authoritative docs, implementation repositories, hosted model proxies, synthetic experiments and practitioner reports are not treated as the same evidence class. No hidden chain-of-thought is stored.