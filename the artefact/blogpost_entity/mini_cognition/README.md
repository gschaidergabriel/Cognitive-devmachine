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

Install the SDK and mount the Together secret only in the execution environment:

```bash
pip install -U together
export TOGETHER_API_KEY=...
bash train_together_v1.sh
```

The shell script stops after **preflight**. It regenerates and validates the corpus, asks Together to validate the
files/template, and prints the server price estimate. It does not create a billed job.

**Important:** the estimate endpoint prices the uploaded data against the selected Together template. It does not
bind `from_hf_model` or `hf_model_revision`, so a successful price estimate is **not** evidence that the 0.5B BYOM
checkpoint is compatible with the template.

Before a billed create, resolve and pin the exact Hugging Face commit of the checkpoint:

```bash
export CLAYCOG_HF_REVISION=<exact-40-hex-Hugging-Face-commit>
python3 launch_together_v1.py --create
```

For the instruct ablation use `CLAYCOG_HF_INSTRUCT_REVISION` instead.

The launcher refuses billed creation without an exact commit pin. It hashes the exact train/validation bytes,
HF model+revision, Together template and training hyperparameters into `claycog-together-campaign/v2`, then derives
a deterministic Together `suffix` from that fingerprint. Before `create`, it lists the Together job ledger and
fails closed if the same campaign suffix already exists.

A same-campaign job in `pending`, `queued`, `running`, `compressing`, `uploading`, `cancel_requested` or `completed`
can never be blindly duplicated by this launcher. A prior `error`/`cancelled` job also blocks by default; one retry
requires the operator to inspect it and supply its exact id with `--retry-job-id <ft-...>`.

### Together 0.5B caveat

As of 2026-08-22, Together's regular supported-model table does not expose a native Qwen2.5 0.5B fine-tune entry.
The current lane therefore uses BYOM. Together documents that the training template architecture must match the
checkpoint; size should be as close as the catalog allows, and if every template is larger the smallest available
one should be selected. The current default candidate remains:

- BYOM weights: `Qwen/Qwen2.5-0.5B`;
- template candidate: `Qwen/Qwen2.5-7B-Instruct-Turbo`.

That pairing is **not assumed compatible** merely from the name or size. `model_limits` must admit full training,
and actual BYOM checkpoint validation remains an empirical Together job gate. There is deliberately no automatic
fallback to a different architecture such as Qwen3.5.

Together's published price surface has a per-job minimum charge. The server estimate is authoritative and this
campaign hard-aborts above the configured `$18` single-job ceiling. Training failures do not become research PASS;
Together currently documents failed jobs as refunded, but any retry still requires the explicit replay gate above.

## 0.5B RAM gate

The official Qwen2.5-0.5B-Instruct Q4_K_M GGUF is around 491 MB; this proves only file size, not runtime RSS.
`quantize_rss_gate_v1.sh` converts the tuned checkpoint, quantizes to Q4_K_M, and requires actual measured
peak process RSS `< 1 GiB` at context 2048.

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

No `go` may claim mathematical correctness, consciousness, compatibility or superiority from training intent alone.
