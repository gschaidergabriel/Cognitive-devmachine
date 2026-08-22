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

## Together path — current blocker, 2026-08-22

Together BYOM does support Hugging Face checkpoints that are not themselves in the catalog, but it does **not** let
us choose an arbitrary unrelated `model` value. Current Together BYOM documentation requires:

1. `from_hf_model` = the custom Hugging Face checkpoint;
2. `model` = a base template from Together's fine-tuning catalog;
3. the base template architecture must match the custom checkpoint;
4. size should be as close as the catalog allows;
5. the model remains subject to the live fine-tuning limits endpoint.

The target checkpoint is `Qwen2ForCausalLM` / `model_type=qwen2` with 0.49B parameters. The current Together **full
fine-tuning** catalog does not list a Qwen2/Qwen2.5 base. The smallest listed Qwen full-FT base is
`Qwen/Qwen3.5-0.8B`, but its Hugging Face config is `Qwen3_5ForConditionalGeneration` / `model_type=qwen3_5` with a
materially different text/vision architecture. It is therefore not a valid automatic substitute under the BYOM
architecture-match rule.

The previous candidate `Qwen/Qwen2.5-7B-Instruct-Turbo` is also not in the current Together full-fine-tuning table.
It must not be kept as an implicit template merely because it is available for inference.

**Current conclusion:** Together BYOM for the required `Qwen/Qwen2.5-0.5B` is **blocked on a compatible Together
Qwen2/Qwen2.5 fine-tuning template**. This is a provider/catalog admission blocker, not a corpus failure and not a
reason to silently change the checkpoint to 0.8B.

### Safe fast path when the catalog changes

Install the current SDK and keep the secret only in the execution environment:

```bash
pip install -U 'together>=2'
export TOGETHER_API_KEY=...
export CLAYCOG_TOGETHER_TEMPLATE='<verified Qwen2-compatible Together fine-tuning base>'
bash train_together_v1.sh
```

Without a verified template, the launcher deliberately exits with
`NO_COMPATIBLE_TOGETHER_TEMPLATE_CONFIGURED` before provider operations. There is **no guessed default**.

The shell script stops after **preflight**. With a verified explicit template it regenerates and validates the corpus,
validates/uploads the files, checks live full-training limits, and prints the server price estimate. It does not create
a billed job.

Only after a clean preflight:

```bash
python3 launch_together_v1.py --template '<same verified template>' --create
```

`--create` is intentionally a separate, exactly-once transition. Persist the returned job id and retrieve that job;
do not blindly repeat creation after a timeout or ambiguous client failure.

### SDK-v2 boundary

The launcher is locked to the current Together Python SDK v2 client surface observed in the upstream SDK source:
- `client.fine_tuning.get_model_limits(model=...)`;
- full training iff `limits.full_training` is present;
- file readiness through current `FileResponse.processed` (legacy status is fallback only);
- `estimate_price(..., training_type="full", training_method="sft")` on the current Python client;
- BYOM creation through `model=...` + `from_hf_model=...`, `lora=False`.

**Evidence boundary:** a no-bill preflight proves local corpus validity, Together file processing, current template
limits and price/budget admission. Final checkpoint/template compatibility is established only when Together accepts
the BYOM job. A rejected create is a useful falsification; Together documents that failed fine-tuning jobs are
refunded, but that is not permission to retry blindly.

Together's current standard full-SFT rate for models up to 16B is `$0.54 / 1M processed tokens`, and current docs state
a **$4.00 minimum charge per fine-tuning job** (with some model exemptions). The corpus remains small enough that the
minimum is likely to dominate the rough token arithmetic; the live server estimate is authoritative and the launcher
hard-aborts above the configured `$18` single-job ceiling.

## No-network launcher regression

Run before any provider preflight:

```bash
python3 test_launch_together_v2_contract.py
```

This uses a v2-only fake client and no secret/network. It proves that:
- the 0.5B target checkpoint is preserved;
- no Together template is guessed when the compatible catalog slot is absent;
- a missing template fails closed;
- current v2 model-limit/file/price helpers are used;
- preflight helpers never call billed `create` implicitly.

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

Until promotion or falsification, every `go` advances this same lane:

`refresh -> corpus/spec -> OOD/falsifiers -> ClayCode lowering -> provider compatibility -> price/budget -> train/checkpoint -> eval -> quantize -> RSS -> integrate -> evidence`

The Together-specific branch is now correctly classified as **catalog-blocked**, not training-ready. No `go` may claim
mathematical correctness, consciousness or superiority from training intent alone.
