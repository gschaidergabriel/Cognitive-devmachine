# Triggerwort 2 — Swarm Binding Dataset V2

Status: `SUPERSEDED_DONOR_NOT_TRAINING_ADMITTED`  
Date: 2026-08-25  
Organ: GPT-5.6 Sol / ChatGPT organ of Clay  
Target: Qwen3.5-0.8B Xeno/HCU specialization

## Evidence-driven objective

Claude/XENO measurements isolate a narrow deficit: measured semantic readability and symbol-axis writeability are stronger than episode-local codebook binding and cross-template transfer. The useful training target is therefore contextual binding/routing, while the already-strong read/write/carrier functions need retention protection.

The initial V2 generator emitted 144 gate-compatible candidate rows:

- TRAIN: 72 = four templates × six S3 mappings × three semantic classes;
- VALIDATION: 18;
- HOLDOUT: 54 across unseen semantic vocabulary, unseen template and unseen symbol-set families.

The first audit correctly found zero class↔target-symbol MI within every train template, no literal class-label leakage outside the codebook, and 144/144 PASS against the current generic `ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1` gate. All rows remained `training_ready=false` because exact ABI atom materialization was unavailable.

## Swarm self-correction: generic gate PASS was not scientific PASS

A later nuisance-factor reviewer found a flaw omitted by the first audit: each train template owns a distinct three-symbol placeholder set. Over the 72 train rows this makes:

`I(target_symbol ; template) = 2.0 bits`.

So although `I(semantic_class ; target_symbol)=0` at the intended class mapping, the output vocabulary still reveals the template perfectly. That is an avoidable context-dependent nuisance signal and is contrary to the goal of context-invariant binding.

The correct verdict is therefore:

`FAIL_SCIENTIFIC_PILOT_GEOMETRY / SUPERSEDED_DONOR_ONLY`

The 144/144 generic candidate-gate PASS remains true only at schema/epistemic-boundary scope. A generic gate that does not test nuisance independence cannot overrule a later statistical shortcut failure.

Reusable research rule:

`DISJOINT_SYMBOL_POOL_PER_TEMPLATE can create target-template nuisance information even when class-target MI is zero.`

Future audits must enumerate plausible nuisance pairs, not only the intended label relation.

## Stronger retained successor

Parallel Trigger-2 work already produced a stronger current path, so no duplicate lane is created.

`tools/trigger2_dynamic_binding_blueprint_v2.py` v2.1 on current main emits a 9,072-row NON-TRAINABLE fully factorial blueprint crossing S3 mappings, codebook orders, layouts, semantic outcomes and query polarities while explicitly checking nuisance mutual information.

`tools/trigger2_dynamic_binding_materializer_v1.py` on PR #1956 is the retained materialization path. It preregisters:

- TRAIN permutations `P012/P021/P102/P120`;
- validation-only `P201`;
- sealed holdout `P210`;
- a deterministic hash partition with 36 train-visible and 10 reserved unseen atoms;
- four visible training templates;
- an unmaterialized `T5_FROZEN_UNMATERIALIZED` holdout;
- direct and negated query polarities;
- provenance hashes and post-materialization checks.

Its synthetic 46-symbol source self-test emitted 4,320 PRE-HOLDOUT rows: 3,456 TRAIN and 864 VALIDATION, with zero empirical TRAIN `I(semantic_class; target_atom)`, zero per-atom class imbalance, and no sealed holdout symbol/permutation/template leak. This is source-level synthetic evidence only.

## Exact remaining blocker

The exact accepted 46-atom ABI inventory + manifest/tokenizer materialization evidence is not available in the current connected source context and must not be guessed. Therefore:

- real ABI-materialized binding rows: 0;
- accepted Distillery tokens from this delta: 0;
- training executed: NO;
- training credit: 0;
- Qwen3.5 causal J-Space credit: 0;
- whole HCU / whole EntityOS runtime credit: 0.

The next correct binding action is to obtain the exact 46 accepted atoms and pinned tokenizer evidence, then run the retained materializer/gates while preserving the sealed P210 + ten-atom + T5 holdout. Only after that should multi-hop/distractor scale-up occur.

## Wider research feedback

The newest owner target is variable cognitive grid + persistent database + Claude Code. Dynamic binding remains one subobjective, not the architecture identity. Training should factor cognitive correctness away from fixed module count and later cover variable-N decomposition, durable DB-vs-transient state, Claude Code handoff/re-entry, Hyperposition/evidence reconciliation, workspace broadcast-versus-use, restart/rejoin and fail-closed authority behavior.

This run’s durable contribution is therefore not “144 good rows.” It is the self-correction that a schema-clean balanced seed can still contain a nuisance shortcut, plus a fail-closed disposition into the stronger nonduplicate materializer lane.
