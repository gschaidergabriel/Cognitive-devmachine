# the artefact — EntityOS + HCU cognitive computer

`the artefact/` is the current-facing product/research workspace for **EntityOS** and its integrated **HCU** cognition/compute architecture. It is not independent authority and not a historical ledger. Re-enter verified `main`, newest owner/supervisor authority and exact runtime evidence before material work.

## Current authority — 2026-08-25

Observed inbox-selected supervisor epoch: **8.73**. Mode: **FREE_ONLY**. `BOOTSTRAP_MINIMAL.json` is still at 8.72 on the observed `main`, so the inbox-selected `SUPERVISOR_STEERING_8_73.json` outranks that lagging mirror until the authority surfaces are synchronized.

Persistent research entity = **Clay**. Temporary workers/models/sessions are organs, not new persistent entities. Product = **EntityOS**. Integrated cognition/compute architecture = **HCU**. Xeno/XCU are compatibility/research aliases only.

Canonical durable state/evidence remains deterministic and outside model-generated cognition/simulation. HCU/J-Space/world-model/workspace outputs are candidate/projection/measurement only. `EffectGate + EffectJournal` remain the real-effect authority. `FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT`.

Current owner authority permits zero-cost development/testing on normal-user local Linux and the authorized `clay-direct-dev` VPS sandbox. Paid/subscription/unknown-cost execution, upgrades/credit purchases, Together and paid fallback remain forbidden. Provider labels alone are not economic proof; concrete credential/model/route provenance remains fail-closed. Local/VPS component execution does not automatically mint canonical, whole-product, HCU-full, J-Space-model or training credit.

## Target causal path

`Typed Entry -> route -> VerifiedEngineAdmission -> verified loader consumption -> GRID10 -> real model execution -> canonical ModelExecution -> InferenceReceipt -> Global J-Space/GWT -> TrainingTrace -> admitted causal dataset`

Pre-load hashing is not loader-consumption attestation. Logical cell count is not resident-model count or physical decode concurrency. Global J-Space/GWT remains a model-specific causal hypothesis; coherence, recurrence, self-report, consensus or output similarity alone do not prove it.

## Live Free-Swarm / Forge / Distillery frontier

The latest committed funnel observed during the preceding 8.72 re-entry records **13,587,261 Free-Swarm tokens**, **292 machine-readable delta records**, **1 nominal Forge ACCEPT**, and **0 Distillery accepted dataset tokens**. Raw worker/token volume therefore remains secondary to executable evidence conversion.

The historical/live nominal `accepted` row is not evidence-qualified under the current exact execution-admission contract and correctly mints zero Distillery packets/tokens.

Current `main` contains the evidence-qualified Forge -> Distillery path. `tools/ingest_forge_accepts_into_distillery.py` delegates admission to the shared Forge evidence discriminator and requires `CLAY_FORGE_EXECUTION_ADMISSION/v1`, including exact source/evaluation/worker/target identities, complete command admission, isolated execution/network namespace and secret fences. A nominal `status=accepted` is insufficient.

The exact-current successor witness in `tools/run_go871_forge_distillery_runtime_gate.py` requires:

1. exact source commit/tree/blob binding;
2. bubblewrap `--unshare-all` admission with secret fences;
3. two reproducible current-source admission-regression passes;
4. deterministic nominal-only ablation failure as the causal counterfactual;
5. rejection of a nominal ACCEPT without execution admission;
6. one evidence-qualified ACCEPT;
7. exactly one new Distillery packet;
8. `accepted_dataset_tokens > 0`;
9. replay adds zero packets/tokens.

Runtime-request PR **#1619** remains the retained Forge runtime lane. No repository-bound terminal Forge -> Distillery result proving the newest replay semantics has been observed, so no Forge operational runtime PASS is claimed.

### GO 01:05 replay-v2 `delta_id` closure

Supervisor 8.73 identified the correct scientific/runtime invariant: Distillery replay identity must be derived from stable measured execution evidence, not the volatile evaluation envelope. Source inspection of the just-fused replay implementation found one remaining envelope leak: `CLAY_FORGE_EXECUTION_REPLAY_IDENTITY/v1` still included `delta_id`. The existing 8.73 regression covered timestamp and candidate-narration mutation but not `delta_id`-only re-emission.

The current GO branch `gpt56sol/go873-distillery-replay-v2-20260825` therefore introduces `CLAY_FORGE_EXECUTION_REPLAY_IDENTITY/v2` with these bounded changes:

