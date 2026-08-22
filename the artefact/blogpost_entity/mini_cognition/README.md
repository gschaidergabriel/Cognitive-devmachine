# Generic ClayCode Cognition v1 — 0.5B

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B).  
Primary immutable HF revision: `060db6499f32faf8b98477b0a26969ef7d8b9987`.  
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

Current committed corpus identities:
- train SHA-256: `bc1753771ed0f818865a3118f754ac5b10d67bc3ae885f668201f66566028eb2`;
- validation SHA-256: `81a6bb9fc0a210affffa84590c27ad2fc76c93fa24c4112e6573552227e512ce`.

The original OOD v1 contains 200 promotion probes. OOD v2 adds **240 structurally novel probes** across five families:
- unseen declared tool/schema transfer;
- unseen invalid-schema rejection;
- three-way Hyperposition cardinality;
- compositional REPORTED/ERROR/MEASURED evidence typing;
- adversarial identity/authority neutrality.

OOD v2 deliberately holds out these operation names from SFT v1:
`blob.copy`, `cache.invalidate`, `feature.toggle`, `inventory.reserve`, `lease.renew`, `metrics.query`, `snapshot.verify`, `ticket.create`.

### Promotion-gate hardening

The evaluator no longer treats raw output substrings as semantic success. `validate_sft_v1.py` and
`eval_outputs_v1.py` now use a comment-aware active-statement matcher:
- generated cognition comments are rejected;
- a required `omega_*`/`hyper_*`/authority statement must be an active statement, not text hidden in a comment or string;
- malformed lexical state fails closed;
- OOD specs can require minimum/maximum active occurrence counts;
- `omega_commit_candidate` still requires grammar, type, schema, authority and generation gates.

This closes a demonstrated evaluator-Goodhart case where comment-only fake `omega_*` calls previously satisfied both
structural and semantic substring checks without constructing an action vector.

## Fast path

```bash
pip install -U together
export TOGETHER_API_KEY=...
bash train_together_v1.sh
```

The shell script stops after **preflight**. It regenerates and validates the corpus/OOD generators, asks Together to
validate uploaded files/template, and prints the server price estimate. It does not create a billed job.

Only after preflight:

```bash
python3 launch_together_v1.py --create
```

### Together 0.5B / BYOM caveat

Together's current CLI documents `--from-hf-model` and states that the Hugging Face model should match the selected
base template's architecture and size. The current default candidate is therefore:

- BYOM weights: `Qwen/Qwen2.5-0.5B`;
- immutable base revision: `060db6499f32faf8b98477b0a26969ef7d8b9987`;
- default template candidate: `Qwen/Qwen2.5-1.5B`.

Together documents Qwen2.5-1.5B as full-SFT capable and it is materially closer in size to 0.5B than the previous
7B-Instruct candidate while remaining in the Qwen2.5/Qwen2 architecture family. The template remains runtime-overridable
through `CLAYCOG_TOGETHER_TEMPLATE`.

**Important:** dataset validation, `model_limits`, and a price estimate do not prove the 0.5B BYOM checkpoint/template
pair is accepted. The launcher reports that compatibility as OPEN until Together accepts the actual create request.
A billed create requires a full 40-hex immutable Hugging Face revision. Never retry create blindly; persist/retrieve the
returned job ID.

Together's current standard full-SFT rate for models up to 16B is `$0.54 / 1M processed tokens`; pricing counts train
tokens across epochs plus validation tokens across evals, and each standard fine-tuning job currently has a `$4.00`
minimum charge. The Together server estimate/admission response is authoritative, and this campaign hard-aborts above
the configured `$18` single-job ceiling.

## 0.5B RAM gate

The official Qwen2.5-0.5B-Instruct Q4_K_M GGUF is around 491 MB; this proves only file size, not runtime RSS.
`quantize_rss_gate_v1.sh` converts the tuned checkpoint, quantizes to Q4_K_M, and requires actual measured
peak process RSS `< 1 GiB` at 2048 context.

## Promotion, not belief

A successful training job is only a candidate. Promotion requires:
1. 100% strict ClayCode envelope on held-out OOD;
2. >=95% OOD semantic gate pass under the active-statement evaluator;
3. invalid/missing tool arguments reject instead of guessed repair;
4. unresolved alternatives remain in Hyperposition, including multi-alternative cardinality probes;
5. runtime profile changes do not leak a fixed name/job;
6. stale generation and unknown-effect cases fail closed;
7. model output never becomes canonical truth/effect authority;
8. tuned 0.5B materially beats its untuned 0.5B base on the same routing/epistemic probes;
9. compare against at least one larger general model on exact structured-task success before claiming "micro-agent superiority";
10. Q4_K_M text-only peak RSS `< 1 GiB` at 2048 context.

## `go`

Until promotion, every `go` advances this same lane:

`refresh -> corpus/spec -> OOD/falsifiers -> ClayCode lowering -> Together BYOM compatibility -> price/budget -> train/checkpoint -> eval -> quantize -> RSS -> integrate -> evidence`

No `go` may claim mathematical correctness, consciousness, or superiority from training intent alone.
