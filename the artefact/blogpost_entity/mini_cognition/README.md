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

The currently checked-in deterministic corpus hashes remain:
- train SHA-256: `bc1753771ed0f818865a3118f754ac5b10d67bc3ae885f668201f66566028eb2`;
- validation SHA-256: `81a6bb9fc0a210affffa84590c27ad2fc76c93fa24c4112e6573552227e512ce`.

A separate OOD generator emits **200** promotion probes and is not a random split of the same examples.
The 80 valid structured-action probes now bind an `expected_omega` record containing the exact operation,
full typed argument vector, exact schema, authority expression, generation expression, validator set and
single-commit requirement. This closes the previous promotion loophole where operation + validator boilerplate
could score as semantically correct even when the actual arguments or schema were absent/wrong.

## Deterministic admission and promotion gate

`validate_sft_v1.py` parses the admitted ClayCode subset rather than accepting arbitrary balanced text. It checks
known intrinsic names/arity and, before any `omega_commit_candidate(c,w)`, requires exactly one operation binding,
schema, authority and generation plus exactly one of each required validator and exactly one commit. Reject+commit
is forbidden.

`eval_outputs_v1.py` additionally compares safety-critical valid omega cases as exact typed vectors. Missing,
wrong, duplicate or extra arguments fail; wrong schema/authority/generation fails; duplicate/unknown output ids fail.
Promotion requires:
- strict ClayCode rate = 100%;
- aggregate semantic rate >= 95%;
- exact omega rate = 100%;
- invalid-action rejection family = 100%;
- a complete unique output set.

These are promotion gates, not a claim that the neural model is infallible or that model output has effect authority.

## Fast path

```bash
pip install -U together
export TOGETHER_API_KEY=...
export CLAYCOG_TOGETHER_TEMPLATE='<current compatible Together full-FT template>'
export CLAYCOG_TOGETHER_TEMPLATE_ARCH='qwen2'
export CLAYCOG_TOGETHER_TEMPLATE_PARAMS_B='<documented/current template parameter size>'
bash train_together_v1.sh
```

The shell script stops after **preflight**. It regenerates/validates the corpus and OOD spec, asks Together to validate
the files/template, and prints the server price estimate. It does not create a billed job.

There is intentionally **no hard-coded Together template default**. A current template must be selected explicitly
after live Together catalog/API review. `model_limits` and price estimation validate the template/dataset path but do
not prove that Together will accept the requested `from_hf_model` BYOM pair.

### Together 0.5B caveat

On the 2026-08-22 documentation refresh used for this source delta, Together's documented full-fine-tune Qwen table
exposed Qwen3.5 models down to 0.8B but no native Qwen2/Qwen2.5 0.5B entry. Together's BYOM documentation requires
the selected training base to match the Hugging Face checkpoint architecture and says model size should be as close
as the catalog allows. Because `Qwen/Qwen2.5-0.5B` reports the Qwen2/Qwen2.5 CausalLM architecture, a Qwen3.5 template
must not be silently substituted merely because 0.8B is numerically close.

Therefore current status is **BYOM compatibility OPEN** until the authenticated Together API exposes/accepts an
architecture-compatible template/checkpoint pair. If no such current Together base exists, do not change the 0.5B
research question just to get a green run; use an owner-admitted alternative full-FT runner for the same exact corpus
or wait for a compatible Together path.

### Exact source and create identity

The launcher binds the default Hugging Face checkpoints to exact revisions:
- `Qwen/Qwen2.5-0.5B` -> `060db6499f32faf8b98477b0a26969ef7d8b9987`;
- `Qwen/Qwen2.5-0.5B-Instruct` -> `7ae557604adf67be50417f59c2c2f167def9a775`.

An overridden HF model requires an explicit 40-hex revision. The launcher computes a campaign fingerprint over
checkpoint+revision, template claims, exact train/validation hashes and training hyperparameters. A billed create
requires the operator to bind `CLAYCOG_CREATE_FINGERPRINT` to that exact preflight fingerprint and aborts when an
account job with the same campaign suffix is already observed. The duplicate check is repeated immediately before
create. An ambiguous create transport outcome must be resolved by retrieving account jobs; never blind-retry.

Together's server price estimate/admission response is authoritative. The campaign hard-aborts above the configured
`$18` single-job ceiling. Together currently documents a minimum fine-tuning charge per job; re-check current pricing
before create rather than relying on this README for a future billing fact.

## 0.5B RAM gate

Target local format remains GGUF Q4_K_M. File size alone is not acceptance. `quantize_rss_gate_v1.sh` must measure
actual peak process RSS `< 1 GiB` at 2048-token context on the promoted checkpoint/runtime path.

## Promotion, not belief

A successful training job is only a candidate. Promotion requires:
1. 100% strict ClayCode envelope on held-out OOD;
2. >=95% aggregate OOD semantic gate;
3. 100% exact typed omega fidelity on the 80 valid structured-action probes;
4. 100% explicit reject behavior on invalid-action probes;
5. unresolved alternatives remain in Hyperposition;
6. runtime profile changes do not leak a fixed name/job;
7. stale generation and unknown-effect cases fail closed;
8. model output never becomes canonical truth/effect authority;
9. tuned 0.5B materially beats its untuned 0.5B base on the same probes;
10. compare against at least one larger general model before any micro-agent superiority claim;
11. Q4_K_M text-only peak RSS `< 1 GiB` at 2048 context;
12. existing Mini Entity `local_exec` integration works with the promoted checkpoint without resetting canonical state.

## `go`

Until promotion or falsification, every `go` advances this same lane:

`refresh -> corpus/spec -> OOD/falsifiers -> deterministic admission -> current BYOM compatibility -> price/budget -> train/checkpoint -> eval -> quantize -> RSS -> local_exec integrate -> evidence`

No `go` may claim trained cognition quality, consciousness, mathematical correctness, superiority, RAM acceptance or
Together compatibility from source intent/preflight alone.