- `delta_id` is excluded from replay identity and from measured-evidence conflict identity;
- source class, provider/model/role, worker, source/evaluation heads, target blob identities, execution-admission digest, metric identity and rebase state remain bound;
- the historical v1 replay hash is retained for provenance;
- a separate v2 replay digest is stored under a unique partial index;
- v1 rows are backfilled to v2 from already-persisted `knowledge_packets.packet_text` and `metadata_json` rather than guessed;
- if historical v1 rows collapse onto the same v2 identity, migration fails closed with `REPLAY_IDENTITY_V2_MIGRATION_CONFLICT` instead of silently accepting an already-inflated dataset;
- rows too old/incomplete to reconstruct v2 are fenced conservatively by available execution coordinates, and changing `delta_id` cannot escape that unknown-state fence;
- durable packet identity now follows replay-v2 identity.

The GitHub source blob `33eae9fcdcca03f5be6b46bacfb8390297a614bd` was byte-matched to the locally compiled/tested blob. A focused deterministic harness produced **4/4 PASS** for `delta_id`-only duplicate +0, measured-evidence conflict, v1->v2 backfill, and unresolved-legacy fail-closed behavior. That harness used a stub admission discriminator, so it is **source-mechanism validation only**, not repository-bound Forge runtime evidence and not EntityOS/HCU/J-Space/training credit.

Regression source: `tests/test_forge_distillery_replay_identity_delta_id_v2_873.py`. Receipt: `research_entity/continuity/receipts/2026-08-25_GO_873_FORGE_REPLAY_DELTA_ID_V2_GPT56SOL.json`.

No unusual model experiment was executed. This user-triggered GO did not expose a shared reproducible immutable request/macrocycle identity sufficient for the canonical create-only experiment lease, therefore `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT` remains correct.

### GO 23:44 witness-to-live promotion delta

Source inspection exposed a remaining conversion gap: the exact-current successor witness proved the `1 -> 1 -> >0 -> replay +0` contract against a disposable temporary Distillery database, so a successful witness could still leave the persistent live Distillery counters unchanged.

Current `main` contains `tools/promote_forge_distillery_runtime_gate.py`. It accepts only a PASS receipt with the exact source identity and intact no-network/no-provider/no-paid fences, re-validates the nested Forge evaluation through the existing evidence discriminator, and routes exactly that one evaluation through the existing `ingest_forge_accepts_into_distillery` authority into the configured live Distillery database. It creates no second Forge ledger, truth store, effect path or model authority.

The retained workflow `.github/workflows/go871-forge-distillery-runtime-gate.yml` requires three successful stages: fail-closed promotion guards, the disposable exact-current witness, and live promotion. A first live promotion must add exactly one packet and a positive `accepted_dataset_tokens` delta; semantic replay must add zero packets and zero tokens. An already-promoted identical evaluation is accepted only as an idempotent replay with zero token delta. The sanitized repository-bound runtime result includes `live_distillery_promotion` evidence and the workflow fails unless all three stages return success.

Commits: `04f11b64e637da256b2d5a95323b40fa80be5545`, `b56767eadce2f12fe05b39176a4eef4f7a80c821`, `9b4a4166cc3d179415c6ed4962c9a7c27c66b825`. Receipt: `research_entity/continuity/receipts/2026-08-24_GO_872_FORGE_LIVE_DISTILLERY_PROMOTION_GPT56SOL_2344P0700.json`.

The previously known run **32742535392** / job **97480167751** was observed queued and predates the newer live-promotion and replay-v2 semantics. It cannot prove the current scope. No repository-bound result containing the current replay-v2 live-promotion evidence has yet been observed, so runtime credit remains zero until the current revision actually executes and persists a terminal receipt.

### GO 23:48 self-hosted execution observability delta

The long-queued self-hosted Forge witness exposed a control-plane ambiguity: dispatch/run existence cannot distinguish a healthy-but-busy runner from an unclaimed/offline execution lane. PR **#1698** merged a bounded non-experimental observer at commit **`af317c1a59411df8e92c0ba15c3b720d56d5ca55`**. `tools/go872_selfhosted_health_receipt.py` binds exact source commit/tree/dirty state plus runner/resource/tool readiness; `.github/workflows/go872-selfhosted-health-worker.yml` measures that state on `[self-hosted, Linux, X64]`; and `.github/workflows/go872-selfhosted-health-observer.yml` separates dispatch acceptance from queued/unclaimed, claimed/nonterminal and terminal outcomes while persisting zero-credit evidence. Secret values are never recorded.

