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

Current committed corpus receipt:
- train: **0 / 1,485 invalid**;
- validation: **0 / 165 invalid**;
- train SHA-256: `bc1753771ed0f818865a3118f754ac5b10d67bc3ae885f668201f66566028eb2`;
- validation SHA-256: `81a6bb9fc0a210affffa84590c27ad2fc76c93fa24c4112e6573552227e512ce`.

The OOD promotion set is deliberately separate from the random SFT split. It now defines **240** cases. The added
`tool_vocabulary_amputation_ood` family is the single unusual experiment for the 2026-08-22 `go`: four operation/schema
families are completely absent from the SFT generator's six-tool vocabulary. Their runtime descriptors are supplied in
the prompt, and the model must bind the unseen operation/schema rather than substitute a memorized training tool.
This converts the tool-neutrality claim from a same-vocabulary argument-variation test into a structural holdout.

## Fast path

```bash
pip install -U together
export TOGETHER_API_KEY=...
bash train_together_v1.sh
```

The shell script stops after **preflight**. It regenerates and validates the corpus, checks the selected Together
training template, asks Together to validate the files, and prints the server price estimate. It does not create a
billed job.

Only after a compatible template is identified and preflight succeeds:

```bash
export CLAYCOG_TOGETHER_TEMPLATE='<compatible Together fine-tuning base>'
export CLAYCOG_TOGETHER_TEMPLATE_ARCH='qwen2'
export CLAYCOG_TOGETHER_TEMPLATE_PARAMS_B='0.5'
python3 launch_together_v1.py --create
```

### Together 0.5B compatibility gate

Together's current fine-tuning CLI documents `--from-hf-model` as a Hugging Face checkpoint that **should match the
selected base model's architecture and size**. Therefore a 7B Qwen2.5 model is not a valid default training template
for a 0.5B Qwen2.5 checkpoint merely because both are in the same family.

The earlier default `Qwen/Qwen2.5-7B-Instruct-Turbo` candidate has been removed. The launcher now fails **before any
Together file upload** unless an explicit current template plus `qwen2` / `0.5B` metadata is supplied. Those local
metadata values are an operator-side admission fence, not compatibility proof: Together's authenticated API remains
authoritative and may still reject the pair.

Current status is therefore:

`BYOM_COMPATIBILITY_OPEN / NO_MATCHING_0.5B_QWEN2_TRAINING_TEMPLATE_CREDITED_YET`.

Do not silently switch to 0.8B, 1.5B, 3B or 7B just to make the provider path green; that changes the owner's 0.5B
research question. If Together exposes/accepts a matching 0.5B Qwen2 template, bind it explicitly and run preflight.
Otherwise retain the same checkpoint/corpus requirement and use another owner-authorized full-FT runner.

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
2. >=95% OOD semantic gate pass across the full 240-case set;
3. the tool-vocabulary-amputation family must not substitute any SFT-seen tool for an unseen runtime tool;
4. invalid/missing tool arguments reject instead of guessed repair;
5. unresolved alternatives remain in Hyperposition;
6. runtime profile changes do not leak a fixed name/job;
7. stale generation and unknown-effect cases fail closed;
8. model output never becomes canonical truth/effect authority;
9. tuned 0.5B materially beats its untuned 0.5B base on the same routing/epistemic probes;
10. compare against at least one larger general model on exact structured-task success before claiming "micro-agent superiority";
11. Q4_K_M text-only peak RSS `< 1 GiB` at 2048 context.

## `go`

Until promotion, every `go` advances this same lane:

`refresh -> corpus/spec -> OOD/falsifiers -> ClayCode lowering -> Together BYOM compatibility -> price/budget -> train/checkpoint -> eval -> quantize -> RSS -> integrate -> evidence`

No `go` may claim mathematical correctness or superiority from training intent alone.
