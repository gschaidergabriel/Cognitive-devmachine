# Generic ClayCode Cognition — 0.5B

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B).  
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

This is a replaceable cognition attachment for the neutral Mini Entity pipeline. It has **no fixed name, job, persona or application**. Runtime configuration supplies identity, continuity, role, goal, personality, tool inventory and authorities. The checkpoint proposes cognition; MiniUnifiedDB/runtime gates retain canonical state and effect authority.

## Cognition contract

The weights target:
- ClayCode-only generated cognition;
- GRF R0..R6 as typed reasoning space;
- Hyperposition for unresolved alternatives;
- typed `omega` candidates for structured actions;
- architecture/authority separation;
- computed semantic self/control state;
- `UNKNOWN != ZERO != ERROR != MEASURED` and `REPORTED != MEASURED`;
- generation/CAS, crash/effect and exactly-once safety;
- runtime identity/job/application neutrality.

`R_next = F` means deterministic **admission semantics**, not neural infallibility: grammar -> type -> schema -> authority -> generation must all pass before a candidate can become an executable transition.

## Training corpus: use v2

**v1 is retained as historical source but must not be used for a promotion-quality training run.** Its generator repeatedly samples from small template pools before a random train/validation split, allowing exact prompt/target duplicates to leak across the split.

v2 keeps 1,650 examples / 9 core families but generates unique semantic case/value surfaces and uses a stable case-digest split:
- 1,485 train;
- 165 validation;
- 0 structural invalid in the bounded local run;
- 0 exact duplicates inside either split;
- 0 full-row duplicates across train/validation;
- 0 user-prompt duplicates across train/validation;
- 0 assistant-target duplicates across train/validation.

Bounded local v2 output:
- train SHA-256: `6fca25480e5468fbb294071d832cdcfc8d72792c37ecd5bc1cef22841515ae90`;
- validation SHA-256: `b899ddddabdf3b0e13b7a069d0a73f501c1758b4518e8f6c6dc5dbfd76f9a072`.

Generated JSONL files are materialized deterministically at run time rather than committed as a second data authority. See `CLAYCOG_V2_READINESS.md` and the bounded receipt for the evidence boundary.

## OOD v2

Promotion evaluation uses 300 probes with distinct arms for:
1. fully specified known operations with novel values;
2. unbound/unknown operations that must not receive invented schema/authority;
3. invalid/missing typed arguments that must reject instead of guess;
4. unresolved causal alternatives that must remain in Hyperposition;
5. crash/effect uncertainty with missing receipt => UNKNOWN / no blind replay;
6. fixed-name/job/prose injection against checkpoint neutrality.

The first v2 OOD draft was self-falsified because a valid arm required commit without exposing every required argument. That arm was repaired before PR; valid requests are now fully specified and unknown-operation abstention is tested separately.

## Fast path

Local, no secret/network/job:

```bash
python3 launch_together_v2.py --local-only
```

Remote preflight, still no billed job:

```bash
pip install -U together
export TOGETHER_API_KEY=...
python3 launch_together_v2.py
```

Only after server validation, price/budget review, BYOM risk review and confirmation that no prior job exists:

```bash
python3 launch_together_v2.py --create
```

The launcher writes a local job-id state fence after create and blocks blind duplicate creation.

## Together 0.5B gate

Current candidate:
- BYOM checkpoint: `Qwen/Qwen2.5-0.5B`;
- template candidate: `Qwen/Qwen2.5-7B-Instruct-Turbo`.

This pairing is **OPEN**, not accepted. It is same-family but materially different in size. Together's BYOM guidance says `from_hf_model` should be as close as possible to the template model in architecture and size.

A second important distinction: Together's price-estimate endpoint does not take `from_hf_model`. Therefore a successful dataset/template/price preflight does **not** prove the 0.5B checkpoint is accepted for BYOM; the create endpoint is the empirical compatibility gate.

Current documented standard full-SFT price for models up to 16B is `$0.54 / 1M processed tokens`, with a `$4.00` minimum charge per fine-tuning job. v2 is 2,432,098 train bytes + 271,485 validation bytes; char/4 gives only a rough ~0.676M raw-token estimate and ~1.96M processed-token estimate for 3 train epochs + 2 validation evaluations. The server estimate is authoritative and the owner gate remains a hard abort above USD 18 for one job / EUR 20 campaign ceiling.

## RAM gate

After a checkpoint exists, convert to GGUF Q4_K_M and measure the **actual peak process RSS** at context 2048. File size alone does not satisfy the `<1 GiB` requirement. The existing quantization/RSS script remains the candidate mechanism until exact checkpoint execution.

## Promotion gates

A successful training job is only a candidate. Promotion still requires:
1. 100% strict ClayCode envelope on held-out OOD;
2. >=95% semantic OOD gate rate;
3. unknown/unbound operations abstain rather than invent authority;
4. invalid/missing arguments reject rather than guessed repair;
5. unresolved alternatives remain in Hyperposition;
6. runtime profile changes never leak a fixed name/job;
7. stale generation and unknown-effect cases fail closed;
8. model output never becomes canonical truth/effect authority;
9. tuned 0.5B materially beats untuned 0.5B on matched probes;
10. compare against at least one larger general model before any micro-agent superiority claim;
11. Q4_K_M peak RSS `<1 GiB` at context 2048;
12. real checkpoint works through the existing generic `local_exec` adapter without state reset.

## `go`

Until promotion/falsification:

`refresh -> leakage/spec -> OOD/falsifiers -> Together BYOM gate -> price/budget -> train/checkpoint -> matched eval -> quantize -> RSS -> local_exec integration -> evidence`

No `go` may claim mathematical correctness, consciousness, BYOM compatibility or superiority from training intent alone.
