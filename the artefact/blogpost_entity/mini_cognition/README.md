# Generic ClayCode Cognition — owner-selected Qwen3.5-0.8B Together lane

Primary paid-training checkpoint: `Qwen/Qwen3.5-0.8B`.

Owner decision on 2026-08-22 selected the directly supported Together Full Fine-Tuning lane. The previous `Qwen/Qwen2.5-0.5B` / `Qwen/Qwen2.5-0.5B-Instruct` pair remains historical comparison evidence only; it is no longer the paid Together training target.

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

## Corpus v2 — canonical paid-training input

`claycog-sft/v2` supersedes v1 for training. **SFT v1 must not be uploaded.**

The original v1 generator emitted 1,650 structurally valid rows but repeatedly sampled from small finite literal/template pools before a random train/validation split. Source analysis bounded that generator to roughly 71 distinct generated scenarios at most. V2 repairs that defect by making scenario parameters and split identities deterministically distinct and enforcing diversity/leakage checks.

Current SFT v2 evidence:
- 1,485 train rows, 1,485 exact-unique;
- 165 validation rows, 165 exact-unique;
- validation stratified at 10% inside every family;
- 0 exact cross-split message overlap;
- 0 exact cross-split user-prompt overlap;
- train structural invalid: 0;
- validation structural invalid: 0;
- train SHA-256: `3c715588d1b040494be48228f165208e2f10202b3f125616741116b90cd21b93`;
- validation SHA-256: `ca284585ba66c532e7e19232edd7f6b5dc1c0969d15cbb9d5ce1cbc202e86f62`.

Exact uniqueness alone is not a claim of semantic generalization. Held-out OOD, compositional OOD and matched untuned-base evaluation remain mandatory.

## Pre-paid corpus/evaluation gates

Before the final billed Together create, the campaign must retain all of these properties:
1. SFT v2 only; no v1 upload;
2. exact train/validation uniqueness and zero exact prompt/message cross-split overlap;
3. 100% strict structural ClayCode validity;
4. runtime-bound entity id, role, goal, personality, tool inventory and authorities;
5. no permanent checkpoint identity/persona/provider/model semantics;
6. exact omega operation + every typed argument/value/type + schema + runtime authority + runtime generation + exactly one grammar/types/schema/authority/generation validation sequence + exactly one commit;
7. missing authority, stale generation, invalid/missing args and unknown-effect recovery remain explicit rejection/UNKNOWN cases;
8. Hyperposition is preserved until evidence supports exact collapse;
9. `UNKNOWN != ZERO != ERROR != MEASURED` and `REPORTED != MEASURED` are retained;
10. OOD operation vocabulary stays disjoint from the paid-training operation vocabulary.

## Compositional OOD exact-vector gate

The evaluation-only `generate_eval_compositional_ood_v1.py` suite contains 320 cases. Its 80 `compositional_hyper_to_omega` cases now carry an `expected_omega` object specifying the exact operation, every typed argument/value, schema, authority expression, generation expression, all five validators and one commit.

`test_eval_compositional_exact_vector_v1.py` proves the evaluator accepts an exact vector and rejects a structurally plausible vector with a deliberately corrupted typed argument. This closes the prior metric gap where marker/operation/schema credit could pass without exact argument fidelity.

The separate OOD operation vocabulary remains unseen by SFT v2: `index.compact`, `blob.verify`, `route.reserve`, `ledger.annotate`.

## Together direct Full-FT path

Together's current supported-model documentation explicitly lists `Qwen/Qwen3.5-0.8B` for **Full fine-tuning**. The old Qwen2.5 BYOM architecture/template blocker therefore does not apply to this owner-selected paid lane.

Canonical direct launcher: `launch_together_qwen35_08b_v1.py`.

The launcher:
- hard-binds the exact model to `Qwen/Qwen3.5-0.8B`;
- regenerates and validates SFT v2 before provider access;
- requires live Together model limits to advertise Full training support;
- uploads the exact train/validation files and waits for provider processing;
- requests a live provider price estimate;
- hard-aborts above USD 18;
- binds model, exact file hashes, epochs, evals, seed, learning rate, warmup ratio, method/type and checkpoint count into a deterministic campaign fingerprint;
- scans provider state for duplicate campaign identity;
- requires the exact preflight fingerprint for create;
- persists a private fsynced `CREATE_ARMED` record before the billed transition;
- creates with zero SDK retries;
- records `UNKNOWN_REMOTE_CREATE` after ambiguous transport outcomes so blind retry is forbidden;
- persists `JOB_KNOWN` before provider re-read;
- verifies the created provider job identity against the exact campaign fields.

**Owner authorization boundary:** the owner selected Qwen3.5-0.8B/Together as the lane. That does **not** authorize a billed `--create` yet. The final paid run requires a fresh explicit owner authorization after corpus/evaluation hardening and an exact live preflight/fingerprint.

Current public standard pricing for Full SFT up to 16B is `$0.54 / 1M processed tokens`, with a `$4.00` minimum standard job charge. The live provider estimate remains authoritative; pricing is not a substitute for preflight.

## Promotion, not belief

A successful training job is only a candidate. Promotion requires:
1. 100% strict ClayCode envelope on held-out OOD;
2. >=95% OOD semantic gate pass;
3. invalid/missing tool arguments reject instead of guessed repair;
4. unresolved alternatives remain in Hyperposition;
5. runtime profile changes do not leak a fixed name/job/persona/model/provider;
6. stale generation and unknown-effect cases fail closed;
7. model output never becomes canonical truth/effect authority;
8. tuned Qwen3.5-0.8B materially beats untuned Qwen3.5-0.8B on the exact same probes;
9. compare against at least one larger general model on exact structured-task success before claiming micro-agent superiority;
10. quantize selected checkpoint to Q4_K_M;
11. actual measured peak process RSS `< 1 GiB` at context 2048; if 0.8B falsifies this existing gate, report the falsification rather than silently weakening the gate;
12. integrate through the existing generic `local_exec` path without resetting MiniUnifiedDB continuity.

## `go`

Until promotion or falsification, every `go` advances this same owner-selected lane:

`refresh -> corpus/spec -> OOD/falsifiers -> exact-vector scoring -> provider Full-FT admission -> price/budget -> explicit owner create authorization -> train/checkpoint -> tuned/base/larger eval -> quantize -> RSS -> integrate -> evidence`

No `go` may claim mathematical correctness, consciousness, provider success or superiority from training intent alone.
