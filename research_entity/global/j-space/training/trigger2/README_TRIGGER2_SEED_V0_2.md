# Trigger-2 audited seed v0.2

Status: **STRUCTURAL PREMATERIALIZATION ONLY**  
Date: 2026-08-25  
Product: EntityOS  
Architecture: HCU  
Supervisor at construction: 8.78 / FREE_ONLY

## Files

- `2026-08-25_TRIGGER2_FUSED_AUDITED_SEED_V0_2.json` — swarm/adjudication record, hypotheses, counterhypothesis, falsifiers, split design and promotion boundary.
- `2026-08-25_TRIGGER2_XENO_ARCHITECTURE_PROTOCOL_SEED_V0_2.jsonl` — 24 source-derived METHOD_ONLY protocol examples aligned to the current Xeno/HCU owner target.
- `2026-08-25_TRIGGER2_XENO_BINDING_STRUCTURAL_SEED_V0_2.jsonl.gz.b64` — base64 text wrapping deterministic gzip of the 234-row structural dynamic-binding seed.

## Binding-seed identities

Expected uncompressed JSONL SHA-256:

`5f6c39f425af4178ebe45895103bacec460f604fad8a5a4486626fdef8eaafc7`

Expected deterministic gzip SHA-256:

`76942d8151422a776b752761a5cd0e4c7a75226887c3d4d753c2835e733189e5`

Rows: `234`

Decode locally without changing bytes:

```sh
base64 -d 2026-08-25_TRIGGER2_XENO_BINDING_STRUCTURAL_SEED_V0_2.jsonl.gz.b64 > seed.jsonl.gz
gzip -dc seed.jsonl.gz > seed.jsonl
sha256sum seed.jsonl.gz seed.jsonl
wc -l seed.jsonl
```

## Corrected holdout design

The parallel Trigger-2 donor seeds were useful but exposed a scientific split problem: a holdout cannot claim **unseen-permutation** transfer if every S3 permutation already appears in training.

This successor therefore uses:

- TRAIN: P0..P4 only, 120 rows, 24 per permutation;
- unseen-permutation holdout: P5 only, 24 rows;
- unseen-template holdout: frozen T5 only, 24 rows;
- unseen-vocabulary holdout: split-isolated lexical family, 24 rows;
- unseen-symbol holdout: accepted ABI atom indices 40..45 only, 18 rows;
- TRAIN atom indices: 0..39 only;
- TRAIN templates T1..T4: 30 rows each;
- TRAIN input layout: 60 codebook-first + 60 case-first;
- TRAIN class × target-atom contingency: exactly one row in each of 3 × 40 cells;
- TRAIN mutual information `I(class; target_atom) = 0.0 bits` by construction.

All six S3 permutations are still represented across the complete benchmark, while P5 remains unseen during training.

## Materialization gate

The current source surfaces used for this cycle prove a 46-atom accepted ABI but do not expose the exact accepted literal atom table. Literal outputs were therefore **not invented**.

Before any row may receive accepted-dataset credit:

1. load the exact 46 accepted literal atom lexemes from the bound Claude ABI package/manifest;
2. substitute atom-index references without changing split membership, S3 mapping or balance;
3. verify exact tokenizer single-token identity and output length;
4. rerun exact class/synonym leakage, lexical-family isolation and family/provenance ancestry split linting;
5. verify target is recomputed from the realized episode codebook;
6. send a small materialized sample through the evidence-qualified Forge/Distillery path;
7. only after that passes, consider expansion toward the larger 20k–50k corpus.

## Credit boundary

This package mints:

- accepted dataset tokens: **0**
- Qwen3.5 J-Space runtime credit: **0**
- training credit: **0**
- full HCU runtime credit: **0**
- whole EntityOS/HCU runtime credit: **0**

It is a reviewed training-data construction delta, not a trained model and not runtime acceptance.