At this delta's final observed boundary no terminal `CLAY_GO872_SELFHOSTED_HEALTH_OBSERVER/v1` or worker health receipt had appeared on `main`. Therefore the observability mechanism is merged while actual self-hosted health remains **runtime pending**; queued status alone is not runner failure, semantic product failure or runtime PASS. Receipt: `research_entity/continuity/receipts/2026-08-24_GO_872_SELFHOSTED_HEALTH_OBSERVABILITY_GPT56SOL_2348P0700.json`. Stale predecessor PR **#1677** was closed as superseded provenance.

## Provider-independent local Qwen3-0.6B J-Space discriminator

Supervisor 8.73 keeps the zero-provider-billing local Qwen3-0.6B path as the highest-information model-specific J-Space discriminator after the Forge/Distillery replay gate is executable-green.

The earlier final-norm/`lm_head`-coupled fastpath remains only a technical readout-steering positive control because its intervention direction is coupled to the same terminal output geometry being scored. It cannot establish an intermediate learned J-Space representation.

The retained workflow still invokes historical compatibility entrypoint `tools/trigger1_local_qwen06_midlayer_causal.sh`, but that launcher no longer executes the superseded A/B/C-labelled midlayer implementation. Its effective scientific path is now `tools/trigger1_local_qwen06_intermediate.sh` -> `tools/trigger1_local_qwen06_intermediate_execute.py` -> `tools/trigger1_intermediate_promotion_bridge.py` -> `tools/trigger1_jspace_promotion_gate.py`.

The stronger intermediate protocol derives a residual direction from semantic approve/disapprove calibration activations at predeclared nonterminal decoder layers, freezes layer/gain before holdout, and requires all six matched controls:

`BASELINE + +VECTOR + SIGN_FLIP + NULL_VECTOR + ORTHOGONAL_SAME_NORM + PERMUTED_SAME_NORM`

Scientific-independence promotion additionally requires derivation/holdout disjointness, counterbalanced output-label mappings, wrong-layer evidence and lesion/rescue. The bridge fails closed unless those facts are present in the measured intermediate result; output-head-derived or evaluation-output-label-derived steering cannot satisfy owner Trigger-1 goal credit.

The compatibility launcher uses the canonical reusable `tools/git_source_identity_v1.py` before and after delegated execution. It requires a clean precondition, compares exact source-identity digests across the run, removes intermediate/direct promotion candidates if repository bytes move, and persists pre/post identities into the historical result filename expected by the retained workflow. This strengthens source/execution provenance without creating a second scientific lane.

The retained owner-only execution definition is `.github/workflows/trigger1-v2-local-fastpath-selfhosted.yml`. Current `main` requires `tools/trigger1_atomic_lease_gate.py` to validate a canonical atomic claim and source ancestry **before** the intervention step. A dispatch issue without exactly one canonical `trigger_key:` binding is therefore inert by design.

The earlier dispatch **#1647** was closed after re-entry because its body contained no canonical trigger key and therefore cannot satisfy the current lease gate. It remains provenance only. No successor unusual experiment may be dispatched until an already-created canonical claim can be referenced reproducibly for the exact user-triggered macrocycle.

### GO 23:33 source/regression delta

The stale `tests/test_trigger1_local_qwen_runtime_preflight_872.py` still referenced the retired `.github/workflows/trigger1-local-qwen06-runtime-proof.yml`. That regression was rebound to the retained launcher and current self-hosted workflow, including assertions for bounded low-disk negative evidence, sanitized terminal receipt persistence, and atomic-lease ordering before intervention. The fix was merged through PR **#1665**; obsolete PR **#1620**, which targeted the former heartbeat-hosted Qwen lane, was closed as superseded.

This is source/control-plane hardening only. It grants zero model-runtime, J-Space-model, HCU-full, training, whole-product or canonical-semantics credit.

### GO 23:33 active-output preservation delta

The retained launcher had a second deterministic low-disk defect: when `available_kb < 4000000`, its bounded cleanup removed `RUNNER_TEMP/clay-trigger1-v2-*`, while the active self-hosted run itself stores evidence beneath that namespace. The launcher could therefore erase its own current output directory before persisting `disk_preflight.json` or a blocked result.

PR **#1670** merged the repair as canonical `main` commit **`3363aaead6b66a29d40493557515aa2a34058303`**. The launcher now canonicalizes and binds the active `OUT_DIR`, excludes exactly that directory from stale-run cleanup, still removes stale Trigger-1 siblings, fails closed if output identity changes, and records `current_output_preserved=true` in low-disk evidence.

The exact merged launcher/test blobs (`43615073745b90f20fc900d37c8ac40a001f1003`, `26f9f100cd78aa01876ad62cef0a9af0f67921a9`) were reconstructed byte-for-byte and exercised with a deterministic fake-`df` condition at **2,500,000 KiB available**: **1/1 regression PASS**. The current evidence directory and evidence-in-progress file survived; stale V2 and legacy-Qwen siblings were removed; the blocked receipt was persisted; no model was loaded, no external LLM provider was called, and no provider credential was read.

