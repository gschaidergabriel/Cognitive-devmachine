# Generic ClayCode Cognition v1 — 0.5B

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B).  
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

This lane turns the existing neutral Mini Entity into a first-party local cognition option without binding the binary or persistent entity identity to one model. The checkpoint has **no fixed name or job**; runtime configuration supplies identity, continuity, role, goal, personality, tool inventory and authorities.

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

`R_next = F` is implemented as **admission semantics**: only a candidate that passes grammar, type, schema, authority and generation validation may become an executable transition. The neural model proposes the vector; the deterministic runtime owns validity and execution.

## Corpus v1

Deterministic seed `20260822` produces **1,650** SFT examples:
- 1,485 train;
- 165 validation;
- 9 families: `omega_valid`, `omega_reject`, `epistemic`, `hyperposition`, `architecture`, `configuration`, `self_state`, `recovery`, `adversarial`.

A separate OOD generator emits **200** promotion probes and is not a random split of the same examples.

### 2026-08-22 admission hardening

The earlier reported `0 / 1,485` train and `0 / 165` validation invalid counts were produced by a **weak structural validator**. That validator checked the outer prefix, brace/parenthesis balance, required binding substrings and a small forbidden-string list, but it did not actually establish the specification's fail-closed rules for unknown intrinsics, bad arity or natural language outside strings.

One bounded mutation falsifier demonstrated the gap: five deliberately invalid but superficially ClayCode-shaped targets were all accepted by the old validator:

1. free prose in the function body;
2. an invented intrinsic;
3. wrong intrinsic arity;
4. trailing garbage after a valid call;
5. an invented constructor.

The current source candidate hardens `validate_sft_v1.py` with:

- strict statement/body grammar;
- recursive call/expression parsing;
- JSON string-literal validation;
- explicit intrinsic allowlist and exact arity checks;
- rejection of trailing non-ClayCode text;
- pre-commit `omega` gate/authority/generation ordering checks;
- rejection of contradictory reject+commit for the same candidate.

`test_validate_sft_v1.py` adds deterministic regressions for the five mutation classes, `omega` ordering, a valid gated `omega` candidate, and all **1,650** targets produced by `generate_sft_v1.py`.

**Evidence boundary:** the mutation bundle was observed to fail under the old admission and pass under the hardened logic. The full 1,650-target regression exists as source but must not be called exact runtime PASS until an actually-started authorized isolated runner executes the exact branch/source identity.

A focused GitHub-hosted workflow now exists on `main` to run this admission regression on future `mini_cognition` pull-request updates. Workflow existence is not test evidence; only an actually-started job with visible steps earns runtime credit.

Historical corpus hashes from the generator before this admission change remain:
- train SHA-256: `bc1753771ed0f818865a3118f754ac5b10d67bc3ae885f668201f66566028eb2`;
- validation SHA-256: `81a6bb9fc0a210affffa84590c27ad2fc76c93fa24c4112e6573552227e512ce`.

The admission hardening does not intentionally mutate generator output; a fresh exact-source run must confirm parity before promotion.

## Fast path

```bash
pip install -U together
export TOGETHER_API_KEY=...
bash train_together_v1.sh
```

The shell script stops after **preflight**. It regenerates and validates the corpus, asks Together to validate the files/template, and prints the server price estimate. It does not create a billed job.

Only after preflight:

```bash
python3 launch_together_v1.py --create
```

### Together 0.5B caveat

As of 2026-08-22, Together's regular supported-model table does not establish native fine-tuning support for this exact `Qwen/Qwen2.5-0.5B` checkpoint. The current campaign therefore treats Hugging Face BYOM checkpoint acceptance as a live server-side gate, not an assumption.

The current launcher pairs:

- BYOM weights: `Qwen/Qwen2.5-0.5B`;
- same-family template candidate: `Qwen/Qwen2.5-7B-Instruct-Turbo`.

That pairing is **not assumed fine-tune compatible** merely because the template exists. The launcher first asks `model_limits` whether the template is currently full-FT capable; exact BYOM checkpoint/template acceptance remains a separate preflight gate. There is deliberately no automatic architecture-changing fallback.

Current public pricing checked on 2026-08-22 lists standard Full SFT up to 16B at `$0.54 / 1M processed tokens` with a `$4.00` minimum charge per training job. The Together server estimate/admission response remains authoritative for the actual campaign, and the launcher hard-aborts above the configured `$18` single-job ceiling. The owner-authorized campaign ceiling remains EUR 20.

No paid job should be created from source readiness alone. A missing secret or uncertain compatibility remains BLOCKED/UNKNOWN rather than guessed.

## 0.5B RAM gate

A Q4_K_M checkpoint file being below 1 GiB does not establish the runtime requirement. `quantize_rss_gate_v1.sh` must measure actual peak process RSS and requires `< 1 GiB` at 2048 context.

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
9. compare against at least one larger general model on exact structured-task success before claiming micro-model superiority;
10. Q4_K_M text-only peak RSS `< 1 GiB` at 2048 context.

## `go`

Until promotion, every `go` advances this same lane:

`refresh -> corpus/spec -> OOD/falsifiers -> ClayCode lowering -> Together BYOM compatibility -> price/budget -> train/checkpoint -> eval -> quantize -> RSS -> integrate -> evidence`

No `go` may claim mathematical correctness, semantic validity, runtime compatibility or superiority from training intent/source coherence alone.
