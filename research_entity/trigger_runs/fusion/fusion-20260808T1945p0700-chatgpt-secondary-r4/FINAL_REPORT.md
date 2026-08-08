# FUSION R4 — AI-Native Programming Languages & AI Speech

**run_id:** `fusion-20260808T1945p0700-chatgpt-secondary-r4`  
**actor:** `chatgpt-secondary`  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c...`  
**upstream:** validated Fusion-1855 CLAY-L4 + current ClayCode CC10 / CC-RC1.5-ICSL  
**promotion:** NONE — architecture/hypothesis delta only

## 1. Executive result

The broad literature does not support a single universal object called an "AI-native programming language" or "AI mother tongue". It supports a **stack of distinct representations with different jobs**.

The strongest R4 result is an OPEN revision of CLAY-L4:

## CLAY-L5 — Five-Plane AI-Native Speech Contract

1. **P0 External Intent** — human/agent prose, goals, vibe, constraints.
2. **P1 Canonical Clay Semantics** — exact typed meaning, claims, causal basis, requirements and authority dependencies.
3. **P2 Discrete Native Rail** — learned model-facing symbols/handles/codebooks.
4. **P3 Latent Native Rail** — hidden states, embeddings or KV-like continuous communication/reasoning state.
5. **P4 Effect/Physical Runtime** — deterministic lowering, tool effects, DB/binary/machine operations and receipts.

Fusion-1855 already separated intent, canonical semantics, native symbols and neural/physical implementation. R4 changes one important point: **hidden-state/KV representations can be a functional cognitive and inter-agent communication medium and therefore need their own causal identity rather than being bundled with passive physical implementation.**

The resulting design is a semantic spine with multiple projections, not one syntax.

## 2. Taxonomy: what the field currently calls AI-native

### A. Intent-native programming

Vibe-coding and related work move the human authoring surface upward from exact syntax to goals, constraints, qualitative preferences and iterative feedback. This is useful for P0 but weak as execution semantics. Ambiguity, reproducibility, maintenance and security remain unsolved if prose itself remains the program.

**RAE consequence:** P0 must compile into a typed intent contract rather than directly becoming truth or effect.

### B. Languages for programming LLM systems

LMQL, PDL, SGLang, Guidance, Outlines and DSPy represent a mature trend: prompting is being converted into explicit programs, constraints, modules, control flow, typed data and optimized runtimes.

- **LMQL** combines text prompting, scripting and output constraints and reports substantial cost savings in its evaluation.
- **PDL** makes prompt/data/model/tool composition declarative and typed.
- **SGLang** co-designs a frontend language with an optimized runtime and structured decoding.
- **Guidance/Outlines** constrain generation at decoding time.
- **DSPy** separates declarative LM-program structure from model-specific prompt/weight optimization.

These are evidence for model-centered programming abstractions, **not evidence that a model internally thinks in their surface syntax**.

### C. Canonical AI/agent executable IR

AINL, COVENANT, SIGIL, FAVA and ETAS converge on a deeper architecture pattern:

`flexible authoring -> explicit IR/graph/types -> validation -> controlled runtime`

- AINL uses graph-first canonical node/edge IR, strict validation and compile-once/run-many execution.
- COVENANT treats workflow prose as source code, compiles it to WAST/WCFG and reports success improving from 50.00% to 83.33% while workflow misalignment falls from 42.50% to 15.83%.
- SIGIL compiles prose skills to typed AG-IR harnesses; mandated-step completion improves from 56% to 86%, full procedure completion increases 2.3x and token use is 0.58x.
- FAVA converts natural-language permission intent into Permission IR, deterministically lowers to an evidence graph and uses SMT before effects; it reports 90.5% aggregate Decision Compliance Rate.
- ETAS gives agent actions, prompts, memory, approvals and traces explicit static/dynamic semantics.
- Proof-Carrying Agent Actions similarly separates proposed action from portable authorization/evidence receipts.

**RAE consequence:** CC-RC1.5 ICSL has strong independent architecture-class support. Natural language or native Clay fluency should never bypass adequacy, capability or commit boundaries.

### D. Learned discrete AI-native speech

The AI Mother Tongue papers and broader emergent-communication work demonstrate that learned symbol/codebook systems are feasible. VQ/VQ-VAE-like discrete bottlenecks can produce reusable symbols and compositional chains.

But the evidence does not justify calling any stable codebook a natural or universal mother tongue. Emergent protocols are sensitive to objective, environment and inductive bias; successful protocols can be opaque and non-systematic. Fusion-1855 further showed by synthetic null that high symbol purity can coexist with zero causal contribution.

Current CC10 gives a direct internal negative result: on an untrained Groq 8B proxy, raw L0 scored 15/16, verbose typed L1 14/16 and compact symbolic representation 9/16. Compactness saved prompt tokens but damaged semantic accuracy.

**RAE consequence:** P2 must be learned and evaluated against causal utility, OOD/compositional generalization, drift and cost — not designed around visual compactness or purity alone.

### E. Continuous latent reasoning

Coconut feeds an LLM's last hidden state back as the next input embedding instead of forcing an intermediate word token. Its results show that continuous reasoning can help on tasks requiring planning/backtracking and can use fewer explicit thinking tokens.

This is important but not conclusive. Community control work has raised a plausible counterhypothesis that part of Coconut's gain may come from curriculum/multi-pass training rather than message content itself. That evidence is not peer-reviewed, but it correctly motivates factorial controls.

**RAE consequence:** latent reasoning is an experimental P3 mechanism, not a reason to eliminate P1/P2.

### F. Continuous latent agent-to-agent communication

Interlat (ACL 2026) is the strongest peer-reviewed evidence in this category. It communicates via last hidden states, reports gains against text/CoT baselines and up to 24x acceleration with learned compression while maintaining competitive performance.

LatentMAS adds implementation evidence for training-free latent collaboration/shared working memory.

A 2026 survey organizes latent communication by WHAT is passed (embeddings/hidden states/KV), WHICH alignment connects sender/receiver and HOW the receiver fuses it. This makes clear there is no one latent protocol.

Most importantly, **Do Latent Channels Actually Communicate?** performs controlled message replacements on Qwen3-4B/8B and shows that aggregate task gains can hide very different mechanisms. Example: on GSM8K Qwen3-4B, the total effect was -1 point but decomposed into a -6.17-point other-example message effect plus +5.17 points of example-specific content. On MATH-500 4B, +15 points decomposed into +8.33 generic/other-example and +6.67 example-specific content.

**RAE consequence:** every P3 claim needs a causal message audit. Accuracy alone is not evidence of communication.

### G. Shared semantic internal representations

The ICLR 2025 Semantic Hub work finds that semantically equivalent inputs across languages, arithmetic, code, vision and audio align in intermediate model layers, and interventions suggest the shared representation is actively used.

This supports the idea of a semantic spine below surface language.

However, a calibrated 2026 re-analysis of the stronger Platonic Representation Hypothesis finds that much apparent **global** convergence disappears after null calibration while **local neighborhood relationships** remain more robust. Other 2026 work also finds representation agreement can coexist with divergent reasoning and low causal influence.

**RAE consequence:** cross-model latent bridges may exploit local semantic geometry, but must be calibrated per model/layer/version. Do not assume a universal coordinate system.

### H. Tokenizer-free / byte-native modeling

Byte Latent Transformer (ACL 2025) matches tokenized models at scale in the reported study using raw bytes grouped into entropy-dependent patches and improves robustness/efficiency in several regimes. This shows a fixed human-designed tokenizer is not a necessary semantic foundation for a language model.

**RAE consequence:** Clay semantics must not be coupled to today's tokenizer. Token/byte/patch vocabulary is a reader/runtime representation choice.

### I. Emergent social language and convention drift

Science Advances 2025 demonstrates that decentralized populations of frozen LLM agents can spontaneously form shared naming conventions, develop collective biases not visible at individual level and be shifted by committed minorities.

This is strong evidence for **system-level protocol dynamics** after deployment. It is not evidence of phenomenal consciousness and not sufficient by itself for RAE emergence promotion.

**RAE consequence:** P2 protocol/codebook state needs version lineage, population drift measurements and minority/adversarial takeover tests.

## 3. Main scientific corrections

1. `AI-native language = one variable` — rejected.
2. `compact symbols = better AI language` — rejected as a general rule.
3. `canonical semantic IR = optimal model surface` — rejected as a general rule.
4. `natural language is required for thought/communication` — challenged.
5. `latent communication is inherently better` — rejected.
6. `end-task gain proves latent semantic transfer` — rejected.
7. `all capable models share one universal latent language` — weakened; local semantic alignment is more defensible.
8. `symbol purity/convergence proves causal reasoning or emergence` — rejected.
9. `AI-native programming = vibe coding` — rejected; compilation/IR/runtime is a major independent branch.
10. `native model speech can authorize effects` — rejected.
11. `tokenizer vocabulary defines native semantics` — challenged.
12. `hidden states/KV can stay bundled with physical runtime` — revised; they can be functional communication state.

## 4. Architecture consequence for FRANK

Recommended OPEN target:

```text
Human / external language
  -> CC-RC1.5 ICSL
  -> P1 Canonical Clay IntentContract / causal semantics
  -> Clay View Router
       -> P2 DISCRETE_NATIVE (learned symbols / compact handles)
       -> P3 LATENT_NATIVE (hidden state / embedding / KV channel)
  -> proposal + projection/causal receipt back to P1
  -> CBCC/COVE closure + semantic firebreaks
  -> capability/effect gateway
  -> effect/outcome/re-entry