This is **source + deterministic preflight regression evidence only**. It mints zero whole EntityOS/HCU, HCU-full, J-Space-model or training credit.

### GO 23:34 strongest-intermediate routing fusion

Source review exposed a promotion mismatch: `trigger1_jspace_promotion_gate.py` v4 requires explicit vector-derivation independence and counterbalanced token-label evaluation, while the still-routed historical midlayer executor constructed its basis from A/B/C-labelled prompts and did not emit the v4 scientific-independence envelope. Current `main` already contained a stronger intermediate residual protocol and a fail-closed bridge, so the correct convergence move was fusion rather than a new implementation lane.

The retained launcher was changed to delegate to that stronger protocol and bridge while retaining its workflow-facing historical filename. `tests/test_trigger1_retained_launcher_fusion.py` locks the route, generic pre/post Git-source identity checks and removal of `trigger1_local_qwen06_midlayer_causal_execute.py` from the executable path.

No new unusual experiment was executed in that macrocycle because no reproducible shared immutable macrocycle/request identity was available beyond minute-level conversation timing. This is a durable source/control-plane/J-Space-readiness delta only and mints zero model-runtime, J-Space-model, HCU-full, training or whole-product credit.

### GO 23:33 promotion-gate metric-modality closure

The current `CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v4` previously enforced label counterbalancing only when `holdout.metric_uses_output_tokens` was the literal boolean `true`. Missing or non-boolean values could therefore evade an explicit holdout metric-modality declaration.

Current `main` requires `metric_uses_output_tokens` to be an explicit boolean. Missing/non-boolean values fail closed with `HOLDOUT_METRIC_OUTPUT_TOKEN_MODALITY_REQUIRED`; token-output metrics still require `label_mapping_counterbalanced=true`. `tests/test_trigger1_jspace_metric_modality_v4.py` locks missing, non-boolean and legitimate counterbalanced cases.

This closes a scientific-independence/evidence-typing bypass without weakening the six-control, disjoint-holdout, wrong-layer or lesion/rescue requirements. The evidence scope remains source/regression-definition only until exact-current test execution is observed; it mints zero provider runtime, whole EntityOS/HCU, HCU-full, J-Space-model or training credit.

Receipt: `research_entity/continuity/receipts/2026-08-24_GO_872_V4_METRIC_MODALITY_FAILCLOSED_GPT56SOL_2333P0700.json`.

### GO 23:48 receipt-bound derivation-independence closure

Issue **#1657** exposed a second-order scientific-evidence defect: merely hardcoding `uses_evaluation_output_labels=false` in the promotion bridge could become a stale false assertion if the upstream executor later changed. Current `main` closes that gap at the evidence boundary rather than by trusting downstream metadata.

`tools/trigger1_local_qwen06_intermediate_execute.py` emits versioned `TRIGGER1_VECTOR_DERIVATION_LABEL_INDEPENDENCE/v1` evidence after deriving the semantic approve/disapprove direction and before resolving evaluation output labels. The receipt binds the exact derivation input family and records both `evaluation_output_labels_resolved_before_derivation=false` and `uses_evaluation_output_labels=false`.

`tools/trigger1_intermediate_promotion_bridge.py` fails closed unless that upstream receipt exists, has the expected schema, matches the derivation prompt-family digest, proves output-label resolution occurred after derivation, and proves evaluation output labels were not used. The direct candidate copies the proven value and binds a digest of the upstream independence receipt instead of manufacturing the fact downstream.

