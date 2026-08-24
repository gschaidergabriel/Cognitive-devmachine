# the artefact — EntityOS + HCU cognitive computer

`the artefact/` is the current-facing product/research workspace for **EntityOS** and its integrated **HCU** cognition/compute architecture. It is not independent authority and not a historical ledger. Re-enter verified `main`, newest owner/supervisor authority and exact runtime evidence before material work.

## Current authority — 2026-08-24

Observed supervisor epoch: **8.72**. Mode: **FREE_ONLY**.

Persistent research entity = **Clay**. Temporary workers/models/sessions are organs, not new persistent entities. Product = **EntityOS**. Integrated cognition/compute architecture = **HCU**. Xeno/XCU are compatibility/research aliases only.

Canonical durable state/evidence remains deterministic and outside model-generated cognition/simulation. HCU/J-Space/world-model/workspace outputs are candidate/projection/measurement only. `EffectGate + EffectJournal` remain the real-effect authority. `FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT`.

Current owner authority permits zero-cost development/testing on normal-user local Linux and the authorized `clay-direct-dev` VPS sandbox. Paid/subscription/unknown-cost execution, upgrades/credit purchases, Together and paid fallback remain forbidden. Provider labels alone are not economic proof; concrete credential/model/route provenance remains fail-closed. Local/VPS component execution does not automatically mint canonical, whole-product, HCU-full, J-Space-model or training credit.

## Target causal path

`Typed Entry -> route -> VerifiedEngineAdmission -> verified loader consumption -> GRID10 -> real model execution -> canonical ModelExecution -> InferenceReceipt -> Global J-Space/GWT -> TrainingTrace -> admitted causal dataset`

Pre-load hashing is not loader-consumption attestation. Logical cell count is not resident-model count or physical decode concurrency. Global J-Space/GWT remains a model-specific causal hypothesis; coherence, recurrence, self-report, consensus or output similarity alone do not prove it.

## Live Free-Swarm / Forge / Distillery frontier

The latest committed funnel observed during the 8.72 re-entry records **13,587,261 Free-Swarm tokens**, **292 machine-readable delta records**, **1 nominal Forge ACCEPT**, and **0 Distillery accepted dataset tokens**. Raw worker/token volume therefore remains secondary to executable evidence conversion.

The historical/live nominal `accepted` row is not evidence-qualified under the current exact execution-admission contract and correctly mints zero Distillery packets/tokens.

Current `main` contains the evidence-qualified Forge -> Distillery path. `tools/ingest_forge_accepts_into_distillery.py` delegates admission to the shared Forge evidence discriminator and requires `CLAY_FORGE_EXECUTION_ADMISSION/v1`, including exact source/evaluation/worker/target identities, complete command admission, isolated execution/network namespace and secret fences. A nominal `status=accepted` is insufficient.

This GO found a narrower replay boundary: prior Distillery deduplication used the SHA-256 of the complete Forge evaluation envelope. Because `evaluated_at` is volatile and candidate hypothesis/falsifier text is explicitly non-measured metadata, the same evidence-bearing execution could be re-emitted with different envelope bytes and be treated as new dataset evidence. PR **#1687** adds `CLAY_FORGE_EXECUTION_REPLAY_IDENTITY/v1` plus `CLAY_FORGE_MEASURED_EVIDENCE_IDENTITY/v1`: timestamp/narration-only replay becomes `DUPLICATE`, while the same stable execution identity with conflicting measured evidence fails closed as `REPLAY_IDENTITY_CONFLICT`. This remains source/regression-definition evidence until exact-head execution.

The exact-current successor witness in `tools/run_go871_forge_distillery_runtime_gate.py` requires:

1. exact source commit/tree/blob binding;
2. bubblewrap `--unshare-all` admission with secret fences;
3. two reproducible current-source admission-regression passes;
4. deterministic nominal-only ablation failure as the causal counterfactual;
5. rejection of a nominal ACCEPT without execution admission;
6. one evidence-qualified ACCEPT;
7. exactly one new Distillery packet;
8. `accepted_dataset_tokens > 0`;
9. identical replay adds zero packets/tokens.

The stronger successor acceptance requirement is to preserve that byte-identical replay gate and also mutate only volatile timestamp/candidate narration while keeping stable execution/measured evidence fixed; this semantic replay must add exactly zero packets/tokens.

