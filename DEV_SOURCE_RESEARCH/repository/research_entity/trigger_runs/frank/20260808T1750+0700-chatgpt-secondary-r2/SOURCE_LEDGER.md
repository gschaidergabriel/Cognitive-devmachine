# FRANK C6 External Research Ledger — Clay-Native Full-Model Substrate

Evidence classes remain separate. These sources constrain/design the target; they do not prove target-Qwen3-4B behavior.

## Model language adaptation / forgetting

1. **Elhady, Agirre, Artetxe — Emergent Abilities of LLMs under Continued Pre-training for Language Adaptation (ACL 2025, DOI 10.18653/v1/2025.acl-long.1547).** Target-language-only CPT can exhibit early catastrophic forgetting not visible in target validation perplexity; source-language mixing, curriculum learning and EMA mitigate parts of the problem. **C6 implication:** Clay perplexity/language-purity cannot be the only stopping criterion; retain frozen baseline capability probes and test staged curricula/EMA/replay.

2. **Yamaguchi et al. — Source-Shielded Updates (ACL 2026, DOI 10.18653/v1/2026.acl-long.865).** Across 7B/13B language adaptation, source-task degradation averaged 20.3%/22.3% for full fine-tuning versus 3.4%/2.8% with protected source-important parameters, while target performance remained competitive. **Boundary:** their method selectively freezes updates and therefore is not the owner-required full-model recipe. **C6 implication:** forgetting risk under full FT is material; C6 should test full-parameter alternatives such as source capability replay, teacher distillation, EMA, regularization and staged LR rather than assuming full FT preserves knowledge.

3. **Liao et al. — Exploring Forgetting in LLM Pre-Training (ACL 2025).** Forgetting exists during pretraining and standard perplexity is insufficient to measure retained entity knowledge. **C6 implication:** evaluate retained facts/skills directly, not only loss.

4. **Towards Effective and Efficient Continual Pre-training of LLMs (ACL 2025).** Data mixture, curriculum and performance-tracking strategies are central to balancing new and retained capabilities. **C6 implication:** Clay full FT should be an adaptive multi-metric curriculum, not a single static corpus.

## Tokenizer / vocabulary

5. **Abagyan et al. — One Tokenizer To Rule Them All: Emergent Language Plasticity via Multilingual Tokenizers (ACL 2026, DOI 10.18653/v1/2026.acl-long.141).** Broader tokenizer coverage improved later language adaptation, with reported win-rate gains up to 20.2% over pretraining-language-specific tokenizers and gains even for unseen languages. **C6 implication:** tokenizer design affects plasticity; Clay vocabulary should be treated as part of training architecture.

6. **Purason et al. — Teaching Old Tokenizers New Words (arXiv:2512.03989, 2025).** Continued BPE training improves use of newly added domain/language vocabulary compared with naive append-only extension. **C6 implication:** benchmark unchanged Qwen BBPE vs preserved-ID extension vs continued Clay-specific merge learning.

7. **Ali et al. — Tokenizer Choice For LLM Training: Negligible or Crucial? (arXiv:2310.08754).** At 2.6B scale tokenizer choices materially changed downstream quality/training cost; inefficient language fit produced large extra cost in tested settings. **C6 implication:** project byte/character compactness is not enough; measure actual Qwen token fertility, semantics and runtime.

8. **Qwen3 official documentation/model card.** Qwen uses byte-level BPE with a large vocabulary (~151k token family); Qwen3-4B is a 4.0B dense causal LM with 36 layers and hidden size 2560. **C6 implication:** adding a few thousand Clay primitives is modest compared with the existing embedding matrix, while wholesale token-ID replacement risks a much larger retraining problem. Existing vocabulary may remain for input competence even if output is Clay-only.

## Learned intermediate representations / DSLs

9. **Paul, Glavaš, Gurevych — IRCoder (arXiv:2403.03894).** Continued causal LM training on nearly 4M source-code/LLVM-IR pairs taught 1.1B–7.3B models the IR and aligned it with multiple programming languages, improving robustness, completion, understanding and instruction following. **C6 implication:** learning a shared machine IR is empirically plausible; parallel natural/code/state <-> Clay corpora are high-value.

10. **NormCode (arXiv:2512.10563).** Separates semantic probabilistic operations from deterministic syntactic/data-flow operations and enforces context isolation. **C6 implication:** one language does not mean one authority/evaluation mode; deterministic Clay operators and probabilistic Clay reasoning need explicit types.

11. **Anka DSL (arXiv:2512.23214).** A constrained DSL can reduce sequencing/state-management errors despite little/no prior language exposure in reported experiments. **Boundary:** preprint/specific benchmark. **C6 implication:** syntax can encode useful inductive bias; full native training can exploit stronger constraints than prompting alone.

12. **Learn2Zinc (arXiv:2607.20456).** Out-of-box small models had near-zero execution accuracy on rare MiniZinc; targeted fine-tuning raised execution validity dramatically, while solution accuracy remained substantially lower. **C6 implication:** distinguish `Clay syntax learned` from `Clay semantics/reasoning learned`; both need separate metrics.

13. **Grammar Prompting for DSL Generation (NeurIPS 2023).** Grammar constraints help LLMs generate structured DSLs. **C6 implication:** grammar/constrained decoding can remain a runtime backstop even after native training.

