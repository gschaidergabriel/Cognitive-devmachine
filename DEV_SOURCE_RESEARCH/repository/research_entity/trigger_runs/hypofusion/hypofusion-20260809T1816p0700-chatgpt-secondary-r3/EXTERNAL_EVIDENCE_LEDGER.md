# HYPOFUSION R3 — External Evidence Ledger

Run: `hypofusion-20260809T1816p0700-chatgpt-secondary-r3`

Rule: external similarity is an analogue until the same mechanism is tested. Project workers sharing Clay ancestry are never counted as independent replication.

## C1 — Adaptive recurrence / halting

- **DIRECT/PARTIAL SUPPORT:** *Scaling up Test-Time Compute with Latent Reasoning: A Recurrent Depth Approach* (NeurIPS 2025). Recurrent depth provides adaptive test-time computation and reports larger benefit on reasoning-heavy cases. This supports recurrence as a compute-allocation mechanism, not the project-specific pressure/trend controller.
- **IMPLEMENTATION PRECEDENT:** *Adaptive recurrent vision performs zero-shot computation scaling to unseen difficulty levels* (NeurIPS 2023). Learnable halting allocates more recurrent computation to harder inputs.
- **COUNTEREVIDENCE / FAILURE MODE:** *Loop, Think, & Generalize: Equivariant Reasoning and the Collapse of Overthinking in Recurrent Architectures* (arXiv 2026). Additional recurrence can cross into overthinking and degrade predictions.
- **BETTER-MECHANISM CANDIDATE / COUNTERHYPOTHESIS:** *Universal Transformers Need Memory* (arXiv 2026). Memory/state capacity changes recurrent-depth behavior and adaptive-computation training can fall into shallow-halting traps.

Fusion consequence: pressure + trend remains a promising internal proxy, but memory/state capacity and overthinking/stability signals become first-class competing controller variables.

## C2/C3 — Compiler semantic preservation, resources and authority

- **DIRECT THEORY/IMPLEMENTATION PRECEDENT:** CompCert verified compiler documentation. Compiler correctness is behavioral/semantic preservation through verified passes, not merely a provenance/hash chain.
- **IMPLEMENTATION PRECEDENT:** WebAssembly Component Model / WIT resources (Bytecode Alliance/Wasmtime). Resources use typed owned/borrowed handles and explicit lifetime semantics.
- **IMPLEMENTATION PRECEDENT:** seL4 capability model documentation. Capabilities are unforgeable authority references; possession/derivation controls access rather than arbitrary structural data.

Fusion consequence: three proof obligations remain distinct: semantic preservation, current resource lifetime, and effect authority/provenance. A typed effect annotation alone cannot establish runtime authority closure.

## C4 — Adaptive visual learner / open set

- **DIRECT/PARTIAL SUPPORT:** OpenMax, CVPR 2016. Explicit unknown/open-set handling addresses the closed-set assumption and open-space risk.
- **PARTIAL ANALOGUE:** Prototypical Networks, NeurIPS 2017. Prototype representations are a simple effective few-shot inductive bias.
- **PARTIAL ANALOGUE:** recent prototype-based continual-learning work with novelty detection provides an implementation analogue for online prototype updates, but does not validate Clay's trust tiers, rollback policy or user-specific utility.

Fusion consequence: explicit UNKNOWN/AMBIGUOUS/CONFLICT and versioned prototype state are externally plausible, but online learning itself must beat a frozen embedding + calibrated prototype/open-set baseline on the Ubuntu H1 task stream.

## C5 — Replay and nondeterminism

- **IMPLEMENTATION PRECEDENT:** FoundationDB deterministic simulation/testing. Seeded deterministic simulation makes complex distributed failures reproducible, while complementary real/API testing covers nondeterminism not modeled by the simulator.
- **IMPLEMENTATION PRECEDENT:** record/replay debugging literature records nondeterministic inputs/decisions to reproduce races and failures.

Fusion consequence: deterministic-by-default execution plus explicit recorded nondeterministic choices is a stronger candidate than pretending one fixed global scheduler captures all production semantics. Outside-in faulting remains complementary.

## C6 — Adaptive lesion / compensation

- **PARTIAL ANALOGUE:** neural lesion/plasticity studies report immediate causal impairment followed by network compensation/recruitment over different time scales.
- **THEORY/MEASUREMENT CAUTION:** activity and causal contribution can dissociate; perturbation design and timing matter.

Fusion consequence: in an adaptive FRANK, lesion effect must be indexed by intervention time, learner state and compensation trajectory. Recovery after adaptation does not by itself refute the acutely lesioned mechanism.

## C7 — Cross-implementation causal equivalence

- **DIRECT THEORY ANALOGUE:** Massidda et al., *Causal Abstraction with Soft Interventions* (CLeaR/PMLR 2023) requires an explicit intervention map between abstraction levels.
- **DIRECT THEORY ANALOGUE:** Otsuka & Saigo, *On the Equivalence of Causal Models* (CLeaR/PMLR 2022) treats consistent translation of intervention calculus as part of causal-model equivalence.
- **IMPLEMENTATION/THEORY PRECEDENT:** Geiger et al., *Inducing Causal Structure for Interpretable Neural Networks* (ICML 2022) uses aligned interchange interventions to test whether a representation realizes a causal abstraction.

Fusion consequence: H1/H2/H3 state/output equivalence is insufficient for causal equivalence. The semantic intervention itself must be translated and validated under the representation mapping.

## C8 — Provenance echo / dependent evidence

- **PARTIAL ANALOGUE / FAILURE MODE:** Krishnamurthy & Hoiles, *Online Reputation and Polling Systems: Data Incest, Social Learning and Revealed Preferences* (2015). Re-use of the same underlying information while treating observations as independent produces overconfidence/bias; graph-aware correction is needed.

Fusion consequence: repeated evidence with shared ancestry must not count as independent reversal evidence. This supports lineage-aware weighting/diversity, but does not establish a universal RAB threshold; the internal benchmark itself shows adaptation penalties at higher diversity requirements.

## Independence and evidence-class audit

- External papers/docs above are independent of the Clay repository.
- Internal synthetic/CI receipts remain internal evidence even when many workers converge on them.
- No external source directly validates live FRANK, Andreas' Ubuntu target, ClayCode production compiler semantics, or the project's exact GWT/ClayGraph/MVC implementation.
- No canonical scientific promotion is justified by this ledger alone.
