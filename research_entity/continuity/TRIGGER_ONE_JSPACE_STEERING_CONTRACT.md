# Trigger `1` — Intensive Global J-Space Steering Research

**Status:** CURRENT OWNER-DIRECTED RESEARCH TRIGGER  
**Scope:** exact user message `1` after whitespace normalization.  
**Product:** EntityOS. **Architecture:** HCU.

## Purpose

`1` starts the dedicated fast-convergence research branch for one goal:

> demonstrate direct, reproducible, vector-based control of an admitted FREE API model through the Global J-Space control path, or produce the highest-information executable delta toward that result.

This trigger is distinct from `go`. It does not reuse or weaken the one-unusual-experiment rule of `GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md`. The owner explicitly authorizes one `1` batch to contain **exactly 10 distinct parallel experiment lanes**.

## Required mechanism path

Research should converge on the strongest empirically supported path, currently:

`Global J-Space/control intent -> JSPACE_VECTOR_CONTROL_ABI/v1 -> model/version/layer-specific JSPACE_LATENT_BASIS_ADAPTER/v1 -> model-specific local vector -> instrumentable model runtime (native llama.cpp cvec when applicable) -> immutable execution/control receipts`.

A provider text-completion call is not direct vector steering merely because its prompt describes a vector. Model/runtime consumption of the intervention must be evidenced.

## Ten experiment lanes

Every normal `1` batch launches the following ten causally distinct lanes in parallel:

1. **runtime_surface** — identify/implement the shortest FREE instrumentable model execution surface; distinguish hosted text inference from genuine hidden-state/cvec control.
2. **adapter_identity** — bind source J-Space packet to exact model/version/tokenizer/runtime/build and `JSPACE_LATENT_BASIS_ADAPTER/v1` identity.
3. **layer_localization** — calibrate candidate intervention layer/range only on the calibration split.
4. **gain_calibration** — calibrate signed gain/alpha only on the calibration split; no holdout peeking.
5. **sign_flip_control** — require directionality against the opposite signed vector.
6. **null_control** — require exact NULL_VECTOR invariance/drift bound.
7. **orthogonal_control** — compare same-norm orthogonal direction to reject generic activation-energy effects.
8. **permuted_control** — compare same-norm permuted vector to reject coordinate-insensitive effects.
9. **seed_holdout_reproduction** — fixed seeds plus disjoint holdout; quantify reproducibility and failure rate.
10. **receipt_chain_and_delta_forge** — bind checkpoint/tokenizer/runtime/build/source/local-vector/cvec/execution identities and turn positive or negative evidence into the smallest executable repo delta.

If a lane cannot execute a real model intervention, it must return an executable discriminator/source delta or an exact blocker; architecture prose alone is not a successful lane.

## FREE research contingent

The owner authorizes this branch to consume a bounded share of the existing FREE token pool. Execution MUST continue to use the repository's typed FREE provider admission, credential+route economic provenance, pre-network revalidation and shared cross-process quota gate.

Hard boundaries remain:

- Together: forbidden.
- PAID/SUBSCRIPTION/UNKNOWN cost: forbidden.
- paid fallback, upgrade, billing activation or credit purchase: forbidden.
- no secret values in logs, receipts, commits or prompts.
- no key rotation to evade provider limits.
- a credential/model route that is not admitted FREE fails closed before model network I/O.

The launcher uses one shared `CLAY_FREE_PROVIDER_BUDGET_DB` across all ten processes so provider concurrency/cooldowns remain globally coordinated.

## Batch and experiment identity

Each launcher invocation creates one immutable `trigger1_batch_id` from UTC start time, repository head and a random invocation nonce. The manifest binds those inputs and its SHA-256.

Each of the ten lanes has immutable identity:

`sha256(trigger1_batch_id || lane_index || experiment_name || experiment_contract_sha256)`.

All lane artifacts live under one batch directory. Results are append-style artifacts; a later correction must not silently rewrite a prior positive or negative result.

## Success law

A direct steering claim requires, at minimum:

- exact model checkpoint/model-id and tokenizer identity;
- exact runtime/build identity;
- exact source `JSPACE_VECTOR_CONTROL_ABI/v1` packet identity;
- exact latent-basis adapter identity;
- exact model-specific local control-vector identity;
- exact native cvec/hook intervention identity when that mechanism is used;
- BASELINE, +VECTOR, SIGN_FLIP, exact NULL_VECTOR, orthogonal same-norm and permuted same-norm controls;
- fixed seeds;
- layer/gain calibration performed only on calibration examples;
- disjoint holdout evaluation;
- reproducible directional effect on holdout;
- execution/native-hook receipts proving the intervention was consumed by the model runtime.

Prompt-only steering, provider/model consensus, source-only tests, or synthetic executor effects do not satisfy this success law.

## Run command

Repository runtime entrypoint:

`bash tools/trigger1_jspace_research.sh`

Default behavior launches 10 parallel lanes. Runtime intensity is configurable by environment/CLI, but the launcher never disables the shared FREE_ONLY economic/quota gates.

## Required batch output

At minimum:

- `batch_manifest.json`
- one directory per lane with its immutable identity/focus;
- child Free-Swarm manifests/status/results;
- `batch_final.json` summarizing lane exit codes and evidence class;
- executable delta candidates or exact blockers from every lane.

A trigger `1` cycle is useful only when it creates a new executable discriminator, implementation/test delta, or direct steering evidence.
