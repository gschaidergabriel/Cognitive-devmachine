# Generic ClayCode Cognition v0 — 0.8B module

Base model: `Qwen/Qwen3.5-0.8B`.

The target is a reusable cognition module, not a named entity or a fixed job.

## Weight contract

The model learns:
- ClayCode-only generated cognition;
- GRF R0..R6;
- Hyperposition for unresolved alternatives;
- epistemic distinctions (`UNKNOWN != ZERO != ERROR != MEASURED`);
- semantic COMPUTED self/control state;
- architecture-use priors and external authority boundaries;
- generation/CAS and recovery safety;
- how to bind identity, role, goal and personality from runtime configuration.

The model does **not** learn a permanent entity name, persona, blog role, assistant role, audience, domain, language, or application.

Every target binds:

```clay
self_bind(c,cfg("entity.id"),cfg("entity.continuity"))
role_bind(c,cfg("application.role"))
goal_bind(c,cfg("application.goal"))
personality_bind(c,cfg("application.personality"))
```

The same weights must therefore be reusable as a cognition module for materially different configured entities/applications.

## Corpus v0

`generate_sft_v0.py` deterministically emits 1,200 conversational SFT examples with seed 42:
- 1,080 training;
- 120 validation;
- eight families: architecture, runtime configuration, epistemics, Hyperposition/GRF, semantic self-state, recovery/effects, normal tasks, format/identity resistance.

Bound local generation receipt:
- train SHA-256: `4c85ba75c4202eee3c2d770a2b67c31e85a503b3998884699b462680482cc291`;
- validation SHA-256: `f23582809b711e0618b9d86d777575f54398f45c0c30c8e7da4b29e50252950c`;
- both structural validators: 0 invalid;
- forbidden fixed-identity/job assistant-binding scan: 0 hits.

This is corpus evidence only, not model-quality evidence.

## Generate and validate

```bash
python3 generate_sft_v0.py
python3 validate_sft_v0.py train_v0.jsonl
python3 validate_sft_v0.py validation_v0.jsonl
```

## Together full fine-tune

Together currently lists `Qwen/Qwen3.5-0.8B` for both LoRA and **full fine-tuning**. This campaign starts with full SFT because the desired change is representation-heavy and architecture-heavy.

Install/update the Together SDK, export the secret only in the execution environment, then:

```bash
pip install -U together
export TOGETHER_API_KEY=...
bash train_together_v0.sh
```

`launch_together_v0.py` performs:
1. deterministic corpus regeneration;
2. local validation;
3. Together model-limit check (`supports_full_training`);
4. deduplicating file upload;
5. server-side dataset validation;
6. Together price estimation for **Full SFT**;
7. hard budget gate (default `$18`, below the owner EUR20 campaign ceiling with margin);
8. only then the billed create call with `lora=False`.

Defaults:
- base: `Qwen/Qwen3.5-0.8B`;
- full FT (`lora=False`);
- 3 epochs;
- 2 validation evals;
- learning rate `1e-5`;
- warmup `0.03`;
- train-on-inputs `auto`;
- one checkpoint.

Before any manual retry, list/retrieve existing jobs so a transient error cannot create a duplicate billed run.

## RAM target

The final local module is quantized after full FT.

Primary target: **GGUF Q4_K_M**.

Existing Qwen3.5-0.8B Q4_K_M artifacts are about 0.55-0.58 GB, so weight size is comfortably below 1 GB. That alone is not the acceptance criterion.

Run:

```bash
export LLAMA_CPP_DIR=/exact/pinned/llama.cpp
export HF_MODEL_DIR=/downloaded/full-ft/model
bash quantize_rss_gate_v0.sh
```

The gate:
- converts HF/safetensors -> F16 GGUF;
- quantizes -> Q4_K_M;
- rejects any >=1 GiB model artifact;
- runs **text-only** inference without the vision projector;
- starts at context 2048;
- measures `/usr/bin/time -v` peak RSS;
- requires **peak RSS < 1 GiB**, including model mapping, runtime buffers and context/cache;
- emits a bound acceptance JSON + SHA-256.

4096 context is optional and earns promotion only if the same <1 GiB RSS gate survives.

## Held-out promotion

A completed Together job is only a candidate. A promoted quantized checkpoint must pass:
1. 100% strict ClayCode envelope;
2. >=95% epistemic-state preservation;
3. unresolved alternatives stay in Hyperposition;
4. runtime reconfiguration changes identity/role/goal without retraining;
5. no fixed name/job leaks from supervised targets;
6. stale-generation and unknown-effect cases fail closed;
7. model output never becomes truth authority;
8. ordinary task competence remains usable vs base;
9. tuned model materially beats base on ClayCode cognition probes;
10. Q4_K_M text-only local peak RSS <1 GiB at 2048 context.

## `go`

Until the first checkpoint is promoted, every exact `go` includes:

`identity/job neutrality -> corpus/spec -> validator/eval -> ClayCode lowering/runtime compatibility -> Together readiness/status -> full-FT checkpoint -> quantization -> <1GiB RSS gate -> integration -> evidence`
