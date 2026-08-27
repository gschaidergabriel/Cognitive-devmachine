# GO runner-scope / real-Qwen fusion — 2026-08-10 00:42 +07

Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Entity role: temporary Clay Research Entity worker; NOT Frank.  
Canonical parent: `RAE-8.8 / r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Fresh main observed before durable write: `0f0b70a97df71c2fbcd51c100d45df0968e473b3`  
Trigger: exact `go`  
Mission: `Frank v0.1 voll lauffähig auf Andreas PC` under Ubuntu developer-system semantics.

## Executive result

This cycle does not change ClayCode semantics and does not promote WP02/BASE. It resolves two important operational truths:

1. Frank's Hostinger lane has now produced a real Qwen3-4B Q8_0 execution receipt, so the previous `real model not yet executed` statement is superseded.
2. Clay's canonical WP02 Hostinger receipt is still absent. A bounded dual-lane PR probe showed the Clay self-hosted job remaining queued while the GitHub-hosted control was acquired but failed before visible steps/logs. The only justified runner conclusion is `NO_ACCESSIBLE_MATCHING_SELF_HOSTED_RUNNER_IN_OBSERVATION_WINDOW`, not permanent repository-scope failure.

## Fresh real-model evidence

Direct Frank receipt: `gschaidergabriel/Dr.-Unterweger:runtime/vps_integrity/real_qwen4b_shadow_latest.json`.

Exact-run evidence includes:
- self-hosted runner `clay`, host `digital-retina`, Linux x86_64, four logical CPUs;
- `ggml-org/Qwen3-4B-Instruct-2507-Q8_0-GGUF`, Q8_0;
- model SHA-256 `ae916ede1c010a26955ee8ae2e908bf8815a3f135ec860439ab924701c69d5f1`;
- pinned llama.cpp commit `936918514ce522b553c0fd80b169a6440e6096c6`;
- four-task fixed accuracy `3/4`;
- fixed cumulative latency `48356.025 ms`;
- mean decode throughput about `10.7053 tok/s`, mean prompt throughput about `39.9413 tok/s`;
- expected `read_state` tool selection and valid arguments in the tool case;
- one modular-arithmetic trajectory emitted the wrong answer with visible `CONFIDENCE=100`.

The confidently-wrong trajectory is direct counterevidence against treating verbalized confidence as calibrated correctness or as autonomous controller authority. Existing conservative V2 work correctly keeps V1 recurrence-saving claims diagnostic-only unless the controller reaches the permitted HALT condition.

No separate Qwen calibration experiment is created here because concurrent shared work already created the calibration/reseed follow-up.

## ClayCode WP02 execution state

Repeated current-main reads of `research_entity/claycode/remote_vps/LATEST_WP02_STRICT.json` returned 404 throughout this cycle. This remains `MISSING_EVIDENCE`, not parser failure and not PASS.

Current main has continued to harden the executable lane:
- V17 remains the selected declarative WP02 candidate;
- strict/interegular plus direct lookahead-boundary regressions remain required;
- Lark/interegular dependencies are run-ephemeral and identity-checked;
- hash-locked dependency material has been added;
- current-main WP06 typed-slice replay remains explicitly separate from WP02 grammar authority;
- new bounded standalone-parser and nontermination sentinels were concurrently added;
- WP14 mixed-commit receipt binding is being hardened.

These are useful test/recovery deltas, but none is a substitute for the missing remote receipt or physical Andreas target evidence.

## Exactly one bounded out-of-the-box experiment executed by this worker

Experiment: `GO-OOB-CLAY-RUNNER-SCOPE-DUAL-LANE-V1`.

Implementation:
- temporary draft PR `#45` only;
- `permissions: contents: read`;
- no checkout;
- no repository writes;
- GitHub-hosted `ubuntu-latest` control job;
- self-hosted `[self-hosted, Linux, X64]` scope-test job;
- same-repository PR guard.

Observed:
- workflow run was created, disproving `workflow never triggered` for this PR path;
- hosted-control job was acquired and completed `failure` before GitHub exposed any steps/log blob;
- selfhosted-scope-test remained `queued` across repeated observations;
- canonical WP02 remote receipt remained absent during the same observation window.

Disposition: `INFORMATIVE_BUT_SCOPE-LIMITED`.

Supported inference: GitHub did not allocate an eligible online+idle self-hosted runner to this Clay job during the observed window.

Not supported: permanent runner misconfiguration, permanent repository binding failure, parser failure, WP02 failure, or Hostinger failure as a machine.

PR #45 was closed without merge. Probe bytes remain non-canonical.

## Capability fusion

Current selected remote execution family remains Hostinger + GitHub Actions because it has demonstrated real Ubuntu/model execution and gives the best exact-environment fit. However, availability for the Clay repository is now explicitly uncertain rather than assumed.

New targeted recommendation materialized as `CAPREC-CLAY-HOSTINGER-RUNNER-SCOPE-20260810`:
- verify `gschaidergabriel/clay-global-research-entity -> Settings -> Actions -> Runners` has an online eligible runner;
- if the current Hostinger service is repository-level bound elsewhere, register a distinct Clay repository runner service on the same VPS;
- use organization-level runner/group sharing only if both repositories are actually under an organization and access policy permits it;
- preserve read-only self-hosted execution, non-persisted checkout credentials, ephemeral/hash-bound dependencies, and separate hosted receipt persistence.

Official GitHub runner documentation supports the mechanism: repository-level runners serve a single repository; organization-level runners can serve multiple authorized repositories; routing requires a matching online and idle runner, otherwise the job stays queued.

No unavailable/unauthorized alternative is selected. Existing owner-fixed provider exclusions remain preserved.

## Hypothesis / strongest counterhypothesis

H1: the immediate ClayCode execution blocker is runner visibility/allocation for the Clay repository, not a need for further language redesign.

Counterhypothesis: the Clay runner is correctly registered and the observed queue is temporary load/labels/runner-state behavior; once allocated, the current WP02 closure may still reveal an actual parser/compiler regression.

Discriminator: first persisted schema-current Hostinger receipt. If it does not materialize, inspect runner registration/status for the Clay repository before further parser changes. If it materializes, analyze component rows and repair only the smallest failing surface.

## Architecture / test / recovery consequence

Architecture delta: `NO_CHANGE` to ClayCode semantics, V17, GWT, Frank Harness, or authority model.

Operational delta:
- do not equate Hostinger machine availability in Frank with automatic Clay repository runner availability;
- make runner scope/status a first-class capability field;
- preserve queued/missing evidence separately from executable failure;
- maintain exact tested-commit/grammar/dependency bindings;
- continue fail-closed release accounting.

## Re-entry / next frontier

1. Verify or provide an eligible self-hosted runner registration visible to the Clay repository.
2. Consume `LATEST_WP02_STRICT.json` only when it actually exists and verify exact commit, V17 SHA, dependency identity/cleanup, strict/full-corpus/canonical rows, OOB and WP06 replay.
3. Repair only receipt-backed failures.
4. Then execute the physical Andreas Ubuntu BASE14 path with all ten applications, real GUI, FULL_FRANK handoff, recovery/authority checks and independent WP14.
5. In parallel but without duplicating current work, use the verified Qwen lane for conservative confidence calibration/reseed and controller evidence.

No paid/final model training was authorized or attempted. `QUEUED != EXECUTED != PASS`.
