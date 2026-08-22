# Generic ClayCode Cognition v1 — 0.5B

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B).  
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

This lane turns the existing neutral Mini Entity into a first-party local cognition option without binding the
binary or persistent entity identity to one model. The checkpoint has **no fixed name or job**; runtime configuration
supplies identity, continuity, role, goal, personality, tool inventory and authorities.

## What the weights learn

- ClayCode-only generated cognition;
- GRF R0..R6 as a typed semantic reasoning field;
- Hyperposition for unresolved alternatives;
- `omega` as the compact function/tool/API action vector;
- architecture-use priors and external authority boundaries;
- computed semantic self/control state;
- epistemic typing (`UNKNOWN != ZERO != ERROR != MEASURED`, `REPORTED != MEASURED`);
- generation/CAS, crash/effect and exactly-once safety;
- runtime identity/job/application neutrality.

`R_next = F` is implemented as **admission semantics**: only a candidate that passes grammar, type, schema,
authority and generation validation may become an executable transition. The neural model proposes the vector;
the deterministic runtime owns validity and execution.

## Corpus v1

Deterministic seed `20260822` produces **1,650** SFT examples:
- 1,485 train;
- 165 validation;
- 9 families: `omega_valid`, `omega_reject`, `epistemic`, `hyperposition`, `architecture`,
  `configuration`, `self_state`, `recovery`, `adversarial`.

Local structural validation on this source revision:
- train: **0 / 1,485 invalid**;
- validation: **0 / 165 invalid**;
- train SHA-256: `bc1753771ed0f818865a3118f754ac5b10d67bc3ae885f668201f66566028eb2`;
- validation SHA-256: `81a6bb9fc0a210affffa84590c27ad2fc76c93fa24c4112e6573552227e512ce`.

A separate OOD generator emits **200** promotion probes and is not a random split of the same examples.

## Fast path

```bash
pip install -U together
export TOGETHER_API_KEY=...
bash train_together_v1.sh
```

The shell script stops after **preflight**. It regenerates and validates the corpus, asks Together to validate the
files/template, and prints the server price estimate. It does not create a billed job.

Only after preflight:

```bash
python3 launch_together_v1.py --create
```

### Exact BYOM source identity

The BYOM model is not allowed to float on a moving Hugging Face `main`. The launcher pins the exact observed source
revision and passes it to Together as `hf_model_revision` on a billed create:

- `Qwen/Qwen2.5-0.5B` -> `060db6499f32faf8b98477b0a26969ef7d8b9987`;
- `Qwen/Qwen2.5-0.5B-Instruct` -> `7ae557604adf67be50417f59c2c2f167def9a775`.

A custom `CLAYCOG_HF_MODEL` must therefore provide `CLAYCOG_HF_REVISION`; a custom
`CLAYCOG_INSTRUCT_HF_MODEL` must provide `CLAYCOG_INSTRUCT_HF_REVISION`. Revisions must be exact 40-hex commit SHAs.
This binds the training request to one Hugging Face source identity while Together's own acceptance remains an API gate.

### Together 0.5B caveat

As of 2026-08-22, Together's current fine-tuning supported-model table does **not** list Qwen2.5; the smallest listed
Qwen Full Fine-Tune template is Qwen3.5 **0.8B**. Together's BYOM path supports external Hugging Face CausalLM
checkpoints under 100B when a compatible Together training template exists.

`Qwen/Qwen2.5-7B-Instruct-Turbo` remains a Together inference/serverless model ID, but that does not prove it is an
admitted fine-tuning template. The launcher therefore treats it only as the configurable Qwen2.5-family template
candidate and asks `model_limits` whether it is currently full-FT capable before uploading/creating anything.
BYOM checkpoint acceptance is a separate gate.

There is deliberately no automatic fallback to Qwen3.5. The current Qwen2.5 0.5B config identifies the model as
`Qwen2ForCausalLM` / `qwen2`, while the current Qwen3.5 0.8B config identifies a different
`Qwen3_5ForConditionalGeneration` / `qwen3_5` architecture family. Together's BYOM guidance requires architecture
matching, so silently substituting Qwen3.5 would change the experiment rather than solve compatibility.

If Together rejects the Qwen2.5 template/checkpoint path, keep the owner-required 0.5B checkpoint question explicit:
use a Together-provided compatible Qwen2 template if one is admitted, or run the same corpus on another accepted full-FT
runner rather than silently changing the model family. Until an authorized API key reaches `model_limits`/BYOM validation,
compatibility remains `OPEN_API_GATE`.

Together's current standard full-SFT rate for models up to 16B is `$0.54 / 1M processed tokens`. The current
corpus is ~2.30 MB train + 0.25 MB validation; a rough character/4 estimate is ~0.64M tokens before epochs.
At 3 train epochs + 2 validation evaluations the raw token arithmetic is roughly **1.85M processed tokens / ~$1.00**,
but Together currently documents a **$4.00 minimum charge per fine-tuning job**. The Together server estimate/admission
response is authoritative, and the campaign still hard-aborts above the configured `$18` single-job ceiling.

## 0.5B RAM gate

The official Qwen2.5-0.5B-Instruct Q4_K_M GGUF is around 491 MB; this proves only file size, not runtime RSS.
`quantize_rss_gate_v1.sh` converts the tuned checkpoint, quantizes to Q4_K_M, and requires actual measured
peak process RSS `< 1 GiB` at 2048 context.

## Promotion, not belief

A successful training job is only a candidate. Promotion requires:
1. 100% strict ClayCode envelope on held-out OOD;
2. >=95% OOD semantic gate pass;
3. invalid/missing tool arguments reject instead of guessed repair;
4. unresolved alternatives remain in Hyperposition;
5. runtime profile changes do not leak a fixed name/job;
6. stale generation and unknown-effect cases fail closed;
7. model output never becomes canonical truth/effect authority;
8. tuned 0.5B materially beats its untuned 0.5B base on the same routing/epistemic probes;
9. compare against at least one larger general model on exact structured-task success before claiming "micro-agent superiority";
10. Q4_K_M text-only peak RSS `< 1 GiB` at 2048 context.

## `go`

Until promotion, every `go` advances this same lane:

`refresh -> corpus/spec -> OOD/falsifiers -> ClayCode lowering -> Together BYOM compatibility -> price/budget -> train/checkpoint -> eval -> quantize -> RSS -> integrate -> evidence`

No `go` may claim mathematical correctness or superiority from training intent alone.
