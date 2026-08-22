# Generic ClayCode Cognition v1 — 0.5B

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B).  
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

This lane turns the neutral Mini Entity into a replaceable first-party local cognition option without binding the
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

## Corpus v2 — current training candidate

A pre-training leakage audit found that corpus v1 reused a very small deterministic scenario pool across its random
train/validation split. Structural validity therefore did not imply useful held-out generalization evidence. Corpus v1
remains historical evidence only; do not use its validation loss as the promotion signal.

`generate_sft_v2.py` now emits **1,800** deterministic examples:
- 1,620 train;
- 180 validation;
- 9 families, exactly 200 cases per family;
- 20 held-out cases per family use disjoint value domains/surface forms;
- every train row is unique;
- every validation row is unique;
- exact train↔validation message overlap: **0**;
- exact train↔validation user-prompt overlap: **0**.

Bound candidate hashes from the isolated regeneration:
- train SHA-256: `ad132881aee5b794a1a81a56bc51af99d09d04c2fdff769f48cf192afa0d2a21`;
- validation SHA-256: `fad0e7a2613e54c3027ca5de8d8917ff3408a8a8a644439be764152648396e6f`.

The existing ClayCode structural validator reports 0 invalid rows on the locally regenerated v2 candidate. The exact
split gate additionally rejects duplicate rows or any exact train/validation collision.

The separate 200-case OOD generator remains the stricter promotion benchmark and is not the random validation split.

## Fast path

```bash
pip install -U together
export TOGETHER_API_KEY=...
bash train_together_v1.sh
```

`train_together_v1.sh` now routes through the v2 corpus and `launch_together_v2.py`. It stops after **preflight** by
default. It regenerates and validates the corpus, enforces the split gate, uploads for Together validation, checks the
candidate template and prints the server price estimate. It does not create a billed job.

Only after an accepted preflight:

```bash
python3 launch_together_v2.py --create
```

### Duplicate-create fence

Before the billed API create call, `launch_together_v2.py` atomically writes a create guard with status
`CREATE_ATTEMPTED_UNKNOWN`. If the process crashes or the network result is ambiguous, the next `--create` aborts and
requires inspection of Together job state instead of blindly creating a second paid job. After a successful create the
same guard is updated with the returned job id.

### Together 0.5B caveat

Together's public fine-tuning catalog currently exposes Qwen3.5 0.8B as the smallest documented Qwen entry and does not
list a Qwen2.5 fine-tuning template. BYOM requires a compatible Together base template for the custom Hugging Face
checkpoint. Therefore the configured `Qwen/Qwen2.5-7B-Instruct-Turbo` default remains an **API probe candidate only**;
it is not compatibility evidence and must fail closed if the live API does not admit full training/BYOM.

There is deliberately no automatic Qwen3.5 fallback: silently changing the architecture/model family would change the
0.5B research question. If Together cannot admit the Qwen2.5 0.5B checkpoint, keep the checkpoint requirement and move
the same corpus to another authorized full-FT runner rather than changing the target without owner direction.

Together's current standard full-SFT rate for models up to 16B is `$0.54 / 1M processed tokens`, with a documented
`$4.00` minimum fine-tuning job charge. The live Together estimate/admission response is authoritative. The campaign
hard-aborts above the configured `$18` single-job ceiling inside the owner EUR20 campaign budget.

## 0.5B RAM gate

Target local format is text-only GGUF `Q4_K_M`. File size is not acceptance. `quantize_rss_gate_v1.sh` requires actual
measured peak process RSS `< 1 GiB` at context 2048 before promotion.

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
9. compare against at least one larger general model on exact structured-task success before claiming micro-agent superiority;
10. Q4_K_M text-only peak RSS `< 1 GiB` at 2048 context.

## `go`

Until promotion, every `go` advances this same lane:

`refresh -> corpus/spec -> leakage/OOD falsifiers -> Together BYOM compatibility -> price/budget -> train/checkpoint -> eval -> quantize -> RSS -> integrate -> evidence`

No `go` may claim consciousness, mathematical correctness, Together compatibility, runtime RAM acceptance or superiority
from source/training intent alone.
