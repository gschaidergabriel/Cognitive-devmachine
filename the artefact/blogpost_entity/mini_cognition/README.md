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

## Safe Together path

```bash
pip install -U together
export TOGETHER_API_KEY=...
# Required: set only after current Together verification identifies a Qwen2-compatible
# full-fine-tuning template. There is intentionally no implicit template default.
export CLAYCOG_TOGETHER_TEMPLATE=...
bash train_together_v1.sh
```

The shell script stops after **preflight**. It regenerates and validates the corpus, asks Together to validate the
explicit template and files, prints the server price estimate, and prints a deterministic `campaign_fingerprint`.
It does not create a billed job.

The fingerprint binds the exact training/validation file digests plus `from_hf_model`, exact Hugging Face model
revision, explicit Together template, epochs, evaluations, training method/type, learning rate, warmup ratio and
checkpoint count. A create must be authorized against exactly that preflight identity:

```bash
export CLAYCOG_CREATE_FINGERPRINT=<exact campaign_fingerprint from the same preflight>
python3 launch_together_v1.py --create
```

A missing or stale fingerprint fails closed. Before remote file allocation on create, the launcher scans the account
for an existing job carrying the deterministic campaign suffix. It repeats the duplicate check immediately before
the billed create to narrow the check/use race. If the create transport outcome is ambiguous (for example, the server
may have accepted the job but the client timed out), **never blind-retry `--create`**: list/retrieve the existing
fine-tuning jobs first. The deterministic suffix exists specifically so such an account-side job can be recognized.

### Together 0.5B caveat — current template blocker

As checked on **2026-08-22**, Together's public fine-tuning supported-model table contains **no Qwen2/Qwen2.5 base**.
For Qwen full fine-tuning it currently lists Qwen3.5 models down to **0.8B**, but Qwen3.5 is a different architecture
from Qwen2.5 and is not silently admitted as a template merely because vendor family and parameter size are close.
Together's BYOM guide requires an external CausalLM/safetensors checkpoint under 100B without `trust_remote_code` and
a Together base/template whose architecture matches and whose size/context are suitable.

`Qwen/Qwen2.5-7B-Instruct-Turbo` is visible as an inference model, but visibility in the inference catalog is not
fine-tuning admission evidence. It is therefore **not an implicit launcher default anymore**. Supply
`CLAYCOG_TOGETHER_TEMPLATE` or `--template` only after current Together verification identifies a Qwen2-compatible
full-FT template. `model_limits` remains the first authenticated template gate. A Qwen3-family template is rejected
locally instead of silently changing the experiment to Qwen3.5-0.8B.

This is currently a **documentation/source blocker, not an authenticated Together runtime observation**. A credentialed
`model_limits` call may still reveal an admitted Qwen2-compatible template not shown in public documentation. If it
does not, retain the Qwen2.5-0.5B research target and use a Together-provided compatible template or another
owner-admitted full-FT runner; do not relabel a different model generation as the 0.5B campaign.

The primary Hugging Face checkpoint is pinned to revision
`285c998059f3e217fe1f05e241d55b5c5eef5bd3`; the instruct ablation is pinned to
`7ae557604adf67be50417f59c2c2f167def9a775`. The exact revision is included in the campaign fingerprint and is passed
as Together `hf_model_revision`; mutable Hugging Face `main` is not accepted for an unknown replacement checkpoint.

Together's current `estimate-price` request does **not** expose `from_hf_model` or `hf_model_revision`. Therefore a
successful price estimate proves only dataset/template/budget admission. It does not prove that Together has accepted
the external Qwen2.5-0.5B checkpoint. Actual BYOM compatibility remains **OPEN** until create accepts the exact
checkpoint/template pair and the job reaches a training state.

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
