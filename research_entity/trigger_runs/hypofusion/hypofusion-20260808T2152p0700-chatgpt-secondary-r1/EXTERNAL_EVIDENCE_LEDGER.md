# Hypofusion H1 — External Evidence Ledger

run_id: `hypofusion-20260808T2152p0700-chatgpt-secondary-r1`
actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol

This ledger separates evidence classes. Similarity to an RAE mechanism is not independent validation of the complete FRANK/Clay stack. Counterevidence is treated as a possible competing explanation or failure mode until discriminating tests decide.

## 1. Long context, selective memory and context interference

### Chroma — Context Rot: How Increasing Input Tokens Impacts LLM Performance
URL: https://www.trychroma.com/research/context-rot
Class: technical research report; replication code at https://github.com/chroma-core/context-rot
Finding: across 18 tested LLMs, use of context became less reliable as input length increased; distractors and structure matter.
Transfer: supports bounded/selective context construction and challenges any assumption that persistent continuity should mean injecting more state into every prompt.
Boundary: not a test of CACC/ClayGraph or FRANK.

### Lost in the Middle
URL: https://arxiv.org/abs/2307.03172
Class: scholarly preprint / widely cited long-context study.
Finding: model use of relevant information varies strongly with position; middle information can be used less reliably.
Transfer: independent argument for selective Assembly/retrieval rather than raw full-history context.

### LongMemEval-V2
URL: https://arxiv.org/abs/2605.12493
Class: 2026 preprint.
Finding: compact evidence-gathering memory methods materially differ in accuracy and latency; a coding-agent memory method reached 72.5% average accuracy vs 48.5% for the strongest reported RAG baseline, but with high latency.
Transfer: memory architecture is an accuracy-latency problem, not simply storage capacity.

### MemGPT / Letta
URL: https://github.com/letta-ai/letta
Class: current open-source implementation.
Finding: stateful agents explicitly manage limited active context and longer-term memory.
Transfer: strong implementation analogue for selective persistent memory; not evidence for Clay's causal receipts or GWT.

## 2. Temporal/relational active memory

### Synapse — Findings ACL 2026
URL: https://aclanthology.org/2026.findings-acl.1108/
DOI: 10.18653/v1/2026.findings-acl.1108
Class: peer-reviewed conference findings paper.
Finding: dynamic graph memory with spreading activation, lateral inhibition, temporal decay and hybrid retrieval improves complex temporal/multi-hop reasoning in its evaluation.
Transfer: direct independent analogue for ClayGraph activation/inhibition/decay and dual-path retrieval.

### MAGMA — ACL 2026
URL: https://aclanthology.org/2026.acl-long.1709/
DOI: 10.18653/v1/2026.acl-long.1709
Class: peer-reviewed ACL long paper.
Finding: separates semantic, temporal, causal and entity graph views and uses policy-guided traversal.
Transfer: supports explicit role/time/causal relation identity rather than flattening all memory into one embedding space.

### HippoRAG
URL: https://arxiv.org/abs/2405.14831
Code: https://github.com/OSU-NLP-Group/HippoRAG
Class: research + implementation.
Finding: graph/PPR long-term memory can outperform conventional RAG on multi-hop tasks while reducing iterative retrieval cost in reported settings.
Transfer: supports graph-mediated associative retrieval as a useful mechanism class.

### Graphiti / Zep
URL: https://github.com/getzep/graphiti
Paper: https://arxiv.org/abs/2501.13956
Class: implementation + preprint.
Finding: temporal validity, provenance episodes, incremental graph updates and hybrid semantic/full-text/graph retrieval.
Transfer: unusually close external analogue for temporal/provenance-preserving derived memory.
Boundary: project/author benchmark claims require independent replication.

## 3. Latent communication and reader rails

### Interlat — ACL 2026
URL: https://aclanthology.org/2026.acl-long.1248/
Class: peer-reviewed ACL paper.
Finding: hidden-state inter-agent communication is technically feasible and can improve compression/latency/task outcomes in its setting.
Transfer: supports P3/latent rails as an optimization candidate.

### Latent Communication Between Language Model Agents
URL: https://arxiv.org/abs/2607.14103
Class: 2026 preprint; important counterevidence.
Finding: latent/SAE channels retained substantially more probe-visible information than text, yet never exceeded text at task level in reported experiments; latent augmentation gave no benefit.
Transfer: strongly supports the CACC rule `information retention != cognitive utility`.

### Do Latent Channels Actually Communicate? A Causal Audit
URL: https://arxiv.org/abs/2607.26773
Class: 2026 preprint; direct Qwen3-4B/Qwen3-8B causal audit.
Finding: aggregate task accuracy can hide opposing effects; message presence, example-specific content and other-agent value are distinct causal quantities.
Transfer: upgrades the MRSC/P3 experiment design: every rail needs controlled message replacement, not only end-task scoring.

