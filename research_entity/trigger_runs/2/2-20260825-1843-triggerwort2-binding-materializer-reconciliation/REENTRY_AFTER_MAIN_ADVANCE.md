# Re-entry after main advance — nuisance-order hardening

Date: 2026-08-25 18:46 +07:00  
Organ: GPT-5.6 Sol / ChatGPT organ  
Trigger: `triggerwort 2`  
Supervisor: 8.78 / FREE_ONLY  
Training executed: NO  
Training credit added: 0

## New main evidence

After the initial run report was committed, canonical `main` advanced to:

`e80ab612cd3831ab6c5c612a8e214fb5595ab6ea`

with the research receipt:

`research_entity/global/j-space/research/2026-08-25_TRIGGER2_FACTORIAL_V3_NUISANCE_DECODER_AUDIT_GPT56SOL.json`.

That audit found a critical shortcut in a separate Trigger-2 V3 generator: its deterministic display-order shuffle seed included the hidden base semantic class. A nuisance-only lookup using visible nonsemantic factors could recover the class on `127/144 = 0.881944...` semantic rows, far above chance `1/3`.

The general rule promoted into this run is:

`RANDOM-LOOKING != INDEPENDENT`.

Independence must be established from the realized joint distribution and counterfactual crossing, not from use of a PRNG/hash.

## Materializer correction

`tools/trigger2_dynamic_binding_materializer_v1.py` was immediately hardened on the same Trigger-2 branch.

New rules:

1. for every fixed semantic family/template/atom triplet/S3 mapping, all six codebook display orders are emitted;
2. display order is therefore not chosen by a seed that contains the semantic label;
3. the audit computes a nuisance-only signature from model-visible nonsemantic factors:
   - template;
   - query polarity;
   - realized S3/permutation identity;
   - episode atom triplet;
   - codebook display order;
4. after semantic evidence is masked, the optimal nuisance-only decoder must be exactly at the three-class chance target in the deterministic synthetic design;
5. class-conditional display-order distributions must be identical;
6. class-symbol MI, held-out permutation/symbol/template isolation and exact provenance binding remain required.

Current hardened branch commit:

`34c49b3830e09ea0d0de97883c3d650fd0a38b52`

Current hardened blob SHA:

`4b0146df8eebed26c87fe45d0d8e369148e2cdeb`

## Deterministic synthetic design census after hardening

With one synthetic TRAIN semantic family, one ancestry-disjoint synthetic VALIDATION family and a 46-surface synthetic atom inventory, the fully crossed design has:

- total PRE-HOLDOUT candidate rows: `25,920`;
- TRAIN rows: `20,736`;
- VALIDATION rows: `5,184`;
- display orders per fixed codebook mapping: `6`;
- train-visible atom identities: `36`;
- reserved unseen atom identities: `10`;
- TRAIN S3: `P012/P021/P102/P120`;
- validation-only S3: `P201`;
- frozen holdout S3: `P210`;
- frozen template body: `T5_FROZEN_UNMATERIALIZED`;
- deterministic TRAIN `I(semantic_class; target_atom) = 0.0 bits` by construction;
- exact class-conditional display-order distribution equality by construction;
- nuisance-only optimal decoder target: `1/3` because every nuisance signature is crossed over all three semantic targets.

This census is deterministic source-design evidence only. It is not a model run, not an ABI-token materialization, not a Distillery admission, and not a training result.

## Remaining gate

Do not emit real training rows until the exact measured 46-atom ABI inventory + manifest bytes and exact tokenizer/model identities are available. Once available:

1. materialize only TRAIN + VALIDATION pre-holdout rows;
2. run the materializer audit;
3. run `tools/trigger2_dynamic_codebook_binding_gate_v2.py` with exact provenance inputs;
4. add an independent nuisance-only challenger and semantic-content ablation over the materialized row projection;
5. keep `P210`, the ten hash-partitioned atoms, the T5 body and holdout lexical ancestry sealed;
6. only after these gates scale to multi-hop/distractor families and integrate the family into the variable-N Zero/EntityOS cognition curriculum.

## Credit boundary

- research negative delta: 1;
- materializer hardening delta: 1;
- real ABI-materialized rows: 0;
- accepted Distillery tokens: 0;
- training executed: NO;
- training credit: 0;
- Qwen3.5 J-Space runtime credit: 0;
- whole HCU runtime credit: 0;
- whole EntityOS runtime credit: 0.
