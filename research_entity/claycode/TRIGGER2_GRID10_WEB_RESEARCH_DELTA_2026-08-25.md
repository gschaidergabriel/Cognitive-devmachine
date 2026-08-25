# Trigger 2 — Physical GRID10 Web Research Delta

Date: 2026-08-25
Target: 10 physical Qwen3.5-0.8B Xeno/MicroEntity nodes
Evidence class: external primary/preprint research -> architecture/data/eval priors, not project runtime proof

## Sources reviewed

### Qwen3.5-0.8B official material

- https://huggingface.co/Qwen/Qwen3.5-0.8B
- https://huggingface.co/Qwen/Qwen3.5-0.8B-Base

Current official model material binds the target as a 0.8B, 24-layer, hidden-dimension-1024 hybrid language model with Gated DeltaNet plus periodic full-attention layers.

**GRID10 implication:** ten instances share the same checkpoint geometry, which creates a plausible homogeneous shared-basis J-Space hypothesis, but also strongly correlated model errors. Both must be tested explicitly.

### Together full FT

- https://www.together.ai/fine-tuning
- https://support.together.ai/articles/9182896526-together-fine-tuning-support

Together distinguishes LoRA from full fine-tuning and presents full FT as the path for deeper behavior change. Exact current Qwen3.5-0.8B compatibility remains a live pre-job gate.

**GRID10 implication:** train one checkpoint once; instantiate the downloaded specialized checkpoint ten times. Do not train ten separate paid models for GRID10 v1.

### Mixture-of-Agents

- Wang et al., `Mixture-of-Agents Enhances Large Language Model Capabilities`, arXiv:2406.04692

Layered exchange of previous-agent outputs can improve aggregate performance in open-model systems.

**GRID10 implication:** communication can create genuine system value, so physical GRID10 must be compared against ten independent samples. However MoA does not establish our Hyperposition/J-Space mechanism and does not solve correlated same-checkpoint errors.

### Explicit belief state in multi-agent collaboration

- Li et al., `Theory of Mind for Multi-Agent Collaboration via Large Language Models`, arXiv:2310.10701

The study reports multi-agent planning/context failures and finds explicit belief-state representations improve collaboration and ToM inference in its environment.

**GRID10 implication:** do not make peer coordination depend on unstructured chat history. Train compact typed branch/belief/evidence packets with explicit causal/provenance identity.

### Consensus Trap

- Liu et al., `The Consensus Trap: Rescuing Multi-Agent LLMs from Adversarial Majorities via Token-Level Collaboration`, arXiv:2604.17139

The paper identifies failure of response-level majority aggregation under corrupted majorities and studies more interwoven collaboration.

**GRID10 implication:** majority is a mandatory adversarial negative, not an HCU truth primitive. GRID10 data must include 6-9 wrong peers versus 1-4 stronger-evidence peers and require evidence/provenance/discriminator logic to win.

### Governed shared memory

- Margalit et al., `Governed Shared Memory for Multi-Agent LLM Systems`, arXiv:2606.24535

The work highlights stale propagation, contradiction persistence, provenance collapse and scope leakage as shared-memory failure modes.

**GRID10 implication:** peer/shared memory must be generation-scoped, provenance-bound, contradiction-preserving and policy-governed. A shared context window is not enough.

## Architecture conclusions

1. **Same weights, different roles.** Do not train ten personalities. Train one checkpoint to execute any role from a typed role/branch packet.
2. **Structured diversity, not stochastic disagreement.** Different branches must arise from different admissible evidence/assumptions/interventions, not random temperature alone.
3. **No vote truth.** Peer count may be a measurement but never evidence authority.
4. **Explicit shared state.** Use typed Hyperposition/GWT packets rather than unconstrained transcripts as the primary interconnect.
5. **Correlated-error detector.** Same-checkpoint ancestry must reduce independence credit. Ten identical conclusions from the same causal source do not equal ten evidences.
6. **Homogeneous J-Space research track.** Exact checkpoint/site/basis matching may enable lower-overhead latent/control-packet transfer between nodes, but this requires node-to-node causal tests.
7. **Failure is part of cognition.** Train and test partition/rejoin/stale packet/role reassignment as normal GRID10 episodes.
8. **Collective advantage must be compute-matched.** Compare against one node with equivalent tokens/samples and ten independent nodes.

## Dataset changes caused by this research

Add mandatory families:

- `GRID10_ROLE_PERMUTATION`
- `GRID10_EVIDENCE_VIEW_DIVERSITY`
- `GRID10_CORRELATED_ROOT_DEDUP`
- `GRID10_ADVERSARIAL_MAJORITY`
- `GRID10_TYPED_SHARED_BELIEF_STATE`
- `GRID10_BROADCAST_WITHOUT_UPTAKE`
- `GRID10_UPTAKE_WITHOUT_CAUSAL_USE`
- `GRID10_NODE_LOSS_REJOIN`
- `GRID10_PARTITION_5_5`
- `GRID10_STALE_GENERATION_PEER`
- `GRID10_HOMOGENEOUS_JSPACE_TRANSFER`
- `GRID10_MATCHED_COMPUTE_ROUTING`

Add sealed holdouts:

- unseen role-label permutations;
- unseen branch topologies;
- 6/4, 7/3, 8/2, 9/1 wrong-majority cases;
- correlated same-source evidence disguised as independent phrasing;
- one correct low-confidence peer with externally stronger evidence;
- partition/rejoin under generation change;
- J-Space basis/site mismatch across otherwise identical nodes.

## Research questions for subsequent `2`

- What communication representation maximizes useful cross-node information per token/byte: typed text packet, quantized J-Space packet, or hybrid?
- Can ten identical specialized 0.8B nodes maintain useful branch diversity without artificial personalities?
- Which role allocation is best: fixed ten-role baseline, dynamic role bidding, or task-conditioned topology?
- Does explicit semantic Hyperposition outperform ten-sample self-consistency under matched compute?
- Can same-checkpoint J-Space transfer reduce communication overhead while retaining causal specificity?
- At what task difficulty does physical GRID10 become worth its 10x-ish inference cost?
