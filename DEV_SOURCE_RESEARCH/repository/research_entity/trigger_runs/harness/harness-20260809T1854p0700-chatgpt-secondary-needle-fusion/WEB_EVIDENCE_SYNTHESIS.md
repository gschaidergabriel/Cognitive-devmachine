# Web Evidence Synthesis — Needle / Tool Routing / Constraints / Calibration

Run: `harness-20260809T1854p0700-chatgpt-secondary-needle-fusion`
Search date: 2026-08-09
Evidence policy: external evidence is used to generate/falsify hypotheses; it does not override direct executable evidence from the exact Needle/Frank artifacts.

## Upstream Needle state

Primary surfaces inspected:
- https://github.com/cactus-compute/needle
- https://huggingface.co/Cactus-Compute/needle

Current official HF files expose:
- `needle.pkl` ~52.6 MB;
- `model.safetensors` ~60.9 MB;
- `needle-cq4.zip` ~16.2 MB;
- `tokenizer.model` ~125 kB;
- model config: d_model=512, 12 encoder layers, 8 decoder layers, 8 attention heads / 4 KV heads, vocab 8192.

The current Python source exposes a contrastive retrieval head and `retrieve_tools()`, in addition to generative tool calling. Current `constrained.py` contains a docstring/code mismatch around JSON-Schema `parameters.properties`: the implementation iterates the direct `parameters` dictionary.

## Structured/constrained decoding

Relevant primary research:
- Park et al., Grammar-Aligned Decoding, 2024: https://arxiv.org/abs/2405.21047
- Geng et al., JSONSchemaBench / Generating Structured Outputs from Language Models, 2025: https://arxiv.org/abs/2501.10868
- Li et al., Efficient Grammar-Constrained Decoding via Parser Stack Classification, 2026: https://arxiv.org/abs/2608.03065

Fusion:
- Grammar-constrained decoding is useful for structural validity, but ordinary token masking can distort the model distribution.
- Therefore downstream correctness and confidence must not be inferred merely from 'the output was allowed by the grammar'.
- Frank's tested fail-closed post-validator is complementary to Needle's partial decoder constraints and should remain mandatory even if upstream grammar handling improves.

## Tool retrieval / large tool inventories

Relevant primary research:
- Molfetta et al., PORTS, EMNLP 2025: https://aclanthology.org/2025.emnlp-main.507/
- Qin et al., Meta-Tool, ACL 2025: https://aclanthology.org/2025.acl-long.1481/
- Liu et al., ToolScope, ACL 2026: https://aclanthology.org/2026.acl-long.1573/
- Patel et al., Dynamic Tool Dependency Retrieval, ACL 2026 Findings: https://aclanthology.org/2026.findings-acl.1680/
- Paramanayakam et al., Less is More, 2024: https://arxiv.org/abs/2411.15399

Fusion:
- Retrieval-before-calling is well motivated when tool inventories consume context or create ambiguity.
- Reported gains elsewhere do NOT establish that Needle top-k will improve Frank; the decisive metric is audited relevant-tool recall@k followed by downstream routing accuracy.
- Needle is unusually attractive for this test because its own training/runtime already contains contrastive query/tool embeddings, avoiding an immediately separate retriever model.

## Tool descriptions and schema wording

Relevant primary research:
- Faghih et al., Tool Preferences in Agentic LLMs are Unreliable, EMNLP 2025: https://aclanthology.org/2025.emnlp-main.1060/
- Hsieh et al., Tool Documentation Enables Zero-Shot Tool-Usage, 2023: https://arxiv.org/abs/2308.00675
- Ghoshal et al., JTPRO, ACL 2026 Findings: https://aclanthology.org/2026.findings-acl.2017/

Fusion:
- Tool descriptions can carry crucial zero-shot semantics.
- They can also bias selection strongly and can be manipulated by wording.
- Hence description removal is not a universal optimization. For Frank/Needle, description policy should be a frozen experimental factor with discriminative, versioned descriptions if used.

