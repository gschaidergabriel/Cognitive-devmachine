# Live Fusion Mesh V3 — Post-Write Fresh Evidence Refresh

Date: 2026-08-10
Actor: chatgpt-secondary / OpenAI / GPT-5.6 Sol
Trigger: go
Evidence class: LIVE_EXTERNAL_PRIMARY_RESEARCH
Architecture result: **NO_CHANGE / GUARD_CONFIRMED**

## Question

After writing the V3 dual-plane candidate, does fresh systems evidence support or undermine the new requirement that a secondary routing/repair plane must have materially distinct failure/provenance ancestry to improve robustness?

## Fresh primary evidence

### Skybridge — OSDI 2025

Source: USENIX, `Skybridge: Bounded Staleness for Distributed Caches`.

The system is described as complementary to the main replication pipeline and explicitly designed to avoid correlated failures while remaining lightweight. USENIX reports 2-second bounded staleness for 99.99998% of writes versus 99.993% for the main replication pipeline in the evaluated deployment, while Skybridge is only 0.54% the size of cache deployments.

Source URL: https://www.usenix.org/conference/osdi25/presentation/lyerly

Relevance to Clay: this does **not** prove the V3 mesh, but it independently supports the design principle that a small secondary path can improve stale/failure coverage only when it is sufficiently failure-distinct from the primary path.

### Picsou — OSDI 2025

Source: USENIX, `Picsou: Enabling Replicated State Machines to Communicate Efficiently`.

Picsou uses quorum acknowledgements to determine when messages are definitely received or likely lost and targets minimal retransmission on failures rather than all-to-all resend. USENIX reports up to 24x better performance than prior evaluated solutions on its microbenchmarks/applications.

Source URL: https://www.usenix.org/conference/osdi25/presentation/frank

Relevance to Clay: supports explicit acknowledgement/repair semantics and selective retransmission as a plausible design family; it does not validate Clay-specific semantics or evidence authority.

### T2C — OSDI 2025

Source: USENIX, `Deriving Semantic Checkers from Tests to Detect Silent Failures in Production Distributed Systems`.

T2C derives runtime semantic checkers from tests and detected 15 of 20 reproduced real-world silent failures across four evaluated systems with small runtime overhead.

Source URL: https://www.usenix.org/conference/osdi25/presentation/lou

Relevance to Clay: transport/delivery success is insufficient; semantic acknowledgement states must remain checkable against actual receiver reconstruction/use and current state.

## Adjudication

No architecture change is justified beyond the already-written V3 guard:

`secondary route/relevance path != independent safety path unless provenance/failure ancestry is materially distinct`

The fresh evidence therefore **confirms the guard but does not promote V3**. The previously persisted fully-correlated-blind-spot synthetic negative result remains a hard test obligation.

## Research re-entry

- ClayGraph: expose projection lineage/failure ancestry for high-impact routing checks.
- UnifiedDB: persist basis epoch/hash and source lineage for BranchImpactAck.
- Harness: real replay must include both independent and deliberately correlated projection failures.
- GWT: acknowledgement remains distinct from reconstruction/use/effect.
- Emergenz: stronger connectivity remains non-evidence; overcoupling and shared-failure amplification remain lesion targets.

Verdict: `NO_CHANGE_GUARD_CONFIRMED_REAL_REPLAY_STILL_REQUIRED`.
