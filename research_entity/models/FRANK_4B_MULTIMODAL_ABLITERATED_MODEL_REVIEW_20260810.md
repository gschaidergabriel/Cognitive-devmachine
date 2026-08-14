# FRANK <=4B Abliterated Multimodal Model Review — 2026-08-10

Status: RESEARCH_DELTA / NO_MODEL_PROMOTION
Origin actor: chatgpt-secondary
Provider/model: OpenAI / GPT-5.6 Sol
Scope: FRANK v0.1 model-facing cognition under hard resource ceiling of current Qwen3.5-4B Q4_K_M runtime

## Decision

Do not replace the current Qwen3.5-4B abliterated baseline yet.

Current internal evidence establishes that the local Qwen3.5-4B-abliterated Q4_K_M can satisfy the SE-XENO semantic bridge test (4/4 valid records, 2/2 omission/unknown handling) but does not establish long-session or multimodal Frank performance. Historical runtime material also shows the Qwen3.5 vision projector (`mmproj`) is already loaded, so obtaining multimodality does not itself require a base-model replacement.

The current BASE_CLAYCODE_RELEASE remains the critical stage. A model promotion should therefore be treated as an H1/H2 benchmark decision rather than disrupting the BASE compiler/runtime critical path.

## Current baseline

Family: Qwen3.5-4B
Derivative: Huihui-Qwen3.5-4B-abliterated lineage
Quantization: Q4_K_M in measured local protocol work
Multimodality: native Qwen3.5 image-text architecture; historical llama.cpp runtime recipe includes an mmproj projector
Training lineage: Frank QLoRA work already exists on the Huihui Qwen3.5-4B abliterated base

Known internal measurements:
- SE-XENO bridge: 4/4 valid first-try records, 2/2 missing-information cases, ~5.3 s/line in the recorded local experiment.
- Historical process snapshot: v26.1 Needle reported 79.9% over 134 mandatory cases, target 90%; this is historical evidence and not a current canonical H1 acceptance receipt.
- Not yet measured in the cited 4B protocol experiment: long-session stability, full-spec retention, model-to-model semantic recovery, multimodal screen/OCR/UI performance.

## External candidate screen

### Candidate A — Qwen3.5-4B, alternate weight-level abliterated derivative

Most conservative challenger. Same underlying Qwen3.5-4B multimodal family and resource class, but a reproducible weight-level refusal-direction ablation is available with Q4_K_M export. This may preserve more of the base model behavior than a text-only fine-tuned uncensoring approach, but this is a hypothesis until matched Frank tests are run.

Disposition: TEST FIRST. Highest-priority challenger because it minimizes architecture and resource confounds.

### Candidate B — Ministral-3-3B-Instruct-2512 abliterated

Native image+text model, function calling, smaller language-model footprint and Q4_K_M abliterated GGUF availability. It is a plausible resource-saving challenger, but there is no current evidence that it beats Qwen3.5-4B on Frank-relevant cognition/vision under matched conditions.

Disposition: TEST AS LOWER-RESOURCE CHALLENGER, not a replacement claim.

### Candidate C — Gemma 4 E4B abliterated

Newer multimodal family with image and audio support. However E4B is 4.5B effective and 8B including embeddings according to the official model card. Under the owner's hard requirement of no greater real resource use than the current 4B setup, it is not eligible for promotion without exact project-hardware evidence proving resource parity. Relevant published benchmark values also do not establish an overall advantage over Qwen3.5-4B for Frank.

Disposition: RESOURCE-SHADOW ONLY / currently ineligible for direct promotion.

### Candidate D — Gemma 4 E2B abliterated

Potentially useful if audio becomes a high-value requirement, but official capability numbers are substantially below the 4B Qwen3.5 class on several reasoning/vision benchmarks. Total parameters including embeddings are also above the nominal effective size.

Disposition: NOT_SELECTED as default Frank cognition candidate; retain only as specialized future experiment.

## Hypothesis and strongest counterhypothesis

H-MODEL-4B-20260810:
A capability-preserving weight-level abliterated Qwen3.5-4B derivative can equal or improve current Frank routing/structured-semantic behavior while preserving native multimodal ability and staying inside the same Q4_K_M resource envelope.

COUNTER-H-MODEL-4B-20260810:
The current Huihui-derived Frank LoRA has task-specific gains that dominate any cleaner base-model ablation; switching derivatives would lose learned Frank behavior and force costly retraining/revalidation without useful outcome gain.

## Required discriminating promotion test

Freeze one matched benchmark harness and compare at minimum:

A. Current Frank v26.1/Huihui Qwen3.5-4B abliterated Q4_K_M + current vision projector.
B. Capability-preserving weight-abliterated Qwen3.5-4B Q4_K_M + equivalent projector; apply/retrain the Frank adapter only through a separately versioned candidate path.
C. Abliterated Ministral-3-3B-Instruct-2512 Q4_K_M + its native vision path.
D. Gemma 4 E4B abliterated only if a preliminary resource shadow proves it does not exceed baseline RAM/VRAM/CPU/p95 latency/energy on the target runtime; otherwise stop candidate D.

Use identical machine, runtime/backend, context target, image set, prompts, seeds, decoding and warm/cold protocol. Preserve raw rows and all mandatory project metadata.

Mandatory task families:
- existing SE-XENO bridge and full-spec retention;
- 134-case Needle mandatory suite plus held-out/OOD routing;
- longitudinal multi-turn battery;
- German instruction following and structured semantic/JSON output;
- UI screenshots, small-text/OCR, dialogs/tables, screen-state change interpretation;
- known/unknown/ambiguous visual cases feeding the Digital Retina/Micro Visual Classifier contract;
- before/after action outcome verification;
- abstention/calibration under missing evidence;
- tool/effect proposal correctness while preserving external authority boundary;
- crash/restart/replay and long-session drift;
- p50/p95/p99 latency, RAM/RSS, VRAM, CPU/GPU utilization, tokens, energy where measurable.

Promotion rule:
NO replacement unless the challenger is Pareto-competitive with the current baseline on Frank task quality, multimodal quality, reliability and recovery, while not exceeding the current model's declared resource envelope. A benchmark gain that costs more project-hardware resources does not satisfy the owner's requirement.

## Architecture consequence

No immediate architecture mutation. Add a model-selection test obligation to H1/H2. Preserve the current Qwen3.5-4B multimodal path and external typed effect authority. Abliteration changes refusal behavior but must not move effect authority into the model; Needle/model output remains proposal evidence only.

## Sources consulted

Internal:
- 000 CLAY / FRANK master project source, current bootstrap.
- research_entity/rooms/PROGRAM_STATE.json
- research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json
- research_entity/global/FRANK_V0_1_ADAPTIVE_VISUAL_LEARNING_DIRECTIVE.md
- Drive research artifacts FREIE-MODELLE.txt, frank-lora-training-suite.txt, prozesse.txt.

External live review (2026-08-10):
- Official Qwen/Qwen3.5-4B model card and benchmark table.
- huihui-ai/Huihui-Qwen3.5-4B-abliterated model card.
- kaineone/Qwen3.5-4B-abliterated model card / Q4_K_M companion format information.
- Official Google Gemma 4 model card.
- Official Mistral Ministral-3-3B-Instruct-2512 model card.
- Abliterated Ministral 3 3B GGUF availability.

Result: NO_MODEL_PROMOTION; BENCHMARK_OBLIGATION_CREATED_IN_RESEARCH_DELTA.