```

The target Qwen-class 4B should therefore be treated as a **multi-view Clay-native model**, not forced to use one textual serialization for storage, reasoning, agent communication and effect control.

Canonical Clay remains the durable exact language. Model-native representations are learned views.

## 5. New contracts to research

### NativeSymbolReceipt

Bind codebook hash/version, canonical anchors, symbol use, drift, permutation/lesion/rescue, OOD/compositional performance, token/latency benefit and raw/canonical/latent controls.

### LatentChannelReceipt

Bind sender/receiver model+layer+checkpoint, extraction/alignment/compression transforms, zero/random/other-example/same-example/self substitutions, downstream causal effects, OOD and uncertainty.

Neither receipt grants authority.

## 6. Highest-information experiments

### P1 — Target Qwen dual-rail factorial

Matched training/compute comparison of:
- natural language;
- P1 canonical Clay;
- P2 learned discrete Clay;
- P3 latent channel;
- P2+P3 hybrid;
- optional adaptive router.

Measure correctness, OOD/compositional generalization, retained capability, tokens, latency, memory/energy, projection errors and authority violations.

### P2 — Latent causal audit

For every candidate sender->receiver channel: zero, random, other-example, same-example and self-substitution messages. Measure both final task effect and internal/re-entry changes.

### P3 — GWT medium orthogonality

Factor representation medium independently from competition/selection, ignition/broadcast and re-entry. A representation should count as workspace content only through causal availability/effect, not because it is readable.

### P4 — Symbol/convention drift

Fixed model weights; vary population topology, external memory, codebook version and committed minority. Measure emergence, drift, recovery and semantic-anchor preservation.

### P5 — Tokenizer independence

Same P1 Clay semantics across tokenized and byte/patch readers. Measure fertility, robustness, latency and OOD without changing canonical semantics.

## 7. Branch feedback

- **Clay:** REVISE + NEW_EXPERIMENT — CLAY-L5 candidate, dual native rail.
- **FRANK:** REVISE + NEW_EXPERIMENT — expose P2/P3 separately, retain gateway.
- **GWT:** REVISE + NEW_EXPERIMENT — representation medium becomes orthogonal factor.
- **Emergenz:** REVISE + NEW_EXPERIMENT — causal latent-message and population-convention interventions.
- **ClayCode:** SUPPORT + REVISE — ICSL strongly supported; add NativeSymbolReceipt/LatentChannelReceipt semantics.
- **Hyperposition:** SUPPORT + REVISE — semantic firebreaks become representation-plane aware.
- **ClayGraph:** REVISE + NEW_EXPERIMENT — store canonical ancestry plus projection versions/receipts, not latent vectors as truth.

## 8. Evidence boundary

High-confidence architecture direction is supported by converging but heterogeneous evidence. Peer-reviewed sources establish specific mechanisms (Interlat, Semantic Hub, SENSE, BLT, social conventions), while many 2026 governance/agent-language papers are recent preprints and need replication. AI Mother Tongue evidence is interesting but remains preprint-level and should not be promoted to universal claims. Implementation projects establish feasibility, not necessity.

No target FRANK/Qwen latent experiment was run in this worker because the required checkpoint/runtime endpoint is not exposed. Therefore CLAY-L5 remains OPEN and no canonical scientific promotion is made.

## 9. Final synthesis

The strongest path for FRANK is not to invent a single alien syntax and force everything through it. It is to build a **native semantic organism with controlled representational polymorphism**:

- humans can speak loosely;
- canonical Clay captures exact committed meaning;
- the model can learn a compact discrete mother tongue;
- models/agents can additionally exchange rich latent state;
- neither native rail is trusted simply because it is native;
- all durable knowledge and effects return through typed semantic/causal receipts and external authority gates.

That architecture is simultaneously more AI-native, more efficient, more experimentally identifiable and safer than collapsing intent, symbols, hidden states and execution into one language.
