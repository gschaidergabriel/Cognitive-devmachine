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

## Corpus v2 — canonical training input

`claycog-sft/v2` supersedes v1 for paid training.

The original v1 generator emitted 1,650 rows, but its families sampled from small repeated literal pools and then
randomly split those rows. Source analysis gives an upper bound of roughly **71 distinct generated scenarios** before
shuffle, so exact scenario duplication across train and validation is expected. Structural validity of v1 therefore
did **not** establish a clean validation split. Keep v1 only as historical evidence; do not upload it for training.

The v2 generator preserves the same nine semantic families and total size while making every scenario split-specific
and deterministic:
- 1,650 total examples;
- 1,485 train, all 1,485 unique;
- 165 validation, all 165 unique;
- 0 exact cross-split message overlap;
- 0 exact cross-split user-prompt overlap;
- structural ClayCode validation remains mandatory;
- validation allocation is stratified at 10% inside every semantic family.

Bound v2 hashes at this source revision:
- train SHA-256: `8a9df9c81c1e7f199bab6cfe65acfec080a87a29eaff02e345b3eb0923d518d6`;
- validation SHA-256: `7bc3d28041b7fd51992e8b62f2a69981016910404b5fc6b7ce2d4444050d21f5`.

A separate OOD generator still emits 200 promotion probes and is not the held-in validation split.

## Fast path

```bash
pip install -U together
export TOGETHER_API_KEY=...
bash train_together_v1.sh
```

Despite the historical filename, the shell/launcher now regenerate and validate **v2** only. The shell stops after
**preflight**. A billed job requires an explicit `--create` after all gates pass.

### Together 0.5B admission reality — 2026-08-22

Together's current documented **Full fine-tuning** table contains Qwen3.5 models down to 0.8B and Qwen3.6 27B,
but no documented Qwen2/Qwen2.5 Full-FT template. The owner-required checkpoint remains
`Qwen/Qwen2.5-0.5B`; it must not silently become Qwen3.5-0.8B merely because that model is trainable.

Together BYOM requires a Together base/training template whose architecture matches the Hugging Face checkpoint.
The launcher therefore keeps `Qwen/Qwen2.5-7B-Instruct-Turbo` only as a **configurable empirical probe**, not as an
assumed compatible template. Before any dataset upload it calls `model_limits` and requires
`supports_full_training == true`. Failure stops with `uploads_started=false` and `job_started=false`.

If Together exposes a documented Qwen2-compatible Full-FT template, pass it with `--template` or
`CLAYCOG_TOGETHER_TEMPLATE`. If not, keep the 0.5B research question and move the same full-SFT campaign to another
owner-admitted full-FT runner rather than changing architecture.

### Cost gate

Together's current standard SFT Full Fine-Tuning rate for models up to 16B is `$0.54 / 1M processed tokens`, with a
current `$4.00` minimum charge per job. The server estimate is authoritative. The launcher still hard-aborts above the
owner campaign's `$18` single-job gate and never creates a job during default preflight.

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

`refresh -> corpus/spec -> OOD/falsifiers -> ClayCode lowering -> Full-FT template admission -> price/budget -> train/checkpoint -> eval -> quantize -> RSS -> integrate -> evidence`

No `go` may claim mathematical correctness, consciousness or superiority from training intent alone.