14. **MLIR / official MLIR dialect and conversion architecture.** One extensible IR can retain multiple abstraction-level dialects and lower typed semantics toward hardware-specific representations. **C6 implication:** “everything is Clay” should mean one semantic IR family with canonical/model/wire/tensor/platform dialects, not one literal text format.

## Latent language / what “thinking Clay” can mean scientifically

15. **Wendler et al. — Do Llamas Work in English? (ACL 2024).** Intermediate representations in multilingual transformers can show language-like phases and a dominant-language tendency.

16. **Ozaki et al. — Do LLMs Need to Think in One Language? (arXiv:2505.21458).** Consistency in inferred latent language was not always necessary for best downstream performance; later layers can adapt toward target output language. **C6 implication:** operationalize “FRANK thinks Clay” as native explicit deliberation/state generation plus causal alignment/probes; do not claim every hidden activation literally is a discrete Clay sentence.

## ClayGraph / persistent memory

17. **Graph-based Agent Memory survey (arXiv:2602.05665).** Separates extraction, storage, retrieval and evolution across graph memory lifecycles. **C6 implication:** ClayGraph should remain a lifecycle/substrate, not a monolithic `query graph` operation.

18. **MRAgent — Memory is Reconstructed, Not Retrieved (arXiv:2606.06036).** Associative graph plus active reconstruction can adapt memory access to intermediate reasoning and reduce costs on reported long-memory benchmarks. **C6 implication:** native Clay can tighten memory<->reasoning interaction, but bounded reconstruction remains important.

19. **MAGMA (ACL 2026).** Uses orthogonal semantic/temporal/causal/entity graph views with query-adaptive traversal. **C6 implication:** semantic unity is compatible with multiple typed relation/topology views, consistent with Hyperposition S/C/P/Q and ClayGraph epochs.

20. **SAGE (arXiv:2605.12061).** Self-evolving graph memory couples writer/reader feedback. **C6 implication:** useful architecture analogue but raises the exact C6 danger of correlated reader-writer feedback; Goodman ancestry and exact authority boundaries remain mandatory.

21. **ShadowMerge (arXiv:2605.09033) / MemMorph (arXiv:2605.26154).** 2026 preprints expose graph-memory relation poisoning and memory-driven tool hijacking as practical attack surfaces. **C6 implication:** because Clay-native memory is closer to cognition/action, selection provenance, epistemic types and Needle independence become stronger—not weaker—requirements.

## Vectors / discrete symbolic bridges

22. **ReaLM (arXiv:2510.09711).** Residual vector quantization maps KG embeddings into compact learnable token sequences for LLM integration. **C6 implication:** Clay can bridge graph/vector/model spaces with discrete codes, but those codes remain derived representations.

23. **Representation Collapsing Problems in Vector Quantization (arXiv:2411.16550).** Codebook/embedding collapse can reduce discriminative capacity. **C6 implication:** any Clay vector-token codebook needs occupancy/diversity/collision monitoring.

24. **TokenCast (arXiv:2508.09191) and prior language-tokenized numeric work.** Continuous values can be discretized into language-like tokens to create a common modeling interface, but discretization changes geometry. **C6 implication:** low-dimensional cognitive values may have Clay token projections; exact numeric payloads/order-aware loss remain available when metric precision matters.

25. **Vector Symbolic Architecture surveys (arXiv:2111.06077 / 2112.15424).** High-dimensional vectors can combine symbolic structure and distributed representations through binding/bundling operations. **C6 implication:** useful research transfer for ClayVector/Hyperposition, not evidence that transformer hidden states or ClayGraph should be replaced by a VSA.

## Privilege / homoiconicity

26. **Wallace et al. — The Instruction Hierarchy (arXiv:2404.13208).** Prompt injection partly stems from models treating differently privileged text as comparable instructions; training explicit instruction priority improves robustness. **C6 implication:** a single Clay language must encode privilege/role structurally and train it, not rely on punctuation or natural-language warnings.

## Project evidence integrated

27. **Clay G9 EPOCH.** Selection-integrity and deterministic-before-generative boundaries; raw vs compiled Groq proxy 6/10 -> 8/10 with fewer prompt tokens; remains HOLD.

28. **ClayGraph G1d Cycle 4.** Semantic epochs + sparse latent field; 30k-node proxy measured lazy touched-node activation median 0.028 ms vs 1.098 ms eager dense decay; cognition benefit unproven; accepted graph remains G0.

29. **ClayCode CC9 CBCC.** Operation-specific multi-epoch basis, canonical resource identity and compositional closure; constructed mixed-basis and alias counterexamples plus Judge0 replication.

30. **GWT Run 4.** A bundled graph+workspace+projection contrast manufactured a large apparent workspace effect in a constructed null where clean workspace intervention recovered zero. **C6 implication:** all-Clay semantics does not eliminate causal-stage confounding.

31. **Hyperposition H3.** Epoch-pinned adaptive topology, relation-instance role identity, bounded activation and workload-aware rematerialization.

32. **FRANK C5.** Certified Cognitive Basis + Reader ABI + Selection Integrity already separates truth, activation, GWT, reader projection and authority. C6 changes the Reader ABI from cross-language translation into a Clay-native view/lowering compiler and makes the whole target architecture semantically Clay-native.

33. **Recovered project source: Synthetic Clay memory/database transcendence.** The intended architecture is that persistent Clay state continues between LLM calls and cue-triggered relations can influence the next Assembly before an explicit memory-search decision. This is a project hypothesis/target concept, not independent evidence.
