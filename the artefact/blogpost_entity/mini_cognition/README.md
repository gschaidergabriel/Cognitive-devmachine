# Generic ClayCode Cognition — 0.5B training lane

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B).  
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

This lane adds a replaceable local cognition module to the neutral Mini Entity. The checkpoint has **no fixed name,
job, persona, application or tool inventory**. Runtime configuration supplies identity, continuity, role, goal,
personality, tools and authorities; the persistent MiniUnifiedDB remains state authority.

## What the weights are intended to learn

- ClayCode-only generated cognition;
- GRF R0..R6 as a typed semantic reasoning field;
- Hyperposition for unresolved alternatives;
- `omega` as the compact typed function/tool/API action candidate;
- architecture-use priors and explicit external authority boundaries;
- computed semantic self/control state without treating it as external evidence;
- epistemic typing (`UNKNOWN != ZERO != ERROR != MEASURED`, `REPORTED != MEASURED`);
- generation/CAS, crash/effect and exactly-once safety;
- runtime identity/job/application neutrality.

`R_next = F` is **admission semantics**, not a neural correctness claim: the model proposes a candidate; deterministic
grammar, type, schema, authority and generation validators decide whether a transition can execute.

## Corpus generations

### v1 — isolated mechanism curriculum

Deterministic seed `20260822` produces **1,650** SFT examples:
- 1,485 train;
- 165 validation;
- 9 families: `omega_valid`, `omega_reject`, `epistemic`, `hyperposition`, `architecture`,
  `configuration`, `self_state`, `recovery`, `adversarial`.

Exact v1 hashes are recorded in `corpus_manifest_v1.json`. The current main-line receipt recorded 0 structural invalid
examples under `validate_sft_v1.py`.

### v2 — compositional candidate

`generate_sft_v2.py` retains all 1,650 v1 examples and adds **600 compositional examples**. The target is not more
surface repetition; the new rows force multiple mechanisms into the same turn:

- Hyperposition -> verified R6 receipt -> exact collapse -> fully gated omega;
- epistemic state -> action/no-action policy;
- valid schema/types + missing authority -> reject;
- valid schema/types/authority + stale generation -> reject;
- unseen runtime operation schemas -> exact typed omega without memorized tool names;
- runtime identity/role/goal/personality swaps -> same generic checkpoint;
- computed self-state -> routing pressure without factual promotion;
- crash ambiguity -> UNKNOWN + no blind replay.

Expected generated size is **2,250** examples (2,025 train / 225 validation). This count is a source invariant until an
isolated execution regenerates and validates the exact branch bytes; do not treat it as runtime evidence merely because
the generator asserts it.

The v2 unusual discriminator is `generate_eval_ood_v2.py`: **320 held-out compositional probes** using additional
operation/schema names and multi-stage requirements. Promotion scoring remains executable through `eval_outputs_v1.py`;
no proposed omega is executed by the evaluator.

## Together training path

Current intended BYOM pair:
- actual weights: `Qwen/Qwen2.5-0.5B`;
- pinned HF revision for the primary candidate: configurable, default currently `060db64`;
- template candidate: `Qwen/Qwen2.5-7B-Instruct` (same Qwen2.5/Qwen2 architecture family);
- training type: full SFT;
- default corpus: v2;
- default epochs: 3;
- deterministic training seed: `20260822`.

Together documents `from_hf_model` as a Hugging Face starting checkpoint and says it should match the selected base
model's architecture and approximate size. Therefore the template is infrastructure/configuration; the 0.5B HF checkpoint
is still the weights being trained. Template admission is **not** proof that Together can load the specific 0.5B BYOM
checkpoint.

### Safe preflight

```bash
pip install -U together
export TOGETHER_API_KEY=...
bash train_together_v1.sh
```

The launcher:
1. regenerates the selected corpus;
2. validates every local assistant target structurally;
3. uploads/validates train + validation JSONL through Together Files;
4. checks the chosen template's current full-training model limits;
5. asks Together for its price/admission estimate;
6. hashes model/revision/template/dataset/hyperparameters into a deterministic campaign id;
7. writes `together_preflight_latest.json` locally;
8. stops without a billed job unless `--create` is explicit.

Create exactly once only after the preflight is acceptable:

```bash
python3 launch_together_v1.py --corpus v2 --create
```

Before create, the script lists existing jobs and fails closed if the same deterministic campaign suffix already exists.
This is a duplicate-create guard, not a distributed transaction; the resulting Together job id remains the durable handle
that must be retrieved rather than blindly re-created.

### Pricing boundary

Together's current standard pricing page lists **full supervised fine-tuning up to 16B at $0.54 per 1M processed tokens**.
Processed tokens are training tokens multiplied by epochs plus validation tokens multiplied by evaluation passes.
The current standard rate table does **not** establish a universal `$4 minimum` for this campaign; specialized large-model
rows may have separate minimums. Therefore the launcher's live Together `estimate_price` response is the budget authority,
and the owner gate still aborts above **$18 for a single job** / **EUR 20 campaign ceiling**.

No cost should be inferred from JSONL byte size alone; tokenizer + server estimate wins.

## BYOM compatibility boundary

Preflight can prove:
- file-format acceptance;
- template full-FT capability;
- price/admission estimate.

It cannot prove that Together will successfully instantiate the pinned `from_hf_model` checkpoint. BYOM compatibility is
promoted only when the create endpoint accepts the exact HF model + revision. If Together rejects the Qwen2.5 template/
0.5B pairing, do **not** silently change the research target to Qwen3.5. Find a compatible Qwen2/Qwen2.5 training template
or run the same exact corpus and checkpoint on another full-FT executor.

## 0.5B RAM gate

The official Qwen2.5-0.5B-Instruct `Q4_K_M` GGUF is about **491 MB**, which proves file size only. The tuned candidate must
be converted/quantized and measured under the real runtime. `quantize_rss_gate_v1.sh` requires actual peak process RSS
`< 1 GiB` at context 2048 before RAM promotion.

## Promotion, not belief

A completed training job is only a candidate. Promotion requires, at minimum:
1. 100% strict ClayCode envelope on held-out OOD;
2. >=95% semantic-gate pass;
3. compositional v2 holdouts materially outperform the untuned 0.5B base;
4. invalid/missing tool arguments reject rather than guessed repair;
5. unresolved alternatives remain Hyperposition until a real discriminator/receipt exists;
6. runtime profile changes do not leak a fixed name/job/persona;
7. stale generation and unknown-effect cases fail closed;
8. model output never becomes canonical truth or effect authority;
9. tuned 0.5B is compared with at least one larger general model on the same executable structured tasks before any
   "micro-agent superiority" claim;
10. Q4_K_M text-only peak RSS is measured `< 1 GiB` at context 2048.

Neither ClayCode behavior nor SFT is evidence of consciousness. Computed internal/self-control variables are part of the
representation contract, not proof of subjective experience.

## `go`

Until promotion/falsification, every `go` advances this same lane:

`refresh -> spec/corpus -> compositional falsifier -> Together BYOM + price gate -> train/checkpoint -> OOD/base/larger-model benchmark -> quantize -> RSS -> local_exec integration -> durable evidence`

No report-only `go` is sufficient while executable/source progress is available.
