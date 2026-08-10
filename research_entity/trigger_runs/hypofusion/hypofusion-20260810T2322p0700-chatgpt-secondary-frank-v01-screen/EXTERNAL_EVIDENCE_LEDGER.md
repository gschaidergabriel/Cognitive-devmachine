# External Evidence Ledger

Run: `hypofusion-20260810T2322p0700-chatgpt-secondary-frank-v01-screen`

Evidence classes are scoped; architectural resemblance is not treated as replication.

## HF-01 — execution-generation fencing / replay-resistant effects

- **WriteGuards (OSDI 2026)** — `DIRECT_SUPPORT / IMPLEMENTATION_PRECEDENT`. Delayed writes during ownership changes are rejected using a fencing value tied to the current owner. This is a close systems analogue to rejecting stale Frank effect writers after execution-generation turnover. Source: USENIX OSDI 2026, Z. Mao et al., *WriteGuards: Distributed Storage Support for Strongly Consistent Caches*.
- **Chubby (OSDI 2006)** — `IMPLEMENTATION_PRECEDENT`. Lease/lock ownership is made reliable through centrally governed lease state and recovery; supports the principle that possession/observation of stale state is not write authority. Source: Mike Burrows, *The Chubby lock service for loosely-coupled distributed systems*.
- **CapLease (arXiv:2608.01710)** — `DIRECT_SUPPORT`. Durable monotonic authorization state is required to prevent semantic replay across replanning/retry/delegation; token identity alone is insufficient. Strong analogue for Frank's reservation/attempt/retry lifecycle.
- **CaMeL (arXiv:2503.18813)** — `DIRECT_SUPPORT` for trusted control/data-flow separation and capabilities around an LLM.
- **Fides (arXiv:2505.23643)** — `DIRECT_SUPPORT` for deterministic integrity/confidentiality labels and policy enforcement.

## HF-02 — structural non-authority for web ingress

- **CaMeL (arXiv:2503.18813)** — `DIRECT_SUPPORT`. Untrusted retrieved data is prevented from determining trusted program flow; capabilities constrain unauthorized flows.
- **Fides (arXiv:2505.23643)** — `DIRECT_SUPPORT`. Dynamic IFC can deterministically enforce a useful subset of agent security policies.
- **AgentSys (arXiv:2602.07398)** — `DIRECT_SUPPORT / BETTER_MECHANISM_CANDIDATE`. Context isolation plus schema-validated boundary returns reduce indirect prompt-injection exposure by preventing raw external traces from persisting in privileged memory.
- **NeuroTaint / Ghost in the Agent (arXiv:2604.23374)** — `COUNTEREVIDENCE / SCOPE_BOUNDARY`. Traditional structural taint can miss semantic transformation, causal influence and cross-session persistence. Implication: Frank should keep hard non-authority enforcement for privileged effects but add semantic provenance/audit rather than assuming labels alone capture all read-side influence.
- **AgentSecBench (arXiv:2605.26269)** — `DIRECT_SUPPORT / EVALUATION_PRECEDENT`. Distinguishes descriptive prompt annotations from enforcing provenance projections and capability restrictions.

## HF-03 — long-horizon memory as execution state

- **MAGE (arXiv:2606.06090)** — `DIRECT_SUPPORT`. Hierarchical execution-state trees isolate faulty branches, reconstruct active state and reduce token use while improving task success over semantic-memory baselines.
- **ESAA (arXiv:2602.23193)** — `IMPLEMENTATION_PRECEDENT`. Append-only event log + deterministic orchestrator + replayable materialized view separates probabilistic intention from deterministic state mutation.
- **Context Folding (ICML 2026 OpenReview)** — `DIRECT_SUPPORT`. Branching/folding completed subtasks can maintain long-horizon performance with much smaller active context.
- **Reasoning/Execution provenance work (arXiv:2606.04990; arXiv:2603.21692)** — `PARTIAL_SUPPORT`. Highlights provenance-bearing traces/state as separate from final-answer correctness.

## HF-04 — adaptive recurrence / stopping / loop stability

- **Learning How Hard to Think (ICLR 2025)** — `DIRECT_SUPPORT`. Input-adaptive compute allocation reduces inference computation without quality loss on tested tasks.
- **CaRT: Teaching LLMs When to Stop Seeking and Start Acting (ICLR 2026 submission)** — `DIRECT_SUPPORT`. Counterfactual termination training improves efficiency and task success.
- **CATS (2026)** — `DIRECT_SUPPORT`. Conformal risk control provides a principled way to choose reasoning effort under explicit error tolerance.
- **Parcae (ICLR 2026 LIT workshop)** — `DIRECT_SUPPORT / FAILURE_MODE`. Looped models can improve quality but require explicit stability conditions; uncontrolled recurrence can exhibit residual explosion/loss spikes.
- **When Shallow Wins (arXiv:2603.03475)** — `COUNTEREVIDENCE / THEORY-EMPIRICAL WARNING`. Correct answers can arise through unstable reasoning and more/deeper reasoning is not monotonic evidence of correctness; stability must be measured separately.

