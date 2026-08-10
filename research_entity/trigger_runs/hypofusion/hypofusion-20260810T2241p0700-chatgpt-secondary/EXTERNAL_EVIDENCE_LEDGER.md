# HYPOFUSION External Evidence Ledger

Run: `hypofusion-20260810T2241p0700-chatgpt-secondary`

Evidence discipline: external architectural similarity is an analogue until the same causal mechanism is tested in Frank. Primary/official sources are preferred; lower-tier discovery pages were not used for promotion.

## E1 — CaMeL / structural control-data separation

- Source: Debenedetti et al., **Defeating Prompt Injections by Design**, arXiv:2503.18813 v2 (2025).
- Class: `DIRECT_SUPPORT | IMPLEMENTATION_PRECEDENT` for structural separation of trusted control flow, untrusted data flow and capability policies.
- Relevant Frank clusters: HF-C4, HF-C6.
- Supports: untrusted external content should not directly control privileged program flow; capability/provenance enforcement belongs outside raw model persuasion.
- Does not prove: Frank's JSON->Clay ingress is sufficient, nor that all contextual prompt injection becomes impossible.

## E2 — Fides / information-flow control for agents

- Source: Costa et al., **Securing AI Agents with Information-Flow Control**, arXiv:2505.23643 (2025).
- Class: `DIRECT_SUPPORT | BETTER_MECHANISM_CANDIDATE`.
- Relevant clusters: HF-C4, HF-C6.
- Supports: deterministic integrity/confidentiality labels and policy enforcement can formalize agent security/utility tradeoffs.
- Import candidate: explicit integrity/confidentiality labels as first-class ClayCode effect/provenance metadata rather than one generic trusted/untrusted bit.

## E3 — contextual prompt-injection critique

- Source: Abdelnabi & Bagdasarian, **AI Agents May Always Fall for Prompt Injections**, arXiv:2605.17634 (2026).
- Class: `COUNTEREVIDENCE | THEORY_CRITIQUE | FAILURE_MODE`.
- Relevant cluster: HF-C4.
- Weakens: any claim that data/instruction separation alone fully solves prompt injection.
- New threat: contextual manipulation can make a forbidden flow appear normatively legitimate or force a security-vs-utility tradeoff.
- Required Frank test: context/norm manipulation attacks in addition to obvious instruction-like text, encoding, multimodal and tool-result attacks.

## E4 — MAGE / memory as execution-state management

- Source: Chen et al., **Beyond Semantic Organization: Memory as Execution State Management for Long-Horizon Agents**, arXiv:2606.06090 (2026).
- Class: `DIRECT_ANALOGUE | BETTER_MECHANISM_CANDIDATE`.
- Relevant clusters: HF-C3, HF-C5.
- Reported result: hierarchical execution-state management improves MemoryArena success by 7.8–20.4 percentage points over baselines while reducing token consumption by 55.1%.
- Frank implication: UnifiedDB memory should be benchmarked on trajectory/state reconstruction and branch correction, not only semantic hit@k.
- Caveat: external architecture uses its own agent/state design; transfer to one-module Frank is unproven.

## E5 — proactive selective memory intervention

- Source: Wu et al., **Remember When It Matters: Proactive Memory Agent for Long-Horizon Agents**, arXiv:2607.08716 (2026).
- Class: `DIRECT_ANALOGUE`.
- Relevant clusters: HF-C3, HF-C5.
- Reported result: selective proactive memory intervention improves pass@1 on Terminal-Bench 2.0 and tau2-Bench, and outperforms passive/general retrieval, always-on injection and advisor-only ablations.
- Frank implication: candidate memory intervention should include an explicit null-intervention action and measure causal use at the next decision.
- Caveat: extra memory-agent compute is a confound; Frank must compare equalized budgets and can implement the mechanism as an internal typed loop-core function rather than a second identity.

## E6 — recurrent-depth test-time reasoning

- Source: Geiping et al., **Scaling up Test-Time Compute with Latent Reasoning: A Recurrent Depth Approach**, arXiv:2502.05171 (2025).
- Class: `PARTIAL_ANALOGUE | DIRECT_SUPPORT_FOR_RECURRENCE_UTILITY_IN_MODEL_CLASS`.
- Relevant cluster: HF-C2.
- Supports: recurrent unrolling can scale test-time reasoning performance without merely emitting more chain-of-thought tokens.
- Does not prove: Frank's organism-level loop-of-loops or GWT controller is the correct recurrence mechanism.

## E7 — causal planning in recurrent Sokoban network

- Source: Taufeeque et al., **Planning in a recurrent neural network that plays Sokoban**, ICLR 2025 OpenReview submission.
- Class: `DIRECT_CAUSAL_ANALOGUE`.
- Relevant cluster: HF-C2.
- Supports: extra recurrent computation can improve planning; interventions on internal plan representations causally change subsequent actions.
- Frank implication: recurrence quality should be measured with interventions/lesions and outcomes, not by recurrence count or synchrony.

## E8 — empowerment + causal learning

- Source: Cao et al., **Towards Empowerment Gain through Causal Structure Learning in Model-Based Reinforcement Learning**, ICLR 2025 / arXiv:2502.10077.
- Class: `PARTIAL_ANALOGUE`.
- Relevant clusters: HF-C5, HF-C8.
- Supports: controllability/empowerment can be a useful exploration signal when coupled to causal structure.
- Does not prove: Frank should maximize empowerment, curiosity or InitiativePulse. Those remain bounded candidate signals and may not mint reward/authority.

## E9 — Kubernetes Lease / coordinated leader election

- Source: official Kubernetes 1.36 Lease and coordinated leader-election documentation (2026).
- Class: `IMPLEMENTATION_PRECEDENT`.
- Relevant cluster: HF-C1.
- Supports: explicit holder identity, renew time, lease duration, transition count and optimistic-concurrency ownership are mature coordination primitives for single-active-controller semantics.
- Frank implication: holder/epoch semantics are reasonable, but Frank's stronger requirement is downstream fencing of state/effect writes after lease transition; a lease object alone is not enough.

## External evidence gaps

- No independent primary evidence was found in this run that specifically validates Frank's `Hyperposition` mechanism beyond generic alternative/dynamic-state analogues.
- No external study directly validates the project's typed multi-timescale reward successor as a whole; retain simple baselines.
- No external source can validate the owner-fixed identity fact `self.root`; that is a project architecture contract, not a scientific claim.