Runtime-request PR **#1619** remains open and requests execution-time selection of canonical `main`. No repository-bound terminal Forge -> Distillery result was found on current `main` during this re-entry, so no Forge operational runtime PASS is claimed.

## Provider-independent local Qwen3-0.6B J-Space discriminator

Supervisor 8.72 prioritizes the zero-provider-billing local Qwen3-0.6B path as the highest-information model-specific J-Space discriminator.

The earlier final-norm/`lm_head`-coupled fastpath remains only a technical readout-steering positive control because its intervention direction is coupled to the same terminal output geometry being scored. It cannot establish an intermediate learned J-Space representation.

The fused current discriminator is `tools/trigger1_local_qwen06_midlayer_causal_execute.py` launched by `tools/trigger1_local_qwen06_midlayer_causal.sh`. It uses a fixed nonterminal middle decoder layer, derives its steering basis from contrastive internal activations rather than output-head rows, preserves substantive downstream transformer computation, selects gain only on calibration data, freezes that gain before disjoint holdout, and requires all six matched controls:

`BASELINE + +VECTOR + SIGN_FLIP + NULL_VECTOR + ORTHOGONAL_SAME_NORM + PERMUTED_SAME_NORM`

The retained owner-only execution definition is `.github/workflows/trigger1-v2-local-fastpath-selfhosted.yml`. Current `main` now requires `tools/trigger1_atomic_lease_gate.py` to validate a canonical atomic claim and source ancestry **before** the midlayer intervention step. A dispatch issue without exactly one canonical `trigger_key:` binding is therefore inert by design.

The earlier dispatch **#1647** was closed after re-entry because its body contained no canonical trigger key and therefore cannot satisfy the current lease gate. It remains provenance only. No successor unusual experiment may be dispatched until an already-created canonical claim can be referenced reproducibly for the exact user-triggered macrocycle.

### GO 23:33 source/regression delta

The stale `tests/test_trigger1_local_qwen_runtime_preflight_872.py` still referenced the retired `.github/workflows/trigger1-local-qwen06-runtime-proof.yml`. That regression was rebound to the retained midlayer launcher and current self-hosted workflow, including assertions for bounded low-disk negative evidence, sanitized terminal receipt persistence, and atomic-lease ordering before intervention. The fix was merged through PR **#1665**; obsolete PR **#1620**, which targeted the former heartbeat-hosted Qwen lane, was closed as superseded.

This is source/control-plane hardening only. It grants zero model-runtime, J-Space-model, HCU-full, training, whole-product or canonical-semantics credit.

### GO 23:33 active-output preservation delta

The retained midlayer launcher had a second deterministic low-disk defect: when `available_kb < 4000000`, its bounded cleanup removed `RUNNER_TEMP/clay-trigger1-v2-*`, while the active self-hosted run itself stores evidence beneath that namespace. The launcher could therefore erase its own current output directory before persisting `disk_preflight.json` or a blocked result.

PR **#1670** merged the repair as canonical `main` commit **`3363aaead6b66a29d40493557515aa2a34058303`**. The launcher now canonicalizes and binds the active `OUT_DIR`, excludes exactly that directory from stale-run cleanup, still removes stale Trigger-1 siblings, fails closed if output identity changes, and records `current_output_preserved=true` in low-disk evidence.

The exact merged launcher/test blobs (`43615073745b90f20fc900d37c8ac40a001f1003`, `26f9f100cd78aa01876ad62cef0a9af0f67921a9`) were reconstructed byte-for-byte and exercised with a deterministic fake-`df` condition at **2,500,000 KiB available**: **1/1 regression PASS**. The current evidence directory and evidence-in-progress file survived; stale V2 and legacy-Qwen siblings were removed; the blocked receipt was persisted; no model was loaded, no external LLM provider was called, and no provider credential was read.

This is **source + deterministic preflight regression evidence only**. It mints zero whole EntityOS/HCU, HCU-full, J-Space-model or training credit. This `go` had no reproducible shared macrocycle/request identity beyond minute precision, so it dispatched **zero** new unusual interventions. The next Trigger-1 action remains lease-gated; do not create a duplicate dispatch merely because the launcher is now repaired.

Receipt: `research_entity/continuity/receipts/2026-08-24_GO_872_TRIGGER1_OUTPUTDIR_PRESERVATION_GPT56SOL_2333.json`.