## HF-05 — global workspace / bandwidth-limited broadcast

- **Coordination Among Neural Modules Through a Shared Global Workspace (ICLR 2022 Oral)** — `DIRECT_SUPPORT_IN_OTHER_DOMAIN`. A limited shared workspace can promote specialization and coordination among modules.
- **Zero-shot cross-modal transfer through a Global Workspace (RLC 2024)** — `DIRECT_SUPPORT_IN_OTHER_DOMAIN`. Full workspace outperformed ablations on cross-modal policy transfer in the tested environments.
- **Shared Recurrent Memory Transformer (2024)** — `PARTIAL_ANALOGUE`. Shared recurrent memory improves coordination in multi-agent pathfinding.
- **Partner Modelling Emerges in Recurrent Agents (NeurIPS 2025 poster)** — `COUNTERHYPOTHESIS_SUPPORT`. Useful structured internal models can emerge without dedicated modules when task pressure makes them useful. Implication: explicit GWT should earn its complexity by causal ablation, not by metaphor.

## HF-06 — higher-order Hyperposition / hypergraph topology

- **Higher-Order Knowledge Representations for Agentic Scientific Reasoning (arXiv:2601.04878)** — `DIRECT_SUPPORT_IN_BOUNDED_DOMAIN`. Hypergraphs preserve irreducible multi-entity relations and support structured traversal.
- **HGMem (arXiv:2512.23959)** — `DIRECT_SUPPORT_IN_BOUNDED_TASKS`. Dynamic hypergraph memory improves multi-step RAG over strong baselines.
- **HKVM-RAG (arXiv:2606.07218)** — `DIRECT_SUPPORT + BOUNDARY_EVIDENCE`. Hypergraph organization improved two multi-hop datasets, while HotpotQA showed that more structured-support coverage need not yield standalone answer-F1 gains.
- **Pairwise is Not Enough / HMAGAT (arXiv:2602.06733)** — `DIRECT_SUPPORT_IN_COORDINATION_TASK`. Higher-order relations help dense multi-agent coordination.

## HF-07 — authoritative state + projections

- **ESAA (arXiv:2602.23193)** — `IMPLEMENTATION_PRECEDENT` for append-only event history, deterministic mutation and rebuildable views.
- **MAGE (arXiv:2606.06090)** — `PARTIAL_SUPPORT` for explicit state/revision/branch structure rather than undifferentiated semantic retrieval.
- **Causal Process Models (CLeaR 2026)** and **Meta-Causal States (ICLR 2025 Spotlight)** — `PARTIAL_ANALOGUE` for sparse time-varying causal topology rather than one static graph.

## HF-08 — typed ClayCode IR / DSL

- **Type-Compliant Adaptation Cascades (ICLR 2026 Poster)** — `PARTIAL_ANALOGUE`. Typed workflows can improve compliance and structured task performance over brittle prompt pipelines.
- **Replacing thinking with tool usage enables reasoning in small language models (ICML 2025 workshop)** — `PARTIAL_ANALOGUE`. A stateful tool controlled by a custom DSL can turn extra computation into verifiable actions and denser rewards.
- **Planning with Schemas (ACL ARR 2026)** — `IMPLEMENTATION_PRECEDENT`. Compact schemas can reduce action-space screening pressure versus enumerating all grounded actions.
- **When2Tool (arXiv:2605.09252)** — `COUNTERHYPOTHESIS_SUPPORT`. Some routing signals are directly decodable from model hidden state; a heavy symbolic stack is not automatically necessary for every internal decision.

## HF-09 — persistent goals / proactive agency / liveness

- **Hierarchical Agenda Reasoning (2026)** — `PARTIAL_SUPPORT`. Persistent goal representations improve strategic multi-turn behavior and allow tactic revision without abandoning higher-level objectives.
- **SAGA goal-evolving agents (2026)** — `PARTIAL_SUPPORT`. Self-generated objective revision can improve open-ended scientific optimization in bounded design tasks.
- **PEPA (arXiv:2603.00117)** — `PARTIAL_ANALOGUE`, not identity/personality evidence for Frank. Demonstrates persistent internally generated goals in an embodied system.
- **Zombie Agents (AIware 2026)** — `FAILURE_MODE`. Long-horizon agents can enter semantic livelock while appearing operational; progress/liveness monitors are required.
- **OneDayAgent (arXiv:2608.05013)** — `IMPLEMENTATION_PRECEDENT`. Managed long-horizon execution benefits from bounded subtasks, execution memory, verification and repair across backends.

## Fusion rule

No external source above is promoted as proof that Frank's implementation works. Each source changes hypothesis weight, mechanism boundaries or required discriminators only. Current target-runtime receipts remain necessary for promotion.