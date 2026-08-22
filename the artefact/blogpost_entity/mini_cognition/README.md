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
# Set this only after current Together verification identifies a Qwen2-compatible
# full-fine-tuning template:
export CLAYCOG_TOGETHER_TEMPLATE=...
bash train_together_v1.sh
```

The shell script stops after **preflight**. It regenerates and validates the corpus, asks Together to validate the
explicit template and files, and prints the server price estimate. It does not create a billed job.

Only after preflight:

```bash
python3 launch_together_v1.py --create
```

### Together 0.5B caveat — current blocker

As checked on **2026-08-22**, Together's current fine-tuning supported-model table contains **no Qwen2/Qwen2.5 base**.
For Qwen full fine-tuning it currently lists Qwen3.5 models down to **0.8B**, but those are a different model generation
and are not silently admitted as templates for the Qwen2.5 checkpoint. Together's BYOM guide requires the Hugging Face
checkpoint to be CausalLM, safetensors, under 100B, without `trust_remote_code`, and paired with a Together base whose
architecture matches and whose size/context are suitable.

`Qwen/Qwen2.5-7B-Instruct-Turbo` remains visible as an inference model, but visibility in the inference catalog is not
evidence that it is currently accepted by the fine-tuning API. It is therefore no longer an implicit launcher default.
The launcher now requires `--template` or `CLAYCOG_TOGETHER_TEMPLATE`, then asks Together `model_limits` and fails closed
unless the supplied template supports full fine-tuning. A Qwen3-family template is rejected rather than silently changing
the experiment from Qwen2.5-0.5B.

This is a **source/documentation blocker, not an API-runtime observation**. A Together-authenticated `model_limits` call may
still reveal an admitted Qwen2-compatible template not shown in the public table. If it does not, keep the 0.5B checkpoint
requirement and either obtain a Together-provided Qwen2-compatible template or run the same corpus on another admitted
full-FT runner. Do not relabel a Qwen3.5-0.8B run as the 0.5B campaign.

The primary Hugging Face checkpoint is now pinned to revision
`285c998059f3e217fe1f05e241d55b5c5eef5bd3`; the instruct ablation is pinned to
`7ae557604adf67be50417f59c2c2f167def9a775`. Together supports `hf_model_revision`, so mutable HF `main` is no longer
accepted by the launcher.

Together's current `estimate-price` API does **not** expose `from_hf_model`. Therefore a successful price estimate proves
only dataset/template/budget admission. It does not prove that Together has accepted the external Qwen2.5-0.5B checkpoint.
The first actual BYOM checkpoint-acceptance gate is the create request, which remains owner-authorized and budget-gated.

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