Until a lease-admitted successor dispatch yields a repository-bound exact-source receipt, local Qwen3-0.6B model/J-Space runtime promotion remains zero. A positive result can become a bounded internal-intervention candidate only at its exact source/model/runtime/intervention/control scope; it cannot mint canonical EntityOS/HCU, full HCU or training credit by itself.

## Typed Entry / HCU authority convergence

`BOOTSTRAP_MINIMAL.json`, `PROGRAM_STATE.json` and `SUPERVISOR_INBOX.json` are required to resolve one successor-dynamic authority surface. This GO lineage observed `BOOTSTRAP_MINIMAL.json` lagging behind `PROGRAM_STATE` and `SUPERVISOR_INBOX`; the current minimal bootstrap has since been synchronized to **8.72** and points at `SUPERVISOR_STEERING_8_72.json`.

This is a control-plane/Typed-Entry-adjacent convergence delta: it removes stale authority islands without creating a second truth/effect/admission authority. It grants no executable HCU/model credit.

The Forge -> Distillery replay hardening is also reusable Typed causal-boundary work: it separates stable evidence-bearing execution identity from volatile observation-envelope identity without creating a competing truth store or effect authority.

Retained donor lane **#1263** remains the single HCU / Typed Entry / Global J-Space donor lane. Its engine/loader work is source/donor evidence until exact admitted execution binds loader consumption, inference receipt and downstream causal traces.

## Evidence credit

Current bounded credit remains conservative:

- historical nominal Forge accepted rows: **1**;
- exact evidence-qualified Forge acceptance proven by terminal successor receipt: **pending**;
- Distillery accepted Forge packets/tokens in the last published live snapshot: **0 / 0**;
- Forge -> Distillery exact-current runtime credit: **0 pending terminal receipt**;
- provider runtime credit: **0 unless exact current authority/receipt promotes only its exact scope**;
- local Qwen3-0.6B midlayer J-Space runtime promotion: **0 pending lease-admitted terminal receipt**;
- whole EntityOS/HCU runtime credit: **0**;
- full HCU runtime credit: **0**;
- J-Space model-runtime credit: **0**;
- training credit: **0**;
- whole-product PASS: **false**.

A source file, test, workflow, deployment, provider HTTP success, token count or model consensus never automatically mints broader credit.

## Current blockers / next exact gates

1. Execute PR **#1687**'s replay-identity regression plus existing Forge -> Distillery ingest/live-bridge regressions on its exact head; fuse only if current `main` remains nonduplicate.
2. Observe a terminal repository-bound result for the open Forge -> Distillery runtime request **#1619**; require `1 qualified ACCEPT -> exactly 1 packet -> accepted_dataset_tokens > 0 -> replay delta 0` before narrowly promoting Forge/Distillery runtime evidence.
3. After replay hardening lands, strengthen the exact-current witness with a timestamp/narration-only semantic replay and require an additional packet/token delta of exactly zero.
4. If either witness fails, repair the measured isolated-executor/bridge blocker only; never weaken evidence admission.
5. For Trigger-1/J-Space, obtain a reproducible shared macrocycle identity, create the canonical atomic claim with create-only semantics, then dispatch exactly one successor issue containing that claim's `trigger_key:`. Without that chain: `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`.
6. On the lease-admitted Qwen run, persist the fused nonterminal midlayer exact-source runtime receipt and classify runner/preflight/dependency/model failure explicitly.
7. Require all six matched controls plus disjoint holdout and activation-derived nonterminal vector construction; reject terminal final-norm/`lm_head`/output-projection shortcuts as J-Space mechanism credit.
8. Continue one canonical Typed Entry -> verified loader -> actual model execution -> InferenceReceipt -> model-specific J-Space causal-control chain through donor #1263.
9. Keep external model calls secondary and behind exact FREE economic provenance. No paid/Together fallback.
10. Optimize executable delta -> evidence-qualified Forge acceptance -> Distillery admission before increasing raw swarm scale.

## Evidence discipline and reentry

For every material claim distinguish direct observation, source-derived claim, inference, generated hypothesis, counterhypothesis, intervention/test and verified scope. Negative evidence is first-class. Auth/rate/quota/runner failure is not automatically product/science failure. A component PASS is not whole-product PASS.

Before substantive continuation: refresh verified `main`; resolve newest owner/supervisor authority; inspect overlapping work; preserve exact source/runtime identities; execute the cheapest high-information discriminator; persist bounded evidence; and re-enter `main` after every material write.
