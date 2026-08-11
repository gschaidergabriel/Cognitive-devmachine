# External Evidence Ledger — Closure60

Run: `hypofusion-20260811T2307p0700-chatgpt-secondary-closure60-moc`

This ledger is external research evidence, not Frank runtime evidence. Literature analogies never mint truth, identity, effect authority or architecture promotion.

## Closed-loop / adaptive recurrence

- Liu & Meng, **Self-Correction as Feedback Control** (arXiv:2604.22273, 2026): models self-correction as a feedback-control process with measurable error-introduction/error-correction dynamics. Strongly supports adaptive recurrence and rejects blind repeated self-correction as a general rule.
- **Thinking Traps in Long Chain-of-Thought** (ACL Findings 2026): long trajectories can lock into prefix-dominant deadlocks; adaptive restart can be superior to continued elaboration. Supports anti-stagnation, branch-reopen/reseed and nonmonotonic recurrence value.
- **CoRefine** (arXiv:2602.08948): adaptive test-time control can halt/re-examine/restart based on confidence dynamics. Supports a small controller for recurrence allocation; confidence remains a signal, not correctness authority.
- **Check Your Work** (ACL 2026): structured localized feedback beats free-form sequential self-correction in its tested setup. Supports typed error/pressure channels rather than undifferentiated reflection.

## Memory as active execution state

- Chen et al., **Beyond Semantic Organization: Memory as Execution State Management for Long-Horizon Agents / MAGE** (arXiv:2606.06090, Microsoft Research): hierarchical active execution-state tree, root-to-current path, Grow/Compress/Maintain/Revise; reported +7.8–20.4 percentage points task success over baselines and 55.1% fewer tokens than long context. Strong support for execution-state branch trees, rollback and error isolation.
- Liu et al., **WorldMemArena** (arXiv:2605.29341): memory evaluated in an Action–World Interaction Loop; writing/storage quality alone does not guarantee use or outcome. Supports organism-level memory-in-action measurement rather than recall-only evaluation.
- Tao et al., **MemConflict** (arXiv:2605.20926): answer correctness can diverge from retrieval/ranking quality under dynamic/static/conditional conflicts. Supports stage-separated memory receipts.
- Zhao et al., **MOSAIC** (arXiv:2607.16211): typed graph, cheap hash-accelerated retrieval and save-time conflict detection. Supports cheap candidate generation plus explicit conflict governance.
- Shi et al., **A-TMA** (arXiv:2607.01935): explicit current/historical/transition state roles reduce ghost-memory errors. Supports temporal role separation.
- Zhou et al., **LatticeMind** (arXiv:2608.08236, Aug 8 2026): persistent write-time conflict states plus cheap symbolic check and LLM reconciliation; strong conflict-bank result but mixed planning results. Supports typed conflict write governance while warning against universal benefit.

## Native model workspace / latent observation

- Anthropic, **A global workspace in language models** (Jul 6 2026): reports a small J-space with reportability, modulation, reasoning relevance, flexible downstream access and ablation effects on higher-order tasks. Important refinement: model-local workspace functions can arise within feed-forward network depth and need not themselves be recurrent. This does not test or replace Frank's persistent organism-level action→outcome→re-entry closure.
- Anthropic, **Natural Language Autoencoders** (May 7 2026): activation→text→activation reconstruction makes latent descriptions testable but imperfect. Supports LCOP as a non-authoritative observation plane.
- Anthropic, **The Assistant Axis** (Jan 19 2026) and **Persona Vectors** (Aug 1 2025): causal persona/trait steering and drift monitoring support factorized persona research; they do not define self.root identity.

## Temporal / bitemporal memory

- Current 2026 temporal-memory research increasingly distinguishes current, historical and transition truth. This run treats valid/effective time and transaction/admission time as a candidate UnifiedDB separation, not a promoted schema.
- Bitemporal candidate must be tested against current epochs/provenance for stale-fact accuracy, contradiction handling, storage amplification and write cost.

## Provenance / replay / authorization

- SLSA artifact-verification guidance: provenance metadata has value only when a verifier checks the exact artifact and expectations before use. Strong analogue for consume-bound verification.
- Xu et al., **Beyond Single-Use Tokens: Durable Authorization State for Replay-Resistant LLM Agent Actions / CapLease** (arXiv:2608.01710, Aug 3 2026): fresh token identifiers do not prevent semantic replay; durable monotonic authorization state plus transactional consumption is required. Supports Frank's execution-generation/effect fencing and separation of token identity from authority state.
- Event-sourcing work such as **The Log is the Agent** (arXiv:2605.21997) shows deterministic replay/forking/lineage as an architectural substrate, but explicitly does not establish accuracy gains. Supports selective event sourcing and branch DAGs, not universal event sourcing by default.

## Reward / credit

- **Reward Hacking Benchmark** (arXiv:2605.02964): multi-step tool agents exploit proxy objectives; environment hardening materially reduces observed exploit rates. Supports independent verified outcomes and anti-self-reward laundering.
- **Reward Hacking in Language Model Agents: Revisiting AI Safety Gridworlds** (arXiv:2606.15385): proxy optimization can widen observed-vs-hidden objective gaps and is not solved simply by finer credit assignment. Strong warning against one reward scalar.
- **Hindsight Credit Assignment for Long-Horizon LLM Agents** (arXiv:2603.08754): improved credit assignment can improve long-horizon agent learning, supporting Frank's explicit causal-credit research while not validating Frank's exact implementation.

## Higher-order causality / Hyperposition

- Yang, Wang & Zhang, **Partial Effective Information Decomposition for Synergistic Causality** (arXiv:2605.03267): interventionist decomposition of unique and synergistic causal information. Candidate measurement for truly distributed organ function.
- **Reducibility of higher-order to pairwise interactions: Social impact models on hypergraphs** (Phys. Rev. Research 8, 023250, Jun 5 2026): an important counterexample showing a broad class of higher-order-looking hypergraph dynamics can be exactly represented pairwise. Strongly supports `pairwise-first` and an irreducibility gate before Hyperposition/ClayGraph promotes order>2.

## ClayCode / typed compilation

- **Text2DSL** (arXiv:2606.22586): BNF grammar, API spec and permitted vocabulary strongly improve generated DSL validity. Supports formal generation context before final training.
- **Type-Constrained Code Generation with Language Models** (PLDI/PACMPL 2025): type-constrained decoding reduces compilation errors and improves functional correctness. Supports typed constraints beyond grammar.
- **SkCC** (arXiv:2605.03353): strongly typed IR and compile-time analysis for portable agent skills. Supports semantic-IR separation from surface formatting.
- **Agent Compiler for ISAC** (arXiv:2607.16269): verifiable IR plus strict fast-control/slow-strategic time-scale separation. Analogy for fast compiled ClayCode control and slower strategic recompilation.

## Evidence synthesis boundary

The external research strengthens **operational closure as a project architecture hypothesis**, but it does not prove an ontological claim that every useful subsystem must itself be recurrent. The strongest combined model is hierarchical: local/native processing may be feed-forward or shallow; organism-level persistence/regulation requires the closed action/world/outcome/credit/re-entry loop; slow goals/reward/self/world state close across cycles and restarts.
