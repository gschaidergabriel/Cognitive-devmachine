# HYPOFUSION External Evidence Ledger

Run: `hypofusion-20260811T2258p0700-chatgpt-secondary`

Evidence was searched by mechanism, not Clay terminology. Primary/official sources dominate; no external source is promoted beyond its tested scope.

## HF-C1 Consume-bound semantic continuity

- **SLSA Build: Verifying artifacts v1.2** — `DIRECT_SUPPORT` for the narrow proposition that provenance metadata has no operational assurance value until a consumer/verifier checks it against expectations before use. Source: https://slsa.dev/spec/v1.2/verifying-artifacts
- **SLSA Provenance** — `IMPLEMENTATION_PRECEDENT` for binding subject/build information so consumers can verify an artifact against expected provenance. Source: https://slsa.dev/spec/v1.0-rc2/provenance
- Scope limit: SLSA is software-supply-chain provenance, not a proof that one universal Frank CBPC abstraction dominates branch-local contracts.

## HF-C2 Reward frontier and exactly-once

- **SQLite Isolation** — `DIRECT_SUPPORT` for snapshot semantics in WAL mode: a read transaction sees an unchanging database snapshot while concurrent writes can commit outside that snapshot. This matches the new internal concern that a deterministic fold can be a valid prefix yet not current. Source: https://sqlite.org/isolation.html
- **SQLite Database Snapshot API** — `IMPLEMENTATION_PRECEDENT` for explicit historical snapshot identity in WAL mode. Source: https://sqlite.org/c3ref/snapshot.html
- **Apache Kafka Design / transactions** — `IMPLEMENTATION_PRECEDENT` that exactly-once processing needs atomic coordination of consumed position/frontier with produced output; idempotence alone is insufficient for end-to-end exactly-once state. Source: https://kafka.apache.org/41/design/design/
- Counterweight: if Frank machine-enforces a topology in which terminal writes cannot coexist with reward folding, a separate frontier primitive may be unnecessary.

## HF-C3 Latent observability vs actionability

- **How Reliable are Causal Probing Interventions? (IJCNLP-AACL 2025)** — `COUNTEREVIDENCE/FAILURE_MODE`: causal probing methods trade completeness against selectivity; stronger interventions can alter non-target properties. Source: https://aclanthology.org/2025.ijcnlp-long.47/
- **Linear Probes Detect Task Format, Not Reasoning Mode in Language Model Hidden States (2026)** — `COUNTEREVIDENCE`: perfect-seeming probe separation can disappear after removing format confounds; reported steering did not establish a functional reasoning-mode link. Source: https://arxiv.org/abs/2606.02907
- **Interpretability without actionability (2026)** — `COUNTEREVIDENCE`: near-perfect internal discrimination did not translate into reliable error correction; some steering caused large collateral damage. Source: https://arxiv.org/abs/2603.18353
- **From Emergence to Control: Probing and Modulating Self-Reflection in Language Models (2025)** — `DIRECT_SUPPORT_WITH_SCOPE`: self-reflection-associated hidden-state directions can be manipulated bidirectionally and can affect reasoning/compute tradeoffs in tested models. Source: https://arxiv.org/abs/2506.12217
- **Sparse Auto-Encoder Interprets Linguistic Features in LLMs (2025)** — `PARTIAL_ANALOGUE`: explicitly separates representation confidence from intervention confidence, reinforcing observability/actionability as distinct measurements. Source: https://arxiv.org/abs/2502.20344
- **Understanding (Un)Reliability of Steering Vectors in Language Models (2025)** — `FAILURE_MODE`: steering vectors show high sample variance and can move behavior opposite the target when the behavior is not represented by a coherent direction. Source: https://arxiv.org/abs/2505.22637
- Fusion effect: strengthens LCOP as an *instrumented evidence plane* while weakening any proposal to let probe accuracy directly authorize runtime control.

## HF-C4 Dual workspace

- **Verbalizable Representations Form a Global Workspace in Language Models (2026)** — `PARTIAL_ANALOGUE`: reports a privileged, verbalizable intermediate representation set with workspace-like functional properties inside language models. Source: https://arxiv.org/abs/2607.15495
- **Coordination Among Neural Modules Through a Shared Global Workspace (ICLR 2022)** — `IMPLEMENTATION_PRECEDENT`: bandwidth-limited shared workspace can coordinate specialized modules and encourage specialization/synchronization. Source: https://openreview.net/forum?id=XzTtHjgPDsT
- **Zero-shot cross-modal transfer through a Global Workspace (2024)** — `IMPLEMENTATION_PRECEDENT`: shared-workspace representation can improve cross-modal transfer under tested conditions. Source: https://openreview.net/forum?id=3afe0i8YxX
- Counterhypothesis remains strong: the 2026 J-space result is model/method specific and may be redundant with explicit ClayGWT; architectural analogy alone does not prove two useful workspaces.

## HF-C5 Persona/appraisal/identity timescales

- **Persistent Instability in LLM Personality Measurements (2025)** — `COUNTEREVIDENCE` against treating psychometric outputs as stable persistent personality: prompt order, persona instructions, reasoning mode and history can materially shift measured traits across many models. Source: https://arxiv.org/abs/2508.04826
- **Cultural Value Alignment via Latent Activation Steering (2026)** — `PARTIAL_ANALOGUE/FAILURE_MODE`: behavioral/latent value dimensions can be steered, but interventions can entangle multiple dimensions. Source: https://arxiv.org/abs/2605.26365
- Fusion effect: strengthens factorization of owner-fixed identity, contextual persona, fast appraisal and slow regulatory state; weakens any single psychometric/persona-vector representation.

## HF-C6 Binary/quantization latent revalidation

- **From Attention to Activation (ICLR 2025)** — `FAILURE_MODE/PARTIAL_ANALOGUE`: hidden-state activation outliers strongly interact with low-bit quantization quality, demonstrating that low-precision transformation is not representation-neutral. Source: https://openreview.net/forum?id=IjduZQK8gM
- **CBQ (ICLR 2025)** and **GuidedQuant (ICML 2025)** — `IMPLEMENTATION_PRECEDENT`: quantization error depends on inter-layer/intra-layer dependencies and feature importance, so behavioral preservation does not imply identical latent geometry. Sources: https://openreview.net/forum?id=eW4yh6HKz4 and https://openreview.net/forum?id=ZawsPjlIGu
- No primary source located in this run directly proving steering/probe transfer invariance across Frank-relevant build/quantization changes. Therefore `H-BINARY-08` remains a conservative revalidation obligation, not a supported claim that transfer always fails.

## HF-C9 SQLite source/topology gate

- **SQLite WAL documentation, WAL-reset bug** — `DIRECT_SUPPORT`: bug present through 3.51.2, fixed in 3.51.3+, requiring WAL mode plus multiple connections and concurrent write/checkpoint timing. Source: https://sqlite.org/wal.html
- **SQLite 3.51.3 release notes** — `DIRECT_SUPPORT` for the fix boundary. Source: https://www3.sqlite.org/releaselog/3_51_3.html
- Fusion effect: current project rejection of an unverified/vulnerable 3.45.1 WAL source remains justified unless exact backport provenance or an enforced unreachable topology is proved.

## Evidence discipline

Matching architecture is `PARTIAL_ANALOGUE` until the same causal mechanism is tested. High decoding accuracy is not causal control. Successful steering is not unique representation. Psychometric stability is not identity. Provenance recording is not consumer verification. Idempotence is not snapshot completeness. Quantized task accuracy is not latent-basis equivalence.