`tests/test_trigger1_intermediate_bridge_gate_v4.py` locks the positive path plus missing-receipt, `true`, family-mismatch`, and post-bridge field-removal negatives. The existing bridge/gate contract fixture was also synchronized to the receipt-bound ABI. Commits include `309f17274299bdf9ab6ff8de3c881c9a1d732cea`, `537f5f6a74957573117f3f0e16bab14c02fb62a8`, `e8609e69fe8cec39e5d14774cf325ac0ec016ddc`, and `0ad125d6504fcd2d0e06514b0dfb918054190620`.

This resolves `TRIGGER1_BRIDGE_GATE_SCHEMA_SEMANTIC_MISMATCH` at source + regression-contract scope. It does not mint local-Qwen runtime, model-specific J-Space, HCU-full, training, canonical-semantics or whole-product credit.

Until a lease-admitted successor dispatch yields a repository-bound exact-source receipt, local Qwen3-0.6B model/J-Space runtime promotion remains zero. A positive result can become a bounded internal-intervention candidate only at its exact source/model/runtime/intervention/control scope; it cannot mint canonical EntityOS/HCU, full HCU or training credit by itself.

## Typed Entry / HCU authority convergence

`BOOTSTRAP_MINIMAL.json`, `PROGRAM_STATE.json` and `SUPERVISOR_INBOX.json` are required to resolve one successor-dynamic authority surface. On the current observed `main`, `SUPERVISOR_INBOX.json` selects **8.73**, while `BOOTSTRAP_MINIMAL.json` still reports **8.72**. Under the repository's authority order this is a lagging mirror, not an ambiguity that permits averaging: 8.73 governs until the lower surface is synchronized.

The replay-v2 delta also advances the Typed Entry/HCU causal-identity discipline without creating a second ingestion authority: it explicitly separates stable measured execution identity from evaluation-envelope identity and preserves fail-closed migration for older admissions.

Retained donor lane **#1263** remains the single HCU / Typed Entry / Global J-Space donor lane. Its engine/loader work is source/donor evidence until exact admitted execution binds loader consumption, inference receipt and downstream causal traces.

## Evidence credit

Current bounded credit remains conservative:

- historical nominal Forge accepted rows: **1**;
- exact evidence-qualified Forge acceptance proven by terminal replay-v2 successor receipt: **pending**;
- Distillery accepted Forge packets/tokens in the last published live snapshot: **0 / 0**;
- Forge -> Distillery exact-current runtime credit: **0 pending terminal replay-v2/live-promotion receipt**;
- provider runtime credit: **0 unless exact current authority/receipt promotes only its exact scope**;
- local Qwen3-0.6B intermediate J-Space runtime promotion: **0 pending lease-admitted terminal receipt**;
- whole EntityOS/HCU runtime credit: **0**;
- full HCU runtime credit: **0**;
- J-Space model-runtime credit: **0**;
- training credit: **0**;
- whole-product PASS: **false**.

A source file, test, workflow, deployment, provider HTTP success, token count or model consensus never automatically mints broader credit.

## Current blockers / next exact gates

1. Execute the replay-v2 regression on an admitted zero-cost **exact-source** surface and require `delta_id`/timestamp/narration-only replay to mint `0` packets and `0` dataset tokens; same replay-v2 identity plus changed measured evidence must fail closed as `REPLAY_IDENTITY_CONFLICT`.
2. Fuse the replay-v2 branch only if current `main` remains nonduplicate and the v1->v2 migration guards remain intact.
3. Execute the current Forge -> Distillery live-promotion witness on the fused source; require one evidence-qualified ACCEPT -> exactly one persistent packet -> `accepted_dataset_tokens > 0` -> semantic replay +0. The older queued run 32742535392 is insufficient for this scope.
4. If that witness or live promotion fails, repair only the measured isolated-executor/bridge/promotion blocker; never weaken evidence admission.
5. Execute the Trigger-1 v4 metric-modality, receipt-bound intermediate bridge/gate and promotion-gate regressions on exact-current source before any later J-Space promotion review.
6. For Trigger-1/J-Space, obtain a reproducible shared macrocycle identity, create the canonical atomic claim with create-only semantics, then dispatch exactly one successor issue containing that claim's `trigger_key:`. Without that chain: `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`.
7. On the lease-admitted Qwen run, persist the strongest-intermediate exact-source runtime receipt and classify runner/preflight/dependency/model failure explicitly.
8. Require all six matched controls, derivation/holdout disjointness, receipt-bound evaluation-label independence, counterbalanced label mapping, wrong-layer and lesion/rescue; reject terminal final-norm/`lm_head`/output-projection and evaluation-label-derived shortcuts as J-Space goal credit.
9. Continue one canonical Typed Entry -> verified loader -> actual model execution -> InferenceReceipt -> model-specific J-Space causal-control chain through donor #1263.
10. Keep external model calls secondary and behind exact FREE economic provenance. No paid/Together fallback.
11. Optimize executable delta -> evidence-qualified Forge acceptance -> Distillery admission before increasing raw swarm scale.

## Evidence discipline and reentry

For every material claim distinguish direct observation, source-derived claim, inference, generated hypothesis, counterhypothesis, intervention/test and verified scope. Negative evidence is first-class. Auth/rate/quota/runner failure is not automatically product/science failure. A component PASS is not whole-product PASS.

Before substantive continuation: refresh verified `main`; resolve newest owner/supervisor authority; inspect overlapping work; preserve exact source/runtime identities; execute the cheapest high-information discriminator; persist bounded evidence; and re-enter `main` after every material write.
