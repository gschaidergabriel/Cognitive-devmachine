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

Previously recorded local structural validation on the original v1 validator/source revision:
- train: **0 / 1,485 invalid**;
- validation: **0 / 165 invalid**;
- train SHA-256: `bc1753771ed0f818865a3118f754ac5b10d67bc3ae885f668201f66566028eb2`;
- validation SHA-256: `81a6bb9fc0a210affffa84590c27ad2fc76c93fa24c4112e6573552227e512ce`.

**Important evidence boundary:** after validator hardening, those old zero-invalid counts do not automatically transfer.
The generated corpus must be rerun through the hardened validator before the next training preflight.

A separate OOD v1 generator emits **200** promotion probes and is not a random split of the same examples.
A second structural-transfer v2 generator emits **160** probes, including 80 valid and 40 invalid `omega`
routes whose operation names are asserted absent from `generate_sft_v1.py`. This is the anti-memorization gate:
a promoted checkpoint must transfer the ClayCode/omega abstraction to unseen operation contracts rather than only
repeat the six SFT operation names. The evaluator binds validators/authority/generation to the actual omega variable
chosen by the model and never executes proposed actions.

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

### Together 0.5B caveat — size match is now fail-closed

Together's current BYOM CLI documentation says `--from-hf-model` should match the base model's **architecture and size**.
The earlier v1 launcher used `Qwen/Qwen2.5-7B-Instruct-Turbo` as a convenient same-family template candidate for the
0.49B checkpoint. That is not a safe admissible default: same family is insufficient when size must also match.

The launcher now defaults the training template to the exact configured 0.5B BYOM model id and performs a static
architecture/size gate **before any file upload or Together client use**. The old 7B pairing is rejected with a
~14.29x size ratio. A template with unknown authoritative size is also rejected rather than guessed.

This does **not** prove Together currently exposes `Qwen/Qwen2.5-0.5B` as a full-training template. API compatibility
remains an empirical open gate. If Together's `model_limits` does not admit an architecture-and-size-compatible ~0.5B
Qwen2/Qwen2.5 template, the Together route is BLOCKED for this research question. Do not silently fall back to 7B or
Qwen3.5 and pretend the required 0.5B experiment was performed.

Together's documented standard full-SFT rate for models up to 16B is `$0.54 / 1M processed tokens`; the current
documentation also states a **$4.00 minimum charge per fine-tuning job**. The Together server estimate/admission
response remains authoritative, and the campaign hard-aborts above the configured `$18` single-job ceiling.

## 0.5B RAM gate

The official Qwen2.5-0.5B-Instruct Q4_K_M GGUF is around 491 MB; this proves only file size, not runtime RSS.
`quantize_rss_gate_v1.sh` converts the tuned checkpoint, quantizes to Q4_K_M, and requires actual measured
peak process RSS `< 1 GiB` at 2048 context.

## Promotion, not belief

A successful training job is only a candidate. Promotion requires:
1. 100% strict ClayCode envelope on held-out OOD;
2. >=95% OOD semantic gate pass;
3. >=95% structural-transfer v2 pass on unseen operation contracts with 100% structural ClayCode validity;
4. invalid/missing tool arguments reject instead of guessed repair;
5. unresolved alternatives remain in Hyperposition;
6. runtime profile changes do not leak a fixed name/job;
7. stale generation and unknown-effect cases fail closed;
8. model output never becomes canonical truth/effect authority;
9. tuned 0.5B materially beats its untuned 0.5B base on the same routing/epistemic/transfer probes;
10. compare against at least one larger general model on exact structured-task success before claiming "micro-agent superiority";
11. Q4_K_M text-only peak RSS `< 1 GiB` at 2048 context.

## `go`

Until promotion, every `go` advances this same lane:

`refresh -> corpus/spec -> hardened validator -> OOD + structural transfer -> Together size/architecture gate -> BYOM API compatibility -> price/budget -> train/checkpoint -> eval -> quantize -> RSS -> integrate -> evidence`

No `go` may claim mathematical correctness, consciousness, Together compatibility or superiority from training intent alone.