## Confidence / abstention

Relevant primary research:
- Guo et al., On Calibration of Modern Neural Networks, ICML 2017: https://proceedings.mlr.press/v70/guo17a.html
- Cattelan & Silva, How to Fix a Broken Confidence Estimator, UAI 2024: https://proceedings.mlr.press/v244/cattelan24a.html
- Gangrade et al., Selective Classification via One-Sided Prediction, AISTATS 2021: https://proceedings.mlr.press/v130/gangrade21a.html

Fusion:
- A score usable for ranking confidence is not automatically a calibrated correctness probability.
- Selective prediction is naturally evaluated by risk-coverage, not by choosing an arbitrary confidence threshold first.
- Because constrained masking changes the candidate distribution, Frank should capture pre-constraint logits/margins/entropy for calibration; post-constraint scores are diagnostic only until validated.

## Multilingual tool calling

Relevant primary research:
- Luo et al., Lost in Execution: On the Multilingual Robustness of Tool Calling, 2026: https://arxiv.org/abs/2601.05366
- Zhang & Zhu, International Tool Calling Dataset, 2026: https://arxiv.org/abs/2603.05515
- Nacar et al., Arabic function calling with FunctionGemma, 2026: https://arxiv.org/abs/2603.16901
- Kavathekar et al., Small Models, Big Tasks, 2025: https://arxiv.org/abs/2504.19277

Fusion:
- Non-English tool calling has failure modes beyond intent recognition, especially argument-value language and execution conventions.
- Small tool-calling models commonly improve with fine-tuning and can struggle with formatting; this is counterevidence to assuming unchanged zero-shot Needle will meet a 90% German gate.
- Frank's deterministic alias/schema/validation shell can eliminate structural failures, but German semantic route quality remains a model-level empirical question.

## Evaluation label quality

Relevant primary research:
- Northcutt et al., Pervasive Label Errors in Test Sets Destabilize Machine Learning Benchmarks, 2021: https://arxiv.org/abs/2103.14749
- Meta Llama evaluation notes also document correcting incomplete/incorrect API benchmark ground truth before evaluation: https://github.com/meta-llama/llama-models/blob/main/models/llama3_1/eval_details.md

Fusion:
- Frank's project-local 328-case report already records concrete wrong labels. Therefore the 90% gate cannot be scientifically interpreted without an audited/versioned gold set and disagreement ledger.

## Runtime/action safety

Relevant primary research:
- Patil et al., GoEX, 2024: https://arxiv.org/abs/2404.06921
- UC Berkeley GoEX project: https://sky.cs.berkeley.edu/project/goex/

Fusion:
- External work separates action proposal from bounded execution and uses undo/damage confinement/least privilege as runtime concepts.
- This is compatible with Frank's stronger local invariant: Needle never mints execution authority; accepted Needle output remains a proposal routed through a separate effect/authority gate.

## Cross-runtime differential testing

External implementation evidence:
- https://huggingface.co/onnx-community/needle-onnx

The ONNX port reports Flax↔PyTorch and PyTorch↔ONNX max-absolute differences well below 1e-3 and byte-identical end-to-end unconstrained greedy output on its parity test. This is useful as a candidate independent runtime for differential testing, but this Harness run has not reproduced those binary-level claims locally.

## Global synthesis

Strongly supported architecture direction:

`input normalization -> complete tool-catalogue preflight -> optional experimentally validated retrieval -> unchanged Needle -> fail-closed structural/semantic validator -> provenance-bound NeedleDecisionReceipt(authority=NONE) -> Clay ingress -> independent authority/effect gate`

Not yet promoted:
- top-k retrieval;
- any confidence threshold;
- description removal/compression recipe;
- zero-shot German acceptance;
- no-finetuning feasibility at the 90% semantic target;
- ONNX parity as locally verified evidence.
