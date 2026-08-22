# Generic ClayCode Cognition — 0.5B

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B). Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.
The checkpoint has no fixed name, job, persona, application, provider or tool inventory. Those bind from runtime configuration.

## Weight behavior target

The weights learn ClayCode-only cognition, GRF R0..R6, explicit Hyperposition, typed `omega` action candidates,
computed control/self state and the authority split. `R_next = F` means deterministic runtime admission after
`grammar -> type -> schema -> authority -> generation`; it is not a claim of neural infallibility. Model output is
neither canonical truth nor effect authority.

## Corpus v2 — canonical training candidate

A pre-training audit falsified corpus v1 as a useful random-split generalization check: its 1,650 rows were repeatedly
sampled from a very small deterministic scenario/template pool, so validation could reward memorized surface patterns.
Corpus v1 remains historical/source evidence, but it is no longer the recommended paid-training input.

`generate_sft_v2.py` deterministically produces **1,800** examples:
- 1,620 train and 180 validation;
- 9 families, exactly 200 cases/family;
- 180 train + 20 held-out cases per family;
- held-out values/surface forms are generated from disjoint domains where applicable;
- 1,620/1,620 train rows unique;
- 180/180 validation rows unique;
- exact train↔validation message overlap: 0;
- exact train↔validation user-prompt overlap: 0.

Bound deterministic hashes from isolated regeneration of the v2 semantics:
- train: `ad132881aee5b794a1a81a56bc51af99d09d04c2fdff769f48cf192afa0d2a21`;
- validation: `fad0e7a2613e54c3027ca5de8d8917ff3408a8a8a644439be764152648396e6f`.

`test_corpus_v2.py` additionally requires all 1,800 targets to pass the strict ClayCode validator and rejects fixed
Zero/blog identity literals. `corpus_split_gate_v2.py` fails closed on duplicates or exact train/validation collisions.
The separate 200-case OOD suite remains the stronger promotion benchmark; v2 validation loss alone cannot promote a model.

## Safe Together path

```bash
pip install -U together
export TOGETHER_API_KEY=...
bash train_together_v1.sh
```

The script now generates and validates corpus v2, applies the split gate, then calls the **thin**
`launch_together_v2.py` adapter. The adapter changes only corpus paths/checks and delegates all provider/billing logic
to the single canonical `launch_together_v1.py` implementation.

Default is preflight only. A billed create requires the exact printed fingerprint:

```bash
export CLAYCOG_CREATE_FINGERPRINT=<exact campaign_fingerprint from this preflight>
python3 launch_together_v2.py --create
```

The canonical launcher provides the durable safety boundary already merged on main: exact dataset/config fingerprint,
deterministic account suffix, account-side duplicate checks, local atomic create-intent ledger and a zero-retry SDK client
for the non-idempotent billed CREATE. An ambiguous remote outcome remains `UNKNOWN_REMOTE_CREATE`; never delete the local
intent merely to retry. Reconcile exact provider state first.

## Together 0.5B caveat

Together has no documented native 0.5B Qwen fine-tune entry in the currently checked public table. The 0.5B path is BYOM.
BYOM needs a compatible Together base/template architecture for the external Hugging Face checkpoint. The configured
`Qwen/Qwen2.5-7B-Instruct-Turbo` is therefore a **live API probe candidate**, not compatibility evidence.
`model_limits` and price estimation can admit the template/corpus but do not prove that
`from_hf_model=Qwen/Qwen2.5-0.5B` is accepted. BYOM compatibility remains OPEN until exact create acceptance and a real
training state are observed. Do not silently fall back to a different architecture/model family.

Current owner gate: maximum single job USD18 within the EUR20 campaign ceiling. The server estimate is authoritative.
No paid create is implied by source readiness.

## Promotion gates

A trained checkpoint is still only a candidate. Promotion requires:
1. 100% strict ClayCode envelope on the 200-case OOD suite;
2. >=95% OOD semantic gate pass;
3. invalid/missing tool arguments reject instead of guessed repair;
4. unresolved alternatives remain in Hyperposition until a discriminator/R6 receipt;
5. no fixed runtime name/job/application leakage;
6. stale generation and unknown-effect cases fail closed;
7. model output never becomes canonical truth/effect authority;
8. tuned 0.5B materially beats untuned 0.5B on the matched probes;
9. comparison against at least one larger general model before any micro-agent-superiority claim;
10. text-only GGUF `Q4_K_M` measured peak process RSS `<1 GiB` at context 2048;
11. integration through the existing generic `local_exec` adapter without resetting MiniUnifiedDB state.

No architecture, SFT loss, self-report or behavior target is evidence of consciousness or mathematical correctness.
