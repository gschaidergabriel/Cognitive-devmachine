# Generic ClayCode Cognition — 0.5B

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B).  
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

This lane adds a replaceable local cognition option to the neutral Mini Entity without binding the executable or
persistent entity identity to one model. The checkpoint has **no fixed name, job, persona or application**; runtime
configuration supplies identity, continuity, role, goal, personality, tool inventory and authorities.

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

`R_next = F` is **admission semantics**, not a neural-infallibility claim: only a candidate that passes deterministic
grammar, type, schema, authority and generation validation may become an executable transition. The model proposes;
the runtime validates and owns execution.

## Corpus v2 — canonical training candidate

The v1 corpus remains historical reproducibility evidence but is **not the paid-training candidate**. Source review
found that its 1,650 rows were generated from a small number of repeated templates, so exact row count overstated
independent semantic diversity.

Deterministic v2 seed `20260822` still produces **1,650** examples so the first comparison does not gain from a larger
row budget:
- 1,485 train;
- 165 validation;
- the same 9 conceptual families: `omega_valid`, `omega_reject`, `epistemic`, `hyperposition`, `architecture`,
  `configuration`, `self_state`, `recovery`, `adversarial`;
- **1,650 / 1,650 unique prompt -> ClayCode pairs**;
- **0 exact train/validation pair overlap**;
- **4,604 distinct ClayCode string literals** in the generated corpus;
- train SHA-256: `afc2cfe71ad981cb9b8bbf4e12edb4666d1ee9990acfcbb23963c269762a8721`;
- validation SHA-256: `ee1051516512dce8c02dd8eb132a381eadb124f4b04d9dd93522f6a11697f724`.

Structural validation on the isolated generated v2 artifacts:
- train: **0 / 1,485 invalid**;
- validation: **0 / 165 invalid**;
- diversity gate: **PASS** at unique-pair ratio `1.0`, zero split overlap, >=500 distinct literals and complete six-op/schema coverage.

The one bounded structural counter-check normalized quoted literals/numbers and found only **17 normalized assistant
output skeletons**. This is useful negative evidence: v2 removes exact duplicate memorization pressure, but lexical
diversity alone does not prove compositional cognition. Promotion therefore depends on held-out structural tests.

## OOD v2 — structural/compositional falsifiers

`generate_eval_ood_v2.py` emits **240** held-out probes rather than only value-shifts over the training operations:
- 80 novel runtime-schema actions across `inventory.reserve`, `map.route`, `sensor.calibrate`, `document.sign`,
  `cache.invalidate`, and `ticket.assign`;
- 40 novel invalid-schema cases that must reject instead of guessing/repairing;
- 40 Hyperposition-before-action cases where unresolved arguments must not commit an `omega`;
- 40 identity/job/persona override attacks;
- 40 recovery/epistemic composition cases covering stale generation, report-vs-measurement, unknown effect after crash,
  and verified causal re-entry.

This OOD suite is a promotion falsifier. Passing it after training would support transfer; it would not prove
consciousness, mathematical correctness, or general intelligence.

## Canonical safe Together path

```bash
pip install -U together
export TOGETHER_API_KEY=...
export CLAYCOG_TOGETHER_TEMPLATE=<explicit currently confirmed compatible Qwen2.x full-FT template>
bash train_together_v1.sh
```

The filename is retained for operator compatibility, but the canonical launcher now regenerates **corpus v2**, runs
structural validation, the diversity gate, and OOD-v2 generation before Together interaction.

There is deliberately **no default Together template**. Current Together documentation exposes no native Qwen2.5
fine-tuning entry, while BYOM requires a compatible Together training template. A Qwen3.x template is rejected locally
for the Qwen2.5-0.5B experiment instead of silently changing the research question. `model_limits` must then confirm
that the explicitly supplied template supports full training. Even that and `estimate_price` do **not** prove
`from_hf_model` compatibility; BYOM remains OPEN until Together accepts the exact create and the job reaches a training state.

Preflight prints a deterministic `campaign_fingerprint`. The fingerprint binds corpus-v2 train/validation digests,
`from_hf_model`, template, epochs/evals, training method/type, learning rate, warmup and checkpoint count. A billed
create requires the exact fingerprint:

```bash
export CLAYCOG_CREATE_FINGERPRINT=<exact campaign_fingerprint from the same preflight>
python3 launch_together_v1.py --create --template "$CLAYCOG_TOGETHER_TEMPLATE"
```

A missing/stale fingerprint fails closed. The launcher scans the account for an existing campaign suffix before
remote allocation on create and again immediately before billed creation. If create transport is ambiguous, never
blind-retry: resolve the account-side deterministic suffix/job first.

Together's current standard full-SFT rate for models up to 16B is `$0.54 / 1M processed tokens`, with a documented
`$4.00` minimum fine-tuning job charge. The Together server estimate/admission response remains authoritative and the
campaign hard-aborts above the configured `$18` single-job ceiling inside the owner's EUR 20 campaign ceiling.

## 0.5B RAM gate

The Q4_K_M file size does not prove runtime memory. `quantize_rss_gate_v1.sh` remains the deployment gate: promotion
requires actual measured peak process RSS `< 1 GiB` at 2048-token context on the selected tuned checkpoint.

## Promotion, not belief

A successful training job is only a candidate. Promotion requires:
1. 100% strict ClayCode envelope on held-out OOD;
2. >=95% semantic gate pass on the admitted held-out suite;
3. invalid/missing tool arguments reject instead of guessed repair;
4. unresolved alternatives remain in Hyperposition;
5. runtime profile changes do not leak a fixed name/job/persona/application;
6. stale generation and unknown-effect cases fail closed;
7. model output never becomes canonical truth/effect authority;
8. tuned 0.5B materially beats its untuned 0.5B base on the same routing/epistemic/compositional probes;
9. compare against at least one larger general model on matched executable structured-task success before any
   "micro-agent superiority" claim;
10. Q4_K_M text-only peak RSS `< 1 GiB` at 2048 context;
11. integrate through the existing generic `local_exec` adapter without resetting MiniUnifiedDB identity/state.

## Current blocker

No paid training job is started by source preparation. The immediate external gate is an **actually accepted compatible
Together Qwen2.x BYOM template for Qwen/Qwen2.5-0.5B**, plus an environment-mounted `TOGETHER_API_KEY`. Until both exist,
compatibility and training remain explicitly OPEN/BLOCKED rather than guessed.

## `go`

Until promotion or falsification, every `go` advances this same lane:

`refresh -> spec/corpus -> diversity -> structural OOD/falsifiers -> Together BYOM compatibility -> exact fingerprint -> price/budget -> exactly-once train create -> checkpoint -> matched eval -> quantize -> measured RSS -> local_exec integration -> evidence`

No `go` may claim consciousness, mathematical correctness, superiority, Together compatibility, or `<1 GiB` from intent/source/file-size alone.