## 4. Workspace mechanisms and their limits

### Verbalizable Representations Form a Global Workspace in Language Models
URL: https://arxiv.org/abs/2607.15495
Lab summary: https://www.anthropic.com/research/global-workspace
Code: https://github.com/anthropics/jacobian-lens
Class: 2026 research paper + released implementation.
Finding: a privileged verbalizable latent J-space in Claude exhibits reportability, top-down modulation, silent intermediate reasoning, broad downstream reuse and causal load-bearing behavior under interventions.
Transfer: strong external support for GWT R5's new distinction between FRANK's system WorkspaceEpisode and a potentially separate model-internal workspace uptake stage.
Boundary: not evidence that Qwen3-4B has the same mechanism; not proof of phenomenal consciousness.

### Coordination Among Neural Modules Through a Shared Global Workspace
URL: https://arxiv.org/abs/2103.01197
Class: peer-reviewed/research lineage.
Finding: bandwidth-limited shared workspace can promote specialization and synchronization.
Transfer: supports testing a non-monotonic/bounded workspace-capacity hypothesis rather than assuming unlimited broadcast is best.

### Biological GNWT/IIT adversarial testing
Class: preregistered adversarial neuroscience evidence (Nature, 2025).
Finding: important predictions of both theories were challenged.
Transfer: biological GWT remains a mechanism source and analogy, not a settled template that can be copied into FRANK.

## 5. Higher-order interaction / Hyperposition

### The Physics of Higher-Order Interactions in Complex Systems
URL: https://www.nature.com/articles/s41567-021-01371-4
Preprint: https://arxiv.org/abs/2110.06023
Class: Nature Physics review.
Finding: pairwise networks can miss genuinely group-level interactions; hypergraphs/simplicial complexes are appropriate in many systems.
Transfer: supports explicit n-ary/higher-order relation identity.

### HyperGraphRAG
URL: https://arxiv.org/abs/2503.21322
Class: research preprint.
Finding: hypergraphs are used to preserve n-ary relationships for RAG instead of reducing every relation to binary edges.
Transfer: concrete AI analogue for Hyperposition/ClayGraph n-ary semantics.

### Hypergraph oversmoothing counterevidence
URL: https://arxiv.org/abs/2607.15773
Class: 2026 preprint.
Finding: stronger multi-way propagation can intensify representation collapse/oversmoothing; reaction-diffusion is proposed as mitigation.
Transfer: higher-order representation does not justify unlimited propagation. ClayGraph/Hyperposition need depth/budget/diversity/inhibition tripwires.

## 6. Emergence and causal synergy

### Partial Effective Information Decomposition for Synergistic Causality
URL: https://arxiv.org/abs/2605.03267
Class: 2026 preprint.
Finding: intervention-grounded decomposition of multivariate influence into unique and synergistic components; can define hyperedge/downward-causal structures.
Transfer: promising E-CERT2 statistic only after intervention identity and reproducible functional effects exist.

### Dewhurst — Causal emergence from effective information: Neither causal nor emergent?
URL: https://doi.org/10.1002/tht3.489
Class: peer-reviewed philosophical/methodological critique.
Finding: argues that effective-information causal emergence may establish an epistemic rather than stronger ontic causal-emergence claim.
Transfer: direct counterargument against promoting FRANK emergence from one information-theoretic scalar.

## 7. UnifiedDB, event sourcing and incremental state

### Polystore architecture using knowledge graphs
URL: https://arxiv.org/abs/2308.03584
Class: research paper/preprint.
Finding: heterogeneous stores can be exposed through a global conceptual schema; reported query-writing simplification came with up to roughly 30% processing overhead in its evaluated scenario.
Transfer: independently supports UnifiedDB's logical-unification/physical-specialization direction while preserving a real overhead counterargument.

### Incremental View Maintenance
URL: https://arxiv.org/abs/1703.07484
Class: research.
Finding: factorized IVM can outperform recomputation substantially in suitable workloads.
Transfer: supports delta-driven rebuildable derived views, not universal incremental superiority.

### Event-sourcing engineering guidance
Sources: AWS Prescriptive Guidance and Microsoft Azure Architecture Center event-sourcing patterns.
Class: authoritative cloud architecture documentation.
Finding: immutable event history/replay gives audit/reconstruction advantages but introduces eventual consistency, idempotency, schema evolution and operational complexity.
Transfer: supports canonical event spine plus explicit countercosts.

### Apache Arrow C Data Interface
URL: https://arrow.apache.org/docs/format/CDataInterface.html
Class: authoritative specification.
Finding: zero-copy sharing is a same-process interface; cross-process transport/persistence require separate mechanisms.
Transfer: preserves CORF's process-boundary distinction.

