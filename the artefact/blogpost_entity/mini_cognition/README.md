# Generic ClayCode Cognition — 0.5B training lane

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B).  
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

This lane adds a replaceable local cognition module to the neutral Mini Entity. The checkpoint has **no fixed name,
job, persona, application or tool inventory**. Runtime configuration supplies identity, continuity, role, goal,
personality, tools and authorities; MiniUnifiedDB remains persistent state authority.

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

## Curriculum generations

### v1 — isolated mechanism curriculum

Deterministic seed `20260822` produces **1,650** examples: 1,485 train / 165 validation across nine families.
The current main-line receipt records 0 structurally invalid v1 targets and exact SHA-256 digests in
`corpus_manifest_v1.json`. The original v1 OOD suite has 200 probes.

### v2 — compositional candidate

`generate_sft_v2.py` retains all **1,650** v1 examples and adds **600 compositional examples**. The point is not
more surface repetition. New rows require multiple cognition mechanisms in one turn:

- Hyperposition -> verified R6 receipt -> exact collapse -> fully gated omega;
- epistemic state -> action/no-action policy;
- valid schema/types + missing authority -> reject;
- valid schema/types/authority + stale generation -> reject;
- unseen runtime operation schemas -> exact typed omega without memorized tool names;
- runtime identity/role/goal/personality swaps -> same generic checkpoint;
- computed self-state -> routing pressure without factual promotion;
- crash ambiguity -> UNKNOWN + no blind replay.

The source invariant is **2,250 examples**: 2,025 train / 225 validation. These numbers become executable evidence only
when an exact branch run actually regenerates and validates them.

`generate_eval_ood_v2.py` is the compositional held-out discriminator: **320 probes** with operation/schema names not
present in v1 and multi-stage requirements. Its job is to falsify the cheap alternative explanation that a 0.5B model
merely learned the ClayCode envelope and isolated templates. `eval_outputs_v1.py` scores saved completions and never
executes an omega candidate.

## Safe Together path

The canonical candidate defaults to:
- corpus: `v2` (`CLAYCOG_CORPUS_VERSION=v1` remains an explicit rollback/ablation);
- BYOM weights: `Qwen/Qwen2.5-0.5B`;
- pinned HF revision: `060db6499f32faf8b98477b0a26969ef7d8b9987`;
- Instruct ablation revision: `7ae557604adf67be50417f59c2c2f167def9a775`;
- Together template candidate: `Qwen/Qwen2.5-1.5B`;
- full SFT, 3 epochs, 2 validation evaluations;
- deterministic training seed `20260822`;
- single-job hard ceiling `$18`, campaign ceiling EUR20.

Together documents `from_hf_model` as a Hugging Face starting checkpoint that should match the selected training
model's architecture and approximate size. Qwen2.5-1.5B is therefore a materially closer empirical template candidate
for Qwen2.5-0.5B than the earlier 7B choice. Together's changelog records Qwen2.5-1.5B full-SFT support, but live
`model_limits` remains the execution-time authority. Template admission is **not** proof that the 0.5B BYOM pair works.

The pinned HF revision and random seed are part of the deterministic campaign fingerprint, so changing either requires
a fresh preflight and cannot silently reuse create authorization.

### Preflight — no billed create

```bash
pip install -U together
export TOGETHER_API_KEY=...
bash train_together_v1.sh
```

The launcher regenerates/validates the selected corpus, uploads the two JSONL files, checks template full-FT support,
asks Together for its server-side price/admission estimate, and prints `campaign_fingerprint`.

That fingerprint binds exact dataset digests, corpus generation, HF checkpoint/revision, template, epochs, evaluations,
training method/type, learning rate, warmup, checkpoint count and random seed. Preflight does **not** create a training job.

### Create exactly once

```bash
export CLAYCOG_CREATE_FINGERPRINT=<exact fingerprint printed by the accepted preflight>
python3 launch_together_v1.py --create
```

A missing/stale fingerprint fails closed. The launcher scans the Together account for the deterministic campaign suffix
before remote file allocation and again immediately before create. If a create outcome is ambiguous — for example,
remote create may have succeeded while the client timed out — **do not retry blindly**. List/retrieve account jobs and
resolve the existing deterministic suffix first. This preserves the stronger idempotency mechanism already accepted in
PR #772.

### Pricing boundary

Together's current standard pricing lists **full supervised fine-tuning up to 16B at $0.54 per 1M processed tokens**.
Processed tokens are training tokens × epochs plus validation tokens × evaluations. The current pricing page also states
that **each fine-tuning job has a $4.00 minimum charge**. Therefore the concrete Together estimate is authoritative for
the actual tokenized corpus, but the campaign must budget at least $4 even if raw arithmetic is lower.

## BYOM compatibility boundary

Preflight can establish:
- local corpus structural validity;
- Together file-format acceptance;
- current template full-FT capability;
- current price/admission estimate.

It cannot establish that Together will instantiate the pinned 0.5B `from_hf_model`. BYOM compatibility remains **OPEN**
until create accepts the exact pair and the job actually reaches training. If Together rejects the Qwen2.5 0.5B/1.5B
pair, do **not** silently change the scientific target to Qwen3.5. Keep the 0.5B target and either identify another
Together-compatible Qwen2/Qwen2.5 template or use the same exact corpus/checkpoint on another admitted full-FT executor.

## Promotion gates

Training completion is only a candidate. Promotion requires:
1. 100% strict ClayCode envelope on held-out OOD;
2. >=95% semantic-gate pass;
3. v2 compositional holdouts materially beat the untuned 0.5B base;
4. invalid/missing arguments reject rather than guessed repair;
5. unresolved alternatives remain Hyperposition until a real discriminator/receipt exists;
6. runtime profile swaps do not leak a fixed name/job/persona;
7. stale generation and unknown-effect cases fail closed;
8. model output never becomes canonical truth or effect authority;
9. compare the tuned 0.5B with at least one larger general model on the same executable structured tasks before any
   micro-agent superiority claim;
10. convert/quantize the selected checkpoint to `Q4_K_M` and measure actual text-only peak process RSS `< 1 GiB` at
    context 2048; GGUF file size alone does not count;
11. integrate only through the existing generic `local_exec` adapter without resetting MiniUnifiedDB state.

Neither ClayCode behavior nor SFT is evidence of consciousness. Computed internal/self-control variables are a
representation/control contract, not proof of subjective experience.

## `go`

Until promotion/falsification:

`refresh -> compositional corpus/falsifier -> exact isolated source gate -> Together preflight -> single create -> retrieve/checkpoint -> OOD/base/larger-model benchmark -> quantize -> RSS -> local_exec integration -> durable evidence`

No report-only `go` is sufficient while executable/source progress is available.
