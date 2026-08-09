# KMP-FRANK-R9-MULTIMODAL-4B-VISION-BACKING-20260809

packet_id: `KMP-FRANK-R9-MULTIMODAL-4B-VISION-BACKING-20260809`
domains: `frank, model_runtime, visual_perception_retina, synthetic_clay, harness`
epistemic_class: `EXTERNAL_PRIMARY_DOCUMENTATION_PLUS_ARCHITECTURE_INFERENCE`
status_hint: `OPEN`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
canonical_parent: `r2:04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Atomic claim

Current official Qwen documentation shows `Qwen3.5-4B` is a 4B causal language model with a Vision Encoder and image-text-to-text support. Therefore FRANK's fixed one-local-4B target has a plausible **physical-backing hypothesis** in which Digital Retina/MVC keeps its Clay-native semantic state, provenance, open-set and intervention contracts while numerical visual features are sourced from the same multimodal 4B rather than a second full vision model.

This is not a model selection and not evidence that the same-4B backing is operationally superior.

## Source refs

- official Qwen Hugging Face model card `Qwen/Qwen3.5-4B`, current 2026-08-09: 4B language model, Vision Encoder, unified vision-language foundation, image-text-to-text usage.
- official Qwen GitHub release news: Qwen3.5-4B released 2026-03-02.
- internal `FRANK_FINAL_BINARY_RESEARCH_CONTRACT.md`.
- internal `FRANK_V0_1_ADAPTIVE_VISUAL_LEARNING_DIRECTIVE.md` and H1 architecture freeze.

## Counterhypothesis

Separate numerical vision backing may be more stable, efficient, inspectable or robust for low-latency open-set user-specific learning. Same-model reuse may correlate perception and reasoning failures or make MVC features fragile across quantization/export/backbone revisions.

## Falsifier / next test

Compare separate-backbone vs same-4B feature backing under matched H1 then target-shaped runtime conditions. Require semantic intervention parity, known/unknown/conflict calibration, open-set rejection, MVC-E1..E7 behavior, feature-version migration, rollback/recovery, latency, RAM, update duty cycle and coupled-failure measurement. Reject physical consolidation if these regress materially.

## Promotion boundary

No promotion before executable H1 evidence and later target-4B/Ubuntu evidence. The fixed semantic architecture does not depend on this physical placement choice.
