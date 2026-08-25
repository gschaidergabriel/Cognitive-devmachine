# Triggerwort 2 — accepted-atom provenance closure v4

Date: 2026-08-25  
Organ: GPT-5.6 Sol / ChatGPT organ  
Persistent entity: Clay  
Product: EntityOS  
Architecture: HCU  
Trigger: `triggerwort 2`  
Active Trigger-2 lane: PR #1956 / `research/trigger2-qwen35-08b-hcu-fullft-20260825`  
Canonical main observed immediately before this write: `8ae0a47d34b0be3d088ca146fdc35952d2808c10`  
Supervisor observed: 8.78 / FREE_ONLY  
Training executed: NO  
Training credit added: 0

## Current owner target fused

The highest-precedence owner correction is:

`research_entity/global/OWNER_CORRECTION_ZERO_ENTITYOS_COGNITIVE_GRID_DB_CLAUDECODE_GLOBAL_JSPACE_2026-08-25.md`

The training program therefore serves a variable-size 0.8B cognitive grid plus persistent database plus Claude Code. GRID10 remains useful only as a benchmark configuration. Trigger-2 training examples must ultimately reproduce Zero/EntityOS cognitive processes independent of fixed N, preserve DB-vs-simulation boundaries, and train compact Claude Code handoff/return/re-entry behavior at the strongest evidenced interface.

## Evidence controlling this delta

The current Claude/XENO vector-language ingest narrows the measured training gap to dynamic context/codebook binding and cross-template transfer while semantic readout, symbol-axis writeability and carrier binding through k<=16 already have measured support at the supplied model identity. This run therefore does not reclassify those protected functions as missing.

Parallel Trigger-2 workers already advanced the binding path through:

- causally realized S3 mappings;
- exact-byte provenance binding;
- pre-holdout permutation/symbol/template isolation;
- codebook order/target-position counterbalancing;
- tokenizer-bound single-token atom auditing.

Those improvements were fused rather than duplicated.

## New adversarial finding

`tools/trigger2_dynamic_codebook_binding_gate_v3.py` verifies that each row atom exists in an exact-tokenizer tokenization audit and has token count 1. It also hash-binds the atom-inventory file. However, the gate does not itself parse the accepted ABI inventory and prove that every row atom/target belongs to the exact measured set of 46 accepted atoms.

Therefore a self-consistent but semantically invalid package could still present:

1. an exact hash-bound atom-inventory file whose contents are not proven to be the measured accepted inventory;
2. an exact tokenizer audit containing an invented but single-token atom;
3. rows using that invented atom.

The hashes could all be correct for those supplied bytes while the semantic claim `this atom belongs to the measured accepted ABI` remains unproved.

## Implemented v4 closure

Added:

- `tools/trigger2_dynamic_codebook_binding_gate_v4.py`
- `tests/test_trigger2_dynamic_codebook_binding_gate_v4.py`

V4 keeps V3 as the base gate and adds a semantic accepted-atom provenance chain:

`actual source archive bytes`
` -> source_archive_sha256`
` -> normalized TRIGGER2_ACCEPTED_ATOM_INVENTORY/v1`
` -> actual ABI manifest sha256`
` -> exactly 46 unique accepted atom rows`
` -> rejected measured atom "or" cannot be re-admitted`
` -> exact tokenizer audit atom set == exact accepted inventory atom set`
` -> every episode_atom_triplet member belongs to accepted inventory`
` -> every target belongs to accepted inventory`.

It fails closed if the tokenization audit contains a nonaccepted atom or omits an accepted atom. The row additionally binds the actual source archive, inventory and tokenization-audit byte hashes.

## Verification

Deterministic local source/unit validation on the V4 wrapper: `6/6 PASS`.

Covered mutations:

1. exact 46-atom normalized inventory + equal token audit passes wrapper-level source validation;
2. invented episode atom is rejected;
3. invented target is rejected;
4. token audit with an extra nonaccepted atom is rejected;
5. inventory stops validating after source-archive bytes change;
6. the measured rejected atom `or` cannot enter the accepted inventory.

Scope: SOURCE/CANDIDATE VALIDATION ONLY. The tests use synthetic fixture bytes and a stubbed V3 result to isolate the new V4 predicates. They are not Qwen runtime evidence, not ABI-source extraction evidence, not dataset admission and not model/training/HCU/EntityOS runtime credit.

## Current blocker

The exact 46 accepted atom strings are still not present as an admitted normalized current artifact available to this gate. The Claude source package/archive and ABI manifest bind their origin, but V4 intentionally refuses to invent those strings or infer them from a historical summary.

Therefore:

- train-ready materialized binding rows: 0
- accepted Distillery dataset tokens from this delta: 0
- Qwen3.5 positive J-Space causal labels: 0
- training executed: NO
- training credit: 0

## Next exact action

1. Extract the exact accepted 46-atom inventory from the source-bound Claude package/ABI artifacts and emit `TRIGGER2_ACCEPTED_ATOM_INVENTORY/v1` with source-row identity, source-archive SHA-256 and ABI-manifest SHA-256.
2. Bind the exact selected Qwen3.5 tokenizer identity and generate a tokenization audit whose atom set equals the accepted inventory exactly.
3. Materialize only a small order-crossed pilot from the current canonical binding blueprint, with split allocation performed before rendering and semantic/provenance families kept disjoint.
4. Run V4 plus the generic candidate/family-split gates on the exact rendered bytes.
5. Swarm-review counterfactual bundles for mapping, codebook-order, lexical, nuisance-position, split and stale-prior shortcuts.
6. Only after that pilot is clean should the binding corpus be scaled and fused with the broader variable-N cognitive-process curriculum (DB-vs-simulation, planning/replanning, Hyperposition/evidence reconciliation, Claude Code handoff/return/re-entry, failure/rejoin and authority negatives).