## 8. ClayCode / typed IR

### IR2Solve
URL: https://arxiv.org/abs/2608.02641
Class: very recent preprint.
Finding: a schema-constrained IR plus deterministic verification/compilation reduces brittle direct LLM code generation and can reduce semantic-call/token cost in reported optimization tasks.
Transfer: independent convergence with ClayCode's `model proposes typed semantics -> deterministic lowering/validation` architecture.

### SkCC
URL: https://arxiv.org/abs/2605.03353
Class: 2026 preprint / current implementation.
Finding: strongly typed SkIR decouples skill semantics from framework-specific formatting and applies compile-time security checks; reported pass-rate and token improvements vary by target framework.
Transfer: strong analogue for canonical semantics plus reader/target-specific compiled surfaces.

## 9. Authority and runtime security

### Securing Agents With Tracked Capabilities
URL: https://doi.org/10.1145/3786335.3813127
Class: peer-reviewed ACM CAIS 2026.
Finding: capability tracking/type-based safety around agent effects/resources.
Transfer: independent support for structural authority boundaries.

### Task Shield — ACL 2025
URL: https://aclanthology.org/2025.acl-long.1435/
Class: peer-reviewed ACL paper.
Finding: task-alignment checks can substantially reduce indirect prompt-injection attack success while retaining task utility in its benchmark.
Counterboundary: demonstrates prompt/model-level defense can help; does not prove it is a sufficient execution boundary.

### Runtime Policy Enforcement for MCP-Based LLM Agents
URL: https://www.mdpi.com/2079-9292/15/13/2829
DOI: 10.3390/electronics15132829
Class: peer-reviewed 2026 journal article.
Finding: deterministic policy enforcement at the actual tool-call boundary substantially outperformed its prompt-only baseline in the reported controlled evaluation; cross-step labels materially contributed.
Transfer: particularly close external analogue for FRANK's isolated capability/effect broker and provenance/information-flow tracking.
Boundary: authors explicitly bound the confirmatory strength of some evaluation subsets.

## 10. Full-model adaptation and tokenizer risk

### Source-Shielded Updates — ACL 2026
URL: https://aclanthology.org/2026.acl-long.865/
DOI: 10.18653/v1/2026.acl-long.865
Class: peer-reviewed ACL long paper.
Finding: standard full fine-tuning caused large source-task degradation in tested 7B/13B language adaptation settings; selective protection reduced degradation substantially.
Transfer: does not overturn the owner-fixed full-model Clay adaptation target, but makes retained-capability shadow gates mandatory evidence rather than optional hygiene.

### Tokenizer/vocabulary adaptation
Class: current NLP research programme including continued-BPE and compatibility-preserving vocabulary adaptation.
Transfer: supports G12's tokenizer factorial; symbolic compactness cannot be assumed to equal model-native efficiency.

## 11. Edge/mobile

Class: official Qwen model geometry + current on-device inference/KV-cache research + practitioner deployments.
Finding: 4B-class local inference is feasible on some devices, but total performance depends strongly on context/prefill, KV precision/cache, backend, RAM, thermal state and sustained workload.
Transfer: strengthens an adaptive resource governor and bounded Assembly rather than a fixed maximum context target.
Boundary: no live FRANK/Qwen Android benchmark was produced in this Hypofusion.

## 12. Bridge / popular-science sources

### Nautilus — Why Conscious AI Is a Bad, Bad Idea
URL: https://nautil.us/why-conscious-ai-is-a-bad-bad-idea-302937
Class: popular-science/opinion bridge by Anil Seth; not primary evidence.
Use: highlights the conceptual error of equating intelligence or humanlike behavior with consciousness and points back toward the need for experimentally grounded criteria.
Transfer: compatible with the RAE boundary that GWT, memory, self-report or integration cannot by themselves establish phenomenal consciousness.

## Overall external result

The strongest external convergence is not with one monolithic Clay architecture. It is with a **pattern**:

- keep active context selective and bounded;
- preserve temporal/provenance structure;
- use hybrid relational/retrieval mechanisms rather than one similarity channel;
- separate canonical semantics from reader/platform-specific representations;
- keep deterministic verification and effect authority outside generative interpretation;
- test workspace/internal communication causally rather than through end accuracy;
- represent higher-order relations when needed but control propagation;
- treat emergence as a multimetric intervention problem.

The strongest external challenges are equally useful:

- more context can hurt;
- graph/hypergraph propagation can oversmooth;
- latent channels can retain information without improving tasks;
- event sourcing/polystores add complexity and consistency overhead;
- full fine-tuning can forget;
- prompt-level security helps but does not close the execution boundary;
- effective-information-style emergence claims remain conceptually contested.
