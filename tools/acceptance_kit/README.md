# Acceptance Kit

Small provider-free mechanical acceptance layer adapted from five existing research-entity patterns: preimage-bound edit scope, exact Git source identity, cross-split leakage checks, Draft 2020-12 schema validation, and receipt discipline. It is deliberately standalone: copy this directory anywhere and run `python3 run_selftest.py`.

## Components

- `preimage_guard.py` binds an existing-file proposal to the exact preimage SHA-256 and declared old-line ranges. Proposal acceptance is not repository truth or mutation authority.
- `source_identity.py` binds Git HEAD/tree, tracked diff bytes, and untracked file bytes. A clean identity is a source-state statement, not runtime evidence.
- `split_guard.py` accepts Needle-style JSONL rows with `id` plus common text fields. It rejects duplicate IDs or exact normalized text surfaces across TRAIN/VALIDATION/HOLDOUT. **PASS does not prove statistical or semantic independence and mints no training credit.** Selftest fixtures are adapted from `gschaidergabriel/oMEGAcV1`, branch `needle-tasks`, `T-0074.input.jsonl`.
- `validate.py` uses `jsonschema.Draft202012Validator` with `schemas/needle_entity_packet.schema.json` (`NEEDLE_ENTITY_PACKET/v1`) and `schemas/needle_entity_result.schema.json` (`needle-entity-result/v1`).
- `receipt.py` emits a deterministic PASS/FAIL receipt with exact command, exit code, tested blob SHA-256 values, and `runtime_credit=0` for unproven layers; nonzero unproven runtime credit is rejected.

## Mechanical acceptance

Run:

    python3 run_selftest.py

Expected: exit 0 and JSON with `"pass": true`. Every component is exercised by at least one positive and one negative test. Dependencies are Python 3, `git`, and `jsonschema`; no network or provider call is required.

Example validator calls:

    python3 validate.py packet PACKET.json
    python3 validate.py result RESULT.meta.json

Example split guard:

    python3 split_guard.py --train train.jsonl --validation validation.jsonl --holdout holdout.jsonl

Scope fence: this kit verifies bounded artifact properties only. It does not grant effect authority, canonical truth, target-runtime credit, dataset admission, model-learning credit, GWT/HCU credit, or whole-product promotion.
